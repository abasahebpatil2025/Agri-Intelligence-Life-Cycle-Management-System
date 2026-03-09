"""
Pre-flight AWS Connectivity Test
Tests AWS credentials and service access before Phase 4 implementation.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.components.secrets_manager import SecretsManager
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_success(message):
    """Print success message."""
    print(f"✓ {message}")


def print_error(message):
    """Print error message."""
    print(f"✗ {message}")


def test_sts_connection(session):
    """Test STS connection and get caller identity."""
    print_header("STS Connection Test")
    
    try:
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print_success("STS connection successful!")
        print(f"  Account ID: {identity['Account']}")
        print(f"  User ARN: {identity['Arn']}")
        print(f"  User ID: {identity['UserId']}")
        return True
        
    except NoCredentialsError:
        print_error("Credential Issue / क्रेडेंशियल समस्या")
        print("  AWS credentials not found. Please check your configuration.")
        print("  AWS क्रेडेंशियल्स सापडले नाहीत. कृपया तुमचे कॉन्फिगरेशन तपासा.")
        return False
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print_error(f"Permission Issue / परवानगी समस्या: {error_code}")
        print(f"  {e.response['Error']['Message']}")
        return False
        
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_bedrock_access(session):
    """Test Bedrock access and list foundation models."""
    print_header("Bedrock Access Test")
    
    try:
        bedrock = session.client('bedrock')
        
        # List foundation models
        response = bedrock.list_foundation_models()
        models = response.get('modelSummaries', [])
        
        print_success(f"Bedrock access successful! Found {len(models)} models.")
        
        # Check for Claude 3 models specifically
        claude_models = [m for m in models if 'claude-3' in m.get('modelId', '').lower()]
        
        if claude_models:
            print_success(f"Claude 3 models available: {len(claude_models)}")
            for model in claude_models[:3]:  # Show first 3
                print(f"  - {model['modelId']}")
        else:
            print_error("Warning: No Claude 3 models found")
            print("  Please ensure 'Model Access' is enabled for Claude 3 in AWS Console.")
            print("  कृपया AWS Console मध्ये Claude 3 साठी 'Model Access' सक्षम केले आहे याची खात्री करा.")
        
        return True
        
    except NoCredentialsError:
        print_error("Credential Issue / क्रेडेंशियल समस्या")
        print("  AWS credentials not found for Bedrock.")
        print("  Bedrock साठी AWS क्रेडेंशियल्स सापडले नाहीत.")
        return False
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'AccessDeniedException':
            print_error("Permission Issue / परवानगी समस्या")
            print("  IAM user does not have BedrockFullAccess policy.")
            print("  IAM युजरला BedrockFullAccess धोरण नाही.")
            print("  Please attach 'AmazonBedrockFullAccess' policy to your IAM user.")
        else:
            print_error(f"Permission Issue / परवानगी समस्या: {error_code}")
            print(f"  {e.response['Error']['Message']}")
        
        return False
        
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_dynamodb_access(session):
    """Test DynamoDB access by listing tables."""
    print_header("DynamoDB Access Test")
    
    try:
        dynamodb = session.client('dynamodb')
        
        # List tables
        response = dynamodb.list_tables()
        tables = response.get('TableNames', [])
        
        print_success(f"DynamoDB access successful! Found {len(tables)} tables.")
        
        if tables:
            print("  Existing tables:")
            for table in tables:
                print(f"    - {table}")
        else:
            print("  No tables found (this is okay for initial setup).")
        
        return True
        
    except NoCredentialsError:
        print_error("Credential Issue / क्रेडेंशियल समस्या")
        print("  AWS credentials not found for DynamoDB.")
        print("  DynamoDB साठी AWS क्रेडेंशियल्स सापडले नाहीत.")
        return False
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'AccessDeniedException':
            print_error("Permission Issue / परवानगी समस्या")
            print("  IAM user does not have DynamoDBFullAccess policy.")
            print("  IAM युजरला DynamoDBFullAccess धोरण नाही.")
            print("  Please attach 'AmazonDynamoDBFullAccess' policy to your IAM user.")
        else:
            print_error(f"Permission Issue / परवानगी समस्या: {error_code}")
            print(f"  {e.response['Error']['Message']}")
        
        return False
        
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def main():
    """Run all pre-flight connectivity tests."""
    print("\n" + "=" * 60)
    print("  AWS PRE-FLIGHT CONNECTIVITY TEST")
    print("  AWS पूर्व-उड्डाण कनेक्टिव्हिटी चाचणी")
    print("=" * 60)
    
    # Initialize SecretsManager and create boto3 session
    print("\nInitializing AWS session...")
    try:
        secrets_mgr = SecretsManager()
        access_key, secret_key = secrets_mgr.get_aws_credentials()
        region = secrets_mgr.get_aws_region()
        
        # Create boto3 session manually
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        print_success(f"AWS session initialized (Region: {region})")
    except Exception as e:
        print_error(f"Failed to initialize AWS session: {str(e)}")
        print("  Please check your .streamlit/secrets.toml configuration.")
        print("  कृपया तुमचे .streamlit/secrets.toml कॉन्फिगरेशन तपासा.")
        sys.exit(1)
    
    # Run all tests
    results = []
    
    results.append(("STS", test_sts_connection(session)))
    results.append(("Bedrock", test_bedrock_access(session)))
    results.append(("DynamoDB", test_dynamodb_access(session)))
    
    # Summary
    print_header("Test Summary / चाचणी सारांश")
    
    all_passed = all(result[1] for result in results)
    
    for service, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {service}: {status}")
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("  ALL TESTS PASSED! Ready for Phase 4 implementation.")
        print("  सर्व चाचण्या उत्तीर्ण झाल्या! Phase 4 अंमलबजावणीसाठी तयार.")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print("  SOME TESTS FAILED. Please fix the issues above.")
        print("  काही चाचण्या अयशस्वी झाल्या. कृपया वरील समस्या सोडवा.")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
