# Python Todo List App with MCP Integration

A Flask-based todo list application that exposes operations as MCP (Model Context Protocol) tools over HTTP and can be deployed to Azure App Service.

## Features

- ✅ **CRUD Operations**: Create, read, update, delete todos
- 🎯 **Priority Management**: Set priority levels (low, medium, high)
- ✅ **Mark Complete/Incomplete**: Toggle completion status
- 🌐 **Web Interface**: Clean, responsive Bootstrap UI
- 💬 **Chat Interface**: Placeholder for future LLM integration
- 🔧 **MCP Tools**: HTTP-accessible tools for external integrations
- ☁️ **Azure Ready**: Optimized for Azure App Service deployment

## MCP Tools Available

The application exposes the following MCP tools over HTTP:

- `create_todo(title, description, priority)` - Create a new todo item
- `list_todos(filter_completed)` - Get all todos with optional filtering
- `update_todo(id, title, description, priority, completed)` - Update existing todo
- `delete_todo(id)` - Delete a todo item
- `mark_todo_complete(id, completed)` - Mark todo as complete/incomplete

## Local Development

### Prerequisites

- Python 3.12+
- Virtual environment (venv)

### Setup

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd python-todo-mcp-agent
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables** (optional):
   ```bash
   set SECRET_KEY=your-secret-key-here
   set DATABASE_URL=sqlite:///todos.db
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

5. **Access the application**:
   - Web Interface: http://localhost:8000
   - Chat Interface: http://localhost:8000/chat
   - Health Check: http://localhost:8000/health
   - MCP Endpoint: http://localhost:8000/mcp
   - MCP Tools: http://localhost:8000/mcp/tools/*

## Azure Deployment

### Prerequisites

- Azure CLI installed and logged in
- Azure Developer CLI (azd) installed

### Deploy with AZD

1. **Initialize AZD**:
   ```bash
   azd init
   ```

2. **Set environment variables**:
   ```bash
   azd env set SECRET_KEY "your-production-secret-key"
   azd env set DATABASE_URL "sqlite:///todos.db"
   ```

3. **Deploy to Azure**:
   ```bash
   azd up
   ```

### Infrastructure

The deployment creates:

- **App Service Plan**: P0V3 (Premium V3, Linux)
- **App Service**: Python 3.12 runtime
- **Managed Identity**: Secure Azure resource access

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │────│   Flask App      │────│   SQLite DB     │
│   (Todo UI)     │    │   (CRUD API)     │    │   (Data Store)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │   MCP Server     │
                       │   (HTTP Tools)   │
                       └──────────────────┘
                                │
                       ┌──────────────────┐
                       │  External Tools  │
                       │  & Integrations  │
                       └──────────────────┘
```

## API Endpoints

### REST API
- `GET /api/todos` - List all todos
- `POST /api/todos` - Create new todo
- `GET /api/todos/{id}` - Get specific todo
- `PUT /api/todos/{id}` - Update todo
- `DELETE /api/todos/{id}` - Delete todo
- `PATCH /api/todos/{id}/complete` - Toggle completion

### MCP Integration
- `GET /mcp` - MCP server info and available tools
- `POST /mcp` - MCP protocol endpoint (JSON-RPC 2.0)
- `GET/POST /mcp/tools/create_todo` - Direct tool access
- `GET/POST /mcp/tools/list_todos` - Direct tool access
- `POST /mcp/tools/update_todo` - Direct tool access
- `POST /mcp/tools/delete_todo` - Direct tool access
- `POST /mcp/tools/mark_todo_complete` - Direct tool access

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key` |
| `DATABASE_URL` | Database connection string | `sqlite:///todos.db` |

## Development Notes

- **Database**: Uses SQLite for simplicity (can be upgraded to Azure SQL)
- **Styling**: Bootstrap 5 with Font Awesome icons
- **Frontend**: Vanilla JavaScript with fetch API
- **Backend**: Flask with SQLAlchemy ORM
- **MCP**: Native JSON-RPC 2.0 implementation in Flask
- **Security**: HTTPS only, managed identity, CORS enabled

## Future Enhancements

- 🤖 **LLM Integration**: Connect chat interface to language models
- 🗄️ **Database Upgrade**: Migrate to Azure SQL Database
- 🔐 **Authentication**: Add user accounts and auth
- 📱 **Mobile App**: React Native or Flutter companion
- 🔍 **Search**: Full-text search capabilities
- 📊 **Analytics**: Usage metrics and insights

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
