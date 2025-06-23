import streamlit as st
import asyncio
import json
from typing import Any, Dict, List

# --- Core imports from your LangGraph project ---
# Make sure this path is correct for your project structure
from graph.builder import graph, State

# --- NEW: Example Prompts ---
EXAMPLE_PROMPTS = [
    "--- Select an Example ---",
    "Check my Gmail for unread emails max of 3",
    "Get me the latest unread email from my gmail max of 3, but don't show me any links.",
    "Get me the upcoming calendar events from my calendar max of 3",
    "What's on my calendar for tomorrow?",
    "Who is the current president of the united states for 2025?",
    "Find information about climate change",
    "Why is Sachin Tendulkar considered the god of cricket?",
    "Give me details about the conflict between Israel and Palestine"
]

# --- Helper function ---
def format_agent_output(output: Dict[str, Any]) -> str:
    """Parses and formats the output from agent nodes for display."""
    if isinstance(output, dict) and "messages" in output:
        last_message = output["messages"][-1]
        content = last_message.content
        try:
            data = json.loads(content)
            if data.get("status") == "SUCCESS":
                return f"✅ **Result:** {data.get('summary', 'No summary provided.')}"
            else:
                return f"❌ **Failure:** {data.get('summary', 'An error occurred.')}"
        except (json.JSONDecodeError, TypeError):
            return f"```\n{content}\n```"
    if isinstance(output, dict) and "current_task" in output:
        return f"📋 **Next Task:** {output['current_task']}"
    return f"```\n{str(output)}\n```"

# --- REFACTORED: Agent Execution Logic ---
async def execute_graph(prompt: str):
    """Adds the prompt to the UI and runs the agent graph, streaming the output."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🧠 Agent is thinking...", expanded=True) as status:
            final_answer = ""
            initial_state = State(messages=[{"role": "user", "content": prompt}])

            async for event in graph.astream_events(initial_state, version="v1"):
                kind = event["event"]
                
                if kind == "on_chain_start":
                    node_name = event["name"]
                    status.write(f"▶️ **Executing:** `{node_name}`")

                elif kind == "on_chain_end":
                    node_name = event["name"]
                    if node_name == "LangGraph" or "__graph__" in node_name:
                        continue
                    output = event["data"].get("output")
                    is_final_planner_step = isinstance(output, dict) and output.get("next_agent") == "END"
                    status.write(f"☑️ **Finished:** `{node_name}`")
                    if is_final_planner_step:
                        status.write("✅ Plan complete. Generating final answer...")
                    else:
                        formatted_output = format_agent_output(output)
                        status.markdown(formatted_output)
                    
                elif kind == "on_graph_end":
                    final_state = event["data"]["output"]
                    final_answer = final_state.get("final_answer", "I have completed the task, but no final answer was generated.")

            status.update(label="✅ Task Complete!", state="complete", expanded=False)
            st.markdown(output.get("final_answer"))
            
            st.session_state.messages.append({"role": "assistant", "content": final_answer})

# --- Main Streamlit App UI ---
st.set_page_config(page_title="Multi-Agent System", layout="wide")
st.title("🤖 Intelligent Multi-Agent System")

# --- NEW: Sidebar UI ---
with st.sidebar:
    st.title("🧪 Example Prompts")
    st.write("Select a pre-written prompt to test the agent's capabilities.")
    
    selected_example = st.selectbox(
        "Choose an example:",
        options=EXAMPLE_PROMPTS,
        index=0,  # Default to the placeholder
        key="example_selector"
    )
    
    run_example_button = st.button("Run Selected Example", use_container_width=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Determine which prompt to run
prompt_to_run = None

# Check if the sidebar button was clicked with a valid example
if run_example_button and selected_example != EXAMPLE_PROMPTS[0]:
    prompt_to_run = selected_example

# Check if the user typed in the main chat input
if chat_input := st.chat_input("Or type your own request here..."):
    prompt_to_run = chat_input

# If there's a prompt to run, execute the graph
if prompt_to_run:
    asyncio.run(execute_graph(prompt_to_run))