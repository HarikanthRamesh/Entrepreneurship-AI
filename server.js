import express from 'express';
import cors from 'cors';
import { GoogleGenerativeAI } from '@google/generative-ai';

const app = express();
const PORT = process.env.PORT || 8000;

// API key and model setup
const API_KEY = 'AIzaSyBz_TfH820RAJWrTKOS0xuaKWUrScUaSX0';
const genAI = new GoogleGenerativeAI(API_KEY);

// CORS config to allow frontend interaction
app.use(cors({
  origin: ["http://localhost:5173", "https://localhost:5173"],
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"]
}));

app.use(express.json());

// Chat sessions storage (in production, use Redis or database)
const chatSessions = new Map();

// Instructions for different user types - Enhanced to match Python functionality
const instructions = {
  aspiring: `You are an entrepreneurship AI mentor and people can ask you suggestions and instructions to how to start or implement their business idea in real time. You have to provide them the step by step procedures to implement their business and helps them to become an entrepreneur.
    
    Focus on:
    - Step-by-step implementation procedures
    - Practical and actionable advice
    - Legal requirements and compliance
    - Market validation strategies
    - Startup fundamentals and best practices
    - Resource allocation and budgeting
    - Timeline planning and milestones
    
    Always provide detailed, structured responses with clear action items.`,
  
  existing: `You are a business growth strategist and digital transformation expert.
    Help existing business owners scale, automate, and digitally transform their businesses.
    Provide suggestions on marketing strategies, technology adoption, operational efficiency, and funding options.
    Focus on growth tactics, competitive positioning, and sustainable business expansion.
    
    Always provide step-by-step guidance for implementation.`,
    
  general: `You are an entrepreneurship AI mentor and people can ask you suggestions and instructions to how to start or implement their business idea in real time. You have to provide them the step by step procedures to implement their business and helps them to become an entrepreneur.`
};

// POST endpoint for chatbot interaction - Enhanced with better error handling
app.post('/api/chat', async (req, res) => {
  try {
    const { message, userType = 'general', sessionId = 'default' } = req.body;
    
    // Input validation
    if (!message || typeof message !== 'string' || message.trim().length === 0) {
      return res.status(400).json({ 
        error: 'Message is required and must be a non-empty string',
        success: false 
      });
    }

    // Validate userType
    const validUserTypes = ['aspiring', 'existing', 'general'];
    const selectedUserType = validUserTypes.includes(userType) ? userType : 'general';

    // Get or create chat session
    const sessionKey = `${selectedUserType}_${sessionId}`;
    let chat = chatSessions.get(sessionKey);
    
    if (!chat) {
      try {
        const model = genAI.getGenerativeModel({
          model: "gemini-1.5-flash",
          systemInstruction: instructions[selectedUserType]
        });
        
        chat = model.startChat({
          history: [],
          generationConfig: {
            maxOutputTokens: 1500, // Increased for more detailed responses
            temperature: 0.7,
            topP: 0.8,
            topK: 40,
          },
        });
        
        chatSessions.set(sessionKey, chat);
        console.log(`✅ New chat session created: ${sessionKey}`);
      } catch (modelError) {
        console.error('Model initialization error:', modelError);
        return res.status(500).json({ 
          error: 'Failed to initialize AI model',
          details: 'Please check API key and model configuration',
          success: false 
        });
      }
    }

    // Send message and get response with timeout handling
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Request timeout')), 30000); // 30 second timeout
    });

    const chatPromise = chat.sendMessage(message.trim());
    
    const result = await Promise.race([chatPromise, timeoutPromise]);
    const response = await result.response;
    const reply = response.text();

    // Log successful interaction
    console.log(`💬 Chat interaction - Session: ${sessionKey}, User: ${selectedUserType}`);

    res.json({ 
      reply: reply.trim(),
      userType: selectedUserType,
      sessionId,
      success: true,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Chat API Error:', error);
    
    // Handle specific error types
    let errorMessage = 'Failed to process chat message';
    let statusCode = 500;
    
    if (error.message === 'Request timeout') {
      errorMessage = 'Request timed out. Please try again.';
      statusCode = 408;
    } else if (error.message.includes('API key')) {
      errorMessage = 'Invalid API configuration';
      statusCode = 401;
    } else if (error.message.includes('quota')) {
      errorMessage = 'API quota exceeded. Please try again later.';
      statusCode = 429;
    }
    
    res.status(statusCode).json({ 
      error: errorMessage,
      details: process.env.NODE_ENV === 'development' ? error.message : undefined,
      success: false,
      timestamp: new Date().toISOString()
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'Chatbot API is running' });
});

// Clear chat session endpoint
app.delete('/api/chat/:sessionId', (req, res) => {
  const { sessionId } = req.params;
  const { userType = 'aspiring' } = req.query;
  
  const sessionKey = `${userType}_${sessionId}`;
  chatSessions.delete(sessionKey);
  
  res.json({ message: 'Chat session cleared' });
});

app.listen(PORT, () => {
  console.log(`🤖 Chatbot API server running on port ${PORT}`);
  console.log(`🔗 Health check: http://localhost:${PORT}/api/health`);
}); 