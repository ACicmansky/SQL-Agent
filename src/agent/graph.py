from typing import TypedDict

import pandas as pd
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from config import LLM_MODEL, MAX_CONVERSATION_HISTORY, MAX_RETRIES
from src.tools.sql_tool import SqlTool
from src.tools.visualization_tool import VisualizationTool

from .agent_prompts import (
    answer_prompt,
    route_question_system_prompt,
    sql_correction_system_prompt,
    sql_system_prompt,
)


class AgentState(TypedDict):
    """Defines the state of the agent."""

    question: str
    chat_history: list[BaseMessage]
    intent: str
    sql_query: str
    dataframe_result: pd.DataFrame | None
    final_answer: str
    chart_image_path: str | None
    error: str | None
    retries: int


class RouterQuery(BaseModel):
    """Routes user query to the appropriate tool."""

    intent: str = Field(..., description="The tool to use, either 'query_database' or 'visualize_data'.")


class AgentNodes:
    """Defines LangGraph nodes of the agent."""

    def __init__(self, sql_tool: SqlTool, vis_tool: VisualizationTool, llm: ChatOpenAI, db_schema: str):
        self.sql_tool = sql_tool
        self.vis_tool = vis_tool
        self.llm = llm
        self.router_llm = llm.with_structured_output(RouterQuery)
        self.db_schema = db_schema

    def __get_history(self, history: list[BaseMessage]) -> str:
        return "\n".join([f"{msg.type}: {msg.content}" for msg in history[-MAX_CONVERSATION_HISTORY:]])

    def route_question(self, state: AgentState) -> AgentState:
        print("Node: route_question")
        history_with_question = state["chat_history"] + [HumanMessage(content=state["question"])]

        route = self.router_llm.invoke(
            [
                SystemMessage(
                    content=route_question_system_prompt(
                        self.__get_history(history_with_question), state["question"]
                    )
                )
            ]
        )
        print(f"Router decided intent: {route.intent}")
        return {"intent": route.intent, "retries": 0}

    def generate_sql(self, state: AgentState):
        print("Node: generate_sql")
        history_with_question = state["chat_history"] + [HumanMessage(content=state["question"])]

        retries = state.get("retries", 0)

        if retries > 0:
            print(f"Correction attempt: {retries}")
            prompt = sql_correction_system_prompt(
                state["question"],
                state["sql_query"],
                state["error"],
                self.__get_history(history_with_question),
                self.db_schema,
            )
        else:
            prompt = sql_system_prompt(
                state["question"], self.__get_history(history_with_question), self.db_schema
            )

        response = self.llm.invoke([SystemMessage(content=prompt)])
        sql_query = response.content.strip().replace("```sql", "").replace("```", "")
        return {"sql_query": sql_query}

    def execute_sql(self, state: AgentState) -> AgentState:
        print("Node: execute_sql")
        query = state["sql_query"]
        result = self.sql_tool.execute_query(query)
        if isinstance(result, str):
            return {"error": result, "retries": state.get("retries", 0) + 1}
        return {"dataframe_result": result, "error": None}

    def execute_visualization(self, state: AgentState) -> AgentState:
        print("Node: execute_visualization")
        df = state["dataframe_result"]
        if df is None or df.empty:
            return {"error_message": "Cannot create a visualization from empty or invalid data."}

        path = self.vis_tool.generate_chart(df, state["question"])
        if "Error:" in path:
            return {"error_message": path}
        return {"chart_image_path": path}

    def generate_answer(self, state: AgentState):
        print("Node: generate_answer")
        history_with_question = state["chat_history"] + [HumanMessage(content=state["question"])]
        df = state["dataframe_result"]
        table_string = df.to_string(index=False) if df is not None and not df.empty else "No data available."

        response = self.llm.invoke(
            [
                SystemMessage(
                    content=answer_prompt(
                        state["question"],
                        table_string,
                        self.__get_history(history_with_question),
                        state.get("chart_image_path") is not None,
                    )
                )
            ]
        )
        return {"final_answer": response.content}

    def handle_failure(self, state: AgentState) -> AgentState:
        print("Node: handle_failure")
        error = state["error"]
        answer = f"""I'm sorry, but I was unable to answer your question.
        After several attempts, I encountered the following error:
        {error}
        Please try rephrasing your question."""
        return {"final_answer": answer}

    def update_chat_history(self, state: AgentState):
        print("Node: update_chat_history")
        chat_history = state["chat_history"]
        chat_history.append(HumanMessage(content=state["question"]))
        assistant_message = state["final_answer"]
        chat_history.append(AIMessage(content=assistant_message))
        return {"chat_history": chat_history}


def route_after_sql_execution(state: AgentState) -> str:
    """Routes to the correct node based on SQL execution result."""
    print("Node: route_after_sql_execution")
    if state.get("error"):
        if state.get("retries", 0) >= MAX_RETRIES:
            print("Max retries reached. Routing to handle_failure.")
            return "handle_failure"
        else:
            print("SQL error detected. Routing back to generate_sql for correction.")
            return "generate_sql"

    if state.get("intent") == "visualize_data":
        return "execute_visualization"
    return "generate_answer"


def build_agent_graph(df: pd.DataFrame, db_schema: str, table_name: str) -> StateGraph[AgentState]:
    """Builds and compiles the LangGraph agent."""
    llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0)
    sql_tool = SqlTool(df, table_name)
    vis_tool = VisualizationTool()
    nodes = AgentNodes(sql_tool, vis_tool, llm, db_schema)

    workflow = StateGraph(AgentState)
    workflow.add_node("route_question", nodes.route_question)
    workflow.add_node("generate_sql", nodes.generate_sql)
    workflow.add_node("execute_sql", nodes.execute_sql)
    workflow.add_node("execute_visualization", nodes.execute_visualization)
    workflow.add_node("generate_answer", nodes.generate_answer)
    workflow.add_node("handle_failure", nodes.handle_failure)
    workflow.add_node("update_chat_history", nodes.update_chat_history)

    workflow.set_entry_point("route_question")

    workflow.add_conditional_edges(
        "route_question",
        lambda s: s["intent"],
        {"query_database": "generate_sql", "visualize_data": "generate_sql"},
    )

    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_conditional_edges("execute_sql", route_after_sql_execution)
    workflow.add_edge("execute_visualization", "generate_answer")
    workflow.add_edge("generate_answer", "update_chat_history")
    workflow.add_edge("handle_failure", "update_chat_history")
    workflow.add_edge("update_chat_history", END)

    chat_graph = workflow.compile()

    print(chat_graph.get_graph().draw_mermaid())

    return chat_graph
