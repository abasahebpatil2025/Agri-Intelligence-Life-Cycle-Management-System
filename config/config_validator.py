"""
Configuration Validator Module

Validates that all required API keys and configuration settings exist
in AWS Secrets Manager on application startup.

This module is part of the Weather Market API Integration feature and ensures
that the application has all necessary credentials before attempting to make
API calls to external services.
"""

import streamlit as st
import boto3
import json
from typing import List, Optional, Dict
from botocore.exceptions import ClientError


class ConfigValidator:
    """
    Validates configuration and manages safe access to API keys from AWS Secrets Manager.
    
    This class ensures that all required API keys exist in AWS Secrets Manager
    before the application attempts to use them, preventing runtime errors
    and providing clear error messages to users.
    """
    
    # List of required secret keys for the application
    REQUIRED_SECRETS: List[str] = [
        "OPENWEATHER_API_KEY",
        "AGMARKNET_API_KEY"
    ]
    
    # AWS Secrets Manager configuration
    SECRET_NAME = "Agri_Intelligence"
    
    def __init__(self):
        """Initialize ConfigValidator with AWS Secrets Manager client."""
        self._secrets_cache: Optional[Dict[str, str]] = None
        self._client = None
    
    def _get_aws_client(self):
        """Get or create AWS Secrets Manager client using environment credentials."""
        if self._client is None:
            # Use AWS credentials from environment (configured via AWS CLI)
            self._client = boto3.client('secretsmanager')
        return self._client
    
    def _fetch_secrets_from_aws(self) -> Dict[str, str]:
        """
        Fetch secrets from AWS Secrets Manager.
        
        Returns:
            Dict containing API keys from AWS Secrets Manager
            
        Raises:
            ClientError: If AWS Secrets Manager call fails
        """
        if self._secrets_cache is not None:
            return self._secrets_cache
        
        try:
            client = self._get_aws_client()
            response = client.get_secret_value(SecretId=self.SECRET_NAME)
            
            # Parse the secret string as JSON
            secret_dict = json.loads(response['SecretString'])
            
            # Cache the secrets
            self._secrets_cache = secret_dict
            
            return secret_dict
            
        except ClientError as e:
            raise Exception(f"Failed to fetch secrets from AWS: {str(e)}")
    
    def validate_secrets(self) -> bool:
        """
        Validate that all required secrets exist in environment variables or AWS Secrets Manager.
        
        Checks environment variables FIRST, then falls back to AWS Secrets Manager.
        This ensures the application works with PowerShell environment variables
        without requiring AWS Secrets Manager to be configured.
        
        Returns:
            bool: True if all required secrets are present in either location, False otherwise
            
        Example:
            >>> validator = ConfigValidator()
            >>> if validator.validate_secrets():
            ...     # Proceed with application initialization
            ...     pass
            ... else:
            ...     # Handle missing secrets error
            ...     pass
        """
        import os
        
        missing_secrets = []
        
        for secret in self.REQUIRED_SECRETS:
            # Priority 1: Check environment variables first
            env_value = os.environ.get(secret, "")
            
            if env_value:
                continue  # Found in environment, no need to check AWS
            
            # Priority 2: Check AWS Secrets Manager
            try:
                secrets = self._fetch_secrets_from_aws()
                if secret in secrets and secrets[secret]:
                    continue  # Found in AWS
            except Exception:
                pass  # AWS fetch failed, continue checking
            
            # Not found in either location
            missing_secrets.append(secret)
        
        return len(missing_secrets) == 0
    
    def get_api_key(self, key_name: str) -> str:
        """
        Safely retrieve an API key from environment variables first,
        then fallback to AWS Secrets Manager.
        
        Provides a centralized method for accessing API keys with proper
        fallback logic. Environment variables take priority over AWS Secrets Manager.
        
        Args:
            key_name: The name of the secret key to retrieve (e.g., "OPENWEATHER_API_KEY")
            
        Returns:
            str: The API key value from environment or AWS Secrets Manager
            
        Raises:
            KeyError: If the requested key does not exist in either location
            
        Example:
            >>> validator = ConfigValidator()
            >>> api_key = validator.get_api_key("OPENWEATHER_API_KEY")
            >>> # Use api_key for API authentication
        """
        import os
        
        # Priority 1: Check environment variables first
        env_value = os.environ.get(key_name, "")
        if env_value:
            return env_value
        
        # Priority 2: Check AWS Secrets Manager
        try:
            secrets = self._fetch_secrets_from_aws()
            
            if key_name not in secrets:
                raise KeyError(
                    f"API key '{key_name}' not found in environment variables or AWS Secrets Manager"
                )
            
            return secrets[key_name]
            
        except Exception as e:
            if isinstance(e, KeyError):
                raise
            raise KeyError(
                f"Failed to retrieve API key '{key_name}' from environment or AWS: {str(e)}"
            )
    
    def get_api_key_from_aws_only(self, key_name: str) -> str:
        """
        Retrieve an API key from AWS Secrets Manager ONLY (no environment fallback).
        
        This method forces AWS Secrets Manager as the source and does not check
        environment variables. Used when AWS should be the authoritative source.
        
        Args:
            key_name: The name of the secret key to retrieve (e.g., "AGMARKNET_API_KEY")
            
        Returns:
            str: The API key value from AWS Secrets Manager
            
        Raises:
            KeyError: If the requested key does not exist in AWS Secrets Manager
        """
        try:
            secrets = self._fetch_secrets_from_aws()
            
            if key_name not in secrets:
                raise KeyError(
                    f"API key '{key_name}' not found in AWS Secrets Manager (secret: {self.SECRET_NAME})"
                )
            
            return secrets[key_name]
            
        except Exception as e:
            if isinstance(e, KeyError):
                raise
            raise KeyError(
                f"Failed to retrieve API key '{key_name}' from AWS Secrets Manager: {str(e)}"
            )
