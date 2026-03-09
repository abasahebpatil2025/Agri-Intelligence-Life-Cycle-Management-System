"""
Unit tests for Price Visualizer Component

Tests Plotly chart creation, Marathi labels, and visualization features.
"""

import pytest
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Import the component
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'components'))
from price_visualizer import PriceVisualizer


class TestPriceVisualizer:
    """Test suite for PriceVisualizer component"""
    
    def test_initialization(self):
        """Test visualizer initialization"""
        visualizer = PriceVisualizer()
        
        assert visualizer is not None
        assert len(visualizer.LABELS) > 0
        assert len(visualizer.COLORS) > 0
    
    def test_marathi_labels_present(self):
        """Test Marathi labels are defined"""
        visualizer = PriceVisualizer()
        
        assert 'x_axis' in visualizer.LABELS
        assert 'y_axis' in visualizer.LABELS
        assert 'actual_price' in visualizer.LABELS
        assert 'predicted_price' in visualizer.LABELS
        
        # Verify Marathi text is present
        assert 'तारीख' in visualizer.LABELS['x_axis']
        assert 'किंमत' in visualizer.LABELS['y_axis']
        assert 'वास्तविक' in visualizer.LABELS['actual_price']
        assert 'अंदाजित' in visualizer.LABELS['predicted_price']
    
    def test_color_scheme_defined(self):
        """Test color scheme is defined"""
        visualizer = PriceVisualizer()
        
        assert 'actual' in visualizer.COLORS
        assert 'predicted' in visualizer.COLORS
        assert 'confidence' in visualizer.COLORS
        
        # Verify blue for actual
        assert visualizer.COLORS['actual'] == '#1f77b4'
        # Verify orange for predicted
        assert visualizer.COLORS['predicted'] == '#ff7f0e'
    
    def test_create_chart_with_actual_and_predicted(self):
        """Test chart creation with actual and predicted prices"""
        visualizer = PriceVisualizer()
        
        # Create sample data
        dates_actual = pd.date_range(start='2024-01-01', periods=30, freq='D')
        actual_prices = pd.DataFrame({
            'date': dates_actual.strftime('%Y-%m-%d'),
            'price': [2500 + i * 10 for i in range(30)]
        })
        
        dates_predicted = pd.date_range(start='2024-01-31', periods=15, freq='D')
        predicted_prices = pd.DataFrame({
            'date': dates_predicted.strftime('%Y-%m-%d'),
            'predicted_price': [2800 + i * 5 for i in range(15)],
            'lower_bound': [2700 + i * 5 for i in range(15)],
            'upper_bound': [2900 + i * 5 for i in range(15)]
        })
        
        # Create chart
        fig = visualizer.create_chart(actual_prices, predicted_prices)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        
        # Verify layout
        assert fig.layout.xaxis.title.text == visualizer.LABELS['x_axis']
        assert fig.layout.yaxis.title.text == visualizer.LABELS['y_axis']
        assert fig.layout.plot_bgcolor == 'white'
        assert fig.layout.paper_bgcolor == 'white'
    
    def test_create_chart_with_confidence_intervals(self):
        """Test chart includes confidence interval shading"""
        visualizer = PriceVisualizer()
        
        actual_prices = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [2500]
        })
        
        predicted_prices = pd.DataFrame({
            'date': ['2024-02-01', '2024-02-02'],
            'predicted_price': [2600, 2650],
            'lower_bound': [2500, 2550],
            'upper_bound': [2700, 2750]
        })
        
        fig = visualizer.create_chart(actual_prices, predicted_prices)
        
        # Should have traces for: upper bound, lower bound (with fill), actual, predicted
        assert len(fig.data) >= 3
        
        # Check for fill attribute in one of the traces
        has_fill = any(trace.fill == 'tonexty' for trace in fig.data)
        assert has_fill
    
    def test_create_chart_actual_only(self):
        """Test chart creation with only actual prices"""
        visualizer = PriceVisualizer()
        
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        actual_prices = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': [2500 + i * 10 for i in range(30)]
        })
        
        predicted_prices = pd.DataFrame()  # Empty
        
        fig = visualizer.create_chart(actual_prices, predicted_prices)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1
    
    def test_create_chart_predicted_only(self):
        """Test chart creation with only predicted prices"""
        visualizer = PriceVisualizer()
        
        actual_prices = pd.DataFrame()  # Empty
        
        dates = pd.date_range(start='2024-02-01', periods=15, freq='D')
        predicted_prices = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'predicted_price': [2600 + i * 5 for i in range(15)],
            'lower_bound': [2500 + i * 5 for i in range(15)],
            'upper_bound': [2700 + i * 5 for i in range(15)]
        })
        
        fig = visualizer.create_chart(actual_prices, predicted_prices)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1
    
    def test_create_chart_limits_actual_to_30_days(self):
        """Test chart limits actual prices to last 30 days"""
        visualizer = PriceVisualizer()
        
        # Create 60 days of actual data
        dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
        actual_prices = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': [2500 + i * 10 for i in range(60)]
        })
        
        predicted_prices = pd.DataFrame()
        
        fig = visualizer.create_chart(actual_prices, predicted_prices)
        
        # Find the actual price trace
        actual_trace = None
        for trace in fig.data:
            if 'वास्तविक' in trace.name:
                actual_trace = trace
                break
        
        # Should only show last 30 days
        if actual_trace:
            assert len(actual_trace.x) == 30
    
    def test_create_simple_chart(self):
        """Test simple chart creation"""
        visualizer = PriceVisualizer()
        
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': [2500 + i * 10 for i in range(10)]
        })
        
        fig = visualizer.create_simple_chart(data, title='Test Chart')
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.layout.title.text == 'Test Chart'
    
    def test_create_comparison_chart(self):
        """Test comparison chart with multiple series"""
        visualizer = PriceVisualizer()
        
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        
        data_dict = {
            'Market A': pd.DataFrame({
                'date': dates.strftime('%Y-%m-%d'),
                'price': [2500 + i * 10 for i in range(10)]
            }),
            'Market B': pd.DataFrame({
                'date': dates.strftime('%Y-%m-%d'),
                'price': [2600 + i * 8 for i in range(10)]
            })
        }
        
        fig = visualizer.create_comparison_chart(data_dict, title='Market Comparison')
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert fig.layout.title.text == 'Market Comparison'
    
    def test_add_annotations(self):
        """Test adding annotations to chart"""
        visualizer = PriceVisualizer()
        
        # Create simple chart
        data = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [2500]
        })
        fig = visualizer.create_simple_chart(data)
        
        # Add annotation
        annotations = [
            {
                'x': '2024-01-01',
                'y': 2500,
                'text': 'Peak Price',
                'showarrow': True
            }
        ]
        
        fig = visualizer.add_annotations(fig, annotations)
        
        assert len(fig.layout.annotations) > 0
        assert fig.layout.annotations[0].text == 'Peak Price'
    
    def test_export_chart_config(self):
        """Test chart configuration export"""
        visualizer = PriceVisualizer()
        
        config = visualizer.export_chart_config()
        
        assert isinstance(config, dict)
        assert 'displayModeBar' in config
        assert 'displaylogo' in config
        assert config['displaylogo'] is False
        assert 'toImageButtonOptions' in config
    
    def test_chart_responsive_height(self):
        """Test chart has appropriate height for Streamlit"""
        visualizer = PriceVisualizer()
        
        actual_prices = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [2500]
        })
        predicted_prices = pd.DataFrame()
        
        fig = visualizer.create_chart(actual_prices, predicted_prices)
        
        # Should have height set for responsive display
        assert fig.layout.height == 500
    
    def test_chart_hover_mode(self):
        """Test chart has unified hover mode"""
        visualizer = PriceVisualizer()
        
        actual_prices = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [2500]
        })
        predicted_prices = pd.DataFrame()
        
        fig = visualizer.create_chart(actual_prices, predicted_prices)
        
        assert fig.layout.hovermode == 'x unified'
    
    def test_chart_legend_position(self):
        """Test chart legend is positioned correctly"""
        visualizer = PriceVisualizer()
        
        actual_prices = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [2500]
        })
        predicted_prices = pd.DataFrame({
            'date': ['2024-02-01'],
            'predicted_price': [2600],
            'lower_bound': [2500],
            'upper_bound': [2700]
        })
        
        fig = visualizer.create_chart(actual_prices, predicted_prices)
        
        # Legend should be horizontal at top
        assert fig.layout.legend.orientation == 'h'
        assert fig.layout.legend.yanchor == 'bottom'
    
    def test_chart_currency_formatting(self):
        """Test chart uses rupee symbol in y-axis"""
        visualizer = PriceVisualizer()
        
        actual_prices = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [2500]
        })
        predicted_prices = pd.DataFrame()
        
        fig = visualizer.create_chart(actual_prices, predicted_prices)
        
        # Y-axis should have rupee prefix
        assert fig.layout.yaxis.tickprefix == '₹'
