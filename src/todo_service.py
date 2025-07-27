"""
Business logic service for Todo operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError

try:
    from models import Todo, db
except ImportError:
    from src.models import Todo, db


class TodoService:
    """Service class for todo operations."""
    
    @staticmethod
    def create_todo(title: str, description: str = None,
                    priority: str = 'medium') -> Dict[str, Any]:
        """
        Create a new todo item.
        
        Args:
            title: Todo title (required)
            description: Todo description (optional)
            priority: Priority level (low, medium, high)
            
        Returns:
            Dictionary with success status and todo data or error message
        """
        try:
            if not title or not title.strip():
                return {
                    'success': False,
                    'error': 'Title is required'
                }
                
            if priority not in ['low', 'medium', 'high']:
                priority = 'medium'
                
            todo = Todo(
                title=title.strip(),
                description=description.strip() if description else None,
                priority=priority
            )
            
            db.session.add(todo)
            db.session.commit()
            
            return {
                'success': True,
                'todo': todo.to_dict()
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    @staticmethod
    def get_todos(filter_completed: Optional[bool] = None) -> List[Dict]:
        """
        Get all todos, optionally filtered by completion status.
        
        Args:
            filter_completed: If True, return only completed todos.
                            If False, return only incomplete todos.
                            If None, return all todos.
                            
        Returns:
            List of todo dictionaries
        """
        try:
            query = Todo.query
            
            if filter_completed is not None:
                query = query.filter(Todo.completed == filter_completed)
                
            todos = query.order_by(Todo.created_at.desc()).all()
            return [todo.to_dict() for todo in todos]
            
        except SQLAlchemyError:
            return []
    
    @staticmethod
    def get_todo_by_id(todo_id: int) -> Optional[Dict]:
        """
        Get a specific todo by ID.
        
        Args:
            todo_id: Todo ID
            
        Returns:
            Todo dictionary or None if not found
        """
        try:
            todo = Todo.query.get(todo_id)
            return todo.to_dict() if todo else None
        except SQLAlchemyError:
            return None
    
    @staticmethod
    def update_todo(todo_id: int, title: str = None,
                    description: str = None, priority: str = None,
                    completed: bool = None) -> Dict[str, Any]:
        """
        Update an existing todo item.
        
        Args:
            todo_id: Todo ID to update
            title: New title (optional)
            description: New description (optional)
            priority: New priority (optional)
            completed: New completion status (optional)
            
        Returns:
            Dictionary with success status and updated todo or error message
        """
        try:
            todo = Todo.query.get(todo_id)
            if not todo:
                return {
                    'success': False,
                    'error': 'Todo not found'
                }
            
            # Update fields if provided
            if title is not None:
                if not title.strip():
                    return {
                        'success': False,
                        'error': 'Title cannot be empty'
                    }
                todo.title = title.strip()
                
            if description is not None:
                todo.description = description.strip() if description else None
                
            if priority is not None:
                if priority in ['low', 'medium', 'high']:
                    todo.priority = priority
                    
            if completed is not None:
                todo.completed = completed
                
            db.session.commit()
            
            return {
                'success': True,
                'todo': todo.to_dict()
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    @staticmethod
    def delete_todo(todo_id: int) -> Dict[str, Any]:
        """
        Delete a todo item.
        
        Args:
            todo_id: Todo ID to delete
            
        Returns:
            Dictionary with success status and message
        """
        try:
            todo = Todo.query.get(todo_id)
            if not todo:
                return {
                    'success': False,
                    'error': 'Todo not found'
                }
                
            db.session.delete(todo)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Todo deleted successfully'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    @staticmethod
    def mark_todo_complete(todo_id: int,
                           completed: bool = True) -> Dict[str, Any]:
        """
        Mark a todo as complete or incomplete.
        
        Args:
            todo_id: Todo ID to update
            completed: Completion status (True for complete,
                       False for incomplete)
            
        Returns:
            Dictionary with success status and updated todo or error message
        """
        return TodoService.update_todo(todo_id, completed=completed)
