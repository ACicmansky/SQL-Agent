from typing import List, TypedDict

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from config import LLM_MODEL, MAX_RETRIES, MAX_CONVERSATION_HISTORY 
from src.tools.sql_tool import SqlTool

from .prompts import (
    answer_prompt,
    sql_correction_system_prompt,
    sql_human_prompt,
    sql_system_prompt,
)


class AgentState(TypedDict):
    """Defines the state of the agent."""

    question: str
    chat_history: List[BaseMessage]
    sql_query: str
    sql_result: str
    answer: str
    error: str | None
    retries: int


class AgentNodes:
    """Defines LangGraph nodes of the agent."""

    def __init__(self, sql_tool: SqlTool, llm: ChatOpenAI, db_schema: str):
        self.sql_tool = sql_tool
        self.llm = llm
        self.db_schema = db_schema

    def __get_history(self, history: List[BaseMessage]) -> str:
        return "\n".join([f"{msg.type}: {msg.content}" for msg in history[-MAX_CONVERSATION_HISTORY:]])

    def generate_sql(self, state: AgentState) -> AgentState:
        print("Node: generate_sql")
        question = state["question"]
        retries = state.get("retries", 0)

        if retries > 0:
            print(f"Correction attempt: {retries}")
            error = state["error"]
            previous_sql_query = state["sql_query"]
            correction_prompt = sql_correction_system_prompt(
                question, previous_sql_query, error, self.db_schema
            )
            prompt = [SystemMessage(content=correction_prompt)]
        else:
            # First attempt
            prompt = [
                SystemMessage(content=sql_system_prompt(self.db_schema)),
                HumanMessage(content=sql_human_prompt(question)),
            ]
        response = self.llm.invoke(prompt)
        sql_query = response.content.strip().replace("```sql", "").replace("```", "")
        return {"sql_query": sql_query, "retries": retries}

    def execute_sql(self, state: AgentState) -> AgentState:
        print("Node: execute_sql")
        query = state["sql_query"]
        result = self.sql_tool.execute_query(query)
        print(f"Query result: {result}")

        if "Error" in result:
            return {"error": result, "retries": state.get("retries", 0) + 1}
        else:
            return {"sql_result": result, "error": None}

    def generate_answer(self, state: AgentState) -> AgentState:
        print("Node: generate_answer")
        question = state["question"]
        sql_result = state["sql_result"]
        response = self.llm.invoke([HumanMessage(content=answer_prompt(question, sql_result))])
        return {"answer": response.content}

    def handle_failure(self, state: AgentState) -> AgentState:
        print("Node: handle_failure")
        error = state["error"]
        answer = f"""I'm sorry, but I was unable to answer your question.
        After several attempts, I encountered the following error:
        {error}
        Please try rephrasing your question."""
        return {"answer": answer}
        

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
    else:
        print("SQL execution successful. Routing to generate_answer.")
        return "generate_answer"


def build_agent_graph(df: pd.DataFrame, db_schema: str, table_name: str) -> StateGraph[AgentState]:
    """Builds and compiles the LangGraph agent."""
    llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0)
    sql_tool = SqlTool(df, table_name)
    nodes = AgentNodes(sql_tool, llm, db_schema)

    workflow = StateGraph(AgentState)
    workflow.add_node("generate_sql", nodes.generate_sql)
    workflow.add_node("execute_sql", nodes.execute_sql)
    workflow.add_node("generate_answer", nodes.generate_answer)
    workflow.add_node("handle_failure", nodes.handle_failure)

    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("generate_answer", END)
    workflow.add_edge("handle_failure", END)

    workflow.add_conditional_edges(
        "execute_sql",
        route_after_sql_execution,
        {
            "generate_sql": "generate_sql",
            "generate_answer": "generate_answer",
            "handle_failure": "handle_failure"
        }
    )
    
    return workflow.compile()
