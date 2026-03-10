# 🌾 Agri-Intelligence & Life-Cycle Management System

A cloud-native agricultural decision support platform leveraging Generative AI and Serverless Architecture to empower Indian farmers with real-time insights.

## 🚀 Why This Solution?
Agriculture in India faces challenges like unpredictable weather and pest outbreaks. Our system acts as an AI-powered Agri-Expert, providing:
- **Instant Disease Diagnosis:** Using Computer Vision to detect crop health.
- **Market Intelligence:** Real-time data to help farmers get the best prices.
- **Smart Storage Monitoring:** IoT-ready infrastructure to track humidity/temperature.

## ☁️ AWS & GenAI Architecture
We have built this on a **Serverless-First** approach:
- **Amazon Bedrock:** Powers our Marathi-language AI Assistant, providing RAG-based crop recommendations.
- **Amazon DynamoDB:** A scalable NoSQL backend that handles our user data and real-time sensor readings (`AgriIntelligence_Data` & `SensorReadings` tables).
- **Amazon S3:** Secure storage for crop images and diagnostic reports.

## 🛠 Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt

2. Configure secrets:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit secrets.toml with your actual credentials
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Start the application:
   ```bash
   streamlit run src/app.py
   ```

## Project Structure

- `src/` - Source code
- `src/components/` - Core components
- `tests/` - Test suite
- `config/` - Configuration files
- `data/` - Data storage

