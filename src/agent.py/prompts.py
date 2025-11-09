def generate_sql_system_prompt(table_name: str, db_schema: str) -> str:
    return f"""You are an expert SQL developer. Write a single, valid SQL SELECT query
    to answer the user's question based on the provided schema.
    The table is named '{table_name}'.

    - Write only SELECT query.
    - Only output the SQL query. Do not add explanations or markdown.
    - Dates are stored in a format compatible with SQL date functions.

    Schema:
    {db_schema}"""


def generate_sql_human_prompt(question: str) -> str:
    return f"""User question: {question}"""


def generate_answer_prompt(question: str, sql_result: str) -> str:
    return f"""A user asked: '{question}'.
    A SQL query returned:\n\n{sql_result}\n\n
    Provide a clear, natural language answer based on these results."""


def generate_answer_error_prompt(question: str, sql_result: str) -> str:
    return f"""An error occurred executing a SQL query for the question '{question}':\n{sql_result}\n\n
    Explain the error to the user and suggest a fix."""
