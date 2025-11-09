import pandas as pd
import pandasql as ps

class SqlTool:
    """Tool for executing SQL queries on pandas DataFrames."""
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def execute_query(self, query: str) -> str:
        """Execute a SQL query using pandasql and returns a formatted string."""
        print(f"Executing query: {query}")
        env = {self.df: self.df.name}
        try:
            result = ps.sqldf(query, env)
            return result.to_markdown(index=False)
        except Exception as e:
            print(f"Error executing query: {e}")
            return str(e)