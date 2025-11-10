import pandas as pd
import pandasql as ps
import re
from typing import Union

from config import MAX_ROWS


class SqlTool:
    """Tool for executing SQL queries on pandas DataFrames."""

    def __init__(self, df: pd.DataFrame, table_name: str):
        self.df = df
        self.table_name = table_name

    def __sanitize_query(self, query: str) -> str:
        """Performs security checks and adds a LIMIT clause to the SQL query."""
        # 1. Check for dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if re.search(r'\b' + keyword + r'\b', query, re.IGNORECASE):
                raise ValueError(f"Dangerous SQL keyword '{keyword}' detected. Only SELECT statements are allowed.")
        
        # 2. Enforce SELECT
        if not re.search(r'^\s*SELECT', query, re.IGNORECASE):
            raise ValueError("Query does not start with SELECT. Only read-only queries are allowed.")
        
        # 3. Add a LIMIT clause
        if not re.search(r'\bLIMIT\b', query, re.IGNORECASE):
            query = query.strip()
            if query.endswith(';'):
                query = query[:-1]
            query += f" LIMIT {MAX_ROWS}"

        return query

    def execute_query(self, query: str) -> Union[pd.DataFrame, str]:
        """
        Sanitizes and executes the SQL query, returning a DataFrame on success
        or an error string on failure.
        """
        print(f"Original query: {query}")
        try:
            safe_query = self.__sanitize_query(query)
            print(f"Sanitized query: {safe_query}")
        except ValueError as e:
            error_message = f"Error: Invalid query. {e}"
            print(error_message)
            return error_message

        env = {self.table_name: self.df}
        try:
            result_df = ps.sqldf(safe_query, env)
            return result_df
        except Exception as e:
            error_message = f"Error: Could not execute the query. Reason: {e}"
            print(error_message)
            return error_message
