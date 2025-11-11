def planner_system_prompt(question: str, chat_history: str, db_schema: str) -> str:
    return f"""
    You are an expert AI data analyst. Your task is to devise a step-by-step plan to answer a user's question
    based on a database schema and conversation history.

    **User Question:** "{question}"

    **Conversation History:**
    {chat_history}

    **Database Schema:**
    {db_schema}

    **Instructions:**
    1.  Analyze the user's question.
    2.  If the question is simple and can be answered with a single SQL query, create a one-step plan.
    3.  If the question is complex and requires multiple steps (e.g., finding top items first, then getting
    details), break it down into a logical sequence of simple steps.
    4.  Each step in your plan should be a clear, concise instruction for a data analyst to follow.
    5.  The final step should often be to "Synthesize the results and answer the user's question", optionally
    mentioning if a visualization is appropriate.
    6.  Output the plan as a numbered list. Do not write any other text or explanation.

    **Example for a complex question:**
    User Question: "Chart the monthly transaction value for the top 2 business transaction types."

    **Your Output Plan:**
    1. Find the top 2 "Bus. Transac. Type" by total "Transaction Value".
    2. For those top 2 transaction types, retrieve their total "Transaction Value" for each month using the
    "Clearing Date".
    3. Create a line chart showing the monthly transaction value for the top 2 business transaction types and
    synthesize the results to answer the user's question.
    """


def step_sql_generation_prompt(plan_step: str, previous_steps_results: str, db_schema: str) -> str:
    return f"""
    You are an expert SQL developer. Your task is to write a single SQLite SQL query to execute a specific
    step of a data analysis plan.

    **Current Step Instruction:** "{plan_step}"

    **Results from Previous Steps (if any):**
    {previous_steps_results if previous_steps_results else "This is the first step."}

    **Database Schema:**
    {db_schema}

    **Instructions:**
    - Write a single, valid SQLite SQL query that accomplishes *only* the current step's instruction.
    - Use the results from previous steps as context if necessary (e.g., for filtering with an IN clause).
    - Only output the SQL query. Do not add explanations or markdown.
    """


def final_answer_synthesis_prompt(question: str, plan: list[str], step_results: list[str]) -> str:
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    results_str = "\n".join(f"Result of Step {i+1}:\n{res}\n" for i, res in enumerate(step_results))

    return f"""
    You are an AI assistant. Your goal is to provide a final, comprehensive answer to the user's question by
    synthesizing the results of a data analysis plan.

    **Original User Question:** "{question}"

    **The plan that was executed:**
    {plan_str}

    **The results of each step:**
    {results_str}

    **Instructions:**
    1.  Review the original question, the plan, and the results of each step.
    2.  Synthesize all the information into a single, clear, and natural language answer.
    3.  Do not mention the steps in your final answer unless it's necessary for clarity.
    4.  If the final result is a table, you can present it in a user-friendly way.
    """
