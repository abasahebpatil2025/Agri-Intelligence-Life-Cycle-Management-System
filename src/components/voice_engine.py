"""
Voice Engine Component

Provides speech-to-text and text-to-speech capabilities for Marathi language.
Uses SpeechRecognition for voice input and gTTS for audio synthesis.
Caches generated audio files for performance optimization.

Requirements: 15.2, 15.3, 15.4, 15.5, 15.6, 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.2, 28.3, 28.4, 28.5
"""

import os
import time
import hashlib
from typing import Optional, Any
from io import BytesIO
import speech_recognition as sr
from gtts import gTTS


class VoiceEngine:
    """
    Voice engine for Marathi speech recognition and synthesis.
    
    Provides speech-to-text conversion using Google Speech Recognition
    and text-to-speech synthesis using Google Text-to-Speech (gTTS).
    Implements caching for frequently used phrases and retry logic for errors.
    """
    
    # Language codes
    MARATHI_LANG_CODE = 'mr'  # For gTTS
    MARATHI_SPEECH_CODE = 'mr-IN'  # For speech recognition
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    
    def __init__(self, cache=None, cache_dir: str = '.voice_cache'):
        """
        Initialize Voice Engine.
        
        Args:
            cache: Optional cache layer for audio file caching
            cache_dir: Directory for storing cached audio files
        """
        self.cache = cache
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Audio cache (in-memory for quick access)
        self.audio_cache = {}
    
    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.
        
        Args:
            text: Text to generate key for
            
        Returns:
            MD5 hash of text as cache key
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def speech_to_text(
        self,
        audio_input: Any,
        language: str = None
    ) -> Optional[str]:
        """
        Convert speech to text using Google Speech Recognition.
        
        Args:
            audio_input: Audio data (speech_recognition.AudioData)
            language: Language code (defaults to Marathi 'mr-IN')
            
        Returns:
            Recognized text, or None if recognition fails
        """
        if language is None:
            language = self.MARATHI_SPEECH_CODE
        
        # Retry logic
        for attempt in range(self.MAX_RETRIES):
            try:
                # Use Google Speech Recognition
                text = self.recognizer.recognize_google(
                    audio_input,
                    language=language
                )
                return text
            
            except sr.UnknownValueError:
                # Speech not understood
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
                return None
            
            except sr.RequestError as e:
                # API error
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
                return None
            
            except Exception as e:
                # Other errors
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
                return None
        
        return None
    
    def text_to_speech(
        self,
        text: str,
        output_path: Optional[str] = None,
        language: str = None
    ) -> Optional[str]:
        """
        Convert text to speech using gTTS.
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file
            language: Language code (defaults to Marathi 'mr')
            
        Returns:
            Path to generated audio file, or None if generation fails
        """
        if language is None:
            language = self.MARATHI_LANG_CODE
        
        # Check cache first
        cache_key = self._get_cache_key(text)
        
        if cache_key in self.audio_cache:
            # Return cached audio path
            return self.audio_cache[cache_key]
        
        try:
            # Generate audio using gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Determine output path
            if output_path is None:
                output_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
            
            # Save audio file
            tts.save(output_path)
            
            # Cache the path
            self.audio_cache[cache_key] = output_path
            
            return output_path
        
        except Exception as e:
            # TTS generation failed
            return None
    
    def text_to_speech_bytes(
        self,
        text: str,
        language: str = None
    ) -> Optional[bytes]:
        """
        Convert text to speech and return as bytes (for streaming).
        
        Args:
            text: Text to convert to speech
            language: Language code (defaults to Marathi 'mr')
            
        Returns:
            Audio data as bytes, or None if generation fails
        """
        if language is None:
            language = self.MARATHI_LANG_CODE
        
        try:
            # Generate audio using gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to BytesIO buffer
            buffer = BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            
            return buffer.getvalue()
        
        except Exception as e:
            # TTS generation failed
            return None
    
    def start_listening(
        self,
        timeout: int = 5,
        phrase_time_limit: int = 10
    ) -> Optional[str]:
        """
        Start listening for voice input from microphone.
        
        Args:
            timeout: Seconds to wait for speech to start
            phrase_time_limit: Maximum seconds for phrase
            
        Returns:
            Recognized text, or None if listening fails
        """
        try:
            # Use microphone as audio source
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Listen for audio
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                # Convert to text
                return self.speech_to_text(audio)
        
        except sr.WaitTimeoutError:
            # No speech detected
            return None
        
        except Exception as e:
            # Other errors
            return None
    
    def play_audio(self, audio_path: str) -> Optional[bytes]:
        """
        Load audio file for playback.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Audio data as bytes for browser playback
        """
        try:
            with open(audio_path, 'rb') as f:
                return f.read()
        except Exception as e:
            return None
    
    def clear_cache(self):
        """Clear audio cache (both in-memory and disk)."""
        # Clear in-memory cache
        self.audio_cache.clear()
        
        # Clear disk cache
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            pass
    
    def get_cache_size(self) -> int:
        """
        Get number of cached audio files.
        
        Returns:
            Number of files in cache
        """
        return len(self.audio_cache)
    
    def is_available(self) -> bool:
        """
        Check if voice engine is available.
        
        Returns:
            True if voice services are available, False otherwise
        """
        try:
            # Test gTTS
            test_text = "test"
            tts = gTTS(text=test_text, lang=self.MARATHI_LANG_CODE)
            return True
        except Exception as e:
            return False
