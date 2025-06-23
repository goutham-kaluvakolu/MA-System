import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from models.llm import get_llm
from graph.state import State
import prompts.google_api_agent_system_prompt
from prompts.google_api_agent_response_formating_prompt import formatting_prompt
from mcp_use import MCPAgent, MCPClient

# This is a new, secondary prompt specifically for the formatting step.
FORMATTING_PROMPT = formatting_prompt
async def google_api_agent_node(state: State) -> dict:
    """
    Interacts with Google APIs via MCPAgent and formats the output
    into the structured JSON required by the planner.

    Args:
        state: The current state of the graph.

    Returns:
        dict: A dictionary with the message to be appended to the state.
    """
    print("---EXECUTING GOOGLE API AGENT---")
    try:
        config = {"mcpServers": {"GMAIL": {"url": "http://localhost:8000/mcp"},"CALENDER": {"url": "http://localhost:8001/mcp"}}}

    # Create MCPClient from config file
        client = MCPClient.from_dict(config)
        llm = get_llm()
        agent = MCPAgent(llm=llm, client=client, max_steps=30)
        
        system_prompt = prompts.google_api_agent_system_prompt.system_prompt
        current_task = state.get("current_task", "No task specified")

        # 2. EXECUTE: Use your custom MCPAgent to get the raw data
        # We create a simple prompt string for your agent's run method
        mcp_prompt_str = (
            f"System Prompt: {system_prompt}\n\n"
            f"User Task: {current_task}"
        )
        print(f"Passing the following task to MCPAgent:\n{current_task}")
        
        # This call gets the raw, unstructured data from the Google API
        raw_response_from_mcp = await agent.run(mcp_prompt_str)
        print(f"Received raw response from MCPAgent:\n{raw_response_from_mcp}")

        # 3. FORMAT: Use a separate LLM call to structure the raw response
        formatting_llm = get_llm()
        
        formatting_messages = [
            SystemMessage(content=FORMATTING_PROMPT),
            HumanMessage(
                content=(
                    f"Original Request: {current_task}\n\n"
                    f"Raw Tool Output to be formatted:\n---\n{raw_response_from_mcp}\n---"
                )
            )
        ]

        structured_response = formatting_llm.invoke(formatting_messages)
        
        final_json_output = structured_response.content
        print(f"Formatted JSON output for Planner:\n{final_json_output}")

        # 4. UPDATE STATE: Return a dictionary to append the single, structured message
        # This preserves the history and gives the Planner exactly what it needs.
        return {
            "messages": [AIMessage(content=final_json_output)]
        }

    except Exception as e:
        print(f"Error in google_api_agent_node: {e}")
        error_output = {
            "status": "FAILURE",
            "summary": f"An error occurred in the Google API agent: {str(e)}",
            "extracted_data": {"emails": [], "events": []},
            "error_message": str(e)
        }
        return {
            "messages": [AIMessage(content=json.dumps(error_output))]
        }