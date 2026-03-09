"""
Unit tests for Marathi Chatbot Component

Tests AWS Bedrock integration, conversation management, and Marathi responses.
Property-based tests for chatbot behavior.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from hypothesis import given, strategies as st, settings

# Import the component
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'components'))
from marathi_chatbot import MarathiChatbot


class TestMarathiChatbot:
    """Test suite for MarathiChatbot component"""
    
    def test_initialization(self):
        """Test chatbot initialization"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        assert chatbot.bedrock_client == mock_bedrock
        assert chatbot.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert len(chatbot.conversation_history) == 0
        assert chatbot.max_history_length == 20
    
    def test_system_prompt_in_marathi(self):
        """Test system prompt is in Marathi"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        # Verify Marathi text in system prompt
        assert 'कृषी' in chatbot.SYSTEM_PROMPT
        assert 'शेतकरी' in chatbot.SYSTEM_PROMPT or 'शेतकऱ्यां' in chatbot.SYSTEM_PROMPT
        assert 'मराठी' in chatbot.SYSTEM_PROMPT
    
    def test_fallback_message_in_marathi(self):
        """Test fallback message is in Marathi"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        assert 'माफ करा' in chatbot.FALLBACK_MESSAGE
        assert 'शेती' in chatbot.FALLBACK_MESSAGE
    
    def test_error_message_in_marathi(self):
        """Test error message is in Marathi"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        assert 'माफ करा' in chatbot.ERROR_MESSAGE
        assert 'तांत्रिक' in chatbot.ERROR_MESSAGE
    
    def test_is_agricultural_query_positive(self):
        """Test agricultural query detection for valid queries"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        assert chatbot._is_agricultural_query("कांद्याची किंमत काय आहे?") is True
        assert chatbot._is_agricultural_query("What is the onion price?") is True
        assert chatbot._is_agricultural_query("शेतीबद्दल माहिती द्या") is True
        assert chatbot._is_agricultural_query("weather forecast") is True
    
    def test_is_agricultural_query_negative(self):
        """Test agricultural query detection for non-agricultural queries"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        assert chatbot._is_agricultural_query("What is the capital of India?") is False
        assert chatbot._is_agricultural_query("Tell me a joke") is False
        assert chatbot._is_agricultural_query("How to cook pasta?") is False
    
    def test_send_message_empty_input(self):
        """Test sending empty message"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        response = chatbot.send_message("")
        
        assert "प्रश्न" in response
    
    def test_send_message_out_of_scope(self):
        """Test sending out-of-scope message returns fallback"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        response = chatbot.send_message("What is the capital of France?")
        
        assert response == chatbot.FALLBACK_MESSAGE
    
    def test_send_message_success(self):
        """Test successful message sending"""
        mock_bedrock = Mock()
        mock_logger = Mock()
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read = Mock(return_value=json.dumps({
            'content': [{'text': 'कांद्याची किंमत आज ₹2500 प्रति क्विंटल आहे.'}]
        }).encode())
        
        mock_bedrock.invoke_model = Mock(return_value=mock_response)
        
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock, logger=mock_logger)
        
        response = chatbot.send_message("कांद्याची किंमत काय आहे?")
        
        assert 'कांद्याची' in response
        assert len(chatbot.conversation_history) == 2  # User + Assistant
        mock_bedrock.invoke_model.assert_called_once()
    
    def test_send_message_bedrock_failure(self):
        """Test message sending handles Bedrock failure"""
        mock_bedrock = Mock()
        mock_bedrock.invoke_model = Mock(side_effect=Exception("Bedrock error"))
        
        mock_logger = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock, logger=mock_logger)
        
        response = chatbot.send_message("कांद्याची किंमत काय आहे?")
        
        assert response == chatbot.ERROR_MESSAGE
        # Verify error was logged
        mock_logger.log_bedrock_call.assert_called()
    
    def test_conversation_history_management(self):
        """Test conversation history is maintained"""
        mock_bedrock = Mock()
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read = Mock(return_value=json.dumps({
            'content': [{'text': 'मी तुम्हाला मदत करू शकतो.'}]
        }).encode())
        
        mock_bedrock.invoke_model = Mock(return_value=mock_response)
        
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        # Send multiple messages
        chatbot.send_message("कांद्याची किंमत काय आहे?")
        chatbot.send_message("हवामान कसे आहे?")
        
        history = chatbot.get_conversation_history()
        
        assert len(history) == 4  # 2 user + 2 assistant messages
        assert history[0]['role'] == 'user'
        assert history[1]['role'] == 'assistant'
    
    def test_conversation_history_trimming(self):
        """Test conversation history is trimmed when exceeds max length"""
        mock_bedrock = Mock()
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read = Mock(return_value=json.dumps({
            'content': [{'text': 'उत्तर'}]
        }).encode())
        
        mock_bedrock.invoke_model = Mock(return_value=mock_response)
        
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        chatbot.max_history_length = 4  # Set low limit for testing
        
        # Send multiple messages
        for i in range(5):
            chatbot.send_message(f"प्रश्न {i}")
        
        history = chatbot.get_conversation_history()
        
        # Should be trimmed to max_history_length
        assert len(history) <= chatbot.max_history_length
    
    def test_get_conversation_history(self):
        """Test getting conversation history"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        # Manually add to history
        chatbot.conversation_history = [
            {'role': 'user', 'content': 'प्रश्न'},
            {'role': 'assistant', 'content': 'उत्तर'}
        ]
        
        history = chatbot.get_conversation_history()
        
        assert len(history) == 2
        assert history[0]['role'] == 'user'
        assert history[1]['role'] == 'assistant'
    
    def test_clear_conversation_history(self):
        """Test clearing conversation history"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        # Add some history
        chatbot.conversation_history = [
            {'role': 'user', 'content': 'प्रश्न'},
            {'role': 'assistant', 'content': 'उत्तर'}
        ]
        
        chatbot.clear_conversation_history()
        
        assert len(chatbot.conversation_history) == 0
    
    def test_get_conversation_summary(self):
        """Test getting conversation summary"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        # Add some history
        chatbot.conversation_history = [
            {'role': 'user', 'content': 'प्रश्न 1'},
            {'role': 'assistant', 'content': 'उत्तर 1'},
            {'role': 'user', 'content': 'प्रश्न 2'},
            {'role': 'assistant', 'content': 'उत्तर 2'}
        ]
        
        summary = chatbot.get_conversation_summary()
        
        assert summary['total_messages'] == 4
        assert summary['user_messages'] == 2
        assert summary['assistant_messages'] == 2
        assert summary['conversation_active'] is True
    
    def test_export_conversation(self):
        """Test exporting conversation as text"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        # Add some history
        chatbot.conversation_history = [
            {'role': 'user', 'content': 'प्रश्न'},
            {'role': 'assistant', 'content': 'उत्तर'}
        ]
        
        exported = chatbot.export_conversation()
        
        assert 'प्रश्न' in exported
        assert 'उत्तर' in exported
    
    def test_export_conversation_empty(self):
        """Test exporting empty conversation"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        exported = chatbot.export_conversation()
        
        assert 'रिक्त' in exported
    
    def test_get_suggested_questions(self):
        """Test getting suggested questions"""
        mock_bedrock = Mock()
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        questions = chatbot.get_suggested_questions()
        
        assert len(questions) > 0
        assert all('?' in q for q in questions)
        # Verify Marathi text
        assert any('कांदा' in q for q in questions)


# Property-Based Tests
class TestMarathiChatbotProperties:
    """Property-based tests for Marathi Chatbot"""
    
    @settings(deadline=None, max_examples=10)
    @given(
        user_input=st.text(min_size=5, max_size=100)
    )
    def test_property_marathi_chatbot_api_integration(self, user_input):
        """
        Property 20: Marathi Chatbot API Integration
        
        GIVEN any user input
        WHEN sent to chatbot
        THEN response is always returned (never crashes)
        
        Validates: Requirement 10.2
        """
        mock_bedrock = Mock()
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read = Mock(return_value=json.dumps({
            'content': [{'text': 'मराठी उत्तर'}]
        }).encode())
        
        mock_bedrock.invoke_model = Mock(return_value=mock_response)
        
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        response = chatbot.send_message(user_input)
        
        # Should always return a string response
        assert isinstance(response, str)
        assert len(response) > 0
    
    @settings(deadline=None, max_examples=10)
    @given(
        marathi_text=st.sampled_from([
            'कांद्याची किंमत काय आहे?',
            'हवामान कसे आहे?',
            'पीक कधी लावावे?',
            'शेतीबद्दल सांगा'
        ])
    )
    def test_property_marathi_response_language(self, marathi_text):
        """
        Property 21: Marathi Response Language
        
        GIVEN Marathi agricultural query
        WHEN processed by chatbot
        THEN response contains Marathi Unicode characters
        
        Validates: Requirement 10.3
        """
        mock_bedrock = Mock()
        
        # Mock Bedrock response with Marathi text
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read = Mock(return_value=json.dumps({
            'content': [{'text': 'हे मराठी उत्तर आहे. कांदा चांगला आहे.'}]
        }).encode())
        
        mock_bedrock.invoke_model = Mock(return_value=mock_response)
        
        chatbot = MarathiChatbot(bedrock_client=mock_bedrock)
        
        response = chatbot.send_message(marathi_text)
        
        # Response should contain Marathi characters (Devanagari script)
        # Check for common Marathi characters
        has_marathi = any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in response)
        assert has_marathi or response == chatbot.FALLBACK_MESSAGE or response == chatbot.ERROR_MESSAGE
