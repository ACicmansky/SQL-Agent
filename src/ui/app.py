import base64

import gradio as gr
from gradio import ChatMessage
from langchain_core.messages import HumanMessage


def run_gradio_ui(ai_agent):
    """Setup and runs the Gradio UI for the AI agent."""
    with gr.Blocks(theme=gr.themes.Soft(), title="AI Data Assistant") as demo:
        gr.Markdown("# 🤖 AI Data Assistant Demo")
        gr.Markdown("Ask questions, get charts, and have a conversation about your data.")

        chatbot = gr.Chatbot(label="Conversation", height=500, resizable=True, type="messages")
        message = gr.Textbox(
            label="Ask a question about the data or request a chart",
            placeholder="e.g., 'Chart transaction values in fiscal years 2011 to 2018.'",
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
            full_final_state = {}
            history_list = agent_state.get("chat_history", [])
            display_history = [
                ChatMessage(role="user" if isinstance(m, HumanMessage) else "assistant", content=m.content)
                for m in history_list
            ]
            display_history.append(ChatMessage(role="user", content=agent_state["question"]))

            for step in ai_agent.stream(agent_state):
                step_name = list(step.keys())[0]
                step_output = step[step_name]

                full_final_state.update(step_output)

                if step_name == "planner":
                    plan_str = "\n".join(f"  - {s}" for s in step_output.get("plan", []))
                    display_history.append(
                        ChatMessage(role="assistant", content=f"I've created a plan:\n{plan_str}")
                    )
                elif step_name == "execute_step":
                    step_num = step_output.get("current_step", 0)
                    if step_num > 0:
                        display_history.append(
                            ChatMessage(role="assistant", content=f"Executing Step {step_num}... Done.")
                        )

                yield display_history, history_list

            if not full_final_state:
                display_history.append(
                    ChatMessage(role="assistant", content="Sorry, an unexpected error occurred.")
                )
                yield display_history, history_list
                return

            final_history_list = full_final_state.get("chat_history")
            chart_path = full_final_state.get("chart_image_path")

            final_display_history = []
            if final_history_list:
                for msg in final_history_list[:-1]:  # All messages except the last AI one
                    role = "user" if isinstance(msg, HumanMessage) else "assistant"
                    final_display_history.append(ChatMessage(role=role, content=msg.content))

                last_ai_message = final_history_list[-1]
                ai_text_content = last_ai_message.content

                display_content = ai_text_content
                if chart_path:
                    try:
                        with open(chart_path, "rb") as f:
                            chart_data = f.read()
                        chart_base64 = base64.b64encode(chart_data).decode("utf-8")
                        display_content = f"""<img src='data:image/png;base64,{chart_base64}' />
                        {ai_text_content}"""

                    except Exception as e:
                        print(f"Error reading chart file: {e}")

                final_display_history.append(ChatMessage(role="assistant", content=display_content))

            yield final_display_history, final_history_list

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
