"""
Price Forecaster Component

Forecasts commodity prices using Facebook Prophet.
Applies sentiment-based adjustments to predictions.
Persists models to S3 for reuse.

Requirements: 4.4, 4.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 20.3
"""

import pandas as pd
import numpy as np
import pickle
import io
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from prophet import Prophet


class PriceForecaster:
    """
    Price forecaster using Facebook Prophet with sentiment adjustment.
    
    Trains on historical price data and generates 15-day forecasts.
    Applies sentiment-based adjustments to predictions.
    Persists models to S3 for reuse.
    """
    
    # Minimum data requirements
    MIN_TRAINING_DAYS = 180
    MAX_MISSING_PCT = 10.0
    
    # Sentiment adjustment factors
    SENTIMENT_ADJUSTMENTS = {
        'Positive': 0.075,   # +7.5%
        'Neutral': 0.0,      # 0%
        'Negative': -0.125   # -12.5%
    }
    
    def __init__(self, model_type: str = 'prophet', s3_client=None, logger=None):
        """
        Initialize Price Forecaster.
        
        Args:
            model_type: Model type (currently only 'prophet' supported)
            s3_client: Optional boto3 S3 client for model persistence
            logger: Optional CloudLogger instance
        """
        self.model_type = model_type
        self.s3_client = s3_client
        self.logger = logger
        self.model = None
        self.training_metadata = {}
        
        # S3 configuration
        self.s3_bucket = None  # Will be set when saving
        self.s3_prefix = 'models/'
    
    def validate_training_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate training data meets minimum requirements.
        
        Args:
            df: DataFrame with 'ds' (date) and 'y' (price) columns
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required columns
        if 'ds' not in df.columns or 'y' not in df.columns:
            return False, "DataFrame must have 'ds' (date) and 'y' (price) columns"
        
        # Check minimum data points
        if len(df) < self.MIN_TRAINING_DAYS:
            return False, f"Insufficient data: {len(df)} days, minimum {self.MIN_TRAINING_DAYS} required"
        
        # Check missing values
        missing_count = df['y'].isnull().sum()
        missing_pct = (missing_count / len(df)) * 100
        
        if missing_pct > self.MAX_MISSING_PCT:
            return False, f"Too many missing values: {missing_pct:.1f}%, maximum {self.MAX_MISSING_PCT}% allowed"
        
        # Check for valid prices (> 0)
        if (df['y'] <= 0).any():
            return False, "All prices must be greater than 0"
        
        return True, ""
    
    def train(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train Prophet model on historical price data.
        
        Args:
            historical_data: DataFrame with columns:
                - date: Date of price observation
                - price: Price value
                - market: Market name (optional)
                
        Returns:
            Dictionary with training metrics and metadata
        """
        start_time = time.time()
        
        try:
            # Prepare data for Prophet (requires 'ds' and 'y' columns)
            df = historical_data.copy()
            
            # Rename columns to Prophet format
            if 'date' in df.columns and 'price' in df.columns:
                df = df.rename(columns={'date': 'ds', 'price': 'y'})
            
            # Convert date to datetime
            df['ds'] = pd.to_datetime(df['ds'])
            
            # Sort by date
            df = df.sort_values('ds').reset_index(drop=True)
            
            # Validate data
            is_valid, error_msg = self.validate_training_data(df)
            if not is_valid:
                if self.logger:
                    self.logger.log_ml_operation(
                        operation='train_model',
                        duration=time.time() - start_time,
                        details={'error': error_msg},
                        error=error_msg
                    )
                raise ValueError(error_msg)
            
            # Initialize Prophet with optimized parameters for speed
            self.model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.05,
                interval_width=0.95
            )
            
            # Fit model
            self.model.fit(df[['ds', 'y']])
            
            # Store training metadata
            training_duration = time.time() - start_time
            self.training_metadata = {
                'training_date': datetime.now().isoformat(),
                'training_duration': training_duration,
                'data_points': len(df),
                'date_range': {
                    'start': df['ds'].min().isoformat(),
                    'end': df['ds'].max().isoformat()
                },
                'price_stats': {
                    'mean': float(df['y'].mean()),
                    'std': float(df['y'].std()),
                    'min': float(df['y'].min()),
                    'max': float(df['y'].max())
                }
            }
            
            # Log successful training
            if self.logger:
                self.logger.log_ml_operation(
                    operation='train_model',
                    duration=training_duration,
                    details=self.training_metadata
                )
            
            return self.training_metadata
        
        except Exception as e:
            if self.logger:
                self.logger.log_ml_operation(
                    operation='train_model',
                    duration=time.time() - start_time,
                    details={'error': str(e)},
                    error=str(e)
                )
            raise
    
    def predict(self, days: int = 15) -> pd.DataFrame:
        """
        Generate price predictions for future days.
        
        Args:
            days: Number of days to forecast (default 15)
            
        Returns:
            DataFrame with columns:
                - date: Forecast date
                - predicted_price: Predicted price
                - lower_bound: Lower confidence bound (95%)
                - upper_bound: Upper confidence bound (95%)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        start_time = time.time()
        
        try:
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=days, freq='D')
            
            # Generate predictions
            forecast = self.model.predict(future)
            
            # Extract only future predictions (last 'days' rows)
            forecast = forecast.tail(days).copy()
            
            # Prepare output DataFrame
            predictions = pd.DataFrame({
                'date': forecast['ds'].dt.strftime('%Y-%m-%d'),
                'predicted_price': forecast['yhat'].round(2),
                'lower_bound': forecast['yhat_lower'].round(2),
                'upper_bound': forecast['yhat_upper'].round(2)
            })
            
            # Ensure no negative prices
            predictions['predicted_price'] = predictions['predicted_price'].clip(lower=0)
            predictions['lower_bound'] = predictions['lower_bound'].clip(lower=0)
            predictions['upper_bound'] = predictions['upper_bound'].clip(lower=0)
            
            # Log prediction
            if self.logger:
                self.logger.log_ml_operation(
                    operation='predict',
                    duration=time.time() - start_time,
                    details={
                        'forecast_days': days,
                        'predictions_count': len(predictions)
                    }
                )
            
            return predictions
        
        except Exception as e:
            if self.logger:
                self.logger.log_ml_operation(
                    operation='predict',
                    duration=time.time() - start_time,
                    details={'error': str(e)},
                    error=str(e)
                )
            raise
    
    def apply_sentiment_adjustment(
        self,
        predictions: pd.DataFrame,
        sentiment: str
    ) -> pd.DataFrame:
        """
        Apply sentiment-based adjustment to predictions.
        
        Args:
            predictions: DataFrame from predict() method
            sentiment: Sentiment ('Positive', 'Neutral', or 'Negative')
            
        Returns:
            DataFrame with adjusted predictions
        """
        if sentiment not in self.SENTIMENT_ADJUSTMENTS:
            if self.logger:
                self.logger.log_ml_operation(
                    operation='apply_sentiment_adjustment',
                    duration=0.0,
                    details={'error': f'Invalid sentiment: {sentiment}'},
                    error=f'Invalid sentiment: {sentiment}'
                )
            sentiment = 'Neutral'  # Default to Neutral for invalid sentiment
        
        adjustment_factor = self.SENTIMENT_ADJUSTMENTS[sentiment]
        
        # Apply adjustment
        adjusted = predictions.copy()
        adjusted['predicted_price'] = (
            adjusted['predicted_price'] * (1 + adjustment_factor)
        ).round(2)
        adjusted['lower_bound'] = (
            adjusted['lower_bound'] * (1 + adjustment_factor)
        ).round(2)
        adjusted['upper_bound'] = (
            adjusted['upper_bound'] * (1 + adjustment_factor)
        ).round(2)
        
        # Ensure no negative prices
        adjusted['predicted_price'] = adjusted['predicted_price'].clip(lower=0)
        adjusted['lower_bound'] = adjusted['lower_bound'].clip(lower=0)
        adjusted['upper_bound'] = adjusted['upper_bound'].clip(lower=0)
        
        # Log adjustment
        if self.logger:
            self.logger.log_ml_operation(
                operation='apply_sentiment_adjustment',
                duration=0.0,
                details={
                    'sentiment': sentiment,
                    'adjustment_factor': adjustment_factor,
                    'adjustment_pct': f'{adjustment_factor * 100:+.1f}%'
                }
            )
        
        return adjusted
    
    def save_model_to_s3(
        self,
        bucket: str,
        commodity: str,
        market: str
    ) -> str:
        """
        Save trained model to S3.
        
        Args:
            bucket: S3 bucket name
            commodity: Commodity name (e.g., 'Onion')
            market: Market name (e.g., 'Nashik')
            
        Returns:
            S3 key of saved model
        """
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")
        
        if self.s3_client is None:
            raise ValueError("S3 client not configured")
        
        start_time = time.time()
        
        try:
            # Create model package
            model_package = {
                'model': self.model,
                'metadata': self.training_metadata,
                'model_type': self.model_type
            }
            
            # Serialize model
            model_bytes = pickle.dumps(model_package)
            
            # Generate S3 key
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_key = f"{self.s3_prefix}{commodity}_{market}_{timestamp}.pkl"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=model_bytes,
                ContentType='application/octet-stream',
                Metadata={
                    'commodity': commodity,
                    'market': market,
                    'model_type': self.model_type,
                    'training_date': self.training_metadata.get('training_date', '')
                }
            )
            
            # Log save operation
            if self.logger:
                self.logger.log_s3_operation(
                    operation='save_model',
                    key=s3_key,
                    details={
                        'bucket': bucket,
                        'commodity': commodity,
                        'market': market,
                        'duration': time.time() - start_time
                    }
                )
            
            return s3_key
        
        except Exception as e:
            if self.logger:
                self.logger.log_s3_operation(
                    operation='save_model',
                    key='',
                    details={'error': str(e)},
                    error=str(e)
                )
            raise
    
    def load_model_from_s3(self, bucket: str, model_key: str) -> Dict[str, Any]:
        """
        Load trained model from S3.
        
        Args:
            bucket: S3 bucket name
            model_key: S3 key of saved model
            
        Returns:
            Model metadata dictionary
        """
        if self.s3_client is None:
            raise ValueError("S3 client not configured")
        
        start_time = time.time()
        
        try:
            # Download from S3
            response = self.s3_client.get_object(Bucket=bucket, Key=model_key)
            model_bytes = response['Body'].read()
            
            # Deserialize model
            model_package = pickle.loads(model_bytes)
            
            # Load model and metadata
            self.model = model_package['model']
            self.training_metadata = model_package.get('metadata', {})
            self.model_type = model_package.get('model_type', 'prophet')
            
            # Log load operation
            if self.logger:
                self.logger.log_s3_operation(
                    operation='load_model',
                    key=model_key,
                    details={
                        'bucket': bucket,
                        'duration': time.time() - start_time,
                        'metadata': self.training_metadata
                    }
                )
            
            return self.training_metadata
        
        except Exception as e:
            if self.logger:
                self.logger.log_s3_operation(
                    operation='load_model',
                    key=model_key,
                    details={'error': str(e)},
                    error=str(e)
                )
            raise
    
    def forecast_with_sentiment(
        self,
        historical_data: pd.DataFrame,
        sentiment: str,
        days: int = 15
    ) -> pd.DataFrame:
        """
        Complete forecasting workflow: train, predict, and apply sentiment.
        
        Args:
            historical_data: Historical price data
            sentiment: Market sentiment ('Positive', 'Neutral', 'Negative')
            days: Number of days to forecast
            
        Returns:
            DataFrame with sentiment-adjusted predictions
        """
        # Train model
        self.train(historical_data)
        
        # Generate predictions
        predictions = self.predict(days=days)
        
        # Apply sentiment adjustment
        adjusted_predictions = self.apply_sentiment_adjustment(predictions, sentiment)
        
        return adjusted_predictions
