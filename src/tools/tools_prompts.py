def chart_details_prompt(question: str, df_head: str, df_columns: str) -> str:
    return f"""
    Given the user's question and the following data, determine the best way to visualize it.

    User Question: "{question}"

    Data Sample (first 5 rows):
    {df_head}

    Columns available: {df_columns}

    Based on this, provide the details for a chart that would best answer the user's question.
    """
    