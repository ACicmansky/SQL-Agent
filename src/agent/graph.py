from typing import TypedDict

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from src.tools.sql_tool import SqlTool

from .prompts import (
    generate_answer_error_prompt,
    generate_answer_prompt,
    generate_sql_human_prompt,
    generate_sql_system_prompt,
)


class AgentState(TypedDict):
    """Defines the state of the agent."""

    question: str
    sql_query: str
    sql_result: str
    answer: str


class AgentNodes:
    """Defines LangGraph nodes of the agent."""

    def __init__(self, sql_tool: SqlTool, llm: ChatOpenAI, db_schema: str):
        self.sql_tool = sql_tool
        self.llm = llm
        self.db_schema = db_schema

    def generate_sql(self, state: AgentState) -> AgentState:
        print(f"Node: {self.generate_sql.__name__}")
        question = state["question"]
        prompt = [
            SystemMessage(content=generate_sql_system_prompt(self.db_schema)),
            HumanMessage(content=generate_sql_human_prompt(question)),
        ]
        response = self.llm.invoke(prompt)
        sql_query = response.content.strip().replace("```sql", "").replace("```", "")
        return {"sql_query": sql_query}

    def execute_sql(self, state: AgentState) -> AgentState:
        print(f"Node: {self.execute_sql.__name__}")
        query = state["sql_query"]
        result = self.sql_tool.execute_query(query)
        print(f"Query result: {result}")
        return {"sql_result": result}

    def generate_answer(self, state: AgentState) -> AgentState:
        print(f"Node: {self.generate_answer.__name__}")
        question = state["question"]
        sql_result = state["sql_result"]
        if "Error:" in sql_result:
            prompt = generate_answer_error_prompt(question, sql_result)
        else:
            prompt = generate_answer_prompt(question, sql_result)
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {"answer": str(response.content)}


def build_agent_graph(df: pd.DataFrame, db_schema: str, table_name: str) -> StateGraph[AgentState]:
    """Builds and compiles the LangGraph agent."""
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    sql_tool = SqlTool(df, table_name)
    nodes = AgentNodes(sql_tool, llm, db_schema)

    workflow = StateGraph(AgentState)
    workflow.add_node("generate_sql", nodes.generate_sql)
    workflow.add_node("execute_sql", nodes.execute_sql)
    workflow.add_node("generate_answer", nodes.generate_answer)

    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "generate_answer")
    workflow.add_edge("generate_answer", END)
    return workflow.compile()
