import gradio as gr
import base64
from gradio import ChatMessage
from langchain_core.messages import HumanMessage


def run_gradio_ui(ai_agent):
    """Setup and runs the Gradio UI for the AI agent."""
    with gr.Blocks(theme=gr.themes.Soft(), title="AI Data Assistant") as demo:
        gr.Markdown("# 🤖 AI Data Assistant Demo")
        gr.Markdown("Ask questions, get charts, and have a conversation about your data.")

        chatbot = gr.Chatbot(label="Conversation", height=500, type="messages")
        message = gr.Textbox(
            label="Ask a question about the data",
            placeholder="e.g., 'What is the highest transaction value in fiscal year 2017?'",
            submit_btn=True,
        )

        chat_history_state = gr.State([])

        def user_interaction(user_message, history_list):
            initial_agent_state = {"question": user_message, "chat_history": history_list}

            temp_display_history = [
                ChatMessage(role="user" if isinstance(m, HumanMessage) else "assistant", content=m.content)
                for m in history_list
            ]
            temp_display_history.append(ChatMessage(role="user", content=user_message))

            return "", temp_display_history, initial_agent_state

        def bot_response(agent_state):
            final_state = ai_agent.invoke(agent_state)

            if final_state is None:
                return [
                    ChatMessage(role="assistant", content="Sorry, an unexpected error occurred.")
                ], agent_state.get("chat_history", [])

            final_history_list = final_state.get("chat_history")
            chart_path = final_state.get("chart_image_path")

            final_display_history = []
            if final_history_list:
                for msg in final_history_list[:-1]:
                    role = "user" if isinstance(msg, HumanMessage) else "assistant"
                    final_display_history.append(ChatMessage(role=role, content=msg.content))

                last_ai_message = final_history_list[-1]
                ai_text_content = last_ai_message.content

                if chart_path:
                    with open(chart_path, "rb") as f:
                        chart_data = f.read()
                    chart_base64 = base64.b64encode(chart_data).decode("utf-8")

                display_content = (f"<img src='data:image/png;base64,{chart_base64}' />\n\n{ai_text_content}") if chart_path else ai_text_content

                final_display_history.append(ChatMessage(role="assistant", content=display_content))

            return final_display_history, final_history_list

        agent_state_holder = gr.State()

        message.submit(
            user_interaction,
            inputs=[message, chat_history_state],
            outputs=[message, chatbot, agent_state_holder],
            queue=False,
        ).then(
            bot_response,
            inputs=[agent_state_holder],
            outputs=[chatbot, chat_history_state],
        )

    print("Launching Gradio UI...")
    demo.launch(share=False)
