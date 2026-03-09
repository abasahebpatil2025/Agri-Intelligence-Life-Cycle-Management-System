"""
Error Handler Module

Provides centralized error handling for the Weather Market API Integration feature.
Displays user-friendly error messages for API failures and configuration errors
while ensuring API keys are never exposed to users.

This module handles various error scenarios including API timeouts, connection errors,
authentication failures, rate limits, and missing configuration.
"""

import streamlit as st
import logging
import requests
from typing import Optional


class ErrorHandler:
    """
    Centralized error handling and user messaging for the application.
    
    This class provides static methods for handling different types of errors
    that can occur during API interactions and configuration validation.
    All error messages are user-friendly and never expose sensitive information
    like API keys.
    """
    
    @staticmethod
    def handle_api_error(error: Exception, api_name: str) -> None:
        """
        Display user-friendly error message for API failures.
        
        Handles various types of API errors including timeouts, connection errors,
        authentication failures, and rate limits. Displays appropriate messages
        to users using Streamlit components and logs detailed error information
        for debugging (without exposing API keys).
        
        Args:
            error: The exception that occurred during API call
            api_name: Name of the API service ("Weather" or "Agmarknet")
            
        Example:
            >>> try:
            ...     response = requests.get(api_url)
            ... except Exception as e:
            ...     ErrorHandler.handle_api_error(e, "Weather")
        """
        # Handle timeout errors
        if isinstance(error, requests.Timeout):
            st.warning(
                f"⏱️ {api_name} API is responding slowly. "
                f"Using cached data if available..."
            )
            logging.warning(f"{api_name} API timeout occurred")
        
        # Handle connection errors
        elif isinstance(error, requests.ConnectionError):
            st.warning(
                f"🔌 Cannot connect to {api_name} API. "
                f"Please check your internet connection."
            )
            logging.error(f"{api_name} API connection error", exc_info=True)
        
        # Handle authentication errors (401)
        elif isinstance(error, requests.HTTPError):
            if hasattr(error, 'response') and error.response is not None:
                status_code = error.response.status_code
                
                if status_code == 401:
                    st.error(
                        f"🔑 {api_name} API authentication failed. "
                        f"Please check your API key configuration."
                    )
                    logging.error(f"{api_name} API authentication failed (401)")
                
                # Handle rate limit errors (429)
                elif status_code == 429:
                    st.warning(
                        f"⏳ {api_name} API rate limit exceeded. "
                        f"Please try again in a few minutes."
                    )
                    logging.warning(f"{api_name} API rate limit exceeded (429)")
                
                # Handle other HTTP errors
                else:
                    st.warning(
                        f"⚠️ {api_name} API returned an error (status {status_code}). "
                        f"Using cached data if available."
                    )
                    logging.error(
                        f"{api_name} API HTTP error: {status_code}",
                        exc_info=True
                    )
            else:
                st.warning(
                    f"⚠️ {api_name} API error occurred. "
                    f"Using cached data if available."
                )
                logging.error(f"{api_name} API HTTP error", exc_info=True)
        
        # Handle all other unexpected errors
        else:
            st.warning(
                f"❌ Unexpected error with {api_name} API. "
                f"Using cached data if available."
            )
            logging.error(
                f"{api_name} API unexpected error: {type(error).__name__}",
                exc_info=True
            )
    
    @staticmethod
    def handle_missing_secrets() -> None:
        """
        Display error message when required API keys are missing from st.secrets.
        
        Shows a clear, formatted error message to users explaining which API keys
        are missing and how to configure them. Stops the application execution
        to prevent runtime errors from missing credentials.
        
        This method should be called when ConfigValidator.validate_secrets()
        returns False.
        
        Example:
            >>> if not ConfigValidator.validate_secrets():
            ...     ErrorHandler.handle_missing_secrets()
        """
        st.error(
            """
            🔑 **Configuration Error**
            
            Required API keys are missing from Streamlit secrets.
            
            Please configure the following in `.streamlit/secrets.toml`:
            
            ```toml
            openweather_api_key = "your_openweather_api_key_here"
            agmarknet_api_key = "your_agmarknet_api_key_here"
            ```
            
            **How to get API keys:**
            - OpenWeatherMap: Sign up at https://openweathermap.org/api
            - Agmarknet: Contact your administrator for access
            
            After adding the keys, restart the application.
            """
        )
        logging.error("Application startup failed: Required API keys missing from secrets")
        st.stop()
