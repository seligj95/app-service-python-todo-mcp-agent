import os
from dotenv import load_dotenv

# Add references
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import McpTool

# Load environment variables from .env file
load_dotenv()
project_endpoint = "[PROJECT_ENDPOINT]"
model_deployment = "gpt-4o"

# Connect to the agents client
agents_client = AgentsClient(
     endpoint=project_endpoint,
     credential=DefaultAzureCredential(
         exclude_environment_credential=True,
         exclude_managed_identity_credential=True
     )
)

# MCP server configuration
mcp_server_url = "[MCP_SERVER_URL]/mcp/stream"
mcp_server_label = "todolist"

# Initialize agent MCP tool
mcp_tool = McpTool(
    server_label=mcp_server_label,
    server_url=mcp_server_url,
)

# Create agent with MCP tool and process agent run
with agents_client:

    # Create a new agent with the mcp tool definitions
    agent = agents_client.create_agent(
    model=model_deployment,
    name="my-mcp-agent",
    instructions="""
     You are a helpful agent that can use MCP tools to assist users. 
     Use the available MCP tools to answer questions and perform tasks.""",
    tools=mcp_tool.definitions,
)

    # Log info
    print(f"Created agent, ID: {agent.id}")
    print(f"MCP Server: {mcp_tool.server_label} at {mcp_tool.server_url}")

    # Create thread for communication
    thread = agents_client.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Create a message on the thread
    message = agents_client.messages.create(
        thread_id=thread.id,
        role="user",
        content="Create a high priority todo to buy groceries.",
    )
    print(f"Created message, ID: {message.id}")

    # Set approval mode
    mcp_tool.set_approval_mode("never")

    # Create and process agent run in thread with MCP tools
    run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id, tool_resources=mcp_tool.resources)
    print(f"Created run, ID: {run.id}")
    
    # Check run status
    print(f"Run completed with status: {run.status}")
    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    # Display run steps and tool calls
    run_steps = agents_client.run_steps.list(thread_id=thread.id, run_id=run.id)
    for step in run_steps:
        print(f"Step {step['id']} status: {step['status']}")

        # Check if there are tool calls in the step details
        step_details = step.get("step_details", {})
        tool_calls = step_details.get("tool_calls", [])

        if tool_calls:
            # Display the MCP tool call details
            print("  MCP Tool calls:")
            for call in tool_calls:
                print(f"    Tool Call ID: {call.get('id')}")
                print(f"    Type: {call.get('type')}")
                print(f"    Type: {call.get('name')}")

        print()  # add an extra newline between steps

    # Fetch and log all messages
    messages = agents_client.messages.list(thread_id=thread.id)
    print("\nConversation:")
    print("-" * 50)
    for msg in messages:
        if msg.text_messages:
            last_text = msg.text_messages[-1]
            print(f"{msg.role.upper()}: {last_text.text.value}")
            print("-" * 50)

    # Clean-up and delete the agent once the run is finished.
    agents_client.delete_agent(agent.id)
    print("Deleted agent")