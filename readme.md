# Intelligent Multi-Agent System

An autonomous multi-agent system built with LangGraph designed to automate complex tasks by delegating work to specialized agents. This system can interact with web search engines and Google services like Gmail and Calendar to process information and act on a user's behalf.

## Features

-   **Task Decomposition:** A central planner agent analyzes user requests and breaks them down into a sequence of actionable steps.
-   **Specialized Agents:** Utilizes distinct agents for different tasks:
    -   **Web Search Agent:** Performs web searches using DuckDuckGo to gather information, research topics, or perform price comparisons.
    -   **Google API Agent:** Interacts with Google services (Gmail, Calendar) to read emails, find events, and create new calendar entries.
-   **Tool-Based Architecture:** Agents leverage external tools through dedicated FastAPI servers, making the system modular and extensible.
-   **Stateful Execution:** The system maintains the state of the entire task, allowing for multi-step workflows where the output of one agent becomes the input for the next.

## System Architecture

The project follows a "coordinator and specialists" model orchestrated by LangGraph.


1.  A user's request initializes the graph's state.
2.  The **Planner Agent** is called. It analyzes the main task and the history of actions, then creates or updates a plan.
3.  The Planner delegates the next step in the plan to either the **Web Search Agent** or the **Google API Agent**.
4.  The specialist agent executes its task. For Google services, it calls a dedicated FastAPI server which handles the API authentication and logic.
5.  The agent returns a structured JSON result, which is added to the graph's state.
6.  The process loops back to the Planner, which analyzes the new state and decides the next step, until the task is complete.

## Core Components

1.  **LangGraph Application (`main.py` or similar):** The main entry point that defines the agent graph, nodes, and edges, and runs the main loop.
2.  **Planner Agent (`planner_node.py`):** The "brain" of the operation. It decides what to do next.
3.  **Web Search Agent (`websearch_agent_node.py`):** A node that uses DuckDuckGo tools to find and synthesize information from the web.
4.  **Google API Agent (`google_api_agent_node.py`):** A node that calls the FastAPI tool servers to interact with Google services.
5.  **Gmail API Server (`gmail_server.py`):** A standalone FastAPI server that wraps the Google Gmail API for reading emails.
6.  **Calendar API Server (`calendar_server.py`):** A standalone FastAPI server that wraps the Google Calendar API for reading and writing events.
