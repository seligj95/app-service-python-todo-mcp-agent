"""
Flask application for Todo List with MCP integration.
"""
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

try:
    from models import db
    from todo_service import TodoService
except ImportError:
    from src.models import db
    from src.todo_service import TodoService


def create_app():
    """Create and configure the Flask application."""
    # Get the absolute path to the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Set paths relative to the project structure
    static_folder = os.path.join(project_root, 'static')
    template_folder = os.path.join(current_dir, 'templates')
    
    app = Flask(
        __name__,
        static_folder=static_folder,
        template_folder=template_folder
    )
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///todos.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Routes
    @app.route('/')
    def index():
        """Main todo list page."""
        return render_template('index.html')
    
    @app.route('/chat')
    def chat():
        """Chat interface page (placeholder)."""
        return render_template('chat.html')
    
    # API Routes
    @app.route('/api/todos', methods=['GET'])
    def get_todos():
        """Get all todos with optional filtering."""
        filter_completed = request.args.get('completed')
        if filter_completed is not None:
            filter_completed = filter_completed.lower() == 'true'
        
        todos = TodoService.get_todos(filter_completed)
        return jsonify(todos)
    
    @app.route('/api/todos', methods=['POST'])
    def create_todo():
        """Create a new todo."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = TodoService.create_todo(
            title=data.get('title'),
            description=data.get('description'),
            priority=data.get('priority', 'medium')
        )
        
        if result['success']:
            return jsonify(result['todo']), 201
        else:
            return jsonify({'error': result['error']}), 400
    
    @app.route('/api/todos/<int:todo_id>', methods=['GET'])
    def get_todo(todo_id):
        """Get a specific todo by ID."""
        todo = TodoService.get_todo_by_id(todo_id)
        if todo:
            return jsonify(todo)
        else:
            return jsonify({'error': 'Todo not found'}), 404
    
    @app.route('/api/todos/<int:todo_id>', methods=['PUT'])
    def update_todo(todo_id):
        """Update a todo."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = TodoService.update_todo(
            todo_id=todo_id,
            title=data.get('title'),
            description=data.get('description'),
            priority=data.get('priority'),
            completed=data.get('completed')
        )
        
        if result['success']:
            return jsonify(result['todo'])
        else:
            return jsonify({'error': result['error']}), 400
    
    @app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
    def delete_todo(todo_id):
        """Delete a todo."""
        result = TodoService.delete_todo(todo_id)
        
        if result['success']:
            return jsonify({'message': result['message']})
        else:
            return jsonify({'error': result['error']}), 400
    
    @app.route('/api/todos/<int:todo_id>/complete', methods=['PATCH'])
    def mark_complete(todo_id):
        """Mark a todo as complete/incomplete."""
        data = request.get_json() or {}
        completed = data.get('completed', True)
        
        result = TodoService.mark_todo_complete(todo_id, completed)
        
        if result['success']:
            return jsonify(result['todo'])
        else:
            return jsonify({'error': result['error']}), 400
    
    # Health check
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({'status': 'healthy', 'service': 'todo-app'})
    
    # MCP protocol endpoint
    @app.route('/mcp', methods=['POST'])
    def mcp_endpoint():
        """Handle MCP protocol requests."""
        try:
            request_data = request.get_json()
            
            # Simple MCP protocol handler
            if not request_data or 'method' not in request_data:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "Invalid Request"}
                }), 400
            
            method = request_data['method']
            request_id = request_data.get('id')
            
            if method == 'initialize':
                # MCP initialization handshake
                params = request_data.get('params', {})
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "todo-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                })
            
            elif method == 'notifications/initialized':
                # Initialization complete notification (no response needed)
                return '', 204
            
            elif method == 'tools/list':
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "create_todo",
                                "description": "Create a new todo item",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Title of the todo item"
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
                            },
                            {
                                "name": "list_todos",
                                "description": "Get all todo items",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "filter_completed": {
                                            "type": "boolean",
                                            "description": "Filter by completion status"
                                        }
                                    }
                                }
                            },
                            {
                                "name": "update_todo",
                                "description": "Update an existing todo item",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "todo_id": {
                                            "type": "integer",
                                            "description": "ID of the todo to update"
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
                            },
                            {
                                "name": "delete_todo",
                                "description": "Delete a todo item",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "todo_id": {
                                            "type": "integer",
                                            "description": "ID of the todo to delete"
                                        }
                                    },
                                    "required": ["todo_id"]
                                }
                            },
                            {
                                "name": "mark_todo_complete",
                                "description": "Mark a todo as complete",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "todo_id": {
                                            "type": "integer",
                                            "description": "ID of the todo to mark"
                                        },
                                        "completed": {
                                            "type": "boolean",
                                            "description": "Completion status",
                                            "default": True
                                        }
                                    },
                                    "required": ["todo_id"]
                                }
                            }
                        ]
                    }
                })
            
            elif method == 'tools/call':
                params = request_data.get('params', {})
                tool_name = params.get('name')
                arguments = params.get('arguments', {})
                
                if tool_name == 'create_todo':
                    result = TodoService.create_todo(
                        arguments.get('title'),
                        arguments.get('description', ''),
                        arguments.get('priority', 'medium')
                    )
                elif tool_name == 'list_todos':
                    result = TodoService.get_todos(
                        arguments.get('filter_completed')
                    )
                elif tool_name == 'update_todo':
                    result = TodoService.update_todo(
                        arguments.get('todo_id'),
                        arguments.get('title'),
                        arguments.get('description'),
                        arguments.get('priority'),
                        arguments.get('completed')
                    )
                elif tool_name == 'delete_todo':
                    result = TodoService.delete_todo(arguments.get('todo_id'))
                elif tool_name == 'mark_todo_complete':
                    result = TodoService.mark_todo_complete(
                        arguments.get('todo_id'),
                        arguments.get('completed', True)
                    )
                else:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }), 400
                
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": str(result)
                            }
                        ]
                    }
                })
            
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown method: {method}"
                    }
                }), 400
                
        except Exception as e:
            return jsonify({
                "jsonrpc": "2.0",
                "id": (request_data.get('id') if 'request_data' in locals()
                       and request_data else None),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }), 500
    
    # Direct tool endpoints for easier testing
    @app.route('/mcp/tools/create_todo', methods=['POST'])
    def mcp_create_todo():
        """Direct endpoint for create_todo tool."""
        data = request.get_json()
        result = TodoService.create_todo(
            data.get('title'),
            data.get('description', ''),
            data.get('priority', 'medium')
        )
        return jsonify(result)
    
    @app.route('/mcp/tools/list_todos', methods=['GET', 'POST'])
    def mcp_list_todos():
        """Direct endpoint for list_todos tool."""
        if request.method == 'POST':
            data = request.get_json() or {}
            filter_completed = data.get('filter_completed')
        else:
            filter_completed = request.args.get('filter_completed')
            if filter_completed is not None:
                filter_completed = filter_completed.lower() == 'true'
        
        result = TodoService.get_todos(filter_completed)
        return jsonify(result)
    
    @app.route('/mcp/tools/update_todo', methods=['POST'])
    def mcp_update_todo():
        """Direct endpoint for update_todo tool."""
        data = request.get_json()
        result = TodoService.update_todo(
            data.get('todo_id'),
            data.get('title'),
            data.get('description'),
            data.get('priority'),
            data.get('completed')
        )
        return jsonify(result)
    
    @app.route('/mcp/tools/delete_todo', methods=['POST'])
    def mcp_delete_todo():
        """Direct endpoint for delete_todo tool."""
        data = request.get_json()
        result = TodoService.delete_todo(data.get('todo_id'))
        return jsonify(result)
    
    @app.route('/mcp/tools/mark_todo_complete', methods=['POST'])
    def mcp_mark_complete():
        """Direct endpoint for mark_todo_complete tool."""
        data = request.get_json()
        result = TodoService.mark_todo_complete(
            data.get('todo_id'),
            data.get('completed', True)
        )
        return jsonify(result)
    
    # MCP info endpoint
    @app.route('/mcp', methods=['GET'])
    def mcp_info():
        """Provide information about the MCP server."""
        return jsonify({
            "name": "todo-mcp-server",
            "version": "1.0.0",
            "description": "MCP server for todo operations in Flask",
            "tools": [
                {
                    "name": "create_todo",
                    "endpoint": "/mcp/tools/create_todo",
                    "method": "POST"
                },
                {
                    "name": "list_todos", 
                    "endpoint": "/mcp/tools/list_todos",
                    "method": "GET|POST"
                },
                {
                    "name": "update_todo",
                    "endpoint": "/mcp/tools/update_todo", 
                    "method": "POST"
                },
                {
                    "name": "delete_todo",
                    "endpoint": "/mcp/tools/delete_todo",
                    "method": "POST"
                },
                {
                    "name": "mark_todo_complete",
                    "endpoint": "/mcp/tools/mark_todo_complete",
                    "method": "POST"
                }
            ]
        })
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
