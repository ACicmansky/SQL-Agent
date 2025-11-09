import gradio as gr
from gradio import ChatMessage


def run_gradio_ui(ai_agent):
    """Setup and runs the Gradio UI for the AI agent."""
    with gr.Blocks(theme=gr.themes.Soft(), title="AI Data Assistant") as demo:
        gr.Markdown("# 🤖 AI Data Assistant")
        gr.Markdown("Ask a question about the data, and the AI will answer it using SQL.")

        chatbot = gr.Chatbot(label="Conversation", height=500, type="messages")
        message = gr.Textbox(
            label="Ask a question about the data",
            placeholder="e.g., 'What is the highest transaction value in fiscal year 2017?'",
            submit_btn=True,
        )
        gr.ClearButton([message, chatbot])

        def user_interaction(user_message, history):
            history.append(ChatMessage(role="user", content=user_message))
            yield history
            for step in ai_agent.stream({"question": user_message}):
                step_name = list(step.keys())[0]
                step_output = step[step_name]
                if step_name == "generate_sql":
                    formatted_sql = f"```sql\n{step_output['sql_query']}\n```"
                    history.append(
                        ChatMessage(
                            role="assistant",
                            content=f"🧠 **Thinking...**\n\n🔍 **Generated SQL:**\n{formatted_sql}\n\n",
                        )
                    )
                elif step_name == "execute_sql":
                    history.append(ChatMessage(role="assistant", content="⚙️ **Executing Query...**\n\n"))
                elif step_name == "generate_answer":
                    history.append(
                        ChatMessage(
                            role="assistant", content=f"✅ **Final Answer:**\n{step_output['answer']}"
                        )
                    )
                yield history

        message.submit(user_interaction, [message, chatbot], chatbot)

    print("Launching Gradio UI...")
    demo.launch(share=False)
