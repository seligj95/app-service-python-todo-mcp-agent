// Chat functionality for MCP Agent
class ChatInterface {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.chatForm = document.getElementById('chatForm');
        this.sendButton = document.getElementById('sendButton');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.sessionId = null;
        
        this.init();
    }
    
    async init() {
        // Initialize chat session
        try {
            await this.initializeSession();
            this.setupEventListeners();
            this.enableInterface();
            this.updateStatus('Ready to chat!', 'connected');
        } catch (error) {
            console.error('Failed to initialize chat:', error);
            this.updateStatus('Failed to connect to AI service', 'error');
        }
    }

    async initializeSession() {
        try {
            const response = await fetch('/api/chat/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.sessionId = data.session_id;
            console.log('Chat session initialized:', this.sessionId);
        } catch (error) {
            console.error('Session initialization failed:', error);
            throw error;
        }
    }

    setupEventListeners() {
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    enableInterface() {
        this.chatInput.disabled = false;
        this.sendButton.disabled = false;
        this.chatInput.focus();
    }

    disableInterface() {
        this.chatInput.disabled = true;
        this.sendButton.disabled = true;
    }

    updateStatus(message, type = 'info') {
        this.statusIndicator.innerHTML = `<span class="status-text status-${type}">${message}</span>`;
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || !this.sessionId) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        this.chatInput.value = '';
        
        // Show loading state
        this.setLoading(true);
        this.updateStatus('AI is thinking...', 'processing');

        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Add assistant response
            this.addMessage(data.response, 'assistant');
            
            // If there were tool calls, show them
            if (data.tool_calls && data.tool_calls.length > 0) {
                this.showToolCalls(data.tool_calls);
            }
            
            this.updateStatus('Ready to chat!', 'connected');
        } catch (error) {
            console.error('Send message failed:', error);
            this.addMessage('Sorry, I encountered an error processing your request. Please try again.', 'assistant', true);
            this.updateStatus('Error occurred', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message${isError ? ' error-message' : ''}`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <strong>${sender === 'user' ? 'You' : 'AI Assistant'}:</strong> ${this.formatMessage(content)}
            </div>
            <div class="message-time">${timestamp}</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showToolCalls(toolCalls) {
        const toolCallDiv = document.createElement('div');
        toolCallDiv.className = 'message tool-call-message';
        
        const timestamp = new Date().toLocaleTimeString();
        let toolCallsHtml = '<div class="message-content"><strong>Tool Calls:</strong><ul>';
        
        toolCalls.forEach(call => {
            toolCallsHtml += `<li><code>${call.tool_name}</code> - ${call.description || 'Tool executed'}</li>`;
        });
        
        toolCallsHtml += '</ul></div>';
        toolCallDiv.innerHTML = toolCallsHtml + `<div class="message-time">${timestamp}</div>`;
        
        this.chatMessages.appendChild(toolCallDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Basic formatting for messages
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    setLoading(loading) {
        const sendText = this.sendButton.querySelector('.send-text');
        const sendLoading = this.sendButton.querySelector('.send-loading');
        
        if (loading) {
            sendText.style.display = 'none';
            sendLoading.style.display = 'inline-block';
            this.disableInterface();
        } else {
            sendText.style.display = 'inline-block';
            sendLoading.style.display = 'none';
            this.enableInterface();
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});
