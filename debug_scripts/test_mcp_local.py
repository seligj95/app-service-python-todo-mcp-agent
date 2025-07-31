#!/usr/bin/env python3
"""
Test MCP server connection locally within the App Service
"""
import requests
import json

def test_mcp_connection():
    """Test local MCP server connection"""
    try:
        print("=== Testing Local MCP Server Info ===")
        response = requests.get("http://localhost:8000/mcp/stream")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        print("\n=== Testing MCP Tools List ===")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        response = requests.post(
            "http://localhost:8000/mcp/stream",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        print("\n=== Testing create_todo Tool ===")
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "create_todo",
                "arguments": {
                    "title": "SSH Test Todo",
                    "description": "Created via SSH testing",
                    "priority": "high"
                }
            }
        }
        response = requests.post(
            "http://localhost:8000/mcp/stream",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        print("\n✅ Local MCP tests completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_connection()
