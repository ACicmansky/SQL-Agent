import pandas as pd
import pandasql as ps

from config import MAX_OUTPUT_ROWS


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
            result_len = len(result)
            if result_len > MAX_OUTPUT_ROWS:
                # Result is too large, return summary
                summary = f"""
                The query returned {result_len} rows, which is too large to display.
                Here are the first {MAX_OUTPUT_ROWS} rows:

                {result.head(MAX_OUTPUT_ROWS).to_string(index=False)}

                Here is a statistical summary of the numeric columns:

                {result.describe().to_string()}
                """
                return summary
            else:
                return result.to_string(index=False)
        except Exception as e:
            print(f"Error executing query: {e}")
            return str(e)
