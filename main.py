"""
Todo MCP Server with FastAPI and Azure AI Foundry Chat - Azure Ready
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
import logging
from contextlib import asynccontextmanager
from datetime import datetime
import os
import uuid
import json
import asyncio

# Azure AI imports (will be imported only when needed to avoid startup issues)
try:
    from azure.ai.projects import AIProjectClient
    from azure.ai.agents.models import MessageTextContent, ListSortOrder, McpTool
    from azure.identity import DefaultAzureCredential
    AZURE_AI_AVAILABLE = True
except ImportError:
    AZURE_AI_AVAILABLE = False
    logging.warning("Azure AI packages not available. Chat functionality will be disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class Resource(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

class Todo(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = ""
    completed: bool = False
    priority: str = "medium"
    created_at: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    session_id: str

class ChatSession(BaseModel):
    session_id: str
    thread_id: Optional[str] = None
    agent_id: Optional[str] = None

# Simple in-memory storage for todos and chat sessions
todos_storage: Dict[int, Todo] = {}
next_id = 1
chat_sessions: Dict[str, ChatSession] = {}

def get_current_time() -> str:
    return datetime.now().isoformat()

# Azure AI Foundry Chat Service
class AzureAIFoundryService:
    def __init__(self):
        self.project_client = None
        self.mcp_server_url = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize Azure AI Foundry connection"""
        logger.info("=== Starting Azure AI Foundry initialization ===")
        
        if not AZURE_AI_AVAILABLE:
            logger.warning("Azure AI packages not available")
            return False
            
        try:
            # Get configuration from environment
            project_endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT')
            model_deployment_name = os.getenv('AZURE_AI_MODEL_DEPLOYMENT_NAME', 'gpt-4-1106-preview')
            app_service_url = os.getenv('AZURE_APP_SERVICE_URL', 'http://localhost:8000')
            
            logger.info("=== Environment Variables ===")
            logger.info(f"  AZURE_AI_PROJECT_ENDPOINT: {project_endpoint}")
            logger.info(f"  AZURE_AI_MODEL_DEPLOYMENT_NAME: {model_deployment_name}")
            logger.info(f"  AZURE_APP_SERVICE_URL: {app_service_url}")
            
            # Also log other Azure-related env vars for debugging
            other_vars = [
                'AZURE_OPENAI_ENDPOINT',
                'AZURE_OPENAI_DEPLOYMENT_NAME', 
                'AZURE_TENANT_ID',
                'AZURE_CLIENT_ID',
                'AZURE_CLIENT_SECRET'
            ]
            for var in other_vars:
                value = os.getenv(var)
                if value:
                    logger.info(f"  {var}: {value[:50]}...")
                else:
                    logger.info(f"  {var}: Not set")
            
            if not project_endpoint:
                logger.error("AZURE_AI_PROJECT_ENDPOINT not configured")
                return False
            
            # Initialize Azure AI Project Client using connection string format
            logger.info("=== Initializing Azure Credentials ===")
            try:
                credential = DefaultAzureCredential()
                logger.info("DefaultAzureCredential created successfully")
                
                # Test credential by getting a token
                logger.info("Testing credential by requesting token...")
                token = credential.get_token("https://cognitiveservices.azure.com/.default")
                logger.info(f"Token acquired successfully, expires: {token.expires_on}")
            except Exception as cred_error:
                logger.error(f"Credential initialization failed: {cred_error}")
                return False
            
            # Try the from_connection_string method first
            logger.info("=== Creating AIProjectClient ===")
            logger.info(f"Using connection string: {project_endpoint}")
            try:
                self.project_client = AIProjectClient.from_connection_string(
                    conn_str=project_endpoint,
                    credential=credential
                )
                logger.info("✓ Successfully created AIProjectClient with connection string")
            except Exception as conn_error:
                logger.error(f"✗ Connection string method failed: {conn_error}")
                logger.info("Trying fallback method with direct endpoint...")
                # Fallback to direct endpoint initialization
                try:
                    # Convert connection string to endpoint URL
                    parts = project_endpoint.split(';')
                    if len(parts) >= 4:
                        endpoint_url = f"https://{parts[3]}.{parts[0]}"
                        logger.info(f"Converted to endpoint URL: {endpoint_url}")
                        self.project_client = AIProjectClient(
                            endpoint=endpoint_url,
                            credential=credential
                        )
                        logger.info("✓ Successfully created AIProjectClient with direct endpoint")
                    else:
                        raise Exception("Invalid connection string format")
                except Exception as direct_error:
                    logger.error(f"✗ Direct endpoint method also failed: {direct_error}")
                    return False
            
            # Set MCP server URL to point to our own app
            self.mcp_server_url = f"{app_service_url}/mcp/stream"
            self.model_deployment_name = model_deployment_name
            
            logger.info(f"Azure AI Foundry initialized successfully")
            logger.info(f"  Project client: {type(self.project_client)}")
            logger.info(f"  MCP Server URL: {self.mcp_server_url}")
            logger.info(f"  Model deployment: {self.model_deployment_name}")
            
            # Test the connection by trying to get project info
            try:
                logger.info("Testing connection by checking project endpoint...")
                endpoint_url = self.project_client.get_endpoint_url()
                logger.info(f"Project endpoint URL: {endpoint_url}")
            except Exception as test_error:
                logger.warning(f"Failed to test connection: {test_error}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure AI Foundry: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
    
    async def create_agent(self) -> Optional[str]:
        """Create an Azure AI Foundry agent with MCP tools"""
        if not self.initialized or not self.project_client:
            return None
            
        try:
            # Create MCP tool configuration
            mcp_tool = McpTool(
                server_label="todo-mcp-server",
                server_url=self.mcp_server_url,
                allowed_tools=[]  # Allow all tools
            )
            
            # Create agent
            agent = self.project_client.agents.create_agent(
                model=self.model_deployment_name,
                name="todo-mcp-agent",
                instructions=(
                    "You are a helpful AI assistant that manages todo items. "
                    "Use the provided MCP tools to help users create, read, update, and delete todos. "
                    "Be conversational and helpful. When users ask about todos, use the appropriate tools "
                    "to perform the requested actions. Always confirm what actions you've taken."
                ),
                tools=mcp_tool.definitions
            )
            
            logger.info(f"Created agent with ID: {agent.id}")
            return agent.id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return None
    
    async def create_thread(self) -> Optional[str]:
        """Create a new conversation thread"""
        if not self.initialized or not self.project_client:
            return None
            
        try:
            thread = self.project_client.agents.threads.create()
            logger.info(f"Created thread with ID: {thread.id}")
            return thread.id
            
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            return None
    
    async def send_message(self, thread_id: str, agent_id: str, message: str) -> Dict[str, Any]:
        """Send a message and get response from the agent"""
        if not self.initialized or not self.project_client:
            return {"error": "Azure AI Foundry not initialized"}
            
        try:
            # Create message
            message_obj = self.project_client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            # Create and run
            run = self.project_client.agents.runs.create(
                thread_id=thread_id,
                agent_id=agent_id
            )
            
            # Wait for completion and handle tool approvals
            tool_calls = []
            while run.status in ["queued", "in_progress", "requires_action"]:
                await asyncio.sleep(1)
                run = self.project_client.agents.runs.get(thread_id=thread_id, run_id=run.id)
                
                if run.status == "requires_action":
                    # Auto-approve all tool calls for now
                    if hasattr(run.required_action, 'submit_tool_approval'):
                        tool_approvals = []
                        for tool_call in run.required_action.submit_tool_approval.tool_calls:
                            tool_calls.append({
                                "tool_name": tool_call.function.name if hasattr(tool_call, 'function') else "unknown",
                                "description": f"Tool call: {tool_call.id}"
                            })
                            tool_approvals.append({
                                "tool_call_id": tool_call.id,
                                "approve": True
                            })
                        
                        if tool_approvals:
                            self.project_client.agents.runs.submit_tool_outputs(
                                thread_id=thread_id,
                                run_id=run.id,
                                tool_approvals=tool_approvals
                            )
            
            # Get the response
            messages = self.project_client.agents.messages.list(
                thread_id=thread_id,
                order=ListSortOrder.DESC,
                limit=1
            )
            
            if messages and messages.data:
                latest_message = messages.data[0]
                if latest_message.role == "assistant" and latest_message.text_messages:
                    response_text = latest_message.text_messages[0].text.value
                    return {
                        "response": response_text,
                        "tool_calls": tool_calls
                    }
            
            return {"response": "I'm sorry, I couldn't process your request.", "tool_calls": []}
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {"error": f"Failed to process message: {str(e)}"}

# Initialize Azure AI Foundry service
ai_foundry_service = AzureAIFoundryService()

# MCP Server Class
class MCPServer:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.initialize_tools()
        self.initialize_resources()
    
    def initialize_tools(self):
        """Initialize available MCP tools"""
        # Create todo tool
        create_todo_tool = Tool(
            name="create_todo",
            description="Create a new todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the todo"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Priority level"
                    }
                },
                "required": ["title"]
            }
        )
        self.tools["create_todo"] = create_todo_tool
        
        # List todos tool
        list_todos_tool = Tool(
            name="list_todos",
            description="Get all todo items",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_completed": {
                        "type": "boolean",
                        "description": "Filter by completion status"
                    }
                }
            }
        )
        self.tools["list_todos"] = list_todos_tool
        
        # Update todo tool
        update_todo_tool = Tool(
            name="update_todo",
            description="Update an existing todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "Todo ID to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Priority level"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Completion status"
                    }
                },
                "required": ["todo_id"]
            }
        )
        self.tools["update_todo"] = update_todo_tool
        
        # Delete todo tool
        delete_todo_tool = Tool(
            name="delete_todo",
            description="Delete a todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "Todo ID to delete"
                    }
                },
                "required": ["todo_id"]
            }
        )
        self.tools["delete_todo"] = delete_todo_tool
        
        # Mark complete tool
        mark_complete_tool = Tool(
            name="mark_todo_complete",
            description="Mark a todo as complete",
            inputSchema={
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "Todo ID to mark"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Completion status",
                        "default": True
                    }
                },
                "required": ["todo_id"]
            }
        )
        self.tools["mark_todo_complete"] = mark_complete_tool
    
    def initialize_resources(self):
        """Initialize available resources"""
        # Sample resource
        sample_resource = Resource(
            uri="mcp://server/todos",
            name="Todo List",
            description="Current todo list data",
            mimeType="application/json"
        )
        self.resources["todos"] = sample_resource
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                },
                "resources": {
                    "subscribe": True,
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "Todo MCP Server",
                "version": "1.0.0"
            }
        }
    
    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools_list = [tool.dict() for tool in self.tools.values()]
        return {"tools": tools_list}
    
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        global next_id
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise HTTPException(status_code=400, detail=f"Tool '{tool_name}' not found")
        
        if tool_name == "create_todo":
            title = arguments.get("title")
            if not title:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Error: Title is required"
                        }
                    ]
                }
            
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
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Todo with ID {todo_id} not found"
                        }
                    ]
                }
            
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
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Todo with ID {todo_id} not found"
                        }
                    ]
                }
            
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
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Todo with ID {todo_id} not found"
                        }
                    ]
                }
            
            todo = todos_storage[todo_id]
            todo.completed = arguments.get("completed", True)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Updated todo completion: {todo.dict()}"
                    }
                ]
            }
        
        return {"content": [{"type": "text", "text": "Tool executed successfully"}]}
    
    async def handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request"""
        resources_list = [resource.dict() for resource in self.resources.values()]
        return {"resources": resources_list}
    
    async def handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri")
        
        if uri == "mcp://server/todos":
            todos_data = [todo.dict() for todo in todos_storage.values()]
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(todos_data)
                    }
                ]
            }
        
        raise HTTPException(status_code=404, detail=f"Resource '{uri}' not found")

# Initialize MCP server
mcp_server = MCPServer()

# Template configuration
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Todo MCP FastAPI Server with Azure AI Foundry Chat")
    
    # Initialize Azure AI Foundry
    await ai_foundry_service.initialize()
    
    yield
    logger.info("Shutting down Todo MCP FastAPI Server")

# Create FastAPI app
app = FastAPI(
    title="Todo MCP Server with Azure AI Foundry Chat",
    description="Model Context Protocol server for todo management with AI chat integration",
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
        "ai_foundry_initialized": ai_foundry_service.initialized
    }

@app.get("/debug/azure-ai-status")
async def azure_ai_debug_status():
    """Comprehensive Azure AI debugging endpoint"""
    import traceback
    from azure.identity import DefaultAzureCredential
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "azure_ai_packages_available": AZURE_AI_AVAILABLE,
        "ai_foundry_service_initialized": ai_foundry_service.initialized,
        "environment_variables": {},
        "credential_test": {},
        "project_client_test": {},
        "agent_test": {}
    }
    
    # Check environment variables
    env_vars = [
        'AZURE_AI_PROJECT_ENDPOINT',
        'AZURE_AI_MODEL_DEPLOYMENT_NAME',
        'AZURE_APP_SERVICE_URL',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_DEPLOYMENT_NAME',
        'AZURE_TENANT_ID',
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'KEY' in var:
                status["environment_variables"][var] = f"{value[:10]}...***"
            else:
                status["environment_variables"][var] = value
        else:
            status["environment_variables"][var] = None
    
    # Test Azure credential
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        status["credential_test"] = {
            "success": True,
            "expires_on": token.expires_on,
            "message": "Credential test successful"
        }
    except Exception as e:
        status["credential_test"] = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    
    # Test project client
    if AZURE_AI_AVAILABLE:
        try:
            project_endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT')
            if project_endpoint:
                from azure.ai.projects import AIProjectClient
                credential = DefaultAzureCredential()
                
                # Try connection string method
                try:
                    client = AIProjectClient.from_connection_string(
                        conn_str=project_endpoint,
                        credential=credential
                    )
                    status["project_client_test"] = {
                        "success": True,
                        "method": "connection_string",
                        "message": "Project client created successfully"
                    }
                except Exception as conn_error:
                    # Try direct endpoint method
                    try:
                        parts = project_endpoint.split(';')
                        if len(parts) >= 4:
                            endpoint_url = f"https://{parts[3]}.{parts[0]}"
                            client = AIProjectClient(
                                endpoint=endpoint_url,
                                credential=credential
                            )
                            status["project_client_test"] = {
                                "success": True,
                                "method": "direct_endpoint",
                                "endpoint_url": endpoint_url,
                                "message": "Project client created with fallback method"
                            }
                        else:
                            raise Exception("Invalid connection string format")
                    except Exception as direct_error:
                        status["project_client_test"] = {
                            "success": False,
                            "connection_string_error": str(conn_error),
                            "direct_endpoint_error": str(direct_error),
                            "traceback": traceback.format_exc()
                        }
            else:
                status["project_client_test"] = {
                    "success": False,
                    "error": "AZURE_AI_PROJECT_ENDPOINT not configured"
                }
        except Exception as e:
            status["project_client_test"] = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    else:
        status["project_client_test"] = {
            "success": False,
            "error": "Azure AI packages not available"
        }
    
    return status

@app.get("/tools")
async def list_tools():
    """REST endpoint to list available tools"""
    return {"tools": [tool.dict() for tool in mcp_server.tools.values()]}

@app.get("/resources")
async def list_resources():
    """REST endpoint to list available resources"""
    return {"resources": [resource.dict() for resource in mcp_server.resources.values()]}

# REST API endpoints for direct usage
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
        title = todo_data.get("title", "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        description = todo_data.get("description", "")
        priority = todo_data.get("priority", "medium")
        
        if priority not in ["low", "medium", "high"]:
            priority = "medium"
        
        todo = Todo(
            id=next_id,
            title=title,
            description=description,
            priority=priority,
            completed=False,
            created_at=get_current_time()
        )
        
        todos_storage[todo.id] = todo
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
        title = todo_data["title"].strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        todo.title = title
    
    if "description" in todo_data:
        todo.description = todo_data["description"]
    
    if "priority" in todo_data:
        priority = todo_data["priority"]
        if priority in ["low", "medium", "high"]:
            todo.priority = priority
    
    if "completed" in todo_data:
        todo.completed = bool(todo_data["completed"])
    
    return todo.dict()

@app.patch("/api/todos/{todo_id}/complete")
async def toggle_todo_complete(todo_id: int, completion_data: dict):
    """Toggle todo completion status"""
    if todo_id not in todos_storage:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    todo = todos_storage[todo_id]
    todo.completed = bool(completion_data.get("completed", not todo.completed))
    
    return todo.dict()

@app.delete("/api/todos/{todo_id}")
async def delete_todo_api(todo_id: int):
    """Delete a todo via REST API"""
    if todo_id not in todos_storage:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    deleted_todo = todos_storage.pop(todo_id)
    return {"message": "Todo deleted successfully", "deleted_todo": deleted_todo.dict()}

# Chat API endpoints
@app.post("/api/chat/session")
async def create_chat_session():
    """Create a new chat session"""
    if not ai_foundry_service.initialized:
        raise HTTPException(status_code=503, detail="Azure AI Foundry service not available")
    
    try:
        session_id = str(uuid.uuid4())
        
        # Create agent and thread
        agent_id = await ai_foundry_service.create_agent()
        thread_id = await ai_foundry_service.create_thread()
        
        if not agent_id or not thread_id:
            raise HTTPException(status_code=500, detail="Failed to create chat session")
        
        # Store session
        chat_sessions[session_id] = ChatSession(
            session_id=session_id,
            thread_id=thread_id,
            agent_id=agent_id
        )
        
        return {"session_id": session_id}
        
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")

@app.post("/api/chat/message")
async def send_chat_message(chat_data: ChatMessage):
    """Send a message to the AI agent"""
    if not ai_foundry_service.initialized:
        raise HTTPException(status_code=503, detail="Azure AI Foundry service not available")
    
    session_id = chat_data.session_id
    message = chat_data.message
    
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session = chat_sessions[session_id]
    
    try:
        # Send message to Azure AI Foundry
        result = await ai_foundry_service.send_message(
            thread_id=session.thread_id,
            agent_id=session.agent_id,
            message=message
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to send chat message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@app.get("/api/chat/status")
async def chat_status():
    """Get the status of the Azure AI Foundry chat service"""
    return {
        "available": ai_foundry_service.initialized,
        "azure_ai_available": AZURE_AI_AVAILABLE,
        "project_endpoint": os.getenv('AZURE_AI_PROJECT_ENDPOINT'),
        "model_deployment": os.getenv('AZURE_AI_MODEL_DEPLOYMENT_NAME'),
        "app_service_url": os.getenv('AZURE_APP_SERVICE_URL')
    }

# MCP Streamable HTTP Endpoints
@app.get("/mcp/stream")
async def mcp_stream_info():
    """Information about the MCP stream endpoint"""
    return {
        "info": "MCP Streamable HTTP Transport Endpoint",
        "description": "This endpoint accepts POST requests with JSON-RPC 2.0 messages for MCP communication",
        "usage": "Use MCP Inspector or send POST requests with proper JSON-RPC payloads",
        "methods": ["POST"],
        "example_request": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
    }

@app.post("/mcp/stream")
async def mcp_stream_endpoint(request: Request):
    """Main MCP endpoint with streamable HTTP support"""
    try:
        message = await request.json()
        logger.info(f"Received MCP message: {message}")
        
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        if method == "initialize":
            result = await mcp_server.handle_initialize(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif method == "tools/list":
            result = await mcp_server.handle_tools_list(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif method == "tools/call":
            result = await mcp_server.handle_tools_call(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif method == "resources/list":
            result = await mcp_server.handle_resources_list(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif method == "resources/read":
            result = await mcp_server.handle_resources_read(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            }
        
    except Exception as e:
        logger.error(f"MCP stream error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": message.get("id") if 'message' in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

@app.get("/mcp/capabilities")
async def mcp_capabilities():
    """Return MCP server capabilities"""
    return {
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
