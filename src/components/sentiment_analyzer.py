"""
Sentiment Analyzer Component

Analyzes agricultural news sentiment using AWS Bedrock Amazon Titan.
Fetches news from RSS feeds and classifies sentiment.
Integrates with CloudLogger for request tracking.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
"""

import json
import feedparser
import time
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter


class SentimentAnalyzer:
    """
    Sentiment analyzer for agricultural news using AWS Bedrock Amazon Titan.
    
    Classifies news sentiment as Positive, Neutral, or Negative.
    Aggregates sentiment across multiple news items.
    """
    
    # Agricultural news RSS feeds
    AGRICULTURAL_RSS_FEEDS = [
        'https://www.agrifarming.in/feed',
        'https://krishijagran.com/rss/news.xml',
        'https://www.thehindubusinessline.com/economy/agri-business/?service=rss',
    ]
    
    # Valid sentiment values
    VALID_SENTIMENTS = ['Positive', 'Neutral', 'Negative']
    
    def __init__(self, bedrock_client, logger=None):
        """
        Initialize Sentiment Analyzer.
        
        Args:
            bedrock_client: boto3 bedrock-runtime client
            logger: Optional CloudLogger instance
        """
        self.bedrock_client = bedrock_client
        self.logger = logger
        
        # Amazon Titan Text Express model ID (AWS native - no marketplace payment issues)
        self.model_id = "amazon.titan-text-express-v1"
        
        # System prompt for sentiment classification
        self.system_prompt = (
            "You are an expert agricultural market analyst. "
            "Classify the following news into 'Positive', 'Neutral', or 'Negative'. "
            "Output ONLY the single word: Positive, Neutral, or Negative. "
            "Do not include any explanation or additional text."
        )
    
    def fetch_news(self, max_items: int = 10) -> List[Dict[str, str]]:
        """
        Fetch agricultural news from RSS feeds.
        
        Args:
            max_items: Maximum number of news items to fetch
            
        Returns:
            List of news items with 'title', 'summary', 'link', 'published'
        """
        news_items = []
        
        for feed_url in self.AGRICULTURAL_RSS_FEEDS:
            try:
                # Parse RSS feed
                feed = feedparser.parse(feed_url)
                
                # Extract news items
                for entry in feed.entries[:max_items]:
                    news_item = {
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': feed.feed.get('title', 'Unknown')
                    }
                    
                    # Only add if we have meaningful content
                    if news_item['title'] or news_item['summary']:
                        news_items.append(news_item)
                    
                    # Stop if we have enough items
                    if len(news_items) >= max_items:
                        break
                
                if len(news_items) >= max_items:
                    break
            
            except Exception as e:
                # Log error but continue with other feeds
                if self.logger:
                    self.logger.log_bedrock_call(
                        request={'operation': 'fetch_news', 'feed_url': feed_url},
                        response={'error': str(e)},
                        error=str(e)
                    )
                continue
        
        # Log successful fetch
        if self.logger:
            self.logger.log_bedrock_call(
                request={'operation': 'fetch_news', 'max_items': max_items},
                response={'items_fetched': len(news_items)}
            )
        
        return news_items
    
    def classify_sentiment(self, text: str) -> str:
        """
        Classify sentiment of a single text using AWS Bedrock Amazon Titan.
        
        Args:
            text: News text to classify
            
        Returns:
            Sentiment: 'Positive', 'Neutral', or 'Negative'
            Defaults to 'Neutral' on error
        """
        if not text or not text.strip():
            return 'Neutral'
        
        try:
            # Prepare request for Amazon Titan (different JSON structure than Claude)
            input_text = f"{self.system_prompt}\n\nNews: {text[:1000]}"
            
            request_body = {
                "inputText": input_text,
                "textGenerationConfig": {
                    "maxTokenCount": 10,  # We only need one word
                    "temperature": 0.0,  # Deterministic output
                    "topP": 1.0,
                    "stopSequences": []
                }
            }
            
            # Log request
            if self.logger:
                self.logger.log_bedrock_call(
                    request={
                        'operation': 'classify_sentiment',
                        'model': self.model_id,
                        'text_length': len(text)
                    },
                    response={'status': 'pending'}
                )
            
            # Call Bedrock with Titan
            start_time = time.time()
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            duration = time.time() - start_time
            
            # Parse Titan response (different structure than Claude)
            response_body = json.loads(response['body'].read())
            sentiment_text = response_body['results'][0]['outputText'].strip()
            
            # Extract sentiment (handle various formats)
            sentiment = self._extract_sentiment(sentiment_text)
            
            # Log successful response
            if self.logger:
                self.logger.log_bedrock_call(
                    request={
                        'operation': 'classify_sentiment',
                        'model': self.model_id,
                        'text_preview': text[:100]
                    },
                    response={
                        'sentiment': sentiment,
                        'raw_response': sentiment_text,
                        'duration': duration
                    }
                )
            
            return sentiment
        
        except Exception as e:
            # Log error and return default
            if self.logger:
                self.logger.log_bedrock_call(
                    request={
                        'operation': 'classify_sentiment',
                        'model': self.model_id
                    },
                    response={'error': str(e)},
                    error=str(e)
                )
            
            # Default to Neutral on any error
            return 'Neutral'
    
    def _extract_sentiment(self, text: str) -> str:
        """
        Extract sentiment from Claude's response.
        
        Args:
            text: Raw response text from Claude
            
        Returns:
            Valid sentiment: 'Positive', 'Neutral', or 'Negative'
        """
        text_upper = text.upper()
        
        # Check for each sentiment
        if 'POSITIVE' in text_upper:
            return 'Positive'
        elif 'NEGATIVE' in text_upper:
            return 'Negative'
        elif 'NEUTRAL' in text_upper:
            return 'Neutral'
        
        # Default to Neutral if unclear
        return 'Neutral'
    
    def aggregate_sentiment(self, news_items: List[Dict[str, str]]) -> Tuple[str, float]:
        """
        Aggregate sentiment across multiple news items.
        
        Args:
            news_items: List of news items (each with 'title' and 'summary')
            
        Returns:
            Tuple of (overall_sentiment, confidence)
            - overall_sentiment: 'Positive', 'Neutral', or 'Negative'
            - confidence: Percentage of items with the majority sentiment (0.0-1.0)
        """
        if not news_items:
            return ('Neutral', 0.0)
        
        sentiments = []
        
        # Classify each news item
        for item in news_items:
            # Combine title and summary for classification
            text = f"{item.get('title', '')} {item.get('summary', '')}"
            sentiment = self.classify_sentiment(text)
            sentiments.append(sentiment)
        
        # Count sentiments
        sentiment_counts = Counter(sentiments)
        
        # Find majority sentiment
        if not sentiment_counts:
            return ('Neutral', 0.0)
        
        overall_sentiment = sentiment_counts.most_common(1)[0][0]
        confidence = sentiment_counts[overall_sentiment] / len(sentiments)
        
        # Log aggregation results
        if self.logger:
            self.logger.log_bedrock_call(
                request={
                    'operation': 'aggregate_sentiment',
                    'total_items': len(news_items)
                },
                response={
                    'overall_sentiment': overall_sentiment,
                    'confidence': confidence,
                    'sentiment_breakdown': dict(sentiment_counts)
                }
            )
        
        return (overall_sentiment, confidence)
    
    def analyze_market_sentiment(self, max_news_items: int = 10) -> Dict[str, Any]:
        """
        Complete market sentiment analysis workflow.
        
        Fetches news, classifies sentiment, and aggregates results.
        
        Args:
            max_news_items: Maximum number of news items to analyze
            
        Returns:
            Dictionary with:
            - overall_sentiment: 'Positive', 'Neutral', or 'Negative'
            - confidence: Confidence score (0.0-1.0)
            - news_count: Number of news items analyzed
            - sentiment_breakdown: Count of each sentiment
            - sample_news: Sample of analyzed news items
        """
        # Fetch news
        news_items = self.fetch_news(max_items=max_news_items)
        
        if not news_items:
            return {
                'overall_sentiment': 'Neutral',
                'confidence': 0.0,
                'news_count': 0,
                'sentiment_breakdown': {},
                'sample_news': []
            }
        
        # Classify and aggregate
        sentiments = []
        analyzed_news = []
        
        for item in news_items:
            text = f"{item.get('title', '')} {item.get('summary', '')}"
            sentiment = self.classify_sentiment(text)
            sentiments.append(sentiment)
            
            analyzed_news.append({
                'title': item.get('title', ''),
                'sentiment': sentiment,
                'source': item.get('source', 'Unknown'),
                'link': item.get('link', '')
            })
        
        # Calculate aggregated sentiment
        sentiment_counts = Counter(sentiments)
        overall_sentiment = sentiment_counts.most_common(1)[0][0] if sentiment_counts else 'Neutral'
        confidence = sentiment_counts[overall_sentiment] / len(sentiments) if sentiments else 0.0
        
        return {
            'overall_sentiment': overall_sentiment,
            'confidence': round(confidence, 2),
            'news_count': len(news_items),
            'sentiment_breakdown': dict(sentiment_counts),
            'sample_news': analyzed_news[:5]  # Return top 5 as sample
        }
