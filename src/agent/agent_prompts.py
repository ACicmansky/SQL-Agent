def sql_system_prompt(question: str, chat_history: str, db_schema: str) -> str:
    return f"""You are an expert SQL developer. Based on the user's question and conversation history, write
    a single, valid SQLite SQL query.

    User Question: {question}

    Conversation History:
    {chat_history}

    Schema:
    {db_schema}

    - Write only SELECT query.
    - Only output the SQL query. Do not add explanations or markdown.
    """


def sql_correction_system_prompt(
    question: str, previous_sql_query: str, error: str, chat_history: str, db_schema: str
) -> str:
    return f"""
    You are an expert SQL developer. You previously attempted to write a SQL query which failed.

    Conversation History:
    {chat_history}

    Original user question: "{question}"
    Previous failed query:
    {previous_sql_query}
    Error message:
    {error}

    Carefully analyze the error and your previous query.
    Then write a corrected SQLite SQL query to answer the user's question.

    - Write only SELECT query.
    - Only output the SQL query. Do not add explanations or markdown.
    - Dates are stored in a format compatible with SQL date functions.

    Schema:
    {db_schema}"""


def answer_prompt(question: str, table_string: str, chat_history: str, exist_chart_image: bool) -> str:
    return f"""
    You are an AI assistant. Based on the user's question, the conversation history, and the results of the
    tools you used, provide a final, comprehensive answer.

    Conversation History:
    {chat_history}

    User Question: {question}

    Tool Results:
    - Data Table:
    {table_string}

    - Visualization:
    {'A chart has been created and is available.' if exist_chart_image else 'No chart was created.'}

    Summarize the findings and answer the user's question in a clear, natural language.
    """


def route_question_system_prompt(chat_history: str, question: str) -> str:
    return f"""
    Based on the user's question and the conversation history, decide whether to query the database for data
    or to create a visualization.

    Conversation History:
    {chat_history}

    User Question: {question}

    If the user is asking for a table, numbers, or specific data points, choose 'query_database'.
    If the user explicitly asks for a 'chart', 'plot', 'graph', or 'visualization', choose 'visualize_data'.
    """
