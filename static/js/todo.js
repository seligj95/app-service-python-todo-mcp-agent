// Todo List JavaScript functionality

class TodoApp {
    constructor() {
        this.todos = [];
        this.init();
    }

    init() {
        this.loadTodos();
        this.bindEvents();
    }

    bindEvents() {
        // Add todo form
        const addForm = document.getElementById('addTodoForm');
        if (addForm) {
            addForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addTodo();
            });
        }

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                this.filterTodos(filter);
                
                // Update active button
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }

    async loadTodos() {
        try {
            const response = await fetch('/api/todos');
            this.todos = await response.json();
            this.renderTodos();
        } catch (error) {
            console.error('Error loading todos:', error);
            this.showError('Failed to load todos');
        }
    }

    async addTodo() {
        const titleInput = document.getElementById('todoTitle');
        const descInput = document.getElementById('todoDescription');
        const priorityInput = document.getElementById('todoPriority');

        const title = titleInput.value.trim();
        if (!title) {
            this.showError('Please enter a title');
            return;
        }

        const todoData = {
            title: title,
            description: descInput.value.trim(),
            priority: priorityInput.value
        };

        try {
            const response = await fetch('/api/todos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(todoData)
            });

            if (response.ok) {
                const newTodo = await response.json();
                this.todos.push(newTodo);
                this.renderTodos();
                
                // Clear form
                titleInput.value = '';
                descInput.value = '';
                priorityInput.value = 'medium';
                
                this.showSuccess('Todo added successfully!');
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to add todo');
            }
        } catch (error) {
            console.error('Error adding todo:', error);
            this.showError('Failed to add todo');
        }
    }

    async updateTodo(id, updates) {
        try {
            const response = await fetch(`/api/todos/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (response.ok) {
                const updatedTodo = await response.json();
                const index = this.todos.findIndex(t => t.id === id);
                if (index !== -1) {
                    this.todos[index] = updatedTodo;
                    this.renderTodos();
                }
                this.showSuccess('Todo updated successfully!');
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to update todo');
            }
        } catch (error) {
            console.error('Error updating todo:', error);
            this.showError('Failed to update todo');
        }
    }

    async deleteTodo(id) {
        if (!confirm('Are you sure you want to delete this todo?')) {
            return;
        }

        try {
            const response = await fetch(`/api/todos/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.todos = this.todos.filter(t => t.id !== id);
                this.renderTodos();
                this.showSuccess('Todo deleted successfully!');
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to delete todo');
            }
        } catch (error) {
            console.error('Error deleting todo:', error);
            this.showError('Failed to delete todo');
        }
    }

    async toggleComplete(id, completed) {
        try {
            const response = await fetch(`/api/todos/${id}/complete`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ completed: completed })
            });

            if (response.ok) {
                const updatedTodo = await response.json();
                const index = this.todos.findIndex(t => t.id === id);
                if (index !== -1) {
                    this.todos[index] = updatedTodo;
                    this.renderTodos();
                }
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to update todo');
            }
        } catch (error) {
            console.error('Error updating todo:', error);
            this.showError('Failed to update todo');
        }
    }

    filterTodos(filter) {
        const todoItems = document.querySelectorAll('.todo-item');
        
        todoItems.forEach(item => {
            const isCompleted = item.classList.contains('completed');
            
            switch(filter) {
                case 'all':
                    item.style.display = 'block';
                    break;
                case 'active':
                    item.style.display = isCompleted ? 'none' : 'block';
                    break;
                case 'completed':
                    item.style.display = isCompleted ? 'block' : 'none';
                    break;
            }
        });
    }

    renderTodos() {
        const container = document.getElementById('todoList');
        if (!container) return;

        if (this.todos.length === 0) {
            container.innerHTML = '<p class="no-todos">No todos yet. Add one above!</p>';
            return;
        }

        const html = this.todos.map(todo => `
            <div class="todo-item ${todo.completed ? 'completed' : ''}" data-id="${todo.id}">
                <div class="todo-content">
                    <div class="todo-header">
                        <input type="checkbox" 
                               class="todo-checkbox" 
                               ${todo.completed ? 'checked' : ''}
                               onchange="todoApp.toggleComplete(${todo.id}, this.checked)">
                        <h3 class="todo-title">${this.escapeHtml(todo.title)}</h3>
                        <span class="todo-priority priority-${todo.priority}">${todo.priority}</span>
                    </div>
                    ${todo.description ? `<p class="todo-description">${this.escapeHtml(todo.description)}</p>` : ''}
                    <div class="todo-meta">
                        <small class="todo-date">Created: ${new Date(todo.created_at).toLocaleString()}</small>
                    </div>
                </div>
                <div class="todo-actions">
                    <button class="btn btn-sm btn-edit" onclick="todoApp.editTodo(${todo.id})">Edit</button>
                    <button class="btn btn-sm btn-delete" onclick="todoApp.deleteTodo(${todo.id})">Delete</button>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    editTodo(id) {
        const todo = this.todos.find(t => t.id === id);
        if (!todo) return;

        const newTitle = prompt('Edit title:', todo.title);
        if (newTitle === null) return;

        const newDescription = prompt('Edit description:', todo.description || '');
        if (newDescription === null) return;

        const newPriority = prompt('Edit priority (low/medium/high):', todo.priority);
        if (newPriority === null) return;

        if (newTitle.trim()) {
            this.updateTodo(id, {
                title: newTitle.trim(),
                description: newDescription.trim(),
                priority: ['low', 'medium', 'high'].includes(newPriority) ? newPriority : 'medium'
            });
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        // Remove existing messages
        const existing = document.querySelector('.message');
        if (existing) {
            existing.remove();
        }

        // Create new message
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${type}`;
        messageEl.textContent = message;

        // Insert at top of page
        document.body.insertBefore(messageEl, document.body.firstChild);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.remove();
            }
        }, 3000);
    }
}

// Initialize the todo app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.todoApp = new TodoApp();
});
