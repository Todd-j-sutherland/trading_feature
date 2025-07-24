"""
Chart generation utilities for the trading analysis dashboard
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any, Optional
import numpy as np


class ChartGenerator:
    """Generate various charts for the trading analysis dashboard"""
    
    def __init__(self):
        """Initialize the chart generator"""
        self.color_scheme = {
            'primary': '#1e3d59',
            'secondary': '#17a2b8',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8'
        }
    
    def create_sentiment_overview_chart(self, sentiment_data: Dict[str, Any], bank_names: Dict[str, str] = None) -> go.Figure:
        """
        Create a sentiment overview chart
        
        Args:
            sentiment_data: Dictionary containing sentiment analysis data
            bank_names: Optional dictionary mapping symbols to display names
            
        Returns:
            Plotly figure object
        """
        try:
            if not sentiment_data:
                return self._create_empty_chart("No sentiment data available")
                
            # Extract sentiment values
            symbols = list(sentiment_data.keys())
            sentiments = [sentiment_data[symbol].get('sentiment', 0) for symbol in symbols]
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=symbols,
                    y=sentiments,
                    marker_color=[
                        self.color_scheme['success'] if s > 0.2 else 
                        self.color_scheme['danger'] if s < -0.2 else 
                        self.color_scheme['warning'] 
                        for s in sentiments
                    ],
                    text=[f"{s:.3f}" for s in sentiments],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="Sentiment Overview by Symbol",
                xaxis_title="Symbols",
                yaxis_title="Sentiment Score",
                template="plotly_white",
                height=400
            )
            
            return fig
            
        except Exception as e:
            return self._create_empty_chart(f"Error creating sentiment chart: {str(e)}")
    
    def create_historical_trends_chart(self, historical_data: pd.DataFrame, symbol: str = None, bank_names: Dict[str, str] = None) -> go.Figure:
        """
        Create a historical trends chart
        
        Args:
            historical_data: DataFrame containing historical data
            symbol: Optional symbol being analyzed
            bank_names: Optional dictionary mapping symbols to display names
            
        Returns:
            Plotly figure object
        """
        try:
            if historical_data is None or historical_data.empty:
                return self._create_empty_chart("No historical data available")
                
            fig = go.Figure()
            
            # If we have sentiment data over time
            if 'timestamp' in historical_data.columns and 'sentiment' in historical_data.columns:
                fig.add_trace(go.Scatter(
                    x=historical_data['timestamp'],
                    y=historical_data['sentiment'],
                    mode='lines+markers',
                    name='Sentiment Trend',
                    line=dict(color=self.color_scheme['primary'], width=2)
                ))
            
            fig.update_layout(
                title=f"Historical Sentiment Trends - {symbol or 'All Symbols'}",
                xaxis_title="Time",
                yaxis_title="Sentiment Score",
                template="plotly_white",
                height=400
            )
            
            return fig
            
        except Exception as e:
            return self._create_empty_chart(f"Error creating historical chart: {str(e)}")
    
    def create_confidence_distribution_chart(self, confidence_data: Dict[str, Any], bank_names: Dict[str, str] = None) -> go.Figure:
        """
        Create a confidence distribution chart
        
        Args:
            confidence_data: Dictionary containing confidence data
            
        Returns:
            Plotly figure object
        """
        try:
            if not confidence_data:
                return self._create_empty_chart("No confidence data available")
            
            symbols = list(confidence_data.keys())
            confidences = [confidence_data[symbol].get('confidence', 0) for symbol in symbols]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=symbols,
                    y=confidences,
                    marker_color=self.color_scheme['info'],
                    text=[f"{c:.3f}" for c in confidences],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="Confidence Distribution by Symbol",
                xaxis_title="Symbols",
                yaxis_title="Confidence Score",
                template="plotly_white",
                height=400
            )
            
            return fig
            
        except Exception as e:
            return self._create_empty_chart(f"Error creating confidence chart: {str(e)}")
    
    def create_correlation_chart(self, symbol: str, correlation_data: Dict[str, Any], bank_names: Dict[str, str] = None) -> go.Figure:
        """
        Create a correlation chart
        
        Args:
            correlation_data: Dictionary containing correlation data
            
        Returns:
            Plotly figure object
        """
        try:
            if not correlation_data:
                return self._create_empty_chart("No correlation data available")
            
            # Simple correlation visualization
            fig = go.Figure()
            fig.add_annotation(
                text="Correlation analysis not yet implemented",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            
            fig.update_layout(
                title="Sentiment Correlation Analysis",
                template="plotly_white",
                height=400
            )
            
            return fig
            
        except Exception as e:
            return self._create_empty_chart(f"Error creating correlation chart: {str(e)}")
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with a message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=400,
            template="plotly_white"
        )
        return fig
