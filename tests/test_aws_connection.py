import boto3
import streamlit as st
from src.components.secrets_manager import SecretsManager

def test_aws_access():
    try:
        # १. SecretsManager चा ऑब्जेक्ट तयार करा
        sm = SecretsManager()
        
        # २. ट्युपल मधून एक्सेस की आणि सीक्रेट की मिळवा
        access_key, secret_key = sm.get_aws_credentials()
        region = sm.get_aws_region()
        
        # ३. साधी STS (Security Token Service) टेस्ट करा
        client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        response = client.get_caller_identity()
        print(f"\n✅ AWS कनेक्शन यशस्वी!")
        print(f"तुमची Account ID: {response['Account']}")
        
    except Exception as e:
        print(f"\n❌ AWS एरर: {str(e)}")

if __name__ == "__main__":
    test_aws_access()