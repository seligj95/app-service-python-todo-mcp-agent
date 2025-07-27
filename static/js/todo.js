/**
 * Todo App JavaScript functionality
 */

class TodoApp {
    constructor() {
        this.currentFilter = 'all';
        this.editModal = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTodos();
        this.editModal = new bootstrap.Modal(document.getElementById('editModal'));
    }

    bindEvents() {
        // Add todo form
        document.getElementById('addTodoForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTodo();
        });

        // Filter buttons
        document.querySelectorAll('[data-filter]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter(e.target.dataset.filter);
            });
        });

        // Edit form
        document.getElementById('saveEditBtn').addEventListener('click', () => {
            this.saveEdit();
        });
    }

    async loadTodos() {
        try {
            let url = '/api/todos';
            if (this.currentFilter === 'complete') {
                url += '?completed=true';
            } else if (this.currentFilter === 'incomplete') {
                url += '?completed=false';
            }

            const response = await fetch(url);
            const todos = await response.json();
            this.renderTodos(todos);
        } catch (error) {
            console.error('Error loading todos:', error);
            this.showError('Failed to load todos');
        }
    }

    async addTodo() {
        const title = document.getElementById('todoTitle').value.trim();
        const description = document.getElementById('todoDescription').value.trim();
        const priority = document.getElementById('todoPriority').value;

        if (!title) {
            this.showError('Title is required');
            return;
        }

        try {
            const response = await fetch('/api/todos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title,
                    description,
                    priority
                })
            });

            if (response.ok) {
                document.getElementById('addTodoForm').reset();
                this.loadTodos();
                this.showSuccess('Todo added successfully');
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to add todo');
            }
        } catch (error) {
            console.error('Error adding todo:', error);
            this.showError('Failed to add todo');
        }
    }

    async toggleComplete(todoId, completed) {
        try {
            const response = await fetch(`/api/todos/${todoId}/complete`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ completed })
            });

            if (response.ok) {
                this.loadTodos();
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to update todo');
            }
        } catch (error) {
            console.error('Error updating todo:', error);
            this.showError('Failed to update todo');
        }
    }

    async deleteTodo(todoId) {
        if (!confirm('Are you sure you want to delete this todo?')) {
            return;
        }

        try {
            const response = await fetch(`/api/todos/${todoId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.loadTodos();
                this.showSuccess('Todo deleted successfully');
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to delete todo');
            }
        } catch (error) {
            console.error('Error deleting todo:', error);
            this.showError('Failed to delete todo');
        }
    }

    editTodo(todo) {
        document.getElementById('editTodoId').value = todo.id;
        document.getElementById('editTodoTitle').value = todo.title;
        document.getElementById('editTodoDescription').value = todo.description || '';
        document.getElementById('editTodoPriority').value = todo.priority;
        this.editModal.show();
    }

    async saveEdit() {
        const id = document.getElementById('editTodoId').value;
        const title = document.getElementById('editTodoTitle').value.trim();
        const description = document.getElementById('editTodoDescription').value.trim();
        const priority = document.getElementById('editTodoPriority').value;

        if (!title) {
            this.showError('Title is required');
            return;
        }

        try {
            const response = await fetch(`/api/todos/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title,
                    description,
                    priority
                })
            });

            if (response.ok) {
                this.editModal.hide();
                this.loadTodos();
                this.showSuccess('Todo updated successfully');
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to update todo');
            }
        } catch (error) {
            console.error('Error updating todo:', error);
            this.showError('Failed to update todo');
        }
    }

    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update button states
        document.querySelectorAll('[data-filter]').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-filter="${filter}"]`).classList.add('active');
        
        this.loadTodos();
    }

    renderTodos(todos) {
        const container = document.getElementById('todoList');
        const emptyState = document.getElementById('emptyState');

        if (todos.length === 0) {
            container.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';
        
        const html = todos.map(todo => this.renderTodoItem(todo)).join('');
        container.innerHTML = html;
    }

    renderTodoItem(todo) {
        const priorityColors = {
            low: 'success',
            medium: 'warning', 
            high: 'danger'
        };

        const priorityColor = priorityColors[todo.priority] || 'secondary';
        const completedClass = todo.completed ? 'text-decoration-line-through text-muted' : '';
        const createdAt = new Date(todo.created_at).toLocaleString();

        return `
            <div class="card mb-2 ${todo.completed ? 'border-success' : ''}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-2">
                                <input type="checkbox" class="form-check-input me-2" 
                                       ${todo.completed ? 'checked' : ''} 
                                       onchange="todoApp.toggleComplete(${todo.id}, this.checked)">
                                <h6 class="mb-0 ${completedClass}">${this.escapeHtml(todo.title)}</h6>
                                <span class="badge bg-${priorityColor} ms-2">${todo.priority}</span>
                            </div>
                            ${todo.description ? `<p class="mb-1 small ${completedClass}">${this.escapeHtml(todo.description)}</p>` : ''}
                            <small class="text-muted">
                                <i class="fas fa-clock me-1"></i>
                                Created: ${createdAt}
                            </small>
                        </div>
                        <div class="ms-3">
                            <button class="btn btn-sm btn-outline-primary me-1" 
                                    onclick="todoApp.editTodo(${JSON.stringify(todo).replace(/"/g, '&quot;')})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" 
                                    onclick="todoApp.deleteTodo(${todo.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('.container');
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 3000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.todoApp = new TodoApp();
});
