import gradio as gr
from gradio import ChatMessage


def run_gradio_ui(ai_agent):
    """Setup and runs the Gradio UI for the AI agent."""
    with gr.Blocks(theme=gr.themes.Soft(), title="AI Data Assistant") as demo:
        gr.Markdown("# 🤖 AI Data Assistant Demo")
        gr.Markdown("Ask a question about the data, and the AI will answer it using SQL.")

        chatbot = gr.Chatbot(label="Conversation", height=500, type="messages")
        message = gr.Textbox(
            label="Ask a question about the data",
            placeholder="e.g., 'What is the highest transaction value in fiscal year 2017?'",
            submit_btn=True,
        )
        gr.ClearButton([message, chatbot])
        state = gr.State()

        def user_interaction(user_message, history):
            history.append(ChatMessage(role="user", content=user_message))
            initial_agent_state = {"question": user_message, "retries": 0}
            return "", history, initial_agent_state

        def bot_response(history, agent_state):
            for step in ai_agent.stream(agent_state):
                step_name = list(step.keys())[0]
                step_output = step[step_name]
                if step_name == "generate_sql":
                    if step_output.get("retries", 0) > 0:
                        history.append(
                            ChatMessage(
                                role="assistant",
                                content="⚠️ **Query failed. Attempting to correct...**\n\n",
                            )
                        )
                        yield history

                    formatted_sql = f"```sql\n{step_output['sql_query']}\n```"
                    history.append(
                        ChatMessage(
                            role="assistant",
                            content=f"🧠 **Thinking...**\n\n🔍 **Generated SQL:**\n{formatted_sql}",
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
                elif step_name == "handle_failure":
                    history.append(
                        ChatMessage(
                            role="assistant", content=f"❌ **Final Answer:**\n{step_output['answer']}"
                        )
                    )
                yield history

        message.submit(
            user_interaction,
            inputs=[message, chatbot],
            outputs=[message, chatbot, state],
            queue=False,
        ).then(
            bot_response,
            inputs=[chatbot, state],
            outputs=[chatbot],
        )

    print("Launching Gradio UI...")
    demo.launch(share=False)
