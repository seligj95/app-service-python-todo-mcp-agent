# MCP Debugging Scripts

This directory contains diagnostic scripts to help debug MCP (Model Context Protocol) connectivity issues in Azure App Service.

## Scripts

### 🔧 `test_mcp_local.py`
Tests local MCP server connection within the App Service instance.
- Tests `http://localhost:8000/mcp/stream`
- Verifies MCP JSON-RPC tools/list
- Tests tool execution

### 🌐 `test_mcp_external.py`
Tests external MCP connection (how Azure AI Agents would connect).
- Tests public app URL MCP endpoint
- Simulates external client connectivity
- Identifies network/CORS issues

### ☁️ `test_azure_ai.py`
Tests Azure AI Agent integration and MCP tool creation.
- Verifies environment variables
- Tests Azure AI SDK imports
- Tests credential and client initialization
- Tests MCP tool creation

### 📊 `test_system_info.py`
Collects system information and network diagnostics.
- System and Python version info
- Environment variables
- Process and network status
- File system information

### 🏃‍♂️ `run_all_tests.py`
Runs all diagnostic tests in sequence with organized output.

## Usage in SSH Session

Once you SSH into your Azure App Service:

```bash
# Navigate to the app directory
cd /home/site/wwwroot

# Run individual tests
python3 debug_scripts/test_mcp_local.py
python3 debug_scripts/test_mcp_external.py
python3 debug_scripts/test_azure_ai.py
python3 debug_scripts/test_system_info.py

# Or run all tests at once
python3 debug_scripts/run_all_tests.py
```

## Expected Outputs

### ✅ Success Indicators
- MCP server responds with JSON
- Tools list shows 5 tools (create_todo, list_todos, etc.)
- Azure AI client initializes successfully
- External URL is accessible

### ❌ Failure Indicators
- Connection refused errors
- Timeout errors
- Missing environment variables
- Azure credential issues
- Network policy restrictions

## Troubleshooting

Based on test results:

1. **Local works, External fails**: Network/CORS issue
2. **Azure AI client fails**: Authentication/endpoint issue
3. **All connections fail**: App not running or port issue
4. **Intermittent failures**: Resource constraints or networking

These tests will help identify the exact point of failure in the MCP integration chain.
