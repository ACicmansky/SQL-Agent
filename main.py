import os
from pathlib import Path

from src.agent.graph import build_agent_graph
from src.data.handler import get_schema_from_dataframe, load_data
from src.ui.app import run_gradio_ui


def main():
    """Main function to set up and run the application."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        return

    file_path = "data_sample/Accrual_Accounts.xlsx"

    df = load_data(file_path)
    table_name = Path(file_path).stem

    db_schema = get_schema_from_dataframe(df, table_name)

    ai_agent = build_agent_graph(df, db_schema, table_name)

    run_gradio_ui(ai_agent)


if __name__ == "__main__":
    main()
