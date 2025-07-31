#!/usr/bin/env python3
"""
Test Azure AI Agent integration with MCP server
"""
import os
import json


def test_azure_ai_mcp():
    """Test Azure AI Agent MCP connection"""
    try:
        print("=== Testing Azure AI Agent MCP Connection ===")
        
        # Check environment variables
        print("\n--- Environment Variables ---")
        endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT')
        project_name = os.getenv('AZURE_AI_PROJECT_NAME')
        deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        app_url = os.getenv('AZURE_APP_SERVICE_URL')
        
        print(f"AZURE_AI_PROJECT_ENDPOINT: {endpoint}")
        print(f"AZURE_AI_PROJECT_NAME: {project_name}")
        print(f"AZURE_OPENAI_DEPLOYMENT_NAME: {deployment_name}")
        print(f"AZURE_APP_SERVICE_URL: {app_url}")
        
        if not all([endpoint, project_name, deployment_name, app_url]):
            print("❌ Missing required environment variables")
            return
        
        # Test Azure AI imports
        print("\n--- Testing Azure AI Imports ---")
        try:
            from azure.identity import DefaultAzureCredential
            from azure.ai.agents import AgentsClient
            from azure.ai.agents.models import McpTool
            print("✅ Azure AI packages imported successfully")
        except ImportError as e:
            print(f"❌ Azure AI import failed: {e}")
            return
        
        # Test credential initialization
        print("\n--- Testing Azure Credential ---")
        try:
            credential = DefaultAzureCredential()
            print("✅ DefaultAzureCredential created")
        except Exception as e:
            print(f"❌ Credential error: {e}")
            return
        
        # Test Azure AI client initialization
        print("\n--- Testing Azure AI Client ---")
        try:
            # Get the proper agents endpoint
            if 'cognitiveservices.azure.com' in endpoint:
                resource_name = endpoint.replace('https://', '').replace('.cognitiveservices.azure.com/', '').replace('.cognitiveservices.azure.com', '')
                agents_endpoint = f"https://{resource_name}.services.ai.azure.com/api/projects/{project_name}"
            else:
                agents_endpoint = endpoint
                
            print(f"Agents endpoint: {agents_endpoint}")
            client = AgentsClient(endpoint=agents_endpoint, credential=credential)
            print("✅ AgentsClient created successfully")
        except Exception as e:
            print(f"❌ Azure AI client error: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test MCP tool creation
        print("\n--- Testing MCP Tool Creation ---")
        try:
            mcp_url = f"{app_url}/mcp/stream"
            print(f"MCP URL: {mcp_url}")
            
            mcp_tool = McpTool(mcp_server_url=mcp_url)
            print(f"✅ MCP Tool created: {mcp_tool}")
        except Exception as e:
            print(f"❌ MCP Tool creation error: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n✅ Azure AI MCP tests completed successfully")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_azure_ai_mcp()
