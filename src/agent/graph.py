from typing import TypedDict

import pandas as pd
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from config import LLM_MODEL, MAX_CONVERSATION_HISTORY, MAX_RETRIES
from src.tools.sql_tool import SqlTool
from src.tools.visualization_tool import VisualizationTool

from .agent_prompts import (
    final_answer_synthesis_prompt,
    planner_system_prompt,
    step_sql_generation_prompt,
)


class AgentState(TypedDict):
    """Defines the state of the agent."""

    question: str
    chat_history: list[BaseMessage]
    dataframe_result: pd.DataFrame | None
    final_answer: str
    chart_image_path: str | None
    error: str | None
    retries: int
    plan: list[str]
    current_step: int
    step_results: list[str]


class AgentNodes:
    """Defines LangGraph nodes of the agent."""

    def __init__(self, sql_tool: SqlTool, vis_tool: VisualizationTool, llm: ChatOpenAI, db_schema: str):
        self.sql_tool = sql_tool
        self.vis_tool = vis_tool
        self.llm = llm
        self.db_schema = db_schema

    def _get_history(self, history: list[BaseMessage]) -> str:
        return "\n".join([f"{msg.type}: {msg.content}" for msg in history[-MAX_CONVERSATION_HISTORY:]])

    def planner(self, state: AgentState):
        print("Node: planner")
        prompt = planner_system_prompt(
            state["question"], self._get_history(state["chat_history"]), self.db_schema
        )
        response = self.llm.invoke([SystemMessage(content=prompt)])
        # Parse the numbered list from response into a Python list
        plan = [step.strip() for step in response.content.split("\n") if step.strip() and step[0].isdigit()]
        print(f"Generated Plan:\n{plan}")
        return {"plan": plan, "current_step": 0, "step_results": []}

    def execute_step(self, state: AgentState):
        print(f"Node: execute_step (Step {state['current_step'] + 1})")
        plan = state["plan"]
        current_step_index = state["current_step"]
        step_instruction = plan[current_step_index]

        # Check if this is a final synthesis/visualization step that doesn't need SQL
        if any(
            keyword in step_instruction.lower()
            for keyword in ["synthesize", "chart", "visualize", "plot", "draw"]
        ):
            print("Step is for synthesis/visualization, skipping SQL execution.")
            return {"current_step": current_step_index + 1}

        previous_results_str = "\n".join(state["step_results"])
        sql_prompt = step_sql_generation_prompt(step_instruction, previous_results_str, self.db_schema)

        retries = 0
        while retries <= MAX_RETRIES:
            sql_query = (
                self.llm.invoke([SystemMessage(content=sql_prompt)])
                .content.strip()
                .replace("```sql", "")
                .replace("```", "")
            )
            result = self.sql_tool.execute_query(sql_query)

            if isinstance(result, pd.DataFrame):
                step_results = state["step_results"] + [result.to_markdown(index=False)]
                return {
                    "step_results": step_results,
                    "current_step": current_step_index + 1,
                    "dataframe_result": result,
                }
            else:
                retries += 1
                print(f"SQL execution failed. Attempt {retries}/{MAX_RETRIES}. Error: {result}")
                sql_prompt = step_sql_generation_prompt(
                    f"""FAILED ATTEMPT. The previous query '{sql_query}' failed with the error: {result}.
                    Please fix it. Original instruction: {step_instruction}""",
                    previous_results_str,
                    self.db_schema,
                )

        return {"error": f"Failed to execute step '{step_instruction}' after {MAX_RETRIES} attempts."}

    def generate_final_answer(self, state: AgentState):
        print("Node: generate_final_answer")
        if any(
            keyword in state["plan"][-2].lower() or keyword in state["plan"][-1].lower()
            for keyword in ["chart", "visualize", "plot", "draw"]
        ):
            print("Visualization requested.")
            df_for_viz = state.get("dataframe_result")
            if df_for_viz is not None and not df_for_viz.empty:
                path = self.vis_tool.generate_chart(df_for_viz, state["question"])
                if "Error:" in path:
                    return {"error": path}
                state["chart_image_path"] = path
            else:
                print("Warning: Visualization requested but no data is available.")

        prompt = final_answer_synthesis_prompt(state["question"], state["plan"], state["step_results"])
        response = self.llm.invoke([SystemMessage(content=prompt)])
        return {"final_answer": response.content, "chart_image_path": state.get("chart_image_path")}

    def handle_failure(self, state: AgentState):
        print("Node: handle_failure")
        error = state["error"]
        answer = f"I'm sorry, but I was unable to complete the plan. I encountered an error:\n`{error}`"
        return {"final_answer": answer}

    def update_chat_history(self, state: AgentState):
        print("Node: update_chat_history")
        chat_history = state["chat_history"]
        chat_history.append(HumanMessage(content=state["question"]))
        chat_history.append(AIMessage(content=state["final_answer"]))
        return {"chat_history": chat_history}


def route_plan(state: AgentState):
    """Routes the agent based on the plan."""
    if state.get("error"):
        return "handle_failure"

    current_step = state.get("current_step", 0)
    plan_length = len(state.get("plan", []))

    if current_step >= plan_length:
        print("Plan complete. Routing to generate_final_answer.")
        return "generate_final_answer"
    else:
        print(f"Plan not complete. Routing to execute_step {current_step + 1}.")
        return "execute_step"


def build_agent_graph(df: pd.DataFrame, db_schema: str, table_name: str):
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    sql_tool = SqlTool(df, table_name)
    vis_tool = VisualizationTool()
    nodes = AgentNodes(sql_tool, vis_tool, llm, db_schema)

    workflow = StateGraph(AgentState)
    workflow.add_node("planner", nodes.planner)
    workflow.add_node("execute_step", nodes.execute_step)
    workflow.add_node("generate_final_answer", nodes.generate_final_answer)
    workflow.add_node("handle_failure", nodes.handle_failure)
    workflow.add_node("update_chat_history", nodes.update_chat_history)

    workflow.set_entry_point("planner")
    workflow.add_conditional_edges("planner", route_plan)
    workflow.add_conditional_edges("execute_step", route_plan)
    workflow.add_edge("generate_final_answer", "update_chat_history")
    workflow.add_edge("handle_failure", "update_chat_history")
    workflow.add_edge("update_chat_history", END)

    return workflow.compile()
