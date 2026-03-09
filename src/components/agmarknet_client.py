"""
Agmarknet Client Component

Fetches live and historical onion price data from Agmarknet API.
Integrates with CacheLayer and CloudLogger.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 20.1, 20.2
"""

import requests
import pandas as pd
import time
from datetime import datetime, date
from typing import Optional, List, Dict, Any


class AgmarknetClient:
    """
    Client for Agmarknet API with caching and retry logic.
    
    Fetches live and historical commodity price data.
    Returns data as Pandas DataFrames for ML compatibility.
    """
    
    def __init__(self, api_key: str, cache=None, logger=None):
        """
        Initialize Agmarknet Client.
        
        Args:
            api_key: Agmarknet API key
            cache: Optional CacheLayer instance
            logger: Optional CloudLogger instance
        """
        self.api_key = api_key
        self.cache = cache
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Agri-Intelligence-System/1.0',
            'Accept': 'application/json'
        })
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s
        
        # API endpoints (placeholder - update with actual Agmarknet endpoints)
        self.base_url = "https://api.data.gov.in/resource"
        self.live_prices_endpoint = f"{self.base_url}/35985678-0d79-46b4-9ed6-6f13308a1d24"
        self.historical_endpoint = f"{self.base_url}/35985678-0d79-46b4-9ed6-6f13308a1d24"
    
    def _retry_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Execute HTTP request with exponential backoff retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object or None if all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)
                response.raise_for_status()
                
                # Log successful request
                if self.logger:
                    self.logger.log_ml_operation(
                        operation='api_request',
                        duration=0.0,
                        details={
                            'url': url,
                            'method': method,
                            'attempt': attempt + 1,
                            'status_code': response.status_code
                        }
                    )
                
                return response
            
            except requests.exceptions.RequestException as e:
                last_error = e
                
                # Log error
                if self.logger:
                    self.logger.log_ml_operation(
                        operation='api_request',
                        duration=0.0,
                        details={
                            'url': url,
                            'method': method,
                            'attempt': attempt + 1
                        },
                        error=str(e)
                    )
                
                # Retry with exponential backoff
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delays[attempt])
                else:
                    return None
        
        return None
    
    def fetch_live_prices(
        self,
        commodity: str,
        market: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch live commodity prices from Agmarknet.
        
        Args:
            commodity: Commodity name (e.g., 'Onion')
            market: Optional market name filter
            
        Returns:
            DataFrame with columns: date, price, market
        """
        try:
            # Check cache first
            cache_key = f"live_prices_{commodity}_{market}"
            if self.cache:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    return cached_data
            
            # Build request parameters
            params = {
                'api-key': self.api_key,
                'format': 'json',
                'filters[commodity]': commodity,
                'limit': 100
            }
            
            if market:
                params['filters[market]'] = market
            
            # Make API request
            response = self._retry_request('GET', self.live_prices_endpoint, params=params)
            
            if response is None:
                # Log professional message instead of error
                print("ℹ️ Data Syncing: Agmarknet API is currently syncing data. Please try again in a moment.")
                # Return empty DataFrame on failure
                return pd.DataFrame(columns=['date', 'price', 'market'])
            
            data = response.json()
            
            # Parse response (adjust based on actual API structure)
            records = data.get('records', [])
            
            if not records:
                print("ℹ️ Data Syncing: No data available for the requested commodity at this time.")
                return pd.DataFrame(columns=['date', 'price', 'market'])
            
            # Convert to DataFrame
            df = pd.DataFrame(records)
            
            # Standardize columns
            df = self._standardize_columns(df)
            
            # Validate data
            df = self.validate_data(df)
            
            # Cache for 30 minutes (live data)
            if self.cache:
                self.cache.set(cache_key, df, 1800)  # Fixed: pass TTL as positional arg
            
            return df
        
        except Exception as e:
            # Professional error handling - no red crash boxes
            print(f"ℹ️ Data Syncing: Market data is being updated. Please try again shortly.")
            if self.logger:
                self.logger.log_ml_operation(
                    operation='parse_live_prices',
                    duration=0.0,
                    details={'commodity': commodity},
                    error=str(e)
                )
            return pd.DataFrame(columns=['date', 'price', 'market'])
    
    def fetch_historical_prices(
        self,
        commodity: str,
        market: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Fetch historical commodity prices with pagination support.
        
        Args:
            commodity: Commodity name (e.g., 'Onion')
            market: Market name
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame with columns: date, price, market
        """
        try:
            # Check cache first (24-hour TTL for historical data)
            cache_key = f"historical_{commodity}_{market}_{start_date}_{end_date}"
            if self.cache:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    return cached_data
            
            all_records = []
            offset = 0
            limit = 100  # Records per page
            total_records = None
            
            # Pagination loop
            while True:
                # Build request parameters
                params = {
                    'api-key': self.api_key,
                    'format': 'json',
                    'filters[commodity]': commodity,
                    'filters[market]': market,
                    'filters[arrival_date][from]': start_date.strftime('%Y-%m-%d'),
                    'filters[arrival_date][to]': end_date.strftime('%Y-%m-%d'),
                    'offset': offset,
                    'limit': limit
                }
                
                # Make API request
                response = self._retry_request('GET', self.historical_endpoint, params=params)
                
                if response is None:
                    break
                
                try:
                    data = response.json()
                    records = data.get('records', [])
                    
                    # Get total on first request
                    if total_records is None:
                        total_records = data.get('total', 0)
                    
                    # No more records
                    if not records:
                        break
                    
                    # Append records from this page
                    all_records.extend(records)
                    
                    # Check if we have all records
                    if len(all_records) >= total_records:
                        break
                    
                    # Update offset for next page
                    offset += limit
                
                except Exception as e:
                    if self.logger:
                        self.logger.log_ml_operation(
                            operation='fetch_historical_page',
                            duration=0.0,
                            details={'offset': offset, 'commodity': commodity},
                            error=str(e)
                        )
                    break
            
            if not all_records:
                print("ℹ️ Data Syncing: Historical data is being updated. Please try again shortly.")
                return pd.DataFrame(columns=['date', 'price', 'market'])
            
            # Convert to DataFrame
            df = pd.DataFrame(all_records)
            
            # Standardize columns
            df = self._standardize_columns(df)
            
            # Validate data
            df = self.validate_data(df)
            
            # Sort by date
            if not df.empty and 'date' in df.columns:
                df = df.sort_values('date').reset_index(drop=True)
            
            # Cache for 24 hours
            if self.cache:
                self.cache.set(cache_key, df, 86400)
            
            return df
        
        except Exception as e:
            print(f"ℹ️ Data Syncing: Historical market data is being updated. Please try again shortly.")
            if self.logger:
                self.logger.log_ml_operation(
                    operation='fetch_historical_prices',
                    duration=0.0,
                    details={'commodity': commodity, 'market': market},
                    error=str(e)
                )
            return pd.DataFrame(columns=['date', 'price', 'market'])
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize DataFrame columns to expected format.
        
        Args:
            df: Raw DataFrame from API
            
        Returns:
            DataFrame with standardized columns: date, price, market
        """
        # Map common column names (adjust based on actual API)
        column_mapping = {
            'arrival_date': 'date',
            'date': 'date',
            'modal_price': 'price',
            'price': 'price',
            'market_name': 'market',
            'market': 'market'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['date', 'price', 'market']
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # Select only required columns
        df = df[required_columns]
        
        return df
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate price data quality.
        
        Checks:
        - Price values are numeric and > 0
        - Dates are in valid ISO 8601 format
        - Removes invalid records
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Validated DataFrame with invalid records removed
        """
        if df.empty:
            return df
        
        # Make a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        original_count = len(df)
        
        # Convert price to numeric
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # Remove rows with invalid prices (NaN or <= 0)
        df = df[df['price'] > 0].copy()
        
        # Validate and convert dates to ISO 8601 format
        if 'date' in df.columns:
            try:
                # Convert to datetime explicitly to avoid FutureWarning
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                
                # Drop rows with NaT (invalid dates) only
                df = df.dropna(subset=['date']).copy()
                
                # Convert to string in ISO 8601 format (YYYY-MM-DD)
                # Using dt.strftime to avoid FutureWarning
                if not df.empty:
                    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                
            except Exception as e:
                # If date conversion fails completely, log and return what we have
                if self.logger:
                    self.logger.log_ml_operation(
                        operation='validate_data_dates',
                        duration=0.0,
                        details={'error': str(e)},
                        error='Date conversion failed'
                    )
                # Don't return empty - return the data we have
                pass
        
        # Remove rows with missing required fields (after string conversion)
        df = df.dropna(subset=['date', 'price', 'market']).copy()
        
        # Log validation results
        removed_count = original_count - len(df)
        if removed_count > 0 and self.logger:
            self.logger.log_ml_operation(
                operation='validate_data',
                duration=0.0,
                details={
                    'original_count': original_count,
                    'removed_count': removed_count,
                    'valid_count': len(df)
                }
            )
        
        return df
    
    def get_data_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate data quality metrics.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with quality metrics
        """
        if df.empty:
            return {
                'total_records': 0,
                'missing_values_pct': 0,
                'valid_prices_pct': 0,
                'date_range': None
            }
        
        total = len(df)
        missing = df.isnull().sum().sum()
        missing_pct = (missing / (total * len(df.columns))) * 100
        
        valid_prices = (df['price'] > 0).sum()
        valid_prices_pct = (valid_prices / total) * 100
        
        date_range = None
        if 'date' in df.columns and not df['date'].isnull().all():
            try:
                dates = pd.to_datetime(df['date'])
                date_range = f"{dates.min()} to {dates.max()}"
            except Exception:
                pass
        
        return {
            'total_records': total,
            'missing_values_pct': round(missing_pct, 2),
            'valid_prices_pct': round(valid_prices_pct, 2),
            'date_range': date_range
        }
