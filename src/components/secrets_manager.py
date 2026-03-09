
"""
Secrets Manager Component

Retrieves AWS credentials from boto3 session (AWS CLI configuration)
and API keys from environment variables or Streamlit secrets as fallback.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
"""

import boto3
import os
from typing import Tuple, Dict


class MissingCredentialError(Exception):
    """Raised when a required credential is missing"""
    pass


class SecretsManager:
    """
    Manages secure credential retrieval.
    
    AWS credentials are retrieved from boto3 session (AWS CLI configuration).
    API keys are retrieved from environment variables.
    """
    
    def __init__(self):
        """Initialize SecretsManager and validate all credentials."""
        self.validate_credentials()
    
    def get_aws_credentials(self) -> Tuple[str, str]:
        """
        Retrieve AWS credentials from boto3 session (AWS CLI configuration).
        
        Returns:
            Tuple[str, str]: (access_key, secret_key)
            
        Raises:
            MissingCredentialError: If AWS credentials are not configured
        """
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            
            if credentials is None:
                raise MissingCredentialError(
                    "AWS credentials not found. Please configure AWS CLI using "
                    "'aws configure' or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
                    "environment variables."
                )
            
            # Get frozen credentials to access key and secret
            frozen_creds = credentials.get_frozen_credentials()
            access_key = frozen_creds.access_key
            secret_key = frozen_creds.secret_key
            
            if not access_key or not secret_key:
                raise MissingCredentialError(
                    "AWS credentials are empty. Please reconfigure AWS CLI."
                )
            
            return access_key, secret_key
            
        except Exception as e:
            if isinstance(e, MissingCredentialError):
                raise
            raise MissingCredentialError(
                f"Failed to retrieve AWS credentials: {str(e)}"
            )
    
    def get_aws_region(self) -> str:
        """
        Retrieve AWS region from boto3 session.
        
        Returns:
            str: AWS region (defaults to 'us-east-1' if not configured)
        """
        try:
            session = boto3.Session()
            region = session.region_name
            return region if region else "us-east-1"
        except Exception:
            return "us-east-1"
    
    def get_openweather_key(self) -> str:
        """
        Retrieve OpenWeatherMap API key from environment variables first,
        then fallback to AWS Secrets Manager if not found.
        
        Returns:
            str: OpenWeatherMap API key
            
        Raises:
            MissingCredentialError: If OpenWeatherMap API key is missing from both sources
        """
        # Priority 1: Check environment variables first
        api_key = os.environ.get("OPENWEATHER_API_KEY", "")
        
        if api_key:
            return api_key
        
        # Priority 2: Fallback to AWS Secrets Manager
        try:
            from config.config_validator import ConfigValidator
            validator = ConfigValidator()
            api_key = validator.get_api_key("OPENWEATHER_API_KEY")
            if api_key:
                return api_key
        except Exception:
            pass  # Continue to error if AWS also fails
        
        raise MissingCredentialError(
            "OpenWeatherMap API key not found. Please set "
            "OPENWEATHER_API_KEY environment variable or add it to AWS Secrets Manager."
        )
    
    def get_agmarknet_key(self) -> str:
        """
        Retrieve Agmarknet API key from AWS Secrets Manager FIRST,
        then fallback to environment variables if AWS is not available.
        
        Returns:
            str: Agmarknet API key
            
        Raises:
            MissingCredentialError: If Agmarknet API key is missing from both sources
        """
        # Priority 1: Check AWS Secrets Manager FIRST
        try:
            from config.config_validator import ConfigValidator
            validator = ConfigValidator()
            api_key = validator.get_api_key_from_aws_only("AGMARKNET_API_KEY")
            if api_key:
                print(f"✅ SUCCESS: AGMARKNET_API_KEY retrieved from AWS Secrets Manager (Agri_Intelligence)")
                return api_key
        except Exception as e:
            print(f"⚠️ AWS Secrets Manager fetch failed: {str(e)}")
            pass  # Continue to environment variable fallback
        
        # Priority 2: Fallback to environment variables
        api_key = os.environ.get("AGMARKNET_API_KEY", "")
        
        if api_key:
            print("⚠️ Using AGMARKNET_API_KEY from environment variables (fallback)")
            return api_key
        
        raise MissingCredentialError(
            "Agmarknet API key not found. Please add AGMARKNET_API_KEY to AWS Secrets Manager "
            "(secret name: Agri_Intelligence) or set AGMARKNET_API_KEY environment variable."
        )
    
    def validate_credentials(self) -> Dict[str, bool]:
        """
        Validate that all required credentials are present.
        
        Returns:
            Dict[str, bool]: Dictionary with validation status for each credential
            
        Raises:
            MissingCredentialError: If any required credential is missing
        """
        validation_results = {
            "aws_credentials": False,
            "openweather_key": False,
            "agmarknet_key": False
        }
        
        errors = []
        
        # Validate AWS credentials
        try:
            self.get_aws_credentials()
            validation_results["aws_credentials"] = True
        except MissingCredentialError as e:
            errors.append(str(e))
        
        # Validate OpenWeatherMap API key
        try:
            self.get_openweather_key()
            validation_results["openweather_key"] = True
        except MissingCredentialError as e:
            errors.append(str(e))
        
        # Validate Agmarknet API key
        try:
            self.get_agmarknet_key()
            validation_results["agmarknet_key"] = True
        except MissingCredentialError as e:
            errors.append(str(e))
        
        # If any validation failed, raise error with all missing credentials
        if errors:
            error_message = "Missing required credentials:\n" + "\n".join(f"- {err}" for err in errors)
            raise MissingCredentialError(error_message)
        
        return validation_results
