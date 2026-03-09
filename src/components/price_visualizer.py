"""
Price Visualizer Component

Creates interactive price charts using Plotly.
Displays historical prices and forecasts with confidence intervals.
Includes Marathi labels for accessibility.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
"""

import pandas as pd
import plotly.graph_objs as go
from typing import Optional, Dict, Any


class PriceVisualizer:
    """
    Price visualizer using Plotly for interactive charts.
    
    Creates dual-line charts with historical and predicted prices.
    Includes confidence intervals and Marathi labels.
    """
    
    # Marathi labels
    LABELS = {
        'x_axis': 'तारीख (Date)',
        'y_axis': 'किंमत - रुपये प्रति क्विंटल (Price - ₹/Quintal)',
        'actual_price': 'वास्तविक किंमत (Actual Price)',
        'predicted_price': 'अंदाजित किंमत (Predicted Price)',
        'confidence_interval': 'विश्वास मर्यादा (Confidence Interval)',
        'title': 'कांदा किंमत अंदाज (Onion Price Forecast)'
    }
    
    # Color scheme
    COLORS = {
        'actual': '#1f77b4',      # Blue
        'predicted': '#ff7f0e',   # Orange
        'confidence': 'rgba(255, 127, 14, 0.2)',  # Light orange with transparency
        'grid': '#e0e0e0'
    }
    
    def __init__(self):
        """Initialize Price Visualizer."""
        pass
    
    def create_chart(
        self,
        actual_prices: pd.DataFrame,
        predicted_prices: pd.DataFrame,
        title: Optional[str] = None,
        commodity: str = 'Onion'
    ) -> go.Figure:
        """
        Create interactive price chart with historical and predicted prices.
        
        Args:
            actual_prices: DataFrame with columns:
                - date: Date string (YYYY-MM-DD)
                - price: Actual price
            predicted_prices: DataFrame with columns:
                - date: Date string (YYYY-MM-DD)
                - predicted_price: Predicted price
                - lower_bound: Lower confidence bound
                - upper_bound: Upper confidence bound
            title: Optional custom title
            commodity: Commodity name for title
            
        Returns:
            Plotly Figure object
        """
        # Create figure
        fig = go.Figure()
        
        # Add confidence interval (shaded area)
        if not predicted_prices.empty and 'lower_bound' in predicted_prices.columns:
            # Upper bound trace
            fig.add_trace(go.Scatter(
                x=predicted_prices['date'],
                y=predicted_prices['upper_bound'],
                mode='lines',
                name=self.LABELS['confidence_interval'],
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Lower bound trace with fill
            fig.add_trace(go.Scatter(
                x=predicted_prices['date'],
                y=predicted_prices['lower_bound'],
                mode='lines',
                name=self.LABELS['confidence_interval'],
                line=dict(width=0),
                fillcolor=self.COLORS['confidence'],
                fill='tonexty',  # Fill to previous trace (upper bound)
                showlegend=True,
                hovertemplate='<b>Date:</b> %{x}<br><b>Range:</b> ₹%{y:.2f}<extra></extra>'
            ))
        
        # Add actual prices (last 30 days)
        if not actual_prices.empty:
            # Take last 30 days
            actual_last_30 = actual_prices.tail(30).copy()
            
            fig.add_trace(go.Scatter(
                x=actual_last_30['date'],
                y=actual_last_30['price'],
                mode='lines+markers',
                name=self.LABELS['actual_price'],
                line=dict(color=self.COLORS['actual'], width=2),
                marker=dict(size=6, color=self.COLORS['actual']),
                hovertemplate='<b>Date:</b> %{x}<br><b>Actual Price:</b> ₹%{y:.2f}<extra></extra>'
            ))
        
        # Add predicted prices
        if not predicted_prices.empty:
            fig.add_trace(go.Scatter(
                x=predicted_prices['date'],
                y=predicted_prices['predicted_price'],
                mode='lines+markers',
                name=self.LABELS['predicted_price'],
                line=dict(color=self.COLORS['predicted'], width=2, dash='solid'),
                marker=dict(size=6, color=self.COLORS['predicted'], symbol='diamond'),
                hovertemplate='<b>Date:</b> %{x}<br><b>Predicted Price:</b> ₹%{y:.2f}<extra></extra>'
            ))
        
        # Update layout
        chart_title = title if title else f"{commodity} {self.LABELS['title'].split('(')[1].split(')')[0]}"
        
        fig.update_layout(
            title={
                'text': chart_title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'family': 'Arial, sans-serif'}
            },
            xaxis_title=self.LABELS['x_axis'],
            yaxis_title=self.LABELS['y_axis'],
            xaxis=dict(
                showgrid=True,
                gridcolor=self.COLORS['grid'],
                tickangle=-45,
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=self.COLORS['grid'],
                tickprefix='₹',
                tickformat=',.0f'
            ),
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=12)
            ),
            margin=dict(l=60, r=40, t=80, b=80),
            height=500,
            font=dict(family='Arial, sans-serif')
        )
        
        return fig
    
    def create_simple_chart(
        self,
        data: pd.DataFrame,
        x_col: str = 'date',
        y_col: str = 'price',
        title: str = 'Price Chart',
        color: str = 'blue'
    ) -> go.Figure:
        """
        Create simple line chart for single data series.
        
        Args:
            data: DataFrame with price data
            x_col: Column name for x-axis
            y_col: Column name for y-axis
            title: Chart title
            color: Line color
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data[x_col],
            y=data[y_col],
            mode='lines+markers',
            name=title,
            line=dict(color=color, width=2),
            marker=dict(size=6),
            hovertemplate='<b>Date:</b> %{x}<br><b>Price:</b> ₹%{y:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=self.LABELS['x_axis'],
            yaxis_title=self.LABELS['y_axis'],
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x',
            height=400
        )
        
        return fig
    
    def create_comparison_chart(
        self,
        data_dict: Dict[str, pd.DataFrame],
        title: str = 'Price Comparison'
    ) -> go.Figure:
        """
        Create comparison chart for multiple price series.
        
        Args:
            data_dict: Dictionary of {label: DataFrame} with 'date' and 'price' columns
            title: Chart title
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for idx, (label, data) in enumerate(data_dict.items()):
            color = colors[idx % len(colors)]
            
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data['price'],
                mode='lines+markers',
                name=label,
                line=dict(color=color, width=2),
                marker=dict(size=5),
                hovertemplate=f'<b>{label}</b><br><b>Date:</b> %{{x}}<br><b>Price:</b> ₹%{{y:.2f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=self.LABELS['x_axis'],
            yaxis_title=self.LABELS['y_axis'],
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x unified',
            legend=dict(
                orientation='v',
                yanchor='top',
                y=1,
                xanchor='left',
                x=1.02
            ),
            height=500
        )
        
        return fig
    
    def add_annotations(
        self,
        fig: go.Figure,
        annotations: list
    ) -> go.Figure:
        """
        Add text annotations to chart.
        
        Args:
            fig: Plotly Figure object
            annotations: List of annotation dicts with keys:
                - x: X coordinate
                - y: Y coordinate
                - text: Annotation text
                - showarrow: Boolean (default True)
                
        Returns:
            Updated Plotly Figure object
        """
        for ann in annotations:
            fig.add_annotation(
                x=ann.get('x'),
                y=ann.get('y'),
                text=ann.get('text', ''),
                showarrow=ann.get('showarrow', True),
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='#636363',
                ax=20,
                ay=-30,
                font=dict(size=10, color='#636363'),
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#636363',
                borderwidth=1
            )
        
        return fig
    
    def export_chart_config(self) -> Dict[str, Any]:
        """
        Get Plotly configuration for Streamlit integration.
        
        Returns:
            Configuration dictionary for st.plotly_chart()
        """
        return {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'price_forecast',
                'height': 600,
                'width': 1000,
                'scale': 2
            }
        }
