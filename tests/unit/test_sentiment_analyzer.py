"""
Unit tests for Sentiment Analyzer Component

Tests AWS Bedrock integration, news fetching, sentiment classification, and aggregation.
Property-based tests for sentiment validity.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from collections import Counter
from hypothesis import given, strategies as st, settings

# Import the component
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'components'))
from sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer component"""
    
    def test_initialization(self):
        """Test analyzer initialization"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        assert analyzer.bedrock_client == mock_bedrock
        assert analyzer.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert "agricultural market analyst" in analyzer.system_prompt.lower()
        assert len(analyzer.VALID_SENTIMENTS) == 3
    
    def test_extract_sentiment_positive(self):
        """Test sentiment extraction for positive responses"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        assert analyzer._extract_sentiment("Positive") == "Positive"
        assert analyzer._extract_sentiment("positive") == "Positive"
        assert analyzer._extract_sentiment("POSITIVE") == "Positive"
        assert analyzer._extract_sentiment("The sentiment is Positive") == "Positive"
    
    def test_extract_sentiment_negative(self):
        """Test sentiment extraction for negative responses"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        assert analyzer._extract_sentiment("Negative") == "Negative"
        assert analyzer._extract_sentiment("negative") == "Negative"
        assert analyzer._extract_sentiment("NEGATIVE") == "Negative"
    
    def test_extract_sentiment_neutral(self):
        """Test sentiment extraction for neutral responses"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        assert analyzer._extract_sentiment("Neutral") == "Neutral"
        assert analyzer._extract_sentiment("neutral") == "Neutral"
        assert analyzer._extract_sentiment("NEUTRAL") == "Neutral"
    
    def test_extract_sentiment_default(self):
        """Test sentiment extraction defaults to Neutral for unclear responses"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        assert analyzer._extract_sentiment("Unknown") == "Neutral"
        assert analyzer._extract_sentiment("") == "Neutral"
        assert analyzer._extract_sentiment("Maybe") == "Neutral"
    
    def test_classify_sentiment_success(self):
        """Test successful sentiment classification"""
        mock_bedrock = Mock()
        mock_logger = Mock()
        
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read = Mock(return_value=json.dumps({
            'content': [{'text': 'Positive'}]
        }).encode())
        
        mock_bedrock.invoke_model = Mock(return_value=mock_response)
        
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock, logger=mock_logger)
        
        sentiment = analyzer.classify_sentiment("Good harvest expected this year")
        
        assert sentiment == "Positive"
        mock_bedrock.invoke_model.assert_called_once()
    
    def test_classify_sentiment_empty_text(self):
        """Test sentiment classification with empty text"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        assert analyzer.classify_sentiment("") == "Neutral"
        assert analyzer.classify_sentiment("   ") == "Neutral"
        assert analyzer.classify_sentiment(None) == "Neutral"
    
    def test_classify_sentiment_bedrock_failure(self):
        """Test sentiment classification defaults to Neutral on Bedrock failure"""
        mock_bedrock = Mock()
        mock_bedrock.invoke_model = Mock(side_effect=Exception("Bedrock error"))
        
        mock_logger = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock, logger=mock_logger)
        
        sentiment = analyzer.classify_sentiment("Some news text")
        
        assert sentiment == "Neutral"
        # Verify error was logged
        mock_logger.log_bedrock_call.assert_called()
    
    def test_fetch_news_success(self):
        """Test successful news fetching from RSS feeds"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        # Mock feedparser
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                title="Good crop yield",
                summary="Farmers report excellent harvest",
                link="http://example.com/1",
                published="2024-01-01",
                get=lambda k, d=None: {
                    'title': 'Good crop yield',
                    'summary': 'Farmers report excellent harvest',
                    'link': 'http://example.com/1',
                    'published': '2024-01-01'
                }.get(k, d)
            )
        ]
        mock_feed.feed = Mock()
        mock_feed.feed.get = Mock(return_value="Test Feed")
        
        with patch('sentiment_analyzer.feedparser.parse', return_value=mock_feed):
            news_items = analyzer.fetch_news(max_items=5)
        
        assert len(news_items) > 0
        assert 'title' in news_items[0]
        assert 'summary' in news_items[0]
    
    def test_fetch_news_feed_error(self):
        """Test news fetching handles feed errors gracefully"""
        mock_bedrock = Mock()
        mock_logger = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock, logger=mock_logger)
        
        # Mock feedparser to raise exception
        with patch('sentiment_analyzer.feedparser.parse', side_effect=Exception("Feed error")):
            news_items = analyzer.fetch_news(max_items=5)
        
        # Should return empty list on error
        assert isinstance(news_items, list)
    
    def test_aggregate_sentiment_majority_positive(self):
        """Test sentiment aggregation with majority positive"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        # Mock classify_sentiment to return predetermined sentiments
        sentiments = ['Positive', 'Positive', 'Positive', 'Neutral', 'Negative']
        with patch.object(analyzer, 'classify_sentiment', side_effect=sentiments):
            news_items = [
                {'title': 'News 1', 'summary': 'Summary 1'},
                {'title': 'News 2', 'summary': 'Summary 2'},
                {'title': 'News 3', 'summary': 'Summary 3'},
                {'title': 'News 4', 'summary': 'Summary 4'},
                {'title': 'News 5', 'summary': 'Summary 5'}
            ]
            
            overall, confidence = analyzer.aggregate_sentiment(news_items)
        
        assert overall == 'Positive'
        assert confidence == 0.6  # 3 out of 5
    
    def test_aggregate_sentiment_majority_negative(self):
        """Test sentiment aggregation with majority negative"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        sentiments = ['Negative', 'Negative', 'Neutral']
        with patch.object(analyzer, 'classify_sentiment', side_effect=sentiments):
            news_items = [
                {'title': 'News 1', 'summary': 'Summary 1'},
                {'title': 'News 2', 'summary': 'Summary 2'},
                {'title': 'News 3', 'summary': 'Summary 3'}
            ]
            
            overall, confidence = analyzer.aggregate_sentiment(news_items)
        
        assert overall == 'Negative'
        assert confidence > 0.6
    
    def test_aggregate_sentiment_empty_list(self):
        """Test sentiment aggregation with empty news list"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        overall, confidence = analyzer.aggregate_sentiment([])
        
        assert overall == 'Neutral'
        assert confidence == 0.0
    
    def test_analyze_market_sentiment_complete_workflow(self):
        """Test complete market sentiment analysis workflow"""
        mock_bedrock = Mock()
        mock_logger = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock, logger=mock_logger)
        
        # Mock fetch_news
        mock_news = [
            {'title': 'Good harvest', 'summary': 'Excellent yield', 'source': 'Test', 'link': 'http://test.com'},
            {'title': 'Price drop', 'summary': 'Market decline', 'source': 'Test', 'link': 'http://test.com'}
        ]
        
        # Mock classify_sentiment
        sentiments = ['Positive', 'Negative']
        
        with patch.object(analyzer, 'fetch_news', return_value=mock_news):
            with patch.object(analyzer, 'classify_sentiment', side_effect=sentiments):
                result = analyzer.analyze_market_sentiment(max_news_items=2)
        
        assert 'overall_sentiment' in result
        assert 'confidence' in result
        assert 'news_count' in result
        assert 'sentiment_breakdown' in result
        assert 'sample_news' in result
        assert result['news_count'] == 2
        assert result['overall_sentiment'] in ['Positive', 'Neutral', 'Negative']
    
    def test_analyze_market_sentiment_no_news(self):
        """Test market sentiment analysis with no news available"""
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        with patch.object(analyzer, 'fetch_news', return_value=[]):
            result = analyzer.analyze_market_sentiment(max_news_items=10)
        
        assert result['overall_sentiment'] == 'Neutral'
        assert result['confidence'] == 0.0
        assert result['news_count'] == 0


# Property-Based Tests
class TestSentimentAnalyzerProperties:
    """Property-based tests for Sentiment Analyzer"""
    
    @settings(deadline=None, max_examples=20)
    @given(
        sentiment_response=st.sampled_from(['Positive', 'Neutral', 'Negative', 
                                           'positive', 'neutral', 'negative',
                                           'POSITIVE', 'NEUTRAL', 'NEGATIVE'])
    )
    def test_property_sentiment_classification_validity(self, sentiment_response):
        """
        Property 9: Sentiment Classification Validity
        
        GIVEN any sentiment response from Bedrock
        WHEN extracted
        THEN result is always one of: Positive, Neutral, Negative
        
        Validates: Requirement 5.3
        """
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        sentiment = analyzer._extract_sentiment(sentiment_response)
        
        assert sentiment in ['Positive', 'Neutral', 'Negative']
    
    @settings(deadline=None, max_examples=20)
    @given(
        num_items=st.integers(min_value=1, max_value=20)
    )
    def test_property_sentiment_aggregation(self, num_items):
        """
        Property 10: Sentiment Aggregation
        
        GIVEN any number of news items
        WHEN aggregated
        THEN overall sentiment is computed and confidence is between 0 and 1
        
        Validates: Requirement 5.4
        """
        mock_bedrock = Mock()
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        
        # Generate random sentiments
        import random
        sentiments = [random.choice(['Positive', 'Neutral', 'Negative']) for _ in range(num_items)]
        
        with patch.object(analyzer, 'classify_sentiment', side_effect=sentiments):
            news_items = [{'title': f'News {i}', 'summary': f'Summary {i}'} for i in range(num_items)]
            overall, confidence = analyzer.aggregate_sentiment(news_items)
        
        assert overall in ['Positive', 'Neutral', 'Negative']
        assert 0.0 <= confidence <= 1.0
    
    @settings(deadline=None, max_examples=10)
    @given(
        text=st.text(min_size=10, max_size=200)
    )
    def test_property_classify_returns_valid_sentiment(self, text):
        """
        Property: Classification Always Returns Valid Sentiment
        
        GIVEN any text input
        WHEN classified (even on error)
        THEN result is always a valid sentiment
        
        Validates: Requirement 5.5
        """
        mock_bedrock = Mock()
        
        # Mock Bedrock to return random valid sentiment
        import random
        mock_response = {
            'body': Mock()
        }
        sentiment_choice = random.choice(['Positive', 'Neutral', 'Negative'])
        mock_response['body'].read = Mock(return_value=json.dumps({
            'content': [{'text': sentiment_choice}]
        }).encode())
        
        mock_bedrock.invoke_model = Mock(return_value=mock_response)
        
        analyzer = SentimentAnalyzer(bedrock_client=mock_bedrock)
        sentiment = analyzer.classify_sentiment(text)
        
        assert sentiment in ['Positive', 'Neutral', 'Negative']
