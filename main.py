"""
Todo MCP Server with FastAPI and Azure AI Agents - Simplified and Working
"""
import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure AI imports
try:
    from azure.identity import DefaultAzureCredential
    from azure.ai.agents import AgentsClient
    from azure.ai.agents.models import McpTool
    AZURE_AI_AVAILABLE = True
    logger.info("✓ Azure AI packages imported successfully")
except ImportError as e:
    AZURE_AI_AVAILABLE = False
    logger.error(f"✗ Azure AI import failed: {e}")

# Configuration (all from environment variables from Bicep deployment)


def get_azure_ai_project_endpoint():
    """Get Azure AI Project endpoint from environment variables"""
    azure_ai_endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT')
    if not azure_ai_endpoint:
        raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")
    
    # Azure AI Foundry endpoint should be a direct URL
    if azure_ai_endpoint.startswith('https://'):
        return azure_ai_endpoint
    
    # Handle legacy Azure ML format if still present
    if ';' in azure_ai_endpoint:
        # Format: "westus.api.azureml.ms;subscription;resourcegroup;projectname"
        parts = azure_ai_endpoint.split(';')
        if len(parts) >= 4:
            # Extract region from "westus.api.azureml.ms"
            region = parts[0].split('.')[0]
            project_name = parts[3]
            return (f"https://{region}.api.azureml.ms/api/projects/"
                    f"{project_name}")
    
    raise ValueError(f"Invalid AZURE_AI_PROJECT_ENDPOINT format: {azure_ai_endpoint}")


PROJECT_ENDPOINT = get_azure_ai_project_endpoint()
MODEL_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
if not MODEL_DEPLOYMENT:
    raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required")

# MCP server URL from Bicep deployment
azure_app_service_url = os.getenv('AZURE_APP_SERVICE_URL')
if not azure_app_service_url:
    raise ValueError("AZURE_APP_SERVICE_URL environment variable is required")

MCP_SERVER_URL = azure_app_service_url + "/mcp/stream"
MCP_SERVER_LABEL = "todolist"


# Pydantic Models
class Todo(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = ""
    completed: bool = False
    priority: str = "medium"
    created_at: Optional[str] = None

class ChatMessage(BaseModel):
    message: str

class ChatSessionMessage(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    agent_id: Optional[str] = None
    thread_id: Optional[str] = None

class ChatSession(BaseModel):
    session_id: str
    agent_id: Optional[str] = None
    thread_id: Optional[str] = None

# Simple in-memory storage for todos
todos_storage: Dict[int, Todo] = {}
next_id = 1

# Session storage for chat sessions
chat_sessions: Dict[str, ChatSession] = {}

def get_current_time() -> str:
    return datetime.now().isoformat()

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return str(uuid.uuid4())

class AzureAIAgentService:
    """Simplified Azure AI Agent Service using the working pattern from new-script.py"""
    
    def __init__(self):
        self.agents_client = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize Azure AI Agents Client"""
        if not AZURE_AI_AVAILABLE:
            logger.warning("Azure AI packages not available")
            return False
            
        try:
            # Create agents client - use managed identity in production, dev credentials locally
            self.agents_client = AgentsClient(
                endpoint=PROJECT_ENDPOINT,
                credential=DefaultAzureCredential()
            )
            
            logger.info("Azure AI Agents Client initialized successfully")
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure AI Agents Client: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
    
    async def create_agent_with_mcp(self, instructions: str = None) -> Optional[str]:
        """Create an agent with MCP tool integration"""
        if not self.is_initialized:
            await self.initialize()
            if not self.is_initialized:
                return None
                
        try:
            # Initialize MCP tool
            mcp_tool = McpTool(
                server_label=MCP_SERVER_LABEL,
                server_url=MCP_SERVER_URL,
            )
            
            # Default instructions if none provided
            if not instructions:
                instructions = """
                You are a helpful agent that can use MCP tools to assist users with todo management. 
                Use the available MCP tools to answer questions and perform tasks like creating, 
                listing, updating, and deleting todos.
                """
            
            # Create agent with MCP tool definitions
            with self.agents_client:
                agent = self.agents_client.create_agent(
                    model=MODEL_DEPLOYMENT,
                    name="todo-mcp-agent",
                    instructions=instructions,
                    tools=mcp_tool.definitions,
                )
                
                logger.info(f"Created agent with MCP tools, ID: {agent.id}")
                return agent.id, mcp_tool
                
        except Exception as e:
            logger.error(f"Error creating agent with MCP: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    async def chat_with_agent(self, message: str) -> ChatResponse:
        """Create a one-time agent interaction (simplified version)"""
        if not self.is_initialized:
            await self.initialize()
            if not self.is_initialized:
                return ChatResponse(response="Azure AI service is not available")
        
        # Create a fresh client for each request to avoid transport issues
        try:
            # Create fresh agents client for this request
            fresh_client = AgentsClient(
                endpoint=PROJECT_ENDPOINT,
                credential=DefaultAzureCredential()
            )
            
            # Initialize MCP tool
            mcp_tool = McpTool(
                server_label=MCP_SERVER_LABEL,
                server_url=MCP_SERVER_URL,
            )
            
            # Default instructions
            instructions = """
            You are a helpful agent that can use MCP tools to assist users with todo management. 
            Use the available MCP tools to answer questions and perform tasks like creating, 
            listing, updating, and deleting todos.
            """
            
            with fresh_client:
                # Create agent with MCP tool definitions
                agent = fresh_client.create_agent(
                    model=MODEL_DEPLOYMENT,
                    name="todo-mcp-agent",
                    instructions=instructions,
                    tools=mcp_tool.definitions,
                )
                logger.info(f"Created agent with MCP tools, ID: {agent.id}")
                
                # Create thread for communication
                thread = fresh_client.threads.create()
                logger.info(f"Created thread, ID: {thread.id}")
                
                # Create message on the thread
                message_obj = fresh_client.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=message,
                )
                logger.info(f"Created message, ID: {message_obj.id}")
                
                # Set MCP tool approval mode
                mcp_tool.set_approval_mode("never")
                
                # Create and process agent run with MCP tools
                run = fresh_client.runs.create_and_process(
                    thread_id=thread.id, 
                    agent_id=agent.id, 
                    tool_resources=mcp_tool.resources
                )
                logger.info(f"Created run, ID: {run.id}")
                
                # Get the response
                messages = fresh_client.messages.list(thread_id=thread.id)
                
                # Extract the assistant's response
                assistant_response = "No response generated"
                for msg in messages:
                    if msg.role == "assistant" and msg.text_messages:
                        last_text = msg.text_messages[-1]
                        assistant_response = last_text.text.value
                        break
                
                # Clean up - delete the agent
                fresh_client.delete_agent(agent.id)
                logger.info("Deleted agent")
                
                return ChatResponse(
                    response=assistant_response,
                    agent_id=agent.id,
                    thread_id=thread.id
                )
                
        except Exception as e:
            logger.error(f"Error in chat_with_agent: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return ChatResponse(response=f"Error: {str(e)}")

# Initialize Azure AI service
ai_service = AzureAIAgentService()

# Template configuration
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Todo MCP FastAPI Server with Azure AI Agents")
    
    # Initialize Azure AI service
    await ai_service.initialize()
    
    yield
    logger.info("Shutting down Todo MCP FastAPI Server")

# Create FastAPI app
app = FastAPI(
    title="Todo MCP Server with Azure AI Agents",
    description="Model Context Protocol server for todo management with AI agent integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main todo list page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Serve the chat interface page"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "todos_count": len(todos_storage),
        "azure_ai_available": AZURE_AI_AVAILABLE,
        "ai_service_initialized": ai_service.is_initialized,
        "project_endpoint": PROJECT_ENDPOINT,
        "mcp_server_url": MCP_SERVER_URL
    }

@app.get("/debug")
async def debug():
    """Debug endpoint with configuration info"""
    return {
        "azure_ai_available": AZURE_AI_AVAILABLE,
        "ai_service_initialized": ai_service.is_initialized,
        "project_endpoint": PROJECT_ENDPOINT,
        "model_deployment": MODEL_DEPLOYMENT,
        "mcp_server_url": MCP_SERVER_URL,
        "mcp_server_label": MCP_SERVER_LABEL,
        "todos_count": len(todos_storage)
    }

# REST API endpoints for direct todo management
@app.get("/api/todos")
async def get_todos(completed: Optional[bool] = None):
    """Get all todos with optional completion filter"""
    todos = list(todos_storage.values())
    
    if completed is not None:
        todos = [todo for todo in todos if todo.completed == completed]
    
    return [todo.dict() for todo in todos]

@app.post("/api/todos")
async def create_todo_api(todo_data: dict):
    """Create a new todo via REST API"""
    global next_id
    try:
        todo = Todo(
            id=next_id,
            title=todo_data["title"],
            description=todo_data.get("description", ""),
            priority=todo_data.get("priority", "medium"),
            created_at=get_current_time()
        )
        todos_storage[next_id] = todo
        next_id += 1
        return todo.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/todos/{todo_id}")
async def update_todo_api(todo_id: int, todo_data: dict):
    """Update a todo via REST API"""
    if todo_id not in todos_storage:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    todo = todos_storage[todo_id]
    
    if "title" in todo_data:
        todo.title = todo_data["title"]
    if "description" in todo_data:
        todo.description = todo_data["description"]
    if "priority" in todo_data:
        todo.priority = todo_data["priority"]
    if "completed" in todo_data:
        todo.completed = todo_data["completed"]
    
    return todo.dict()

@app.delete("/api/todos/{todo_id}")
async def delete_todo_api(todo_id: int):
    """Delete a todo via REST API"""
    if todo_id not in todos_storage:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    deleted_todo = todos_storage.pop(todo_id)
    return {"message": "Todo deleted successfully", "deleted_todo": deleted_todo.dict()}

# AI Chat API endpoints
@app.post("/api/chat/session", response_model=ChatSession)
async def create_chat_session():
    """Create a new chat session"""
    if not ai_service.is_initialized:
        raise HTTPException(
            status_code=503, 
            detail="Azure AI service is not available"
        )
    
    session_id = generate_session_id()
    session = ChatSession(session_id=session_id)
    chat_sessions[session_id] = session
    
    return session

@app.post("/api/chat/message", response_model=ChatResponse)
async def chat_with_ai_session(chat_message: ChatSessionMessage):
    """Send a message to the AI agent using session"""
    if not ai_service.is_initialized:
        raise HTTPException(
            status_code=503, 
            detail="Azure AI service is not available"
        )
    
    # Validate session exists
    if chat_message.session_id not in chat_sessions:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found"
        )
    
    session = chat_sessions[chat_message.session_id]
    response = await ai_service.chat_with_agent(chat_message.message)
    
    # Update session with agent/thread info if available
    if response.agent_id:
        session.agent_id = response.agent_id
    if response.thread_id:
        session.thread_id = response.thread_id
    
    return response

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(chat_message: ChatMessage):
    """Send a message to the AI agent with MCP tools (legacy endpoint)"""
    if not ai_service.is_initialized:
        raise HTTPException(
            status_code=503, 
            detail="Azure AI service is not available"
        )
    
    response = await ai_service.chat_with_agent(chat_message.message)
    return response

@app.get("/api/chat/status")
async def chat_status():
    """Get the status of the Azure AI chat service"""
    return {
        "available": ai_service.is_initialized,
        "azure_ai_packages_available": AZURE_AI_AVAILABLE,
        "project_endpoint": PROJECT_ENDPOINT,
        "model_deployment": MODEL_DEPLOYMENT,
        "mcp_server_configured": bool(MCP_SERVER_URL)
    }

# MCP Server Implementation
class MCPServer:
    def __init__(self):
        self.tools = {
            "create_todo": {
                "name": "create_todo",
                "description": "Create a new todo item",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Title of the todo"},
                        "description": {"type": "string", "description": "Optional description"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority level"}
                    },
                    "required": ["title"]
                }
            },
            "list_todos": {
                "name": "list_todos",
                "description": "Get all todo items",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filter_completed": {"type": "boolean", "description": "Filter by completion status"}
                    }
                }
            },
            "update_todo": {
                "name": "update_todo",
                "description": "Update an existing todo item",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "todo_id": {"type": "integer", "description": "Todo ID to update"},
                        "title": {"type": "string", "description": "New title"},
                        "description": {"type": "string", "description": "New description"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority level"},
                        "completed": {"type": "boolean", "description": "Completion status"}
                    },
                    "required": ["todo_id"]
                }
            },
            "delete_todo": {
                "name": "delete_todo",
                "description": "Delete a todo item",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "todo_id": {"type": "integer", "description": "Todo ID to delete"}
                    },
                    "required": ["todo_id"]
                }
            },
            "mark_todo_complete": {
                "name": "mark_todo_complete",
                "description": "Mark a todo as complete",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "todo_id": {"type": "integer", "description": "Todo ID to mark"},
                        "completed": {"type": "boolean", "description": "Completion status", "default": True}
                    },
                    "required": ["todo_id"]
                }
            }
        }

    async def handle_request(self, request_data: dict) -> dict:
        """Handle MCP JSON-RPC requests"""
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": True, "listChanged": True}
                    },
                    "serverInfo": {
                        "name": "Todo MCP Server",
                        "version": "1.0.0"
                    }
                }
            elif method == "tools/list":
                result = {"tools": list(self.tools.values())}
            elif method == "tools/call":
                result = await self.handle_tool_call(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }

    async def handle_tool_call(self, params: dict) -> dict:
        """Handle MCP tool calls"""
        global next_id
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "create_todo":
            title = arguments.get("title")
            if not title:
                raise ValueError("Title is required")
            
            todo = Todo(
                id=next_id,
                title=title,
                description=arguments.get("description", ""),
                priority=arguments.get("priority", "medium"),
                created_at=get_current_time()
            )
            todos_storage[next_id] = todo
            next_id += 1
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Created todo: {todo.dict()}"
                    }
                ]
            }
            
        elif tool_name == "list_todos":
            filter_completed = arguments.get("filter_completed")
            todos = list(todos_storage.values())
            
            if filter_completed is not None:
                todos = [todo for todo in todos if todo.completed == filter_completed]
            
            todos_data = [todo.dict() for todo in todos]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Found {len(todos_data)} todos: {todos_data}"
                    }
                ]
            }
            
        elif tool_name == "update_todo":
            todo_id = arguments.get("todo_id")
            if todo_id not in todos_storage:
                raise ValueError(f"Todo {todo_id} not found")
            
            todo = todos_storage[todo_id]
            if "title" in arguments:
                todo.title = arguments["title"]
            if "description" in arguments:
                todo.description = arguments["description"]
            if "priority" in arguments:
                todo.priority = arguments["priority"]
            if "completed" in arguments:
                todo.completed = arguments["completed"]
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Updated todo: {todo.dict()}"
                    }
                ]
            }
            
        elif tool_name == "delete_todo":
            todo_id = arguments.get("todo_id")
            if todo_id not in todos_storage:
                raise ValueError(f"Todo {todo_id} not found")
            
            deleted_todo = todos_storage.pop(todo_id)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Deleted todo: {deleted_todo.dict()}"
                    }
                ]
            }
            
        elif tool_name == "mark_todo_complete":
            todo_id = arguments.get("todo_id")
            if todo_id not in todos_storage:
                raise ValueError(f"Todo {todo_id} not found")
            
            todo = todos_storage[todo_id]
            todo.completed = arguments.get("completed", True)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Marked todo as {'complete' if todo.completed else 'incomplete'}: {todo.dict()}"
                    }
                ]
            }
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

# Initialize MCP server
mcp_server = MCPServer()

# MCP Server endpoints (for direct MCP client access)
@app.get("/mcp/stream")
async def mcp_stream_info():
    """Information about the MCP stream endpoint"""
    return {
        "info": "MCP Streamable HTTP Transport Endpoint",
        "description": "This endpoint provides access to todo management tools via MCP",
        "mcp_server_url": MCP_SERVER_URL,
        "available_tools": [
            "create_todo", 
            "list_todos", 
            "update_todo", 
            "delete_todo", 
            "mark_todo_complete"
        ]
    }

@app.post("/mcp/stream")
async def mcp_stream_endpoint(request: Request):
    """Main MCP endpoint with JSON-RPC support"""
    try:
        request_data = await request.json()
        logger.info(f"MCP request: {request_data}")
        
        response_data = await mcp_server.handle_request(request_data)
        logger.info(f"MCP response: {response_data}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in MCP endpoint: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
        }

@app.options("/mcp/stream")
async def mcp_stream_options():
    """Handle CORS preflight for MCP stream endpoint"""
    return {
        "status": "ok",
        "methods": ["POST", "OPTIONS"],
        "headers": ["Content-Type", "Accept"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
