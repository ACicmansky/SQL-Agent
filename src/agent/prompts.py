def sql_system_prompt(db_schema: str) -> str:
    return f"""You are an expert SQL developer. Write a single, valid SQL SELECT query
    to answer the user's question based on the provided schema.

    - Write only SELECT query.
    - Only output the SQL query. Do not add explanations or markdown.
    - Dates are stored in a format compatible with SQL date functions.

    Schema:
    {db_schema}"""


def sql_human_prompt(question: str) -> str:
    return f"""User question: {question}"""


def answer_prompt(question: str, sql_result: str) -> str:
    return f"""A user asked: '{question}'.
    A SQL query returned:\n\n{sql_result}\n\n
    Provide a clear, natural language answer based on these results with exact numbers."""


def sql_correction_system_prompt(question: str, previous_sql_query: str, error: str, db_schema: str) -> str:
    return f"""
    You are an expert SQL developer. You previously attempted to write a SQL query which failed.
    Original user question: "{question}"
    Previous failed query:
    {previous_sql_query}
    Error message:
    {error}

    Please analyze the error and the original query.
    Then write a corrected SQL query to answer the user's question.

    - Write only SELECT query.
    - Only output the SQL query. Do not add explanations or markdown.
    - Dates are stored in a format compatible with SQL date functions.

    Schema:
    {db_schema}"""
