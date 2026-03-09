"""
S3 Bucket Setup Script

Creates S3 bucket with folder structure, lifecycle policies, and versioning.
Run this script once to set up the S3 infrastructure.

Requirements: Task 11 - Phase 2
"""

import boto3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import streamlit as st
    from src.components.secrets_manager import SecretsManager
    
    # Get AWS credentials
    secrets_mgr = SecretsManager()
    access_key, secret_key = secrets_mgr.get_aws_credentials()
    region = st.secrets.get('aws', {}).get('AWS_REGION', 'us-east-1')
except Exception as e:
    print(f"Error loading credentials: {e}")
    print("Please ensure .streamlit/secrets.toml is configured correctly")
    sys.exit(1)


def get_account_id(sts_client):
    """Get AWS account ID"""
    try:
        response = sts_client.get_caller_identity()
        return response['Account']
    except Exception as e:
        print(f"Error getting account ID: {e}")
        return None


def create_bucket(s3_client, bucket_name, region):
    """Create S3 bucket"""
    try:
        if region == 'us-east-1':
            # us-east-1 doesn't need LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"✓ Created bucket: {bucket_name}")
        return True
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"✓ Bucket already exists: {bucket_name}")
        return True
    except Exception as e:
        print(f"✗ Error creating bucket: {e}")
        return False


def create_folder_structure(s3_client, bucket_name):
    """Create folder structure using empty objects"""
    folders = ['models/', 'qr-codes/', 'logs/']
    
    for folder in folders:
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=folder,
                Body=b''
            )
            print(f"✓ Created folder: {folder}")
        except Exception as e:
            print(f"✗ Error creating folder {folder}: {e}")
            return False
    
    return True


def enable_versioning(s3_client, bucket_name):
    """Enable bucket versioning"""
    try:
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print(f"✓ Enabled versioning for bucket")
        return True
    except Exception as e:
        print(f"✗ Error enabling versioning: {e}")
        return False


def set_lifecycle_policy(s3_client, bucket_name):
    """Set lifecycle policy to move models/ to Glacier after 90 days"""
    lifecycle_policy = {
        'Rules': [
            {
                'ID': 'MoveModelsToGlacier',
                'Status': 'Enabled',
                'Filter': {
                    'Prefix': 'models/'
                },
                'Transitions': [
                    {
                        'Days': 90,
                        'StorageClass': 'GLACIER'
                    }
                ]
            }
        ]
    }
    
    try:
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_policy
        )
        print(f"✓ Set lifecycle policy: models/ → Glacier after 90 days")
        return True
    except Exception as e:
        print(f"✗ Error setting lifecycle policy: {e}")
        return False


def set_bucket_policy(s3_client, bucket_name, account_id):
    """Configure bucket policy for private access"""
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DenyPublicAccess",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                "Condition": {
                    "StringNotEquals": {
                        "aws:PrincipalAccount": account_id
                    }
                }
            }
        ]
    }
    
    try:
        import json
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print(f"✓ Set bucket policy for private access")
        return True
    except Exception as e:
        print(f"✗ Error setting bucket policy: {e}")
        return False


def test_upload_download(s3_client, bucket_name):
    """Test upload and download operations"""
    test_key = 'models/test-model.txt'
    test_content = b'Test Prophet model data'
    
    try:
        # Test upload
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content
        )
        print(f"✓ Test upload successful: {test_key}")
        
        # Test download
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=test_key
        )
        downloaded_content = response['Body'].read()
        
        if downloaded_content == test_content:
            print(f"✓ Test download successful: content matches")
        else:
            print(f"✗ Test download failed: content mismatch")
            return False
        
        # Clean up test file
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=test_key
        )
        print(f"✓ Test cleanup successful")
        
        return True
    except Exception as e:
        print(f"✗ Error during upload/download test: {e}")
        return False


def main():
    """Main setup function"""
    print("=" * 60)
    print("S3 Bucket Setup - Agri-Intelligence System")
    print("=" * 60)
    print()
    
    # Initialize AWS clients
    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )
    
    sts_client = boto3.client(
        'sts',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )
    
    # Get account ID
    print("Step 1: Getting AWS Account ID...")
    account_id = get_account_id(sts_client)
    if not account_id:
        print("✗ Failed to get account ID")
        sys.exit(1)
    print(f"✓ Account ID: {account_id}")
    print()
    
    # Create bucket name
    bucket_name = f"agri-intelligence-bucket-{account_id}"
    print(f"Step 2: Creating S3 bucket: {bucket_name}")
    if not create_bucket(s3_client, bucket_name, region):
        sys.exit(1)
    print()
    
    # Create folder structure
    print("Step 3: Creating folder structure...")
    if not create_folder_structure(s3_client, bucket_name):
        sys.exit(1)
    print()
    
    # Enable versioning
    print("Step 4: Enabling bucket versioning...")
    if not enable_versioning(s3_client, bucket_name):
        sys.exit(1)
    print()
    
    # Set lifecycle policy
    print("Step 5: Setting lifecycle policy...")
    if not set_lifecycle_policy(s3_client, bucket_name):
        sys.exit(1)
    print()
    
    # Set bucket policy
    print("Step 6: Configuring bucket policy...")
    if not set_bucket_policy(s3_client, bucket_name, account_id):
        print("⚠ Warning: Could not set bucket policy (may require additional permissions)")
    print()
    
    # Test upload/download
    print("Step 7: Testing upload/download operations...")
    if not test_upload_download(s3_client, bucket_name):
        sys.exit(1)
    print()
    
    print("=" * 60)
    print("✓ S3 Setup Complete!")
    print("=" * 60)
    print(f"Bucket Name: {bucket_name}")
    print(f"Region: {region}")
    print(f"Folders: models/, qr-codes/, logs/")
    print(f"Versioning: Enabled")
    print(f"Lifecycle: models/ → Glacier after 90 days")
    print("=" * 60)


if __name__ == '__main__':
    main()
