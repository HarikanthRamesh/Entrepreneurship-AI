"""
Entrepreneurship AI Chatbot API Server
=====================================

This FastAPI server provides a chatbot API for entrepreneurship mentoring with support for:
- Multiple user types (aspiring, existing, general entrepreneurs)
- Session management for conversation continuity
- Comprehensive error handling and validation
- CORS support for frontend integration
- Health monitoring and session management endpoints

Dependencies:
- fastapi: Web framework for building APIs
- uvicorn: ASGI server for running FastAPI
- google-generativeai: Google's Gemini AI integration
- python-multipart: For handling form data
- python-dotenv: For environment variable management

Setup:
1. Install dependencies: pip install fastapi uvicorn google-generativeai python-multipart python-dotenv
2. Set environment variables or update API_KEY directly
3. Run with: uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
import logging
from contextlib import asynccontextmanager

import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = 'AIzaSyBz_TfH820RAJWrTKOS0xuaKWUrScUaSX0'  # In production, use environment variables
REQUEST_TIMEOUT = 30  # seconds
MAX_OUTPUT_TOKENS = 1500

# Configure Google AI
genai.configure(api_key=API_KEY)

# Global chat sessions storage (in production, use Redis or database)
chat_sessions: Dict[str, Any] = {}

# Enhanced instructions for different user types
INSTRUCTIONS = {
    "aspiring": """You are an entrepreneurship AI mentor and people can ask you suggestions and instructions to how to start or implement their business idea in real time. You have to provide them the step by step procedures to implement their business and helps them to become an entrepreneur.
    
    Focus on:
    - Step-by-step implementation procedures
    - Practical and actionable advice
    - Legal requirements and compliance
    - Market validation strategies
    - Startup fundamentals and best practices
    - Resource allocation and budgeting
    - Timeline planning and milestones
    
    Always provide detailed, structured responses with clear action items.""",
    
    "existing": """You are a business growth strategist and digital transformation expert.
    Help existing business owners scale, automate, and digitally transform their businesses.
    Provide suggestions on marketing strategies, technology adoption, operational efficiency, and funding options.
    Focus on growth tactics, competitive positioning, and sustainable business expansion.
    
    Always provide step-by-step guidance for implementation.""",
    
    "general": """You are an entrepreneurship AI mentor and people can ask you suggestions and instructions to how to start or implement their business idea in real time. You have to provide them the step by step procedures to implement their business and helps them to become an entrepreneur."""
}

# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    userType: str = Field(default="general", description="Type of user: aspiring, existing, or general")
    sessionId: str = Field(default="default", description="Session identifier for conversation continuity")
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()
    
    @validator('userType')
    def validate_user_type(cls, v):
        valid_types = ['aspiring', 'existing', 'general']
        return v if v in valid_types else 'general'

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    reply: str
    userType: str
    sessionId: str
    success: bool = True
    timestamp: str

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    details: Optional[str] = None
    success: bool = False
    timestamp: str

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    message: str
    timestamp: str

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    logger.info("🚀 Starting Entrepreneurship AI Chatbot API")
    logger.info(f"📊 API Key configured: {'✅' if API_KEY else '❌'}")
    yield
    logger.info("🛑 Shutting down Entrepreneurship AI Chatbot API")
    # Clean up chat sessions
    chat_sessions.clear()

# Initialize FastAPI app
app = FastAPI(
    title="Entrepreneurship AI Chatbot API",
    description="AI-powered chatbot for entrepreneurship mentoring and business guidance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration - matches original server.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Utility functions
def get_session_key(user_type: str, session_id: str) -> str:
    """Generate session key for chat storage"""
    return f"{user_type}_{session_id}"

async def create_chat_session(user_type: str) -> Any:
    """Create a new chat session with the specified user type"""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=INSTRUCTIONS[user_type]
        )
        
        chat = model.start_chat(
            history=[],
        )
        
        return chat
    except Exception as e:
        logger.error(f"Failed to create chat session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize AI model"
        )

async def send_message_with_timeout(chat: Any, message: str) -> str:
    """Send message to chat with timeout handling"""
    try:
        # Create timeout task
        timeout_task = asyncio.create_task(asyncio.sleep(REQUEST_TIMEOUT))
        
        # Create chat task (run in thread pool since it's not async)
        chat_task = asyncio.create_task(
            asyncio.get_event_loop().run_in_executor(
                None, lambda: chat.send_message(message)
            )
        )
        
        # Race between timeout and chat response
        done, pending = await asyncio.wait(
            [timeout_task, chat_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        # Check which task completed first
        if timeout_task in done:
            raise HTTPException(status_code=408, detail="Request timed out. Please try again.")
        
        # Get the chat result
        result = await chat_task
        return result.text
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        if "API key" in str(e).lower():
            raise HTTPException(status_code=401, detail="Invalid API configuration")
        elif "quota" in str(e).lower():
            raise HTTPException(status_code=429, detail="API quota exceeded. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail="Failed to process chat message")

# API Endpoints

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for interacting with the AI chatbot
    
    This endpoint:
    1. Validates the incoming request
    2. Manages chat sessions for conversation continuity
    3. Sends messages to the AI model with timeout handling
    4. Returns structured responses with error handling
    
    Args:
        request: ChatRequest containing message, userType, and sessionId
        
    Returns:
        ChatResponse with AI reply and metadata
        
    Raises:
        HTTPException: For various error conditions (validation, timeout, API errors)
    """
    try:
        # Generate session key
        session_key = get_session_key(request.userType, request.sessionId)
        
        # Get or create chat session
        if session_key not in chat_sessions:
            chat_sessions[session_key] = await create_chat_session(request.userType)
            logger.info(f"✅ New chat session created: {session_key}")
        
        chat = chat_sessions[session_key]
        
        # Send message and get response with timeout
        reply = await send_message_with_timeout(chat, request.message)
        
        # Log successful interaction
        logger.info(f"💬 Chat interaction - Session: {session_key}, User: {request.userType}")
        
        return ChatResponse(
            reply=reply.strip(),
            userType=request.userType,
            sessionId=request.sessionId,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API status
    
    Returns:
        HealthResponse indicating the API is running
    """
    return HealthResponse(
        status="OK",
        message="Chatbot API is running",
        timestamp=datetime.now().isoformat()
    )

@app.delete("/api/chat/{session_id}")
async def clear_chat_session(session_id: str, userType: str = "aspiring"):
    """
    Clear a specific chat session
    
    Args:
        session_id: The session identifier to clear
        userType: The user type for the session (query parameter)
        
    Returns:
        Success message
    """
    session_key = get_session_key(userType, session_id)
    
    if session_key in chat_sessions:
        del chat_sessions[session_key]
        logger.info(f"🗑️ Chat session cleared: {session_key}")
    
    return {"message": "Chat session cleared", "sessionId": session_id}

@app.get("/api/sessions")
async def get_active_sessions():
    """
    Get information about active chat sessions (for monitoring)
    
    Returns:
        Dictionary with session information
    """
    return {
        "activeSessions": len(chat_sessions),
        "sessions": list(chat_sessions.keys()),
        "timestamp": datetime.now().isoformat()
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc) if os.getenv("NODE_ENV") == "development" else None,
            timestamp=datetime.now().isoformat()
        ).dict()
    )

# Main execution
if __name__ == "__main__":
    """
    Run the server directly with uvicorn
    
    For development:
        python server.py
        
    For production:
        uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
    """
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )