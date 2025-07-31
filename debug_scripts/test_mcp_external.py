#!/usr/bin/env python3
"""
Test external MCP connection (how Azure AI Agents would connect)
"""
import requests
import json
import os

# Your app's public URL
APP_URL = os.getenv('AZURE_APP_SERVICE_URL', 'https://az-tda-app-wgznky2irncfe.azurewebsites.net')


def test_external_mcp():
    """Test external MCP connection like Azure AI Agents would"""
    try:
        print("=== Testing External MCP Connection ===")
        print(f"App URL: {APP_URL}")
        print(f"Testing: {APP_URL}/mcp/stream")
        
        # Test server info from external URL
        print("\n--- Testing External Server Info ---")
        response = requests.get(f"{APP_URL}/mcp/stream", timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Test tools list from external URL
        print("\n--- Testing External Tools List ---")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        response = requests.post(
            f"{APP_URL}/mcp/stream",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test tool execution from external URL
        print("\n--- Testing External Tool Execution ---")
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "create_todo",
                "arguments": {
                    "title": "External SSH Test Todo",
                    "description": "Created via external MCP testing",
                    "priority": "medium"
                }
            }
        }
        response = requests.post(
            f"{APP_URL}/mcp/stream",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        print("\n✅ External MCP tests completed")
        
    except Exception as e:
        print(f"❌ External MCP Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_external_mcp()
