def chart_details_prompt(question: str, df_head_markdown: str, column_list: list[str]) -> str:
    return f"""
    You are an expert data visualization assistant. Your task is to determine the best chart to create based
    on a user's question and a sample of the data.

    User Question: "{question}"

    Data Sample (in Markdown format):
    {df_head_markdown}

    Columns available: {column_list}

    Based on this, provide the details for a chart that would best answer the user's question.

    **Crucial Instructions:**
    1.  You **must** choose the `x_column` and `y_column` from the exact strings in the 'Columns available'
    list. Do not infer or change column names.
    2.  For a pie chart, the `x_column` should be the categorical label and the `y_column` should be
    the numerical value.
    """
