"""
Connection Validator Component

Validates AWS service connections and logs status to terminal.
Provides explicit SUCCESS/ERROR messages for debugging.

Requirements: Deployment readiness verification
"""

import boto3
import json
from typing import Tuple, Optional
from botocore.exceptions import ClientError, NoCredentialsError


class ConnectionValidator:
    """
    Validates connections to AWS services with explicit logging.
    
    Provides terminal output for:
    - Bedrock (AI models)
    - DynamoDB (data storage)
    - SageMaker (ML inference)
    - S3 (file storage)
    - SNS (notifications)
    """
    
    @staticmethod
    def validate_bedrock(bedrock_client, model_id: str = "amazon.nova-lite-v1:0") -> Tuple[bool, str]:
        """
        Validate Bedrock connection with a minimal test call.
        
        Args:
            bedrock_client: boto3 bedrock-runtime client
            model_id: Model ID to test (default: amazon.nova-lite-v1:0)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Minimal test request
            test_body = {
                "messages": [{"role": "user", "content": [{"text": "Hi"}]}],
                "inferenceConfig": {"max_new_tokens": 10, "temperature": 0.7}
            }
            
            response = bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(test_body)
            )
            
            # Parse response to confirm it's valid
            response_body = json.loads(response['body'].read())
            if 'output' in response_body:
                region = bedrock_client.meta.region_name
                print(f"✅ SUCCESS: Connected to Bedrock ({model_id}) in {region}")
                return True, f"Connected to Bedrock ({model_id})"
            else:
                print(f"⚠️ WARNING: Bedrock responded but format unexpected")
                return False, "Unexpected response format"
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            if error_code == 'ThrottlingException':
                print(f"⚠️ WARNING: Bedrock throttled (quota exceeded) - {error_msg}")
                return False, f"Throttled: {error_msg}"
            elif error_code == 'ResourceNotFoundException':
                print(f"❌ ERROR: Bedrock model not found - {model_id}")
                return False, f"Model not found: {model_id}"
            else:
                print(f"❌ ERROR: Bedrock connection failed - {error_code}: {error_msg}")
                return False, f"{error_code}: {error_msg}"
                
        except NoCredentialsError:
            print(f"❌ ERROR: AWS credentials not configured for Bedrock")
            return False, "No AWS credentials"
            
        except Exception as e:
            print(f"❌ ERROR: Bedrock connection failed - {str(e)}")
            return False, str(e)
    
    @staticmethod
    def validate_dynamodb(dynamodb_client, test_table: str = "AgriIntelligence_Data") -> Tuple[bool, str]:
        """
        Validate DynamoDB connection by checking table existence.
        
        Args:
            dynamodb_client: boto3 DynamoDB client
            test_table: Table name to check (default: AgriIntelligence_Data)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Try to describe the table
            response = dynamodb_client.describe_table(TableName=test_table)
            
            table_status = response['Table']['TableStatus']
            region = dynamodb_client.meta.region_name
            
            if table_status == 'ACTIVE':
                print(f"✅ SUCCESS: Connected to DynamoDB (table: {test_table}) in {region}")
                return True, f"Connected to DynamoDB ({test_table})"
            else:
                print(f"⚠️ WARNING: DynamoDB table exists but status is {table_status}")
                return False, f"Table status: {table_status}"
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            if error_code == 'ResourceNotFoundException':
                region = dynamodb_client.meta.region_name
                print(f"⚠️ WARNING: DynamoDB table '{test_table}' not found in {region} (will be created on first use)")
                return True, f"Client connected (table will be auto-created)"
            else:
                print(f"❌ ERROR: DynamoDB connection failed - {error_code}: {error_msg}")
                return False, f"{error_code}: {error_msg}"
                
        except NoCredentialsError:
            print(f"❌ ERROR: AWS credentials not configured for DynamoDB")
            return False, "No AWS credentials"
            
        except Exception as e:
            print(f"❌ ERROR: DynamoDB connection failed - {str(e)}")
            return False, str(e)
    
    @staticmethod
    def validate_s3(s3_client, test_bucket: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate S3 connection by listing buckets or checking specific bucket.
        
        Args:
            s3_client: boto3 S3 client
            test_bucket: Optional bucket name to check
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if test_bucket:
                # Check specific bucket
                s3_client.head_bucket(Bucket=test_bucket)
                region = s3_client.meta.region_name
                print(f"✅ SUCCESS: Connected to S3 (bucket: {test_bucket}) in {region}")
                return True, f"Connected to S3 ({test_bucket})"
            else:
                # Just list buckets to verify connection
                response = s3_client.list_buckets()
                bucket_count = len(response.get('Buckets', []))
                print(f"✅ SUCCESS: Connected to S3 ({bucket_count} buckets accessible)")
                return True, f"Connected to S3 ({bucket_count} buckets)"
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            if error_code == '404' or error_code == 'NoSuchBucket':
                print(f"⚠️ WARNING: S3 bucket '{test_bucket}' not found (will be created on first use)")
                return True, "Client connected (bucket will be auto-created)"
            else:
                print(f"❌ ERROR: S3 connection failed - {error_code}: {error_msg}")
                return False, f"{error_code}: {error_msg}"
                
        except NoCredentialsError:
            print(f"❌ ERROR: AWS credentials not configured for S3")
            return False, "No AWS credentials"
            
        except Exception as e:
            print(f"❌ ERROR: S3 connection failed - {str(e)}")
            return False, str(e)
    
    @staticmethod
    def validate_sns(sns_client) -> Tuple[bool, str]:
        """
        Validate SNS connection by listing topics.
        
        Args:
            sns_client: boto3 SNS client
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # List topics to verify connection
            response = sns_client.list_topics()
            topic_count = len(response.get('Topics', []))
            region = sns_client.meta.region_name
            print(f"✅ SUCCESS: Connected to SNS ({topic_count} topics) in {region}")
            return True, f"Connected to SNS ({topic_count} topics)"
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            print(f"❌ ERROR: SNS connection failed - {error_code}: {error_msg}")
            return False, f"{error_code}: {error_msg}"
                
        except NoCredentialsError:
            print(f"❌ ERROR: AWS credentials not configured for SNS")
            return False, "No AWS credentials"
            
        except Exception as e:
            print(f"❌ ERROR: SNS connection failed - {str(e)}")
            return False, str(e)
    
    @staticmethod
    def validate_sagemaker(sagemaker_client, endpoint_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate SageMaker connection by listing endpoints or checking specific endpoint.
        
        Args:
            sagemaker_client: boto3 SageMaker client
            endpoint_name: Optional endpoint name to check
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if endpoint_name:
                # Check specific endpoint
                response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
                status = response['EndpointStatus']
                region = sagemaker_client.meta.region_name
                
                if status == 'InService':
                    print(f"✅ SUCCESS: Connected to SageMaker (endpoint: {endpoint_name}) in {region}")
                    return True, f"Connected to SageMaker ({endpoint_name})"
                else:
                    print(f"⚠️ WARNING: SageMaker endpoint exists but status is {status}")
                    return False, f"Endpoint status: {status}"
            else:
                # Just list endpoints to verify connection
                response = sagemaker_client.list_endpoints()
                endpoint_count = len(response.get('Endpoints', []))
                region = sagemaker_client.meta.region_name
                print(f"✅ SUCCESS: Connected to SageMaker ({endpoint_count} endpoints) in {region}")
                return True, f"Connected to SageMaker ({endpoint_count} endpoints)"
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            if error_code == 'ValidationException' and 'Could not find endpoint' in error_msg:
                print(f"⚠️ WARNING: SageMaker endpoint '{endpoint_name}' not found")
                return False, f"Endpoint not found: {endpoint_name}"
            else:
                print(f"❌ ERROR: SageMaker connection failed - {error_code}: {error_msg}")
                return False, f"{error_code}: {error_msg}"
                
        except NoCredentialsError:
            print(f"❌ ERROR: AWS credentials not configured for SageMaker")
            return False, "No AWS credentials"
            
        except Exception as e:
            print(f"❌ ERROR: SageMaker connection failed - {str(e)}")
            return False, str(e)
