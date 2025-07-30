#!/usr/bin/env python3
"""
Debug script to test MCP integration with Azure AI Agents
Based on the working sample script
"""
import os
import asyncio
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import McpTool

# Configuration from our deployed environment
PROJECT_ENDPOINT = "https://az-tda-foundry-wgznky2irncfe.services.ai.azure.com/api/projects/az-tda-project-wgznky2irncfe"
MODEL_DEPLOYMENT = "gpt-4o"
MCP_SERVER_URL = "https://az-tda-app-wgznky2irncfe.azurewebsites.net/mcp/stream"
MCP_SERVER_LABEL = "todolist"

def main():
    print("Testing MCP integration with Azure AI Agents...")
    print(f"Project Endpoint: {PROJECT_ENDPOINT}")
    print(f"MCP Server: {MCP_SERVER_URL}")
    
    # Connect to the agents client
    agents_client = AgentsClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential()
    )
    
    # Initialize agent MCP tool
    mcp_tool = McpTool(
        server_label=MCP_SERVER_LABEL,
        server_url=MCP_SERVER_URL,
    )
    print(f"MCP Tool initialized: {mcp_tool.server_label} at {mcp_tool.server_url}")
    
    # Create agent with MCP tool and process agent run
    with agents_client:
        try:
            # Create a new agent with the mcp tool definitions
            agent = agents_client.create_agent(
                model=MODEL_DEPLOYMENT,
                name="debug-mcp-agent",
                instructions="""
                You are a helpful agent that can use MCP tools to assist users. 
                Use the available MCP tools to answer questions and perform tasks.""",
                tools=mcp_tool.definitions,
            )
            print(f"Created agent, ID: {agent.id}")
            print(f"MCP Tool definitions: {len(mcp_tool.definitions) if mcp_tool.definitions else 0} tools")
            
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
            print("Set MCP tool approval mode to 'never'")
            
            # Create and process agent run in thread with MCP tools
            print("Creating and processing run...")
            run = agents_client.runs.create_and_process(
                thread_id=thread.id, 
                agent_id=agent.id, 
                tool_resources=mcp_tool.resources
            )
            print(f"Created run, ID: {run.id}")
            
            # Check run status
            print(f"Run completed with status: {run.status}")
            if run.status == "failed":
                print(f"Run failed: {getattr(run, 'last_error', 'Unknown error')}")
                
            # Display run steps and tool calls
            try:
                run_steps = agents_client.run_steps.list(thread_id=thread.id, run_id=run.id)
                print(f"Retrieved run steps...")
                for step in run_steps:
                    print(f"Step {step.id} status: {step.status}")
                    
                    # Check if there are tool calls in the step details
                    step_details = getattr(step, 'step_details', None)
                    if step_details:
                        tool_calls = getattr(step_details, 'tool_calls', [])
                        
                        if tool_calls:
                            # Display the MCP tool call details
                            print("  MCP Tool calls:")
                            for call in tool_calls:
                                print(f"    Tool Call ID: {getattr(call, 'id', 'N/A')}")
                                print(f"    Type: {getattr(call, 'type', 'N/A')}")
                                print(f"    Name: {getattr(call, 'name', 'N/A')}")
                        else:
                            print("  No tool calls in this step")
                    else:
                        print("  No step details available")
            except Exception as e:
                print(f"Error retrieving run steps: {e}")
            
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
            
        except Exception as e:
            print(f"Error during agent interaction: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
