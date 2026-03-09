"""
DynamoDB Table Setup Script

Creates all required DynamoDB tables for the Agri-Intelligence System.
Tables: FarmerProfiles, PriceTrends, SensorReadings, QRCodes, UserAccounts

Requirements: 12.3, 14.1, 14.2, 21.5, 23.4, 29.3

Usage:
    python src/setup_dynamodb.py
"""

import boto3
import sys
from botocore.exceptions import ClientError

sys.path.insert(0, 'src/components')
from secrets_manager import SecretsManager, MissingCredentialError


def create_dynamodb_client():
    """
    Create and return DynamoDB client using credentials from secrets.
    
    Returns:
        boto3 DynamoDB client
    """
    try:
        secrets = SecretsManager()
        access_key, secret_key = secrets.get_aws_credentials()
        region = secrets.get_aws_region()
        
        client = boto3.client(
            'dynamodb',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        return client
    
    except MissingCredentialError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def create_farmer_profiles_table(client):
    """
    Create FarmerProfiles table.
    
    Partition Key: farmer_id
    Stores: name, location, primary_crops, farm_size, storage_capacity
    """
    table_name = "FarmerProfiles"
    
    try:
        response = client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'farmer_id', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'farmer_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand billing
        )
        
        print(f"✓ Created table: {table_name}")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
            return True
        else:
            print(f"❌ Error creating {table_name}: {e}")
            return False


def create_price_trends_table(client):
    """
    Create PriceTrends table.
    
    Partition Key: commodity
    Sort Key: date
    Stores: price, market, sentiment
    """
    table_name = "PriceTrends"
    
    try:
        response = client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'commodity', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'date', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'commodity', 'AttributeType': 'S'},
                {'AttributeName': 'date', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"✓ Created table: {table_name}")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
            return True
        else:
            print(f"❌ Error creating {table_name}: {e}")
            return False


def create_sensor_readings_table(client):
    """
    Create SensorReadings table with TTL.
    
    Partition Key: storage_id
    Sort Key: timestamp
    TTL: 30 days (expires_at attribute)
    Stores: temperature, humidity, health_status
    """
    table_name = "SensorReadings"
    
    try:
        response = client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'storage_id', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'storage_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"✓ Created table: {table_name}")
        
        # Wait for table to be active before enabling TTL
        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        # Enable TTL (30 days)
        client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'expires_at'
            }
        )
        
        print(f"  ✓ Enabled TTL (30 days) on {table_name}")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
            # Try to enable TTL if not already enabled
            try:
                client.update_time_to_live(
                    TableName=table_name,
                    TimeToLiveSpecification={
                        'Enabled': True,
                        'AttributeName': 'expires_at'
                    }
                )
                print(f"  ✓ Enabled TTL on existing table")
            except ClientError:
                pass  # TTL might already be enabled
            return True
        else:
            print(f"❌ Error creating {table_name}: {e}")
            return False


def create_qr_codes_table(client):
    """
    Create QRCodes table with GSI.
    
    Partition Key: lot_id
    GSI: farmer_id-index (for querying by farmer)
    Stores: crop_type, grade, harvest_date, farmer_id
    """
    table_name = "QRCodes"
    
    try:
        response = client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'lot_id', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'lot_id', 'AttributeType': 'S'},
                {'AttributeName': 'farmer_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'farmer_id-index',
                    'KeySchema': [
                        {'AttributeName': 'farmer_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"✓ Created table: {table_name}")
        print(f"  ✓ Created GSI: farmer_id-index")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
            return True
        else:
            print(f"❌ Error creating {table_name}: {e}")
            return False


def create_user_accounts_table(client):
    """
    Create UserAccounts table with GSI.
    
    Partition Key: farmer_id
    GSI: phone-index (for login by phone number)
    Stores: name, phone, location, storage_capacity, pin_hash, preferences
    """
    table_name = "UserAccounts"
    
    try:
        response = client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'farmer_id', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'farmer_id', 'AttributeType': 'S'},
                {'AttributeName': 'phone', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'phone-index',
                    'KeySchema': [
                        {'AttributeName': 'phone', 'KeyType': 'HASH'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"✓ Created table: {table_name}")
        print(f"  ✓ Created GSI: phone-index")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠ Table already exists: {table_name}")
            return True
        else:
            print(f"❌ Error creating {table_name}: {e}")
            return False


def list_tables(client):
    """
    List all DynamoDB tables in the account.
    
    Returns:
        List of table names
    """
    try:
        response = client.list_tables()
        return response.get('TableNames', [])
    except ClientError as e:
        print(f"❌ Error listing tables: {e}")
        return []


def verify_tables(client):
    """
    Verify all required tables exist.
    
    Returns:
        bool: True if all tables exist
    """
    required_tables = [
        'FarmerProfiles',
        'PriceTrends',
        'SensorReadings',
        'QRCodes',
        'UserAccounts'
    ]
    
    existing_tables = list_tables(client)
    
    print("\n" + "="*60)
    print("Table Verification")
    print("="*60)
    
    all_exist = True
    for table in required_tables:
        if table in existing_tables:
            print(f"✓ {table}")
        else:
            print(f"✗ {table} - NOT FOUND")
            all_exist = False
    
    return all_exist


def main():
    """Main setup function"""
    print("="*60)
    print("DynamoDB Table Setup - Agri-Intelligence System")
    print("="*60)
    print()
    
    # Create DynamoDB client
    print("Connecting to AWS DynamoDB...")
    client = create_dynamodb_client()
    print("✓ Connected successfully")
    print()
    
    # Create tables
    print("Creating tables...")
    print("-"*60)
    
    results = []
    results.append(create_farmer_profiles_table(client))
    results.append(create_price_trends_table(client))
    results.append(create_sensor_readings_table(client))
    results.append(create_qr_codes_table(client))
    results.append(create_user_accounts_table(client))
    
    # Verify tables
    all_verified = verify_tables(client)
    
    # Summary
    print()
    print("="*60)
    if all(results) and all_verified:
        print("✓ Setup Complete! All tables are ready.")
    else:
        print("⚠ Setup completed with some warnings. Check messages above.")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Verify tables in AWS Console: https://console.aws.amazon.com/dynamodb")
    print("2. Run the application: streamlit run app.py")
    print()


if __name__ == "__main__":
    main()
