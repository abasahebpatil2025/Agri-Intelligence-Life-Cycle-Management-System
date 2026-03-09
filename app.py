"""
कृषी बुद्धिमत्ता आणि जीवन-चक्र व्यवस्थापन प्रणाली
Agri-Intelligence & Life-Cycle Management System

Main Streamlit application with Marathi interface.
"""

import streamlit as st
import sys
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

sys.path.insert(0, 'src/components')
sys.path.insert(0, 'src')
sys.path.insert(0, 'src/integration')

from secrets_manager import SecretsManager, MissingCredentialError
from user_manager import UserManager
from cache_layer import CacheLayer
from agmarknet_client import AgmarknetClient
from market_locator import MarketLocator
from iot_simulator import IoTSimulator
from smart_storage_monitor import SmartStorageMonitor
from cloud_logger import CloudLogger
from dynamodb_store import DynamoDBStore
from qr_generator import QRGenerator
from qr_scanner import QRScanner
from voice_engine import VoiceEngine
from marathi_chatbot import MarathiChatbot
from enhanced_market_tab import show_enhanced_market_intel_tab
from connection_validator import ConnectionValidator
import plotly.graph_objects as go
from io import BytesIO
from PIL import Image
import boto3


# Page configuration
st.set_page_config(
    page_title="कृषी बुद्धिमत्ता प्रणाली",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state with Guest Access by default
if 'farmer_id' not in st.session_state:
    st.session_state.farmer_id = 'guest'
if 'farmer_name' not in st.session_state:
    st.session_state.farmer_name = 'अतिथी वापरकर्ता'
if 'user' not in st.session_state:
    # Default guest user profile
    st.session_state.user = {
        'farmer_id': 'guest',
        'name': 'अतिथी वापरकर्ता',
        'location': 'पुणे',
        'storage_capacity': 1000,
        'phone': 'N/A'
    }
if 'user_manager' not in st.session_state:
    st.session_state.user_manager = UserManager()
if 'cache_layer' not in st.session_state:
    st.session_state.cache_layer = CacheLayer()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'guest_mode' not in st.session_state:
    st.session_state.guest_mode = True
if 'voice_mode' not in st.session_state:
    st.session_state.voice_mode = False

# Initialize components
@st.cache_resource
def get_market_locator():
    """Initialize MarketLocator with caching"""
    try:
        secrets_manager = SecretsManager()
        api_key = secrets_manager.get_agmarknet_key()
        cache = CacheLayer()
        agmarknet_client = AgmarknetClient(api_key=api_key, cache=cache)
        return MarketLocator(agmarknet_client=agmarknet_client, cache=cache)
    except:
        return None


@st.cache_resource
def get_smart_storage_components():
    """Initialize Smart Storage components with caching"""
    try:
        secrets_manager = SecretsManager()
        aws_access_key, aws_secret_key = secrets_manager.get_aws_credentials()
        aws_region = secrets_manager.get_aws_region()
        
        import boto3
        
        # Initialize AWS clients
        dynamodb_client = boto3.client(
            'dynamodb',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        sns_client = boto3.client(
            'sns',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Validate connections
        ConnectionValidator.validate_dynamodb(dynamodb_client)
        ConnectionValidator.validate_sns(sns_client)
        
        # Initialize components
        logger = CloudLogger()
        dynamodb_store = DynamoDBStore(dynamodb_client, logger)
        iot_simulator = IoTSimulator(
            storage_id='storage_001',
            dynamodb_store=dynamodb_store,
            logger=logger
        )
        
        smart_storage_monitor = SmartStorageMonitor(
            iot_simulator=iot_simulator,
            dynamodb_store=dynamodb_store,
            sns_client=sns_client,
            logger=logger
        )
        
        return iot_simulator, smart_storage_monitor
    except Exception as e:
        print(f"❌ ERROR: Smart Storage initialization failed - {str(e)}")
        return None, None


@st.cache_resource
def get_qr_components():
    """Initialize QR Generator and Scanner components with caching"""
    try:
        secrets_manager = SecretsManager()
        aws_access_key, aws_secret_key = secrets_manager.get_aws_credentials()
        aws_region = secrets_manager.get_aws_region()
        
        import boto3
        
        # Initialize AWS clients
        dynamodb_client = boto3.client(
            'dynamodb',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Validate connections
        ConnectionValidator.validate_dynamodb(dynamodb_client)
        ConnectionValidator.validate_s3(s3_client, test_bucket='agri-intelligence-bucket')
        
        # Initialize components
        logger = CloudLogger()
        dynamodb_store = DynamoDBStore(dynamodb_client, logger)
        
        qr_generator = QRGenerator(
            dynamodb_store=dynamodb_store,
            s3_client=s3_client,
            bucket_name='agri-intelligence-bucket'
        )
        
        qr_scanner = QRScanner(dynamodb_store=dynamodb_store)
        
        return qr_generator, qr_scanner
    except Exception as e:
        print(f"❌ ERROR: QR components initialization failed - {str(e)}")
        return None, None


@st.cache_resource
def get_voice_engine():
    """Initialize Voice Engine with caching"""
    try:
        cache = CacheLayer()
        voice_engine = VoiceEngine(cache=cache)
        return voice_engine
    except Exception as e:
        return None


@st.cache_resource
def get_marathi_chatbot():
    """Initialize Marathi Chatbot with Bedrock client"""
    try:
        secrets_manager = SecretsManager()
        aws_access_key, aws_secret_key = secrets_manager.get_aws_credentials()
        aws_region = secrets_manager.get_aws_region()
        
        # Initialize Bedrock runtime client
        bedrock_client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Validate Bedrock connection
        ConnectionValidator.validate_bedrock(bedrock_client, model_id="amazon.nova-lite-v1:0")
        
        logger = CloudLogger()
        chatbot = MarathiChatbot(bedrock_client=bedrock_client, logger=logger)
        
        return chatbot
    except Exception as e:
        print(f"❌ ERROR: Marathi Chatbot initialization failed - {str(e)}")
        return None


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_weather_data(location: str):
    """Get weather data with 30-minute caching"""
    try:
        secrets_manager = SecretsManager()
        api_key = secrets_manager.get_openweather_key()
        cache = CacheLayer()
        
        from weather_client import WeatherClient
        weather_client = WeatherClient(api_key=api_key, cache=cache)
        
        # Fetch current weather
        weather_data = weather_client.fetch_current_weather(location)
        return weather_data
    except Exception as e:
        return None


def save_disease_photo_to_s3(uploaded_file):
    """
    Save uploaded disease photo to S3 bucket
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (success: bool, s3_path: str)
    """
    try:
        secrets_manager = SecretsManager()
        aws_access_key, aws_secret_key = secrets_manager.get_aws_credentials()
        aws_region = secrets_manager.get_aws_region()
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Generate unique filename
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        farmer_id = st.session_state.farmer_id
        filename = f"disease-scans/{farmer_id}/{timestamp}_{uploaded_file.name}"
        
        # Upload to S3
        bucket_name = 'agri-intelligence-bucket'
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=uploaded_file.getvalue(),
            ContentType=uploaded_file.type
        )
        
        s3_path = f"s3://{bucket_name}/{filename}"
        return True, s3_path
        
    except Exception as e:
        return False, str(e)


def generate_price_prediction(commodity: str, location: str):
    """
    Generate 15-day price prediction using Prophet and Titan for Marathi summary
    
    Args:
        commodity: Commodity name (e.g., 'Onion', 'Tomato')
        location: User location
        
    Returns:
        Dictionary with:
            - success: bool
            - predictions: DataFrame with predictions
            - summary: Marathi summary from Titan
            - error: Error message if failed
    """
    try:
        # Import required components
        from price_forecaster import PriceForecaster
        from sentiment_analyzer import SentimentAnalyzer
        from cloud_logger import CloudLogger
        
        # Initialize components
        secrets_manager = SecretsManager()
        aws_access_key, aws_secret_key = secrets_manager.get_aws_credentials()
        aws_region = secrets_manager.get_aws_region()
        
        bedrock_client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Validate Bedrock connection (for price prediction)
        ConnectionValidator.validate_bedrock(bedrock_client, model_id="amazon.nova-lite-v1:0")
        
        logger = CloudLogger()
        
        # Generate mock historical data (in production, fetch from Agmarknet)
        # For demo, create 180 days of historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate realistic price data with trend and seasonality
        base_price = 2400
        trend = np.linspace(0, 200, len(dates))
        seasonality = 100 * np.sin(np.linspace(0, 4*np.pi, len(dates)))
        noise = np.random.normal(0, 50, len(dates))
        prices = base_price + trend + seasonality + noise
        
        historical_data = pd.DataFrame({
            'date': dates,
            'price': prices
        })
        
        # Initialize and train Prophet model
        forecaster = PriceForecaster(logger=logger)
        forecaster.train(historical_data)
        
        # Generate 15-day predictions
        predictions = forecaster.predict(days=15)
        
        # Get sentiment analysis
        sentiment_analyzer = SentimentAnalyzer(bedrock_client=bedrock_client, logger=logger)
        sentiment, confidence = sentiment_analyzer.aggregate_sentiment([
            {'title': f'{commodity} market news', 'summary': 'Market conditions stable'}
        ])
        
        # Apply sentiment adjustment
        predictions = forecaster.apply_sentiment_adjustment(predictions, sentiment)
        
        # Generate Marathi summary using Titan
        marathi_summary = generate_marathi_market_summary(
            commodity, predictions, sentiment, bedrock_client, logger
        )
        
        return {
            'success': True,
            'predictions': predictions,
            'summary': marathi_summary,
            'sentiment': sentiment,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'predictions': None,
            'summary': None,
            'sentiment': None,
            'error': str(e)
        }


def generate_marathi_market_summary(commodity, predictions, sentiment, bedrock_client, logger):
    """
    Generate Marathi market summary using Amazon Titan
    
    Args:
        commodity: Commodity name
        predictions: DataFrame with predictions
        sentiment: Market sentiment
        bedrock_client: Bedrock client
        logger: CloudLogger
        
    Returns:
        Marathi summary string
    """
    try:
        # Prepare data for Titan
        avg_price = predictions['predicted_price'].mean()
        first_price = predictions['predicted_price'].iloc[0]
        last_price = predictions['predicted_price'].iloc[-1]
        price_change = ((last_price - first_price) / first_price) * 100
        
        # Create prompt for Titan
        prompt = f"""तुम्ही एक कृषी बाजार तज्ञ आहात. खालील माहितीवर आधारित मराठीत बाजार विश्लेषण द्या:

पीक: {commodity}
पुढील १५ दिवसांचा अंदाज:
- सुरुवातीची किंमत: ₹{first_price:.0f} प्रति क्विंटल
- शेवटची किंमत: ₹{last_price:.0f} प्रति क्विंटल
- सरासरी किंमत: ₹{avg_price:.0f} प्रति क्विंटल
- किंमत बदल: {price_change:+.1f}%
- बाजार भावना: {sentiment}

कृपया खालील मुद्द्यांवर मराठीत विश्लेषण द्या (२-३ परिच्छेद):
1. किंमत ट्रेंड (वाढणार की कमी होणार?)
2. शेतकऱ्यांसाठी सल्ला (आता विकावे की थांबावे?)
3. बाजार परिस्थिती

फक्त मराठीत उत्तर द्या, सोप्या भाषेत."""

        # Call Titan
        request_body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 500,
                "temperature": 0.7,
                "topP": 0.9,
                "stopSequences": []
            }
        }
        
        response = bedrock_client.invoke_model(
            modelId="amazon.titan-text-express-v1",
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        summary = response_body['results'][0]['outputText'].strip()
        
        # Log the operation
        if logger:
            logger.log_bedrock_call(
                request={'operation': 'market_summary', 'commodity': commodity},
                response={'summary_length': len(summary)}
            )
        
        return summary
        
    except Exception as e:
        # Fallback summary if Titan fails
        if price_change > 0:
            return f"पुढील १५ दिवसांत {commodity} च्या किंमतीत {price_change:.1f}% वाढ होण्याची शक्यता आहे. सरासरी किंमत ₹{avg_price:.0f} प्रति क्विंटल राहण्याची अपेक्षा आहे. बाजार भावना {sentiment} आहे."
        else:
            return f"पुढील १५ दिवसांत {commodity} च्या किंमतीत {abs(price_change):.1f}% घट होण्याची शक्यता आहे. सरासरी किंमत ₹{avg_price:.0f} प्रति क्विंटल राहण्याची अपेक्षा आहे. बाजार भावना {sentiment} आहे."


def show_login_registration():
    """Display login and registration forms in sidebar"""
    st.sidebar.title("🌾 शेतकरी लॉगिन")
    st.sidebar.markdown("---")
    
    # Tab selection
    tab = st.sidebar.radio(
        "निवडा:",
        ["लॉगिन", "नवीन नोंदणी"],
        label_visibility="collapsed"
    )
    
    if tab == "लॉगिन":
        show_login_form()
    else:
        show_registration_form()


def show_login_form():
    """Display login form"""
    st.sidebar.subheader("📱 लॉगिन करा")
    
    with st.sidebar.form("login_form"):
        phone = st.text_input("मोबाईल नंबर", placeholder="9876543210")
        pin = st.text_input("पिन (4 अंक)", type="password", max_chars=4)
        submit = st.form_submit_button("लॉगिन करा", width='stretch')
        
        if submit:
            if not phone or not pin:
                st.error("कृपया मोबाईल नंबर आणि पिन भरा")
            else:
                success, farmer_id = st.session_state.user_manager.authenticate(phone, pin)
                
                if success:
                    account = st.session_state.user_manager.get_user_account(farmer_id)
                    st.session_state.farmer_id = farmer_id
                    st.session_state.farmer_name = account['name']
                    st.session_state.user = account
                    st.session_state.guest_mode = False
                    st.success(f"स्वागत आहे, {account['name']}!")
                    st.rerun()
                else:
                    st.error("चुकीचा मोबाईल नंबर किंवा पिन")


def show_registration_form():
    """Display registration form"""
    st.sidebar.subheader("📝 नवीन नोंदणी")
    
    with st.sidebar.form("registration_form"):
        name = st.text_input("नाव", placeholder="रमेश पाटील")
        phone = st.text_input("मोबाईल नंबर", placeholder="9876543210")
        location = st.text_input("ठिकाण", placeholder="नाशिक")
        storage_capacity = st.number_input("साठवण क्षमता (क्विंटल)", min_value=0.0, value=100.0)
        pin = st.text_input("पिन (4 अंक)", type="password", max_chars=4)
        pin_confirm = st.text_input("पिन पुन्हा टाका", type="password", max_chars=4)
        submit = st.form_submit_button("नोंदणी करा", width='stretch')
        
        if submit:
            if not all([name, phone, location, pin, pin_confirm]):
                st.error("कृपया सर्व माहिती भरा")
            elif pin != pin_confirm:
                st.error("पिन जुळत नाही")
            elif len(pin) != 4 or not pin.isdigit():
                st.error("पिन 4 अंकी असावा")
            else:
                try:
                    farmer_id = st.session_state.user_manager.register_farmer(
                        name=name,
                        phone=phone,
                        location=location,
                        storage_capacity=storage_capacity,
                        pin=pin
                    )
                    st.success(f"नोंदणी यशस्वी! आता लॉगिन करा")
                    st.info("लॉगिन टॅबवर जा आणि तुमचा मोबाईल नंबर आणि पिन वापरा")
                except ValueError as e:
                    st.error(f"त्रुटी: {str(e)}")


def show_farmer_profile():
    """Display farmer profile in sidebar with live weather (works for both guest and logged-in users)"""
    # Get user data from session state (works for guest mode too)
    if st.session_state.guest_mode:
        account = st.session_state.user
    else:
        account = st.session_state.user_manager.get_user_account(st.session_state.farmer_id)
        st.session_state.user = account
    
    st.sidebar.title("👨‍🌾 वापरकर्ता प्रोफाइल")
    st.sidebar.divider()
    
    # Dynamic profile information with bilingual labels
    st.sidebar.write(f"**नाव (Name):** {account.get('name', 'अतिथी वापरकर्ता')}")
    st.sidebar.write(f"**ठिकाण (Location):** {account.get('location', 'पुणे')}")
    st.sidebar.write(f"**साठवण क्षमता (Capacity):** {account.get('storage_capacity', 1000)} क्विंटल")
    
    # Show guest mode indicator
    if st.session_state.guest_mode:
        st.sidebar.caption("🔓 अतिथी मोड (Guest Mode Active)")
    
    st.sidebar.divider()
    
    # Live Weather Widget with bilingual labels
    st.sidebar.subheader("🌤️ हवामान (Weather)")
    
    # Get location from user profile
    location = account.get('location', 'पुणे')
    
    # Fetch weather data with caching
    weather_data = get_weather_data(location)
    
    if weather_data:
        # Extract weather information
        temp = weather_data.get('temp', 0)
        humidity = weather_data.get('humidity', 0)
        description = weather_data.get('description_mr', weather_data.get('description', 'N/A'))
        
        # Map icon code to emoji
        icon_code = weather_data.get('icon', '')
        icon_map = {
            '01d': '☀️', '01n': '🌙',
            '02d': '⛅', '02n': '☁️',
            '03d': '☁️', '03n': '☁️',
            '04d': '☁️', '04n': '☁️',
            '09d': '🌧️', '09n': '🌧️',
            '10d': '🌦️', '10n': '🌧️',
            '11d': '⛈️', '11n': '⛈️',
            '13d': '❄️', '13n': '❄️',
            '50d': '🌫️', '50n': '🌫️'
        }
        icon = icon_map.get(icon_code, '🌤️')
        
        # Display weather metrics with bilingual labels
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric(
                "तापमान (Temperature)",
                f"{temp:.0f}°C",
                help="Temperature"
            )
        with col2:
            st.metric(
                "आर्द्रता (Humidity)",
                f"{humidity:.0f}%",
                help="Humidity"
            )
        
        # Weather description with icon
        st.sidebar.write(f"{icon} **स्थिती (Status):** {description}")
        
        # Location and last updated
        st.sidebar.caption(f"📍 पुणे (Pune)")
        st.sidebar.caption(f"🕐 10:33 PM")
    
    else:
        # Fallback to mock data if weather API unavailable
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("तापमान (Temperature)", "२८°C", "↑ 2°")
        with col2:
            st.metric("आर्द्रता (Humidity)", "६५%", "↓ 5%")
        
        st.sidebar.write("🌤️ **स्थिती (Status):** साफ आकाश")
        st.sidebar.caption(f"📍 पुणे (Pune)")
        st.sidebar.caption(f"🕐 10:33 PM")
        st.sidebar.caption("⚠️ लाइव्ह डेटा उपलब्ध नाही")
    
    st.sidebar.divider()
    
    # Login/Logout button
    if st.session_state.guest_mode:
        if st.sidebar.button("🔐 लॉगिन करा", width='stretch'):
            st.session_state.guest_mode = False
            st.session_state.farmer_id = None
            st.session_state.farmer_name = None
            st.session_state.user = None
            st.rerun()
    else:
        if st.sidebar.button("🚪 लॉगआउट", width='stretch'):
            # Return to guest mode
            st.session_state.guest_mode = True
            st.session_state.farmer_id = 'guest'
            st.session_state.farmer_name = 'अतिथी वापरकर्ता'
            st.session_state.user = {
                'farmer_id': 'guest',
                'name': 'अतिथी वापरकर्ता',
                'location': 'पुणे',
                'storage_capacity': 1000,
                'phone': 'N/A'
            }
            st.session_state.chat_history = []
            st.rerun()


def show_dashboard_tab():
    """Display personalized dashboard tab with user-specific content"""
    st.header("🏠 मुख्य डॅशबोर्ड")

    # Welcome message with dynamic name
    user = st.session_state.user
    if user:
        st.markdown(f"### स्वागत आहे, {user.get('name', 'शेतकरी')}! 🙏")
        st.caption(f"आज: {datetime.now().strftime('%d %B %Y, %A')}")

    st.markdown("---")

    # Quick Access Buttons
    st.subheader("⚡ द्रुत प्रवेश")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 बाजार दर", width='stretch'):
            st.info("बाजार शोध टॅबवर जा")

    with col2:
        if st.button("📦 साठवणूक", width='stretch'):
            st.info("स्मार्ट साठवणूक टॅबवर जा")

    with col3:
        if st.button("📱 QR तयार करा", width='stretch'):
            st.info("ग्रेडिंग टॅबवर जा")

    with col4:
        if st.button("🤖 AI मदत", width='stretch'):
            st.info("AI मदतनीस टॅबवर जा")

    st.markdown("---")

    # Section 1: My Storage
    st.subheader("📦 माझे स्टोरेज (My Storage)")

    # Get real storage data
    iot_simulator, smart_storage_monitor = get_smart_storage_components()
    
    if iot_simulator and smart_storage_monitor:
        storage_id = "storage_001"
        current_status = smart_storage_monitor.get_current_status(storage_id)
        
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            temp = current_status.get('temperature')
            if temp is not None:
                st.metric(
                    label="तापमान",
                    value=f"{temp:.1f}°C",
                    delta=None,
                    delta_color="normal"
                )
            else:
                st.metric(label="तापमान", value="N/A")

        with col2:
            humidity = current_status.get('humidity')
            if humidity is not None:
                st.metric(
                    label="आर्द्रता",
                    value=f"{humidity:.1f}%",
                    delta=None,
                    delta_color="normal"
                )
            else:
                st.metric(label="आर्द्रता", value="N/A")

        with col3:
            health_status = current_status.get('health_status', 'Unknown')
            if health_status == 'Safe':
                st.success("**स्थिती**\n\n✅ सुरक्षित")
            elif health_status == 'Warning':
                st.warning("**स्थिती**\n\n⚠️ सावधान")
            elif health_status == 'Alert':
                st.error("**स्थिती**\n\n🚨 धोका")
            else:
                st.info("**स्थिती**\n\n❓ अज्ञात")

        with col4:
            st.metric(
                label="साठवण क्षमता",
                value=f"{user.get('storage_capacity', 100)} क्विंटल" if user else "100 क्विंटल",
                delta="",
            )
    else:
        # Fallback to placeholder data if components unavailable
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="तापमान",
                value="N/A",
                delta_color="normal"
            )

        with col2:
            st.metric(
                label="आर्द्रता",
                value="N/A",
                delta_color="normal"
            )

        with col3:
            st.info("**स्थिती**\n\n❓ अज्ञात")

        with col4:
            st.metric(
                label="साठवण क्षमता",
                value=f"{user.get('storage_capacity', 100)} क्विंटल" if user else "100 क्विंटल",
                delta="",
            )

    st.markdown("---")

    # Section 2: My QR Codes
    st.subheader("📱 माझे QR कोड (My QR Codes)")

    # Mock QR code data
    qr_codes = [
        {"lot_id": "LOT001", "crop": "Onion", "grade": "A", "date": "2024-03-01", "status": "✅ Active"},
        {"lot_id": "LOT002", "crop": "Tomato", "grade": "B", "date": "2024-02-28", "status": "✅ Active"},
        {"lot_id": "LOT003", "crop": "Onion", "grade": "A", "date": "2024-02-25", "status": "🔒 Sold"},
    ]

    if qr_codes:
        # Display in grid layout
        cols = st.columns(3)
        for idx, qr in enumerate(qr_codes):
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f"""
**{qr['crop']} - Grade {qr['grade']}**

📦 Lot: {qr['lot_id']}
📅 Date: {qr['date']}
{qr['status']}
                    """)
                    if st.button(f"पहा", key=f"qr_{idx}", width='stretch'):
                        st.info(f"QR कोड {qr['lot_id']} तपशील")
    else:
        st.info("अद्याप QR कोड तयार केलेले नाहीत. ग्रेडिंग टॅबवर जा.")

    st.markdown("---")

    # Section 3: My History
    st.subheader("📊 माझा इतिहास (My History)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### अलीकडील क्रियाकलाप")
        activities = [
            {"time": "आज, 10:30 AM", "activity": "बाजार दर तपासले", "icon": "📊"},
            {"time": "काल, 3:45 PM", "activity": "QR कोड तयार केला", "icon": "📱"},
            {"time": "काल, 11:20 AM", "activity": "किंमत अंदाज पाहिला", "icon": "💹"},
            {"time": "2 दिवसांपूर्वी", "activity": "साठवणूक तपासली", "icon": "📦"},
        ]

        for activity in activities:
            col_icon, col_text = st.columns([1, 5])
            with col_icon:
                st.write(activity["icon"])
            with col_text:
                st.write(f"**{activity['activity']}**")
                st.caption(activity["time"])

    with col2:
        st.markdown("#### किंमत अंदाज इतिहास")
        forecast_history = [
            {"commodity": "Onion", "market": "नाशिक APMC", "date": "आज", "price": "₹2,450"},
            {"commodity": "Tomato", "market": "पुणे APMC", "date": "काल", "price": "₹3,200"},
            {"commodity": "Onion", "market": "मुंबई APMC", "date": "2 दिवसांपूर्वी", "price": "₹2,520"},
        ]

        for forecast in forecast_history:
            st.markdown(f"""
**{forecast['commodity']}** - {forecast['market']}
{forecast['price']} | {forecast['date']}
            """)
            st.markdown("---")

    st.markdown("---")

    # Section 4: Conversation History
    st.subheader("💬 संभाषण इतिहास (Conversation History)")

    if st.session_state.chat_history:
        # Show last 3 conversations
        recent_chats = st.session_state.chat_history[-3:]
        for chat in recent_chats:
            if chat['role'] == 'user':
                st.markdown(f"**तुम्ही:** {chat['content'][:100]}...")
    else:
        st.info("अद्याप संभाषण नाही. AI मदतनीस टॅबवर जा.")

    st.markdown("---")

    # Section 5: Personalized Recommendations
    st.subheader("💡 शिफारसी (Recommendations)")

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
**आजचा सल्ला:**
- मुंबई APMC मध्ये कांद्याचा दर सर्वाधिक आहे (₹2,520)
- साठवणूक स्थिती चांगली आहे - विक्रीसाठी योग्य वेळ
        """)

    with col2:
        st.warning("""
**लक्षात ठेवा:**
- पुढील 3 दिवसांत पाऊस अपेक्षित
- साठवणूक तापमान नियमित तपासा
        """)

    # Feature Usage Stats
    st.markdown("---")
    st.subheader("📈 आकडेवारी (Statistics)")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("एकूण QR कोड", "3", "+1")

    with col2:
        st.metric("बाजार तपासणी", "12", "+3")

    with col3:
        st.metric("AI प्रश्न", len(st.session_state.chat_history), "")




def show_market_intel_tab():
    """Display market intelligence tab with MarketLocator"""
    st.header("🏪 बाजार बुद्धिमत्ता")
    
    # Get user location
    user = st.session_state.user
    user_location = user.get('location', 'नाशिक') if user else 'नाशिक'
    
    # Commodity selector
    col1, col2 = st.columns([2, 1])
    with col1:
        commodity = st.selectbox(
            "पीक निवडा (Select Commodity)",
            ["Onion", "Tomato", "Potato", "Cotton"],
            help="बाजार दर पाहण्यासाठी पीक निवडा"
        )
    
    with col2:
        if st.button("🔄 दर रिफ्रेश करा", width='stretch'):
            st.cache_resource.clear()
            st.rerun()
    
    st.write(f"**तुमचे ठिकाण:** {user_location}")
    st.caption(f"🕐 शेवटचे अपडेट: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}")
    
    st.markdown("---")
    
    # Initialize MarketLocator
    market_locator = get_market_locator()
    
    # Section 1: Nearest Markets
    st.subheader("📍 जवळचे बाजार (Nearest Markets)")
    
    if market_locator:
        try:
            # Find nearest markets
            with st.spinner("बाजार शोधत आहे..."):
                nearest_markets = market_locator.find_nearest_markets(
                    farmer_location=f"{user_location}, Maharashtra",
                    count=5
                )
            
            if nearest_markets:
                st.success(f"✅ {len(nearest_markets)} जवळचे बाजार सापडले!")
                
                # Create DataFrame for display
                market_data = []
                for market in nearest_markets:
                    market_data.append({
                        "बाजार": market['market_name'],
                        "अंतर": f"{market['distance_km']:.1f} किमी",
                        "प्रवास वेळ": f"{market['travel_time_minutes']:.0f} मिनिटे"
                    })
                
                df = pd.DataFrame(market_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Show map if coordinates available
                if nearest_markets and 'latitude' in nearest_markets[0]:
                    st.markdown("#### 🗺️ बाजार नकाशा")
                    map_data = pd.DataFrame([
                        {
                            'lat': market.get('latitude'),
                            'lon': market.get('longitude')
                        }
                        for market in nearest_markets
                        if market.get('latitude') and market.get('longitude')
                    ])
                    
                    if not map_data.empty:
                        st.map(map_data)
                
            else:
                st.warning("बाजार सापडले नाहीत. कृपया तुमचे ठिकाण तपासा.")
        
        except Exception as e:
            st.error(f"त्रुटी: {str(e)}")
            nearest_markets = None
    else:
        nearest_markets = None
    
    # Fallback to mock data if needed
    if not nearest_markets:
        st.info("नमुना डेटा दाखवत आहे")
        
        mock_data = pd.DataFrame({
            "बाजार": ["नाशिक APMC", "पुणे APMC", "मुंबई APMC", "औरंगाबाद APMC", "अहमदनगर APMC"],
            "अंतर": ["15 किमी", "180 किमी", "220 किमी", "210 किमी", "95 किमी"],
            "प्रवास वेळ": ["23 मिनिटे", "270 मिनिटे", "330 मिनिटे", "315 मिनिटे", "143 मिनिटे"]
        })
        
        st.dataframe(mock_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Section 2: Market Rate Comparison
    st.subheader("💰 बाजार दर तुलना (Market Rate Comparison)")
    
    # Mock rate data with trends
    rate_data = [
        {"बाजार": "मुंबई APMC", "पीक": commodity, "दर (₹/क्विंटल)": 2520, "ट्रेंड": "↑", "बदल": "+5%"},
        {"बाजार": "नाशिक APMC", "पीक": commodity, "दर (₹/क्विंटल)": 2450, "ट्रेंड": "↑", "बदल": "+3%"},
        {"बाजार": "अहमदनगर APMC", "पीक": commodity, "दर (₹/क्विंटल)": 2420, "ट्रेंड": "→", "बदल": "0%"},
        {"बाजार": "औरंगाबाद APMC", "पीक": commodity, "दर (₹/क्विंटल)": 2400, "ट्रेंड": "↓", "बदल": "-2%"},
        {"बाजार": "पुणे APMC", "पीक": commodity, "दर (₹/क्विंटल)": 2380, "ट्रेंड": "↓", "बदल": "-4%"}
    ]
    
    rate_df = pd.DataFrame(rate_data)
    
    # Style the dataframe
    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: lightgreen' if v else '' for v in is_max]
    
    # Display with styling
    styled_df = rate_df.style.apply(highlight_max, subset=['दर (₹/क्विंटल)'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Highlight best market
    best_market = rate_df.loc[rate_df['दर (₹/क्विंटल)'].idxmax()]
    st.success(f"💡 **सर्वोत्तम बाजार:** {best_market['बाजार']} - सर्वाधिक दर ₹{best_market['दर (₹/क्विंटल)']} ({best_market['बदल']})")
    
    st.markdown("---")
    
    # Additional insights
    st.subheader("📊 बाजार अंतर्दृष्टी")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="सरासरी दर",
            value=f"₹{rate_df['दर (₹/क्विंटल)'].mean():.0f}",
            delta="+2.5%"
        )
    
    with col2:
        st.metric(
            label="सर्वोच्च दर",
            value=f"₹{rate_df['दर (₹/क्विंटल)'].max()}",
            delta="↑"
        )
    
    with col3:
        st.metric(
            label="किमान दर",
            value=f"₹{rate_df['दर (₹/क्विंटल)'].min()}",
            delta="↓"
        )
    
    # Tips
    st.info("""
💡 **सल्ला:**
- सर्वोच्च दर असलेल्या बाजारात विक्री करा
- प्रवास खर्च विचारात घ्या
- बाजार ट्रेंड पहा (↑ वाढत आहे, ↓ कमी होत आहे)
    """)
    
    st.markdown("---")
    
    # Section 3: Transport Booking (वाहतूक सोय)
    st.subheader("🚚 वाहतूक सोय (Transport Facility)")
    
    st.markdown("### वाहतूक बुक करा (Book Transport)")
    st.caption("तुमच्या पिकाला साठवणुकीतून बाजारात नेण्यासाठी वाहतूक बुक करा")
    
    # Transport booking form
    with st.expander("📋 वाहतूक तपशील भरा (Fill Transport Details)", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Source location (from user profile)
            source_location = st.text_input(
                "प्रारंभ स्थान (From Location)",
                value=user_location,
                disabled=True,
                help="तुमचे साठवणूक स्थान"
            )
            
            # Destination market
            destination_market = st.selectbox(
                "गंतव्य बाजार (To Market)",
                ["मुंबई APMC", "नाशिक APMC", "पुणे APMC", "औरंगाबाद APMC", "अहमदनगर APMC"],
                help="पीक नेण्यासाठी बाजार निवडा"
            )
            
            # Commodity
            transport_commodity = st.selectbox(
                "पीक (Commodity)",
                ["Onion", "Tomato", "Potato", "Cotton", "Tur", "Soybean"],
                help="वाहतुकीसाठी पीक निवडा"
            )
        
        with col2:
            # Quantity
            transport_quantity = st.number_input(
                "प्रमाण (क्विंटल) - Quantity (Quintals)",
                min_value=1.0,
                max_value=1000.0,
                value=50.0,
                step=10.0,
                help="वाहतुकीसाठी प्रमाण"
            )
            
            # Vehicle type
            vehicle_type = st.selectbox(
                "वाहन प्रकार (Vehicle Type)",
                ["छोटा ट्रक (Small Truck - 2 टन)", "मध्यम ट्रक (Medium Truck - 5 टन)", "मोठा ट्रक (Large Truck - 10 टन)"],
                help="वाहन प्रकार निवडा"
            )
            
            # Pickup date
            pickup_date = st.date_input(
                "पिकअप तारीख (Pickup Date)",
                value=datetime.now(),
                help="वाहतूक पिकअप तारीख"
            )
        
        # Book transport button
        if st.button("🚚 वाहतूक बुक करा (Book Transport)", width='stretch', type="primary"):
            with st.spinner("वाहतूक बुक करत आहे..."):
                # Simulate booking delay
                import time
                time.sleep(1)
                
                # Generate booking ID
                booking_id = f"TRN{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Store booking in session state
                if 'transport_bookings' not in st.session_state:
                    st.session_state.transport_bookings = []
                
                booking_details = {
                    'booking_id': booking_id,
                    'from': source_location,
                    'to': destination_market,
                    'commodity': transport_commodity,
                    'quantity': transport_quantity,
                    'vehicle': vehicle_type,
                    'pickup_date': pickup_date.strftime('%d/%m/%Y'),
                    'status': 'Confirmed',
                    'timestamp': datetime.now().strftime('%d/%m/%Y %I:%M %p')
                }
                
                st.session_state.transport_bookings.append(booking_details)
                
                st.success(f"✅ वाहतूक यशस्वीरित्या बुक झाली!")
                st.info(f"""
**बुकिंग तपशील:**

📋 **बुकिंग ID:** {booking_id}

📍 **मार्ग:** {source_location} → {destination_market}

🌾 **पीक:** {transport_commodity} ({transport_quantity} क्विंटल)

🚚 **वाहन:** {vehicle_type}

📅 **पिकअप तारीख:** {pickup_date.strftime('%d/%m/%Y')}

✅ **स्थिती:** पुष्टी झाली (Confirmed)
                """)
                
                st.balloons()
    
    st.markdown("---")
    
    # Available Transport Providers
    st.subheader("🚛 उपलब्ध वाहतूक सेवा (Available Transport Providers)")
    
    # Mock transport provider data
    transport_providers = [
        {
            "नाव (Name)": "महाराष्ट्र ट्रान्सपोर्ट",
            "वाहन (Vehicle)": "मध्यम ट्रक (5 टन)",
            "दर (Rate)": "₹8/किमी",
            "रेटिंग (Rating)": "⭐⭐⭐⭐⭐ 4.8",
            "मोबाईल (Phone)": "9876543210"
        },
        {
            "नाव (Name)": "शिवशाही लॉजिस्टिक्स",
            "वाहन (Vehicle)": "मोठा ट्रक (10 टन)",
            "दर (Rate)": "₹12/किमी",
            "रेटिंग (Rating)": "⭐⭐⭐⭐ 4.5",
            "मोबाईल (Phone)": "9876543211"
        },
        {
            "नाव (Name)": "किसान ट्रान्सपोर्ट सेवा",
            "वाहन (Vehicle)": "छोटा ट्रक (2 टन)",
            "दर (Rate)": "₹6/किमी",
            "रेटिंग (Rating)": "⭐⭐⭐⭐ 4.6",
            "मोबाईल (Phone)": "9876543212"
        },
        {
            "नाव (Name)": "अग्री लॉजिस्टिक्स प्रो",
            "वाहन (Vehicle)": "मध्यम ट्रक (5 टन)",
            "दर (Rate)": "₹9/किमी",
            "रेटिंग (Rating)": "⭐⭐⭐⭐⭐ 4.9",
            "मोबाईल (Phone)": "9876543213"
        }
    ]
    
    providers_df = pd.DataFrame(transport_providers)
    st.dataframe(providers_df, use_container_width=True, hide_index=True)
    
    st.info("""
💡 **वाहतूक टिप्स:**
- किंमत आणि अंतर विचारात घ्या
- रेटिंग पहा आणि विश्वासार्ह सेवा निवडा
- आगाऊ बुकिंग करा (1-2 दिवस आधी)
- वाहन क्षमता तुमच्या प्रमाणानुसार निवडा
    """)
    
    # Show existing bookings if any
    if 'transport_bookings' in st.session_state and st.session_state.transport_bookings:
        st.markdown("---")
        st.subheader("📋 माझी बुकिंग्ज (My Bookings)")
        
        for booking in reversed(st.session_state.transport_bookings[-3:]):  # Show last 3 bookings
            with st.expander(f"🚚 {booking['booking_id']} - {booking['status']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**मार्ग:** {booking['from']} → {booking['to']}")
                    st.write(f"**पीक:** {booking['commodity']}")
                    st.write(f"**प्रमाण:** {booking['quantity']} क्विंटल")
                
                with col2:
                    st.write(f"**वाहन:** {booking['vehicle']}")
                    st.write(f"**पिकअप:** {booking['pickup_date']}")
                    st.write(f"**बुक केले:** {booking['timestamp']}")
                
                if booking['status'] == 'Confirmed':
                    st.success("✅ पुष्टी झाली (Confirmed)")
    
    st.markdown("---")
    
    # Section 4: 15-Day Price Prediction
    st.subheader("📈 १५ दिवसांचा किंमत अंदाज (15-Day Price Forecast)")
    
    # Generate prediction button
    if st.button("🔮 किंमत अंदाज तयार करा", width='stretch', type="primary"):
        with st.spinner("Prophet model वापरून अंदाज तयार करत आहे..."):
            prediction_result = generate_price_prediction(commodity, user_location)
        
        if prediction_result['success']:
            predictions_df = prediction_result['predictions']
            marathi_summary = prediction_result['summary']
            
            # Display Marathi Summary from Titan
            st.success("✅ अंदाज तयार झाला!")
            st.info(f"**🤖 AI विश्लेषण:**\n\n{marathi_summary}")
            
            st.markdown("---")
            
            # Display Chart: Actual vs Predicted
            st.markdown("#### 📊 किंमत ट्रेंड चार्ट")
            
            fig = go.Figure()
            
            # Actual prices (last 30 days - mock data)
            actual_dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            actual_prices = [2400 + np.random.randint(-100, 100) for _ in range(30)]
            
            fig.add_trace(go.Scatter(
                x=actual_dates,
                y=actual_prices,
                mode='lines',
                name='वास्तविक किंमत (Actual)',
                line=dict(color='#2E86AB', width=3),
                hovertemplate='तारीख: %{x|%d %b}<br>किंमत: ₹%{y}<extra></extra>'
            ))
            
            # Predicted prices (next 15 days)
            pred_dates = pd.to_datetime(predictions_df['date'])
            pred_prices = predictions_df['predicted_price']
            lower_bound = predictions_df['lower_bound']
            upper_bound = predictions_df['upper_bound']
            
            fig.add_trace(go.Scatter(
                x=pred_dates,
                y=pred_prices,
                mode='lines+markers',
                name='अंदाजित किंमत (Predicted)',
                line=dict(color='#F77F00', width=3, dash='dash'),
                marker=dict(size=6),
                hovertemplate='तारीख: %{x|%d %b}<br>अंदाज: ₹%{y}<extra></extra>'
            ))
            
            # Confidence interval (shaded area)
            fig.add_trace(go.Scatter(
                x=pred_dates.tolist() + pred_dates.tolist()[::-1],
                y=upper_bound.tolist() + lower_bound.tolist()[::-1],
                fill='toself',
                fillcolor='rgba(247, 127, 0, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='विश्वास मर्यादा (95%)',
                hoverinfo='skip'
            ))
            
            fig.update_layout(
                title=f"{commodity} - किंमत अंदाज (Price Forecast)",
                xaxis_title="तारीख (Date)",
                yaxis_title="किंमत ₹/क्विंटल (Price ₹/Quintal)",
                hovermode='x unified',
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Display Prediction Table
            st.markdown("#### 📅 दिनांक-निहाय अंदाज (Date-wise Forecast)")
            
            # Format table for display
            display_df = predictions_df.copy()
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d %b %Y')
            display_df = display_df.rename(columns={
                'date': 'तारीख',
                'predicted_price': 'अंदाजित किंमत (₹)',
                'lower_bound': 'किमान (₹)',
                'upper_bound': 'कमाल (₹)'
            })
            
            # Add trend indicator
            display_df['ट्रेंड'] = ['↑' if i > 0 and display_df['अंदाजित किंमत (₹)'].iloc[i] > display_df['अंदाजित किंमत (₹)'].iloc[i-1] 
                                    else '↓' if i > 0 and display_df['अंदाजित किंमत (₹)'].iloc[i] < display_df['अंदाजित किंमत (₹)'].iloc[i-1]
                                    else '→' for i in range(len(display_df))]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Key insights
            st.markdown("---")
            st.markdown("#### 💡 मुख्य मुद्दे (Key Insights)")
            
            col1, col2, col3 = st.columns(3)
            
            avg_price = predictions_df['predicted_price'].mean()
            max_price = predictions_df['predicted_price'].max()
            min_price = predictions_df['predicted_price'].min()
            
            with col1:
                st.metric("सरासरी अंदाजित किंमत", f"₹{avg_price:.0f}")
            
            with col2:
                st.metric("कमाल अंदाजित किंमत", f"₹{max_price:.0f}")
            
            with col3:
                st.metric("किमान अंदाजित किंमत", f"₹{min_price:.0f}")
            
            # Disclaimer
            st.caption("⚠️ **अस्वीकरण:** हा अंदाज Prophet ML model आणि ऐतिहासिक डेटावर आधारित आहे. वास्तविक किंमती बाजार परिस्थितीनुसार बदलू शकतात.")
            
        else:
            st.error(f"❌ अंदाज तयार करताना त्रुटी: {prediction_result['error']}")
            st.info("कृपया पुन्हा प्रयत्न करा किंवा दुसरे पीक निवडा.")
    
    else:
        st.info("👆 वरील बटण दाबा आणि पुढील १५ दिवसांचा किंमत अंदाज पहा")


def show_chatbot_tab():
    """Display AI chatbot tab with voice mode support and photo upload for disease detection"""
    st.header("🤖 AI मदतनीस")
    
    st.markdown("### मराठी चॅटबॉट")
    st.caption("शेती संबंधित प्रश्न विचारा...")
    
    # Check if voice mode is enabled
    voice_mode = st.session_state.voice_mode
    
    if voice_mode:
        st.info("🎤 आवाज मोड सक्षम आहे")
    
    # Initialize voice engine if voice mode is enabled
    voice_engine = None
    if voice_mode:
        voice_engine = get_voice_engine()
        if not voice_engine or not voice_engine.is_available():
            st.warning("⚠️ आवाज सुविधा उपलब्ध नाही. कृपया टेक्स्ट मोड वापरा.")
            voice_mode = False
    
    # Photo Upload Section for Disease Detection
    st.markdown("---")
    with st.expander("📸 पीक रोग ओळख (Crop Disease Detection)", expanded=False):
        st.markdown("""
        **फोटो अपलोड करा आणि रोगाबद्दल माहिती मिळवा**
        
        🔬 तुमच्या पिकाच्या पानाचा फोटो अपलोड करा. आम्ही तो सुरक्षितपणे save करू आणि तुम्हाला सल्ला देऊ.
        """)
        
        uploaded_file = st.file_uploader(
            "पानाचा फोटो निवडा (Select leaf photo)",
            type=['png', 'jpg', 'jpeg'],
            help="संक्रमित पानाचा स्पष्ट फोटो अपलोड करा"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(uploaded_file, caption="अपलोड केलेला फोटो", use_container_width=True)
            
            with col2:
                st.info("""
                **📋 पुढील पायरी:**
                
                1. फोटो S3 मध्ये save होत आहे...
                2. कृपया खाली तुम्हाला काय दिसतं ते वर्णन करा
                3. AI तुम्हाला सल्ला देईल
                """)
                
                # Save to S3
                if st.button("💾 फोटो Save करा आणि विश्लेषण सुरू करा", width='stretch'):
                    with st.spinner("फोटो save करत आहे..."):
                        success, s3_path = save_disease_photo_to_s3(uploaded_file)
                    
                    if success:
                        st.success(f"✅ फोटो save झाला: {s3_path}")
                        
                        # Store in session for reference
                        st.session_state.last_uploaded_photo = s3_path
                        
                        st.markdown("---")
                        st.markdown("**🔍 आता फोटोचे वर्णन करा:**")
                        st.caption("उदाहरण: 'पानावर पिवळे ठिपके आहेत' किंवा 'पान कोमेजून गेलं आहे'")
                    else:
                        st.error("❌ फोटो save करताना त्रुटी. कृपया पुन्हा प्रयत्न करा.")
        
        st.caption("⚠️ **नोंद:** Automated Photo Analysis लवकरच येणार आहे. सध्या कृपया फोटोचे वर्णन द्या.")
    
    st.markdown("---")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Play audio if available and voice mode is on
            if voice_mode and message["role"] == "assistant" and "audio" in message:
                if voice_engine:
                    audio_bytes = voice_engine.play_audio(message["audio"])
                    if audio_bytes:
                        st.audio(audio_bytes, format='audio/mp3')
    
    # Voice input section (if voice mode enabled)
    if voice_mode and voice_engine:
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("**🎤 आवाज इनपुट**")
        
        with col2:
            if st.button("🎙️ बोला", width='stretch'):
                with st.spinner("ऐकत आहे..."):
                    recognized_text = voice_engine.start_listening(timeout=5, phrase_time_limit=10)
                
                if recognized_text:
                    st.success(f"✅ ओळखले: {recognized_text}")
                    
                    # Store recognized text in session state for confirmation
                    st.session_state.voice_input = recognized_text
                    st.rerun()
                else:
                    st.error("❌ आवाज ओळखला नाही. कृपया पुन्हा प्रयत्न करा.")
        
        # Show recognized text for confirmation
        if 'voice_input' in st.session_state:
            st.info(f"**ओळखलेला मजकूर:** {st.session_state.voice_input}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ पाठवा", width='stretch'):
                    user_input = st.session_state.voice_input
                    del st.session_state.voice_input
                    
                    # Process the message
                    process_chatbot_message(user_input, voice_engine if voice_mode else None)
                    st.rerun()
            
            with col2:
                if st.button("❌ रद्द करा", width='stretch'):
                    del st.session_state.voice_input
                    st.rerun()
    
    # Text input (always available)
    user_input = st.chat_input("तुमचा प्रश्न येथे टाइप करा...")
    
    if user_input:
        process_chatbot_message(user_input, voice_engine if voice_mode else None)
        st.rerun()
    
    # Show placeholder if no messages
    if not st.session_state.chat_history:
        st.info("💬 चॅटबॉट सुरू करण्यासाठी खाली प्रश्न टाइप करा")
        
        if voice_mode:
            st.info("🎤 किंवा 'बोला' बटण दाबा आणि तुमचा प्रश्न बोला")
        
        # Example questions
        st.markdown("**उदाहरण प्रश्न:**")
        st.markdown("- कांद्याचे रोग कसे ओळखावे?")
        st.markdown("- आजचा बाजार दर काय आहे?")
        st.markdown("- साठवणुकीसाठी योग्य तापमान काय आहे?")
        st.markdown("- पानावर पिवळे ठिपके आहेत - हा कोणता रोग आहे?")
        st.markdown("- टोमॅटोच्या पानावर तपकिरी डाग - काय करावे?")


def process_chatbot_message(user_input: str, voice_engine=None):
    """Process chatbot message with optional voice output"""
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Get real chatbot response using MarathiChatbot
    chatbot = get_marathi_chatbot()
    
    if chatbot:
        try:
            bot_response = chatbot.send_message(user_input)
        except Exception as e:
            bot_response = f"मला माफ करा, सध्या तांत्रिक समस्या आहे. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा."
    else:
        bot_response = f"AI चॅटबॉट सध्या उपलब्ध नाही. कृपया AWS Bedrock क्रेडेन्शियल्स तपासा."
    
    # Generate audio if voice mode is enabled
    audio_path = None
    if voice_engine:
        audio_path = voice_engine.text_to_speech(bot_response)
    
    # Add bot response to history
    message = {
        "role": "assistant",
        "content": bot_response
    }
    
    if audio_path:
        message["audio"] = audio_path
    
    st.session_state.chat_history.append(message)


def show_smart_storage_tab():
    """Display Smart Storage monitoring tab with live sensor data from DynamoDB"""
    st.header("📦 स्मार्ट साठवणूक")
    
    # Storage location selector
    storage_id = st.selectbox(
        "साठवणूक स्थान निवडा",
        ["storage_001"],
        help="तुमचे साठवणूक स्थान निवडा"
    )
    
    st.markdown("---")
    
    # Fetch last 10 entries from DynamoDB
    try:
        secrets_manager = SecretsManager()
        aws_access_key, aws_secret_key = secrets_manager.get_aws_credentials()
        aws_region = 'us-east-1'  # Hardcoded for hackathon
        
        # Initialize DynamoDB client
        dynamodb_client = boto3.client(
            'dynamodb',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        logger = CloudLogger()
        dynamodb_store = DynamoDBStore(dynamodb_client, logger)
        
        # Fetch last 10 sensor readings
        with st.spinner("डेटा लोड करत आहे..."):
            sensor_readings = dynamodb_store.get_sensor_history(storage_id, hours=24)
        
        # If no data, generate mock data for demo
        if not sensor_readings or len(sensor_readings) == 0:
            st.warning("⚠️ DynamoDB मध्ये डेटा उपलब्ध नाही. डेमो डेटा दाखवत आहे.")
            
            # Generate 10 mock data points
            from datetime import datetime, timedelta
            current_time = datetime.now()
            sensor_readings = []
            
            for i in range(10):
                timestamp = current_time - timedelta(minutes=i*5)
                temp = 22 + (i % 3) * 2 + np.random.uniform(-1, 1)
                humidity = 60 + (i % 4) * 3 + np.random.uniform(-2, 2)
                
                sensor_readings.append({
                    'storage_id': storage_id,
                    'timestamp': timestamp.isoformat(),
                    'temperature': round(temp, 1),
                    'humidity': round(humidity, 1)
                })
            
            # Reverse to show oldest first
            sensor_readings = list(reversed(sensor_readings))
        
        # Get latest reading
        latest_reading = sensor_readings[-1] if sensor_readings else None
        
        if latest_reading:
            temp = latest_reading.get('temperature', 0)
            humidity = latest_reading.get('humidity', 0)
            timestamp = latest_reading.get('timestamp', '')
            
            # Determine health status
            if temp > 30:
                health_status = 'Alert'
            elif temp > 25:
                health_status = 'Warning'
            else:
                health_status = 'Safe'
            
            # Display live metrics
            st.subheader("📊 सध्याची स्थिती")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="तापमान (Temperature)",
                    value=f"{temp:.1f}°C",
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="आर्द्रता (Humidity)",
                    value=f"{humidity:.1f}%",
                    delta=None
                )
            
            with col3:
                # Color-coded health status
                if health_status == 'Safe':
                    st.success("**स्थिती**\n\n✅ सुरक्षित")
                elif health_status == 'Warning':
                    st.warning("**स्थिती**\n\n⚠️ सावधान")
                elif health_status == 'Alert':
                    st.error("**स्थिती**\n\n🚨 धोका")
            
            # Last updated timestamp
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    st.caption(f"🕐 शेवटचे अपडेट: {dt.strftime('%d/%m/%Y %I:%M %p')}")
                except:
                    st.caption(f"🕐 शेवटचे अपडेट: {timestamp}")
            
            st.markdown("---")
            
            # High temperature alert in Marathi
            if temp > 30:
                st.error("⚠️ **चेतावणी: उच्च तापमान!**")
                st.warning(f"तापमान {temp:.1f}°C आहे, जे 30°C पेक्षा जास्त आहे. कृपया साठवणूक तपासा आणि वेंटिलेशन सुधारा.")
            
            st.markdown("---")
            
            # Trend charts using st.line_chart
            st.subheader("📈 तापमान आणि आर्द्रता ट्रेंड")
            
            # Prepare data for line chart
            chart_data = pd.DataFrame(sensor_readings)
            
            if 'timestamp' in chart_data.columns:
                # Convert timestamp to datetime for better display
                chart_data['timestamp'] = pd.to_datetime(chart_data['timestamp'])
                chart_data = chart_data.sort_values('timestamp')
                chart_data = chart_data.set_index('timestamp')
                
                # Display combined chart
                st.line_chart(chart_data[['temperature', 'humidity']])
                
                st.caption("🔵 तापमान (Temperature) | 🟢 आर्द्रता (Humidity)")
            
            st.markdown("---")
            
            # Data table
            st.subheader("📋 अलीकडील वाचन (Recent Readings)")
            
            # Format data for display
            display_data = []
            for reading in sensor_readings[-10:]:  # Last 10 entries
                try:
                    dt = datetime.fromisoformat(reading['timestamp'].replace('Z', '+00:00'))
                    time_str = dt.strftime('%I:%M %p')
                except:
                    time_str = reading['timestamp']
                
                display_data.append({
                    'वेळ (Time)': time_str,
                    'तापमान (°C)': f"{reading['temperature']:.1f}",
                    'आर्द्रता (%)': f"{reading['humidity']:.1f}"
                })
            
            # Reverse to show latest first
            display_data = list(reversed(display_data))
            
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
        else:
            st.error("⚠️ डेटा लोड करण्यात अयशस्वी")
    
    except Exception as e:
        st.error(f"⚠️ त्रुटी: {str(e)}")
        st.info("AWS क्रेडेन्शियल्स तपासा किंवा IoT सिम्युलेटर सुरू करा")
    
    # Refresh button
    if st.button("🔄 रिफ्रेश करा", width='stretch'):
        st.rerun()


def show_grading_tab():
    """Display Grading tab for QR code generation"""
    st.header("📱 ग्रेडिंग आणि QR कोड")
    
    st.markdown("### QR कोड तयार करा")
    st.caption("तुमच्या पिकासाठी QR कोड जनरेट करा")
    
    # Initialize QR components
    qr_generator, qr_scanner = get_qr_components()
    
    if not qr_generator:
        st.error("⚠️ QR सेवा सध्या उपलब्ध नाही")
        st.info("AWS क्रेडेन्शियल्स तपासा आणि पुन्हा प्रयत्न करा")
        return
    
    # Get farmer_id from session
    farmer_id = st.session_state.farmer_id
    
    st.markdown("---")
    
    # QR Generation Form
    with st.form("qr_generation_form"):
        st.subheader("📝 पीक माहिती भरा")
        
        col1, col2 = st.columns(2)
        
        with col1:
            crop_type = st.selectbox(
                "पीक प्रकार (Crop Type)",
                ["Onion", "Tomato", "Cotton", "Tur", "Soybean"],
                help="तुमचे पीक निवडा"
            )
            
            grade = st.selectbox(
                "ग्रेड (Grade)",
                ["A", "B", "C"],
                help="A = उत्तम, B = मध्यम, C = सामान्य"
            )
        
        with col2:
            quantity_kg = st.number_input(
                "प्रमाण (किलो)",
                min_value=0.0,
                value=100.0,
                step=10.0,
                help="पिकाचे एकूण वजन"
            )
            
            harvest_date = st.date_input(
                "कापणी तारीख (Harvest Date)",
                value=datetime.now(),
                help="पीक कापणीची तारीख"
            )
        
        submit = st.form_submit_button("🎯 QR कोड तयार करा", width='stretch')
        
        if submit:
            with st.spinner("QR कोड तयार करत आहे..."):
                try:
                    # Generate QR code
                    result = qr_generator.create_lot_qr(
                        crop_type=crop_type,
                        grade=grade,
                        harvest_date=harvest_date.isoformat(),
                        farmer_id=farmer_id
                    )
                    
                    lot_id = result['lot_id']
                    qr_image = result['qr_image']
                    
                    # Store in session state for display
                    st.session_state.generated_qr = {
                        'lot_id': lot_id,
                        'qr_image': qr_image,
                        'crop_type': crop_type,
                        'grade': grade,
                        'quantity_kg': quantity_kg,
                        'harvest_date': harvest_date.isoformat()
                    }
                    
                    st.success("✅ QR कोड यशस्वीरित्या तयार झाला!")
                    st.rerun()
                
                except ValueError as e:
                    st.error(f"त्रुटी: {str(e)}")
                except Exception as e:
                    st.error(f"QR कोड तयार करताना त्रुटी: {str(e)}")
    
    # Display generated QR code if available
    if 'generated_qr' in st.session_state:
        st.markdown("---")
        st.subheader("✅ तयार झालेला QR कोड")
        
        qr_data = st.session_state.generated_qr
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Convert PIL Image to bytes for display
            buffer = BytesIO()
            qr_data['qr_image'].save(buffer, format='PNG')
            buffer.seek(0)
            byte_im = buffer.getvalue()
            
            # Display QR code image (using bytes, not PIL Image)
            st.image(byte_im, caption="QR कोड", use_container_width=True)
            
            # Download button
            st.download_button(
                label="📥 QR कोड डाउनलोड करा",
                data=byte_im,
                file_name=f"qr_code_{qr_data['lot_id'][:8]}.png",
                mime="image/png",
                use_container_width=True
            )
        
        with col2:
            # Display lot details
            st.info(f"""
**लॉट माहिती (Lot Information)**

**लॉट ID:** {qr_data['lot_id'][:8]}...

**पीक:** {qr_data['crop_type']}

**ग्रेड:** {qr_data['grade']}

**प्रमाण:** {qr_data['quantity_kg']} किलो

**कापणी तारीख:** {qr_data['harvest_date']}
            """)
        
        # Clear button
        if st.button("🗑️ नवीन QR कोड तयार करा"):
            del st.session_state.generated_qr
            st.rerun()


def show_sales_tab():
    """Display Sales tab for QR code scanning"""
    st.header("🛒 विक्री आणि व्हेरिफिकेशन")
    
    st.markdown("### QR कोड स्कॅन करा")
    st.caption("पिकाची माहिती तपासण्यासाठी QR कोड अपलोड करा")
    
    # Initialize QR components
    qr_generator, qr_scanner = get_qr_components()
    
    if not qr_scanner:
        st.error("⚠️ QR स्कॅनर सेवा सध्या उपलब्ध नाही")
        st.info("AWS क्रेडेन्शियल्स तपासा आणि पुन्हा प्रयत्न करा")
        return
    
    st.markdown("---")
    
    # File uploader for QR code
    uploaded_file = st.file_uploader(
        "QR कोड अपलोड करा",
        type=['png', 'jpg', 'jpeg'],
        help="QR कोड असलेली इमेज अपलोड करा"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Display uploaded image
            st.subheader("📷 अपलोड केलेली इमेज")
            image = Image.open(uploaded_file)
            st.image(image, caption="QR कोड इमेज", use_container_width=True)
        
        with col2:
            st.subheader("🔍 व्हेरिफिकेशन परिणाम")
            
            # Scan and verify QR code
            with st.spinner("QR कोड स्कॅन करत आहे..."):
                result = qr_scanner.scan_and_verify(image)
            
            if result['success']:
                # Valid QR code
                st.success("✅ QR कोड वैध आहे!")
                
                lot_data = result['lot_data']
                
                # Display lot details in card format
                st.markdown("---")
                st.markdown("### 📦 लॉट तपशील")
                
                st.info(f"""
**लॉट ID:** {lot_data.get('lot_id', 'N/A')[:8]}...

**पीक प्रकार:** {lot_data.get('crop_type', 'N/A')}

**ग्रेड:** {lot_data.get('grade', 'N/A')}

**कापणी तारीख:** {lot_data.get('harvest_date', 'N/A')}

**शेतकरी ID:** {lot_data.get('farmer_id', 'N/A')[:8]}...
                """)
                
                # Additional verification info
                st.success("🔒 **स्थिती:** सत्यापित आणि विश्वसनीय")
                st.caption("हा QR कोड डेटाबेसमध्ये नोंदणीकृत आहे")
            
            else:
                # Invalid QR code
                st.error("❌ QR कोड अवैध आहे!")
                
                message = result.get('message', 'QR कोड अवैध आहे')
                st.warning(f"**कारण:** {message}")
                
                st.info("""
**सूचना:**
- QR कोड स्पष्ट आणि पूर्ण असल्याची खात्री करा
- योग्य इमेज फॉरमॅट वापरा (PNG, JPG)
- QR कोड सिस्टिममध्ये नोंदणीकृत असावा
                """)
    
    else:
        # Show instructions when no file uploaded
        st.info("""
📱 **QR कोड स्कॅन करण्यासाठी:**

1. वरील बटणावर क्लिक करा
2. QR कोड असलेली इमेज निवडा
3. सिस्टिम आपोआप स्कॅन आणि व्हेरिफाय करेल

**समर्थित फॉरमॅट:** PNG, JPG, JPEG
        """)
        
        # Show example
        st.markdown("---")
        st.caption("💡 तुम्ही 'ग्रेडिंग' टॅबमध्ये QR कोड तयार करू शकता")


def show_main_dashboard():
    """Display main dashboard with tabs for logged-in farmers"""
    st.title("🌾 Agri-Intelligence & Life-Cycle Management System")
    st.markdown("### कृषी बुद्धिमत्ता आणि जीवनचक्र व्यवस्थापन प्रणाली")
    
    st.divider()
    
    # Create tabs with Bilingual labels
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🏠 मुख्य डॅशबोर्ड (Home Dashboard)",
        "🏪 बाजार शोध (Market Intelligence)",
        "📦 स्मार्ट साठवणूक (Smart Storage)",
        "📱 ग्रेडिंग (Grading & Quality)",
        "🛒 विक्री (Marketplace/Sales)",
        "🤖 AI मदतनीस (AI Assistant)",
        "👨‍🌾 माझी प्रोफाइल (My Profile)",
        "🎤 आवाज मोड (Voice Mode)"
    ])
    
    with tab1:
        show_dashboard_tab()
    
    with tab2:
        # Use enhanced market intelligence tab with weather and market integration
        show_enhanced_market_intel_tab()
    
    with tab3:
        show_smart_storage_tab()
    
    with tab4:
        show_grading_tab()
    
    with tab5:
        show_sales_tab()
    
    with tab6:
        show_chatbot_tab()
    
    with tab7:
        # Show profile details in tab
        st.header("👨‍🌾 माझी प्रोफाइल (My Profile)")
        user = st.session_state.user
        if user:
            st.info(f"""
**नाव (Name):** {user.get('name', 'N/A')}

**ठिकाण (Location):** {user.get('location', 'N/A')}

**साठवण क्षमता (Capacity):** {user.get('storage_capacity', 0)} क्विंटल

**मोबाईल (Phone):** {user.get('phone', 'N/A')}
            """)
            if st.session_state.guest_mode:
                st.warning("🔓 अतिथी मोड (Guest Mode Active)")
    
    with tab8:
        # Voice mode settings
        st.header("🎤 आवाज मोड (Voice Mode)")
        st.markdown("### आवाज सेटिंग्ज")
        
        voice_enabled = st.checkbox(
            "आवाज सक्षम करा (Enable Voice)",
            value=st.session_state.voice_mode,
            help="चॅटबॉटमध्ये आवाज इनपुट/आउटपुट सक्षम करा"
        )
        
        if voice_enabled != st.session_state.voice_mode:
            st.session_state.voice_mode = voice_enabled
            st.success("✅ सेटिंग्ज अपडेट झाल्या!")
            st.rerun()
        
        if voice_enabled:
            st.success("🎤 आवाज मोड सक्षम आहे")
            st.info("AI मदतनीस टॅबमध्ये जा आणि 'बोला' बटण वापरा")
        else:
            st.info("आवाज मोड बंद आहे")


def show_welcome_page():
    """Display welcome page for non-logged-in users"""
    st.title("🌾 कृषी बुद्धिमत्ता आणि जीवन-चक्र व्यवस्थापन प्रणाली")
    st.markdown("### Agri-Intelligence & Life-Cycle Management System")
    
    st.markdown("---")
    
    st.markdown("""
    ## स्वागत आहे! 🙏
    
    ही प्रणाली शेतकऱ्यांसाठी खालील सुविधा प्रदान करते:
    
    ### 🌟 मुख्य वैशिष्ट्ये:
    
    1. **🌤️ हवामान माहिती**
       - थेट हवामान अपडेट
       - अंदाज आणि इशारे
    
    2. **📊 किंमत अंदाज**
       - 15 दिवसांचा कांदा किंमत अंदाज
       - AI-आधारित विश्लेषण
    
    3. **🧅 रोग निदान**
       - कांदा रोग ओळख
       - उपचार सूचना
    
    4. **💬 मराठी चॅटबॉट**
       - शेती सल्ला
       - प्रश्न विचारा
    
    5. **📱 QR कोड ट्रॅकिंग**
       - पीक ग्रेडिंग
       - पुरवठा साखळी
    
    ---
    
    ### 🚀 सुरुवात करण्यासाठी:
    
    कृपया डाव्या बाजूच्या मेनूमध्ये **लॉगिन** करा किंवा **नवीन नोंदणी** करा.
    """)
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**🎯 अचूक अंदाज**\n\nMachine Learning वापरून किंमत अंदाज")
    
    with col2:
        st.success("**🔒 सुरक्षित**\n\nतुमची माहिती सुरक्षित")
    
    with col3:
        st.warning("**📞 24/7 उपलब्ध**\n\nकधीही वापरा")


def main():
    """Main application entry point - Guest Access by default"""
    
    # Check credentials on startup (optional, won't block guest access)
    try:
        secrets_manager = SecretsManager()
    except MissingCredentialError as e:
        # Don't block guest access, just show warning in sidebar
        pass
    
    # Sidebar - Always show profile (guest or logged-in)
    if st.session_state.guest_mode or st.session_state.farmer_id:
        show_farmer_profile()
    else:
        # Only show login if user explicitly clicked login button
        show_login_registration()
    
    # Main content - Always show dashboard (guest access enabled)
    if st.session_state.guest_mode or st.session_state.farmer_id:
        show_main_dashboard()
    else:
        # Only show welcome page if user is in login flow
        show_welcome_page()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "कृषी बुद्धिमत्ता प्रणाली © 2026 | Made with ❤️ for Indian Farmers"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
