"""
Comprehensive Test Suite for Entrepreneurship AI Chatbot API
===========================================================

This test suite covers:
- API endpoint functionality
- Error handling and validation
- Session management
- Different user types
- Timeout handling
- Integration testing

Run tests with: pytest test_server.py -v
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime

# Import the FastAPI app
from server import app, chat_sessions, INSTRUCTIONS

# Create test client
client = TestClient(app)

class TestHealthEndpoint:
    """Test the health check endpoint"""
    
    def test_health_check_success(self):
        """Test successful health check"""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "OK"
        assert data["message"] == "Chatbot API is running"
        assert "timestamp" in data

class TestChatEndpoint:
    """Test the main chat endpoint"""
    
    def setup_method(self):
        """Clear chat sessions before each test"""
        chat_sessions.clear()
    
    def test_chat_valid_request(self):
        """Test successful chat interaction"""
        with patch('server.genai.GenerativeModel') as mock_model:
            # Mock the AI model and chat
            mock_chat = Mock()
            mock_response = Mock()
            mock_response.text = "Here's how to start your business: 1. Research your market..."
            mock_chat.send_message.return_value = mock_response
            
            mock_model_instance = Mock()
            mock_model_instance.start_chat.return_value = mock_chat
            mock_model.return_value = mock_model_instance
            
            # Send chat request
            response = client.post("/api/chat", json={
                "message": "How do I start a business?",
                "userType": "aspiring",
                "sessionId": "test_session"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["userType"] == "aspiring"
            assert data["sessionId"] == "test_session"
            assert "reply" in data
            assert "timestamp" in data
    
    def test_chat_empty_message(self):
        """Test chat with empty message"""
        response = client.post("/api/chat", json={
            "message": "",
            "userType": "general"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_invalid_user_type(self):
        """Test chat with invalid user type defaults to general"""
        with patch('server.genai.GenerativeModel') as mock_model:
            mock_chat = Mock()
            mock_response = Mock()
            mock_response.text = "General business advice..."
            mock_chat.send_message.return_value = mock_response
            
            mock_model_instance = Mock()
            mock_model_instance.start_chat.return_value = mock_chat
            mock_model.return_value = mock_model_instance
            
            response = client.post("/api/chat", json={
                "message": "Test message",
                "userType": "invalid_type"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["userType"] == "general"  # Should default to general
    
    def test_chat_session_persistence(self):
        """Test that chat sessions persist across requests"""
        with patch('server.genai.GenerativeModel') as mock_model:
            mock_chat = Mock()
            mock_response = Mock()
            mock_response.text = "Response"
            mock_chat.send_message.return_value = mock_response
            
            mock_model_instance = Mock()
            mock_model_instance.start_chat.return_value = mock_chat
            mock_model.return_value = mock_model_instance
            
            # First request
            response1 = client.post("/api/chat", json={
                "message": "First message",
                "sessionId": "persistent_session"
            })
            assert response1.status_code == 200
            
            # Second request with same session
            response2 = client.post("/api/chat", json={
                "message": "Second message",
                "sessionId": "persistent_session"
            })
            assert response2.status_code == 200
            
            # Model should only be created once
            assert mock_model.call_count == 1
    
    def test_chat_different_user_types_instructions(self):
        """Test that different user types get different instructions"""
        with patch('server.genai.GenerativeModel') as mock_model:
            mock_chat = Mock()
            mock_response = Mock()
            mock_response.text = "Response"
            mock_chat.send_message.return_value = mock_response
            
            mock_model_instance = Mock()
            mock_model_instance.start_chat.return_value = mock_chat
            mock_model.return_value = mock_model_instance
            
            # Test aspiring entrepreneur
            client.post("/api/chat", json={
                "message": "Test",
                "userType": "aspiring",
                "sessionId": "aspiring_session"
            })
            
            # Check that the model was created with aspiring instructions
            mock_model.assert_called_with(
                model_name="gemini-1.5-flash",
                system_instruction=INSTRUCTIONS["aspiring"]
            )
            
            # Reset mock
            mock_model.reset_mock()
            
            # Test existing business owner
            client.post("/api/chat", json={
                "message": "Test",
                "userType": "existing",
                "sessionId": "existing_session"
            })
            
            # Check that the model was created with existing instructions
            mock_model.assert_called_with(
                model_name="gemini-1.5-flash",
                system_instruction=INSTRUCTIONS["existing"]
            )

class TestSessionManagement:
    """Test session management endpoints"""
    
    def setup_method(self):
        """Clear chat sessions before each test"""
        chat_sessions.clear()
    
    def test_clear_session(self):
        """Test clearing a chat session"""
        # First, create a session
        chat_sessions["aspiring_test_session"] = Mock()
        
        # Clear the session
        response = client.delete("/api/chat/test_session?userType=aspiring")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Chat session cleared"
        assert data["sessionId"] == "test_session"
        
        # Verify session was removed
        assert "aspiring_test_session" not in chat_sessions
    
    def test_get_active_sessions(self):
        """Test getting active sessions information"""
        # Add some mock sessions
        chat_sessions["general_session1"] = Mock()
        chat_sessions["aspiring_session2"] = Mock()
        
        response = client.get("/api/sessions")
        assert response.status_code == 200
        
        data = response.json()
        assert data["activeSessions"] == 2
        assert "general_session1" in data["sessions"]
        assert "aspiring_session2" in data["sessions"]
        assert "timestamp" in data

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def setup_method(self):
        """Clear chat sessions before each test"""
        chat_sessions.clear()
    
    def test_api_key_error(self):
        """Test handling of API key errors"""
        with patch('server.genai.GenerativeModel') as mock_model:
            mock_model.side_effect = Exception("API key invalid")
            
            response = client.post("/api/chat", json={
                "message": "Test message",
                "sessionId": "error_session"
            })
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "Failed to initialize AI model" in data["detail"]
    
    def test_quota_exceeded_error(self):
        """Test handling of quota exceeded errors"""
        with patch('server.genai.GenerativeModel') as mock_model:
            mock_chat = Mock()
            mock_chat.send_message.side_effect = Exception("quota exceeded")
            
            mock_model_instance = Mock()
            mock_model_instance.start_chat.return_value = mock_chat
            mock_model.return_value = mock_model_instance
            
            response = client.post("/api/chat", json={
                "message": "Test message",
                "sessionId": "quota_session"
            })
            
            assert response.status_code == 429
            data = response.json()
            assert "quota exceeded" in data["detail"].lower()
    
    def test_timeout_handling(self):
        """Test timeout handling"""
        with patch('server.genai.GenerativeModel') as mock_model:
            mock_chat = Mock()
            # Simulate a long-running request
            def slow_response(message):
                import time
                time.sleep(35)  # Longer than timeout
                return Mock(text="Response")
            
            mock_chat.send_message.side_effect = slow_response
            
            mock_model_instance = Mock()
            mock_model_instance.start_chat.return_value = mock_chat
            mock_model.return_value = mock_model_instance
            
            response = client.post("/api/chat", json={
                "message": "Test message",
                "sessionId": "timeout_session"
            })
            
            # Should timeout and return 408
            assert response.status_code == 408
            data = response.json()
            assert "timeout" in data["detail"].lower()

class TestValidation:
    """Test input validation"""
    
    def test_message_too_long(self):
        """Test message length validation"""
        long_message = "x" * 2001  # Exceeds max length
        
        response = client.post("/api/chat", json={
            "message": long_message,
            "userType": "general"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_message(self):
        """Test missing message field"""
        response = client.post("/api/chat", json={
            "userType": "general"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_whitespace_only_message(self):
        """Test message with only whitespace"""
        response = client.post("/api/chat", json={
            "message": "   \n\t   ",
            "userType": "general"
        })
        
        assert response.status_code == 422  # Validation error

class TestCORSAndMiddleware:
    """Test CORS and middleware functionality"""
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/api/chat")
        
        # Check that CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

# Integration test class
class TestIntegration:
    """Integration tests that test the full flow"""
    
    def setup_method(self):
        """Clear chat sessions before each test"""
        chat_sessions.clear()
    
    def test_full_conversation_flow(self):
        """Test a complete conversation flow"""
        with patch('server.genai.GenerativeModel') as mock_model:
            mock_chat = Mock()
            responses = [
                "Great question! Here's how to start...",
                "For funding, consider these options...",
                "Legal requirements include..."
            ]
            mock_chat.send_message.side_effect = [
                Mock(text=resp) for resp in responses
            ]
            
            mock_model_instance = Mock()
            mock_model_instance.start_chat.return_value = mock_chat
            mock_model.return_value = mock_model_instance
            
            session_id = "integration_test"
            
            # First message
            response1 = client.post("/api/chat", json={
                "message": "How do I start a business?",
                "userType": "aspiring",
                "sessionId": session_id
            })
            assert response1.status_code == 200
            assert responses[0] in response1.json()["reply"]
            
            # Second message in same session
            response2 = client.post("/api/chat", json={
                "message": "What about funding?",
                "userType": "aspiring",
                "sessionId": session_id
            })
            assert response2.status_code == 200
            assert responses[1] in response2.json()["reply"]
            
            # Third message in same session
            response3 = client.post("/api/chat", json={
                "message": "Legal requirements?",
                "userType": "aspiring",
                "sessionId": session_id
            })
            assert response3.status_code == 200
            assert responses[2] in response3.json()["reply"]
            
            # Verify all messages used the same chat session
            assert mock_chat.send_message.call_count == 3

# Performance and load testing
class TestPerformance:
    """Basic performance tests"""
    
    def setup_method(self):
        """Clear chat sessions before each test"""
        chat_sessions.clear()
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        with patch('server.genai.GenerativeModel') as mock_model:
            mock_chat = Mock()
            mock_response = Mock()
            mock_response.text = "Concurrent response"
            mock_chat.send_message.return_value = mock_response
            
            mock_model_instance = Mock()
            mock_model_instance.start_chat.return_value = mock_chat
            mock_model.return_value = mock_model_instance
            
            results = []
            
            def make_request(session_id):
                response = client.post("/api/chat", json={
                    "message": f"Test message {session_id}",
                    "sessionId": f"concurrent_{session_id}"
                })
                results.append(response.status_code)
            
            # Create multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=make_request, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # All requests should succeed
            assert all(status == 200 for status in results)
            assert len(results) == 5

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])