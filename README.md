# To-do MCP Agent with Azure AI

A FastAPI-based to-do list application with Azure AI Agents integration and Model Context Protocol (MCP) server functionality.

## Features

- 🤖 **AI-Powered Chat**: Azure AI Agents with GPT-4o for natural language to-do management
- 🔧 **MCP Integration**: Model Context Protocol server for AI tool access
- ✅ **To-do Management**: Full CRUD operations with priority levels
- 🌐 **Web Interface**: Clean, responsive UI with chat functionality
- ☁️ **Azure Deployment**: Ready for Azure App Service with AI Foundry

## Quick Start

### Prerequisites

- Python 3.11+
- Azure subscription (for AI features)
- Azure Developer CLI (azd)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd python-todo-mcp-agent
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Run locally**:
   ```bash
   python main.py
   ```
   
   > **Note**: The app will start successfully and provide basic to-do functionality without any environment variables. AI chat features require Azure resource deployment and configuration (see below).

3. **Configure Azure AI (Optional)**:
   For AI chat features in your local environment, if you have AI Foundry resources already deployed, set these environment variables. Ensure you're logged into the Azure CLI using `az login` as that credential is required to access the chat.
   
   **Option A: Create a `.env` file in the project root:**
   ```bash
   # .env file - Optional for local AI Chat functionality
   AZURE_AI_PROJECT_ENDPOINT=https://my-ai-project-abc123.westus.ai.azure.com
   AZURE_AI_PROJECT_NAME=my-todo-project
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   AZURE_APP_SERVICE_URL=http://localhost:8000
   ```
   
   **Option B: Set environment variables in PowerShell:**
   ```powershell
   $env:AZURE_AI_PROJECT_ENDPOINT="https://my-ai-project-abc123.westus.ai.azure.com"
   $env:AZURE_AI_PROJECT_NAME="my-todo-project"
   $env:AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
   $env:AZURE_APP_SERVICE_URL="http://localhost:8000"
   ```
   
   **Option C: Set environment variables in Command Prompt:**
   ```cmd
   set AZURE_AI_PROJECT_ENDPOINT=https://my-ai-project-abc123.eastus2.ai.azure.com
   set AZURE_AI_PROJECT_NAME=my-todo-project
   set AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   set AZURE_APP_SERVICE_URL=http://localhost:8000
   ```

4. **Access the app**:
   - To-do List: http://localhost:8000 ✅ (always works)
   - AI Chat: http://localhost:8000/chat ⚠️ (requires Azure setup)
   - Health Check: http://localhost:8000/health ✅ (always works)

### Azure Deployment

Deploy with one command:

```bash
azd up
```

This creates:
- Azure AI Foundry resource with GPT-4o
- Azure AI Foundry project
- App Service with managed identity
- All necessary role assignments

## How It Works

The application combines three key components:

1. **To-do Management**: Standard CRUD operations for managing tasks
2. **MCP Server**: Exposes to-do operations as tools that AI agents can use
3. **AI Chat Interface**: Azure AI Agents that can interact with your to-dos through natural language

### Example Chat Interactions

- "Create a high priority to-do to finish the project"
- "Show me all my incomplete to-dos"
- "Mark the project to-do as complete"
- "What to-dos do I have for today?"

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chat UI       │────│   FastAPI App    │────│   In-Memory     │
│   (AI Agent)    │    │   + MCP Server   │    │   To-do Store   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │   Azure AI       │
                       │   Foundry +      │
                       │   GPT-4o         │
                       └──────────────────┘
```

## Model Context Protocol (MCP)

This application implements a complete MCP server following the [MCP specification](https://modelcontextprotocol.io/introduction). The MCP server exposes to-do management functionality as tools that AI agents can discover and use.

### MCP Documentation and Resources

See **[Connect to Model Context Protocol servers (preview)](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/model-context-protocol#how-it-works)** to learn about the agent integration this is used in this app.

### Important Limitations and Requirements

⚠️ **Azure AI Foundry MCP Connectivity**: Currently, Azure AI Foundry may have network restrictions that prevent connecting to external MCP servers. This is a known limitation in certain Azure regions and configurations.

**Requirements for MCP in Azure:**
- Azure AI Foundry project must be in a supported region. See the supported regions [here](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/model-context-protocol#how-it-works).
- Network policies must allow outbound connections to MCP servers
- MCP server must be publicly accessible with proper CORS configuration
- API version compatibility with Azure AI Agents service

**Workaround**: While MCP integration is implemented and working locally, you can still use the AI chat functionality through the direct agent API endpoints.

### MCP Tools Available

The application exposes these tools for AI agents:

- `create_todo` - Create new to-dos with title, description, and priority
- `list_todos` - List all to-dos or filter by completion status  
- `update_todo` - Update existing to-do properties
- `delete_todo` - Delete to-dos by ID
- `mark_todo_complete` - Toggle completion status

### Testing MCP Locally

You can test the MCP server directly:

```bash
# Test MCP server info
curl http://localhost:8000/mcp/stream

# Test tool discovery
curl -X POST http://localhost:8000/mcp/stream \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## API Endpoints

### Web Interface
- `GET /` - To-do list page
- `GET /chat` - AI chat interface
- `GET /health` - Health check

### REST API
- `GET /api/todos` - List to-dos
- `POST /api/todos` - Create to-do
- `PUT /api/todos/{id}` - Update to-do
- `DELETE /api/todos/{id}` - Delete to-do

### AI Chat API
- `POST /api/chat/session` - Create chat session
- `POST /api/chat/message` - Send message to AI agent

### MCP Server
- `GET /mcp/stream` - MCP server info
- `POST /mcp/stream` - MCP JSON-RPC endpoint

## License

MIT License
