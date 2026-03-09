"""
Marathi Chatbot Component

Agricultural assistant chatbot using AWS Bedrock Amazon Titan.
Responds in Marathi language with conversation context.
Integrates with CloudLogger for interaction tracking.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
"""

import json
import time
from typing import List, Dict, Any, Optional


class MarathiChatbot:
    """
    Marathi language chatbot for agricultural assistance using AWS Bedrock Amazon Titan.
    
    Provides farming advice, answers questions about crops, prices, and weather.
    Maintains conversation context and logs all interactions.
    """
    
    # Marathi system prompt
    SYSTEM_PROMPT = """तुम्ही एक मराठी भाषेतील कृषी सहाय्यक आहात. तुमचे नाव "कृषी मित्र" आहे.

तुमची जबाबदारी:
- शेतकऱ्यांना पीक जीवनचक्र, किंमती आणि हवामान याबद्दल मदत करा
- कांदा, टोमॅटो, कापूस, तूर, सोयाबीन यासारख्या पिकांबद्दल माहिती द्या
- बाजार किंमती, हवामान अंदाज आणि पीक व्यवस्थापन याबद्दल सल्ला द्या
- पीक रोग ओळख आणि उपचार याबद्दल मार्गदर्शन करा
- जर शेतकरी पानाच्या लक्षणांचे वर्णन करत असेल (पिवळे ठिपके, कोमेजलेले पान, तपकिरी डाग), तर संभाव्य रोग ओळखा आणि उपचार सुचवा
- नेहमी मराठी भाषेत उत्तर द्या
- सोप्या आणि समजण्यायोग्य भाषेत बोला
- शेतकऱ्यांशी आदराने आणि मैत्रीपूर्ण रीतीने संवाद साधा

महत्वाचे नियम:
- फक्त शेती संबंधित प्रश्नांची उत्तरे द्या
- जर प्रश्न शेतीशी संबंधित नसेल, तर विनम्रपणे सांगा की तुम्ही फक्त शेती विषयांवर मदत करू शकता
- तांत्रिक शब्दांचा वापर करताना त्यांचे स्पष्टीकरण द्या
- व्यावहारिक आणि कृती करण्यायोग्य सल्ला द्या
- रोग ओळखताना, संभाव्य कारणे आणि उपचार दोन्ही सांगा"""

    # Out-of-scope fallback message
    FALLBACK_MESSAGE = "मला माफ करा, मी फक्त शेती संबंधित प्रश्नांची उत्तरे देऊ शकतो. कृपया कांदा, टोमॅटो, किंमती, हवामान किंवा पीक व्यवस्थापन याबद्दल विचारा."
    
    # Error message
    ERROR_MESSAGE = "मला माफ करा, सध्या तांत्रिक समस्या आहे. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा."
    
    # Agricultural keywords for scope validation
    AGRICULTURAL_KEYWORDS = [
        'शेती', 'पीक', 'कांदा', 'टोमॅटो', 'कापूस', 'तूर', 'सोयाबीन',
        'किंमत', 'बाजार', 'हवामान', 'पाऊस', 'पाणी', 'खत', 'बियाणे',
        'कीटक', 'रोग', 'लागवड', 'कापणी', 'शेतकरी', 'जमीन', 'मशागत',
        'पान', 'ठिपके', 'पिवळे', 'तपकिरी', 'कोमेजलेले', 'संक्रमण',
        'onion', 'tomato', 'cotton', 'price', 'weather', 'crop', 'farm',
        'leaf', 'disease', 'spots', 'yellow', 'brown', 'wilted', 'infection'
    ]
    
    def __init__(self, bedrock_client, logger=None):
        """
        Initialize Marathi Chatbot.
        
        Args:
            bedrock_client: boto3 bedrock-runtime client
            logger: Optional CloudLogger instance
        """
        self.bedrock_client = bedrock_client
        self.logger = logger
        
        # Amazon Nova Lite model ID (us-east-1)
        self.model_id = "amazon.nova-lite-v1:0"
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        # Max conversation history length
        self.max_history_length = 20
    
    def _is_agricultural_query(self, user_input: str) -> bool:
        """
        Check if user query is related to agriculture.
        
        Args:
            user_input: User's input text
            
        Returns:
            True if query is agricultural, False otherwise
        """
        user_input_lower = user_input.lower()
        
        # Check for agricultural keywords
        for keyword in self.AGRICULTURAL_KEYWORDS:
            if keyword in user_input_lower:
                return True
        
        return False
    
    def send_message(self, user_input: str) -> str:
        """
        Send message to chatbot and get response.
        
        Args:
            user_input: User's message in Marathi or English
            
        Returns:
            Bot's response in Marathi
        """
        if not user_input or not user_input.strip():
            return "कृपया तुमचा प्रश्न विचारा."
        
        start_time = time.time()
        
        try:
            # Check if query is agricultural
            if not self._is_agricultural_query(user_input):
                # Log out-of-scope query
                if self.logger:
                    self.logger.log_bedrock_call(
                        request={
                            'operation': 'marathi_chatbot',
                            'user_input': user_input[:100],
                            'scope': 'out_of_scope'
                        },
                        response={'message': self.FALLBACK_MESSAGE}
                    )
                return self.FALLBACK_MESSAGE
            
            # Add user message to history
            self.conversation_history.append({
                'role': 'user',
                'content': user_input
            })
            
            # Build messages for Nova
            messages = [{"role": "user", "content": [{"text": self.SYSTEM_PROMPT}]}]
            
            # Add conversation history (last 10 messages)
            recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
            for msg in recent_history[:-1]:  # Exclude current user message
                messages.append({
                    "role": msg['role'],
                    "content": [{"text": msg['content']}]
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": [{"text": user_input}]
            })
            
            # Prepare request for Amazon Nova
            request_body = {
                "messages": messages,
                "inferenceConfig": {
                    "max_new_tokens": 1000,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
            
            # Log request
            if self.logger:
                self.logger.log_bedrock_call(
                    request={
                        'operation': 'marathi_chatbot',
                        'model': self.model_id,
                        'user_input': user_input[:100],
                        'history_length': len(self.conversation_history)
                    },
                    response={'status': 'pending'}
                )
            
            # Call Bedrock with Titan
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            duration = time.time() - start_time
            
            # Parse Nova response
            response_body = json.loads(response['body'].read())
            bot_response = response_body['output']['message']['content'][0]['text'].strip()
            
            # Add bot response to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': bot_response
            })
            
            # Trim history if too long
            if len(self.conversation_history) > self.max_history_length:
                # Keep system context by removing oldest user-assistant pairs
                self.conversation_history = self.conversation_history[-self.max_history_length:]
            
            # Log successful response
            if self.logger:
                self.logger.log_bedrock_call(
                    request={
                        'operation': 'marathi_chatbot',
                        'model': self.model_id,
                        'user_input': user_input[:100]
                    },
                    response={
                        'bot_response': bot_response[:100],
                        'duration': duration,
                        'history_length': len(self.conversation_history)
                    }
                )
            
            return bot_response
        
        except Exception as e:
            # Log error
            if self.logger:
                self.logger.log_bedrock_call(
                    request={
                        'operation': 'marathi_chatbot',
                        'model': self.model_id,
                        'user_input': user_input[:100]
                    },
                    response={'error': str(e)},
                    error=str(e)
                )
            
            # Return error message in Marathi
            return self.ERROR_MESSAGE
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history.
        
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        return self.conversation_history.copy()
    
    def clear_conversation_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        
        if self.logger:
            self.logger.log_bedrock_call(
                request={'operation': 'clear_history'},
                response={'status': 'success'}
            )
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get summary of current conversation.
        
        Returns:
            Dictionary with conversation statistics
        """
        user_messages = [msg for msg in self.conversation_history if msg['role'] == 'user']
        assistant_messages = [msg for msg in self.conversation_history if msg['role'] == 'assistant']
        
        return {
            'total_messages': len(self.conversation_history),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'conversation_active': len(self.conversation_history) > 0
        }
    
    def export_conversation(self) -> str:
        """
        Export conversation history as formatted text.
        
        Returns:
            Formatted conversation text
        """
        if not self.conversation_history:
            return "संवाद इतिहास रिक्त आहे."
        
        lines = []
        for msg in self.conversation_history:
            role = "शेतकरी" if msg['role'] == 'user' else "कृषी मित्र"
            lines.append(f"{role}: {msg['content']}\n")
        
        return "\n".join(lines)
    
    def get_suggested_questions(self) -> List[str]:
        """
        Get list of suggested questions in Marathi.
        
        Returns:
            List of suggested question strings
        """
        return [
            "कांद्याची आजची बाजार किंमत काय आहे?",
            "पुढील आठवड्यात हवामान कसे असेल?",
            "कांद्याच्या पिकाची काळजी कशी घ्यावी?",
            "कांद्याच्या किंमतीचा अंदाज काय आहे?",
            "कांद्याच्या पिकात कोणते रोग येतात?",
            "कांदा कधी लावावा?",
            "कांद्याला किती पाणी लागते?",
            "कांद्याला कोणते खत द्यावे?",
            "पानावर पिवळे ठिपके आहेत - हा कोणता रोग आहे?",
            "टोमॅटोच्या पानावर तपकिरी डाग आहेत - काय करावे?"
        ]
