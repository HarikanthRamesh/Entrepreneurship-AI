# Entrepreneurship AI Chatbot - Setup and Deployment Guide

## Overview

This guide will help you set up and deploy the Python FastAPI-based entrepreneurship chatbot that replaces the original Node.js server while maintaining full compatibility with your existing frontend.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for version control)

### 1. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 2. Environment Setup (Recommended)

Create a `.env` file in the project root:

```env
# API Configuration
GOOGLE_API_KEY=AIzaSyBz_TfH820RAJWrTKOS0xuaKWUrScUaSX0
NODE_ENV=development

# Server Configuration
HOST=0.0.0.0
PORT=8000
REQUEST_TIMEOUT=30
MAX_OUTPUT_TOKENS=1500

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:5173,https://localhost:5173
```

### 3. Run the Server

```bash
# Development mode (with auto-reload)
python server.py

# Or using uvicorn directly
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

The server will start on `http://localhost:8000`

## 📋 API Endpoints

### Chat Endpoint
- **URL**: `POST /api/chat`
- **Purpose**: Send messages to the AI chatbot
- **Request Body**:
  ```json
  {
    "message": "How do I start a business?",
    "userType": "aspiring",  // "aspiring", "existing", or "general"
    "sessionId": "unique_session_id"
  }
  ```
- **Response**:
  ```json
  {
    "reply": "Here's how to start your business...",
    "userType": "aspiring",
    "sessionId": "unique_session_id",
    "success": true,
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
  ```

### Health Check
- **URL**: `GET /api/health`
- **Purpose**: Check if the API is running
- **Response**:
  ```json
  {
    "status": "OK",
    "message": "Chatbot API is running",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
  ```

### Clear Session
- **URL**: `DELETE /api/chat/{sessionId}?userType=aspiring`
- **Purpose**: Clear a specific chat session
- **Response**:
  ```json
  {
    "message": "Chat session cleared",
    "sessionId": "session_id"
  }
  ```

### Active Sessions
- **URL**: `GET /api/sessions`
- **Purpose**: Get information about active sessions (monitoring)
- **Response**:
  ```json
  {
    "activeSessions": 5,
    "sessions": ["aspiring_session1", "general_session2"],
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
  ```

## 🔧 Configuration Options

### User Types

The chatbot supports three user types, each with specialized instructions:

1. **aspiring**: For aspiring entrepreneurs starting new businesses
2. **existing**: For existing business owners looking to grow/scale
3. **general**: General entrepreneurship guidance

### Model Configuration

The AI model can be configured in `server.py`:

```python
# Model settings
MODEL_NAME = "gemini-1.5-flash"
MAX_OUTPUT_TOKENS = 1500
TEMPERATURE = 0.7
TOP_P = 0.8
TOP_K = 40
```

### CORS Settings

Update CORS settings for your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest httpx pytest-asyncio

# Run all tests
pytest test_server.py -v

# Run specific test class
pytest test_server.py::TestChatEndpoint -v

# Run with coverage
pip install pytest-cov
pytest test_server.py --cov=server --cov-report=html
```

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I start a business?", "userType": "aspiring"}'

# Test session clearing
curl -X DELETE "http://localhost:8000/api/chat/test_session?userType=aspiring"
```

## 🌐 Frontend Integration

### JavaScript/React Integration

Use the provided `ChatbotClient` class from `frontend_integration_example.js`:

```javascript
// Initialize the client
const chatbot = new ChatbotClient('http://localhost:8000');

// Set user type
chatbot.setUserType('aspiring');

// Send a message
const response = await chatbot.sendMessage('How do I start a business?');
console.log(response.reply);
```

### React Component

```jsx
import { ChatComponent } from './frontend_integration_example.js';

function App() {
  return (
    <div className="App">
      <ChatComponent />
    </div>
  );
}
```

### Vanilla JavaScript

```javascript
// Initialize the app
const chatApp = new VanillaChatApp('chat-container');
```

## 🚀 Deployment

### Development Deployment

```bash
# Using uvicorn with auto-reload
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Production Deployment

#### Option 1: Direct Uvicorn

```bash
# Production server with multiple workers
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Option 2: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Build and run:

```bash
docker build -t entrepreneurship-chatbot .
docker run -p 8000:8000 entrepreneurship-chatbot
```

#### Option 3: Cloud Deployment

**Heroku**:
1. Create `Procfile`:
   ```
   web: uvicorn server:app --host 0.0.0.0 --port $PORT
   ```
2. Deploy:
   ```bash
   git add .
   git commit -m "Deploy chatbot"
   git push heroku main
   ```

**AWS/GCP/Azure**: Use their respective container services or serverless functions.

## 🔒 Security Considerations

### API Key Management

1. **Never commit API keys to version control**
2. Use environment variables:
   ```python
   import os
   API_KEY = os.getenv('GOOGLE_API_KEY')
   ```
3. Use secrets management services in production

### Rate Limiting

Add rate limiting for production:

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    # ... existing code
```

### Input Validation

The API includes comprehensive input validation:
- Message length limits
- User type validation
- Session ID sanitization
- Request timeout handling

## 📊 Monitoring and Logging

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
```

### Health Monitoring

Monitor the `/api/health` endpoint and `/api/sessions` for system health.

### Metrics Collection

Consider adding metrics collection:

```bash
pip install prometheus-client
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **API Key Issues**:
   - Verify the API key is correct
   - Check Google AI Studio quotas
   - Ensure the API key has proper permissions

3. **CORS Issues**:
   - Update `allow_origins` in CORS middleware
   - Check frontend URL matches exactly

4. **Port Conflicts**:
   ```bash
   # Use different port
   uvicorn server:app --port 8001
   ```

5. **Memory Issues**:
   - Clear chat sessions periodically
   - Implement session cleanup
   - Use Redis for session storage in production

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 📈 Performance Optimization

### Session Management

Implement automatic session cleanup:

```python
import asyncio
from datetime import datetime, timedelta

async def cleanup_old_sessions():
    while True:
        # Clean up sessions older than 1 hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        # Implementation depends on session storage
        await asyncio.sleep(3600)  # Run every hour
```

### Caching

Consider implementing response caching for common queries:

```bash
pip install redis
```

### Database Integration

For production, consider using a database for session storage:

```bash
pip install sqlalchemy asyncpg  # PostgreSQL
# or
pip install sqlalchemy aiosqlite  # SQLite
```

## 🔄 Migration from Node.js

### API Compatibility

The Python API maintains 100% compatibility with the original Node.js API:
- Same endpoints (`/api/chat`, `/api/health`)
- Same request/response formats
- Same error handling patterns
- Same CORS configuration

### Frontend Changes

**No frontend changes required!** The API is drop-in compatible.

### Environment Variables

Update your environment variables:
- `NODE_ENV` → Still supported for compatibility
- Add `GOOGLE_API_KEY` if using environment variables

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google AI Python SDK](https://github.com/google/generative-ai-python)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test files for examples
3. Check the API documentation
4. Review the frontend integration examples

## 📝 License

This project maintains the same license as the original codebase.