/**
 * Frontend Integration Example for Entrepreneurship AI Chatbot
 * ===========================================================
 * 
 * This file demonstrates how to integrate the Python FastAPI chatbot
 * with a frontend application (React, Vue, vanilla JS, etc.)
 * 
 * Features demonstrated:
 * - Sending chat messages to the API
 * - Handling different user types
 * - Session management
 * - Error handling and retry logic
 * - Loading states and user feedback
 */

class ChatbotClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.sessionId = this.generateSessionId();
        this.userType = 'general'; // Default user type
    }

    /**
     * Generate a unique session ID for conversation continuity
     */
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Set the user type for the chatbot interaction
     * @param {string} type - 'aspiring', 'existing', or 'general'
     */
    setUserType(type) {
        const validTypes = ['aspiring', 'existing', 'general'];
        this.userType = validTypes.includes(type) ? type : 'general';
    }

    /**
     * Send a message to the chatbot API
     * @param {string} message - The user's message
     * @param {Object} options - Additional options
     * @returns {Promise<Object>} - API response
     */
    async sendMessage(message, options = {}) {
        const {
            timeout = 35000, // 35 second timeout (slightly longer than server timeout)
            retries = 2,
            onProgress = null
        } = options;

        // Input validation
        if (!message || typeof message !== 'string' || message.trim().length === 0) {
            throw new Error('Message is required and must be a non-empty string');
        }

        const requestData = {
            message: message.trim(),
            userType: this.userType,
            sessionId: this.sessionId
        };

        // Retry logic
        for (let attempt = 1; attempt <= retries + 1; attempt++) {
            try {
                if (onProgress) {
                    onProgress(`Sending message... (attempt ${attempt})`);
                }

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);

                const response = await fetch(`${this.baseUrl}/api/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                
                if (onProgress) {
                    onProgress('Message sent successfully');
                }

                return data;

            } catch (error) {
                console.error(`Attempt ${attempt} failed:`, error);

                // Don't retry on certain errors
                if (error.name === 'AbortError') {
                    throw new Error('Request timed out. Please try again.');
                }
                
                if (error.message.includes('401') || error.message.includes('Invalid API')) {
                    throw new Error('Authentication error. Please check API configuration.');
                }

                // If this was the last attempt, throw the error
                if (attempt === retries + 1) {
                    throw error;
                }

                // Wait before retrying (exponential backoff)
                await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt - 1) * 1000));
            }
        }
    }

    /**
     * Clear the current chat session
     */
    async clearSession() {
        try {
            const response = await fetch(
                `${this.baseUrl}/api/chat/${this.sessionId}?userType=${this.userType}`,
                { method: 'DELETE' }
            );

            if (response.ok) {
                // Generate new session ID for fresh start
                this.sessionId = this.generateSessionId();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Failed to clear session:', error);
            return false;
        }
    }

    /**
     * Check API health
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/api/health`);
            return response.ok ? await response.json() : null;
        } catch (error) {
            console.error('Health check failed:', error);
            return null;
        }
    }
}

// React Component Example
const ChatComponent = () => {
    const [messages, setMessages] = React.useState([]);
    const [inputMessage, setInputMessage] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);
    const [userType, setUserType] = React.useState('general');
    const [error, setError] = React.useState(null);
    const [chatbot] = React.useState(() => new ChatbotClient());

    // Update chatbot user type when state changes
    React.useEffect(() => {
        chatbot.setUserType(userType);
    }, [userType, chatbot]);

    const sendMessage = async () => {
        if (!inputMessage.trim() || isLoading) return;

        const userMessage = inputMessage.trim();
        setInputMessage('');
        setError(null);
        setIsLoading(true);

        // Add user message to chat
        setMessages(prev => [...prev, {
            id: Date.now(),
            text: userMessage,
            sender: 'user',
            timestamp: new Date().toISOString()
        }]);

        try {
            const response = await chatbot.sendMessage(userMessage, {
                onProgress: (status) => console.log(status)
            });

            // Add AI response to chat
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                text: response.reply,
                sender: 'ai',
                timestamp: response.timestamp,
                userType: response.userType
            }]);

        } catch (error) {
            setError(error.message);
            console.error('Chat error:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = async () => {
        const success = await chatbot.clearSession();
        if (success) {
            setMessages([]);
            setError(null);
        }
    };

    return React.createElement('div', { className: 'chat-container' }, [
        // User type selector
        React.createElement('div', { key: 'selector', className: 'user-type-selector' }, [
            React.createElement('label', { key: 'label' }, 'User Type: '),
            React.createElement('select', {
                key: 'select',
                value: userType,
                onChange: (e) => setUserType(e.target.value)
            }, [
                React.createElement('option', { key: 'general', value: 'general' }, 'General'),
                React.createElement('option', { key: 'aspiring', value: 'aspiring' }, 'Aspiring Entrepreneur'),
                React.createElement('option', { key: 'existing', value: 'existing' }, 'Existing Business Owner')
            ])
        ]),

        // Messages display
        React.createElement('div', { key: 'messages', className: 'messages' },
            messages.map(msg => 
                React.createElement('div', {
                    key: msg.id,
                    className: `message ${msg.sender}`
                }, [
                    React.createElement('div', { key: 'text', className: 'text' }, msg.text),
                    React.createElement('div', { key: 'time', className: 'timestamp' }, 
                        new Date(msg.timestamp).toLocaleTimeString()
                    )
                ])
            )
        ),

        // Error display
        error && React.createElement('div', { key: 'error', className: 'error' }, error),

        // Input area
        React.createElement('div', { key: 'input', className: 'input-area' }, [
            React.createElement('input', {
                key: 'textinput',
                type: 'text',
                value: inputMessage,
                onChange: (e) => setInputMessage(e.target.value),
                onKeyPress: (e) => e.key === 'Enter' && sendMessage(),
                placeholder: 'Ask about your business idea...',
                disabled: isLoading
            }),
            React.createElement('button', {
                key: 'send',
                onClick: sendMessage,
                disabled: isLoading || !inputMessage.trim()
            }, isLoading ? 'Sending...' : 'Send'),
            React.createElement('button', {
                key: 'clear',
                onClick: clearChat
            }, 'Clear Chat')
        ])
    ]);
};

// Vanilla JavaScript Example
class VanillaChatApp {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.chatbot = new ChatbotClient();
        this.messages = [];
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        this.container.innerHTML = `
            <div class="chat-app">
                <div class="user-type-selector">
                    <label>User Type:</label>
                    <select id="userTypeSelect">
                        <option value="general">General</option>
                        <option value="aspiring">Aspiring Entrepreneur</option>
                        <option value="existing">Existing Business Owner</option>
                    </select>
                </div>
                
                <div id="messagesContainer" class="messages-container">
                    <!-- Messages will be inserted here -->
                </div>
                
                <div id="errorContainer" class="error-container" style="display: none;">
                    <!-- Errors will be shown here -->
                </div>
                
                <div class="input-container">
                    <input type="text" id="messageInput" placeholder="Ask about your business idea..." />
                    <button id="sendButton">Send</button>
                    <button id="clearButton">Clear Chat</button>
                </div>
                
                <div id="loadingIndicator" class="loading" style="display: none;">
                    Thinking...
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        const userTypeSelect = document.getElementById('userTypeSelect');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const clearButton = document.getElementById('clearButton');

        userTypeSelect.addEventListener('change', (e) => {
            this.chatbot.setUserType(e.target.value);
        });

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        sendButton.addEventListener('click', () => this.sendMessage());
        clearButton.addEventListener('click', () => this.clearChat());
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;

        messageInput.value = '';
        this.showLoading(true);
        this.hideError();

        // Add user message
        this.addMessage(message, 'user');

        try {
            const response = await this.chatbot.sendMessage(message);
            this.addMessage(response.reply, 'ai');
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    addMessage(text, sender) {
        const messagesContainer = document.getElementById('messagesContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.innerHTML = `
            <div class="message-text">${text}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        `;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async clearChat() {
        await this.chatbot.clearSession();
        document.getElementById('messagesContainer').innerHTML = '';
        this.hideError();
    }

    showLoading(show) {
        const loading = document.getElementById('loadingIndicator');
        const sendButton = document.getElementById('sendButton');
        loading.style.display = show ? 'block' : 'none';
        sendButton.disabled = show;
    }

    showError(message) {
        const errorContainer = document.getElementById('errorContainer');
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
    }

    hideError() {
        const errorContainer = document.getElementById('errorContainer');
        errorContainer.style.display = 'none';
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChatbotClient, ChatComponent, VanillaChatApp };
}

// Usage examples:
// 
// For React:
// ReactDOM.render(React.createElement(ChatComponent), document.getElementById('root'));
//
// For Vanilla JS:
// const app = new VanillaChatApp('chat-container');
//
// For direct API usage:
// const chatbot = new ChatbotClient();
// chatbot.setUserType('aspiring');
// const response = await chatbot.sendMessage('How do I start a tech startup?');