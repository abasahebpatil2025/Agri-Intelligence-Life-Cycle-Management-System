# Agri-Intelligence & Life-Cycle Management System

A cloud-native agricultural decision support platform for Indian farmers.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

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
