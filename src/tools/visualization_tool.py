import os
import uuid

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config import CHART_OUTPUT_PATH, LLM_MODEL

from .tools_prompts import chart_details_prompt


class ChartDetails(BaseModel):
    """Details for generating a chart."""

    chart_type: str = Field(
        ..., description="The type of chart to generate: 'bar', 'line', 'pie', 'scatter'."
    )
    x_column: str = Field(..., description="The column to use for the x-axis.")
    y_column: str = Field(..., description="The column to use for the y-axis.")
    title: str = Field(..., description="A descriptive title for the chart.")


class VisualizationTool:
    """A tool for generating data visualizations."""

    def __init__(self):
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0).with_structured_output(ChartDetails)
        if not os.path.exists(CHART_OUTPUT_PATH):
            os.makedirs(CHART_OUTPUT_PATH)

    def _get_chart_details(self, df: pd.DataFrame, question: str) -> ChartDetails:
        """Uses an LLM to determine the best chart to create."""
        df_head = df.head().to_string(index=False)
        prompt_content = chart_details_prompt(question, df_head, list(df.columns))
        return self.llm.invoke([SystemMessage(content=prompt_content)])

    def generate_chart(self, df: pd.DataFrame, question: str) -> str:
        """Generates a chart and returns the file path."""
        print("Node: generate_chart")
        try:
            details = self._get_chart_details(df, question)
            print(
                f"""LLM decided to create a '{details.chart_type}' chart with X='{details.x_column}'
                and Y='{details.y_column}'."""
            )

            if details.x_column not in df.columns or details.y_column not in df.columns:
                error_msg = f"""
                Error: LLM hallucinated column names. X='{details.x_column}', Y='{details.y_column}'.
                Available columns: {list(df.columns)}
                """
                print(error_msg)
                return error_msg

            plt.figure(figsize=(10, 6))

            if details.chart_type == "bar":
                sns.barplot(data=df, x=details.x_column, y=details.y_column)
            elif details.chart_type == "line":
                sns.lineplot(data=df, x=details.x_column, y=details.y_column)
            elif details.chart_type == "pie":
                df.set_index(details.x_column)[details.y_column].plot.pie(
                    autopct="%1.1f%%", startangle=90, legend=False
                )
                plt.ylabel("")
            elif details.chart_type == "scatter":
                sns.scatterplot(data=df, x=details.x_column, y=details.y_column)
            else:
                return f"Error: Unsupported chart type '{details.chart_type}' selected by LLM."

            plt.title(details.title)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            filepath = os.path.join(CHART_OUTPUT_PATH, f"{uuid.uuid4()}.png")
            plt.savefig(filepath)
            plt.close()

            print(f"Chart saved to {filepath}")
            return filepath
        except Exception as e:
            error_msg = f"Error generating chart: {e}"
            print(error_msg)
            return error_msg
