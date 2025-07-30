# Todo MCP Agent with Azure AI

A FastAPI-based todo list application with Azure AI Agents integration and Model Context Protocol (MCP) server functionality.

## Features

- 🤖 **AI-Powered Chat**: Azure AI Agents with GPT-4o for natural language todo management
- 🔧 **MCP Integration**: Model Context Protocol server for AI tool access
- ✅ **Todo Management**: Full CRUD operations with priority levels
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

3. **Access the app**:
   - Todo List: http://localhost:8000
   - AI Chat: http://localhost:8000/chat
   - Health Check: http://localhost:8000/health

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

1. **Todo Management**: Standard CRUD operations for managing tasks
2. **MCP Server**: Exposes todo operations as tools that AI agents can use
3. **AI Chat Interface**: Azure AI Agents that can interact with your todos through natural language

### Example Chat Interactions

- "Create a high priority todo to finish the project"
- "Show me all my incomplete todos"
- "Mark the project todo as complete"
- "What todos do I have for today?"

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chat UI       │────│   FastAPI App    │────│   In-Memory     │
│   (AI Agent)    │    │   + MCP Server   │    │   Todo Store    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │   Azure AI       │
                       │   Foundry +      │
                       │   GPT-4o         │
                       └──────────────────┘
```

## Model Context Protocol (MCP)

This application implements a complete MCP server following the [MCP specification](https://modelcontextprotocol.io/introduction). The MCP server exposes todo management functionality as tools that AI agents can discover and use.

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

- `create_todo` - Create new todos with title, description, and priority
- `list_todos` - List all todos or filter by completion status  
- `update_todo` - Update existing todo properties
- `delete_todo` - Delete todos by ID
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
- `GET /` - Todo list page
- `GET /chat` - AI chat interface
- `GET /health` - Health check

### REST API
- `GET /api/todos` - List todos
- `POST /api/todos` - Create todo
- `PUT /api/todos/{id}` - Update todo
- `DELETE /api/todos/{id}` - Delete todo

### AI Chat API
- `POST /api/chat/session` - Create chat session
- `POST /api/chat/message` - Send message to AI agent

### MCP Server
- `GET /mcp/stream` - MCP server info
- `POST /mcp/stream` - MCP JSON-RPC endpoint

## Configuration

Environment variables are automatically configured during Azure deployment:

- `AZURE_AI_PROJECT_ENDPOINT` - AI Foundry endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME` - GPT-4o deployment name
- `AZURE_APP_SERVICE_URL` - App service URL for MCP

## Development

The app uses:
- **FastAPI** for the web framework
- **Azure AI Agents** for AI functionality
- **Bootstrap 5** for UI styling
- **In-memory storage** for simplicity (easily upgradeable)

## License

MIT License
