import pandas as pd
import pandasql as ps


class SqlTool:
    """Tool for executing SQL queries on pandas DataFrames."""

    def __init__(self, df: pd.DataFrame, table_name: str):
        self.df = df
        self.table_name = table_name

    def execute_query(self, query: str) -> str:
        """Execute a SQL query using pandasql and returns a formatted string."""
        print(f"Executing query: {query}")
        env = {self.table_name: self.df}
        try:
            result = ps.sqldf(query, env)
            return result.to_markdown(index=False)
        except Exception as e:
            print(f"Error executing query: {e}")
            return str(e)
