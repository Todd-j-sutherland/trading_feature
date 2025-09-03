"""
Chart generation components for the dashboard
Handles creation of all plotly charts with professional styling
"""

import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from ..utils.logging_config import setup_dashboard_logger, log_chart_generation, log_error_with_context
from ..utils.helpers import get_color_for_sentiment

logger = setup_dashboard_logger(__name__)

class ChartGenerator:
    """Generates professional charts for the dashboard"""
    
    def __init__(self):
        self.default_colors = {
            'positive': '#27ae60',
            'negative': '#e74c3c', 
            'neutral': '#6c757d',
            'primary': '#3498db',
            'secondary': '#2ecc71',
            'warning': '#f39c12'
        }
        
        # Professional chart styling
        self.layout_style = {
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'font': {'family': 'Inter'},
            'margin': {'l': 60, 'r': 60, 't': 60, 'b': 60}
        }
        
        logger.info("ChartGenerator initialized with professional styling")
    
    def create_sentiment_overview_chart(self, all_data: Dict, bank_names: Dict) -> go.Figure:
        """
        Create professional overview chart of all bank sentiments
        
        Args:
            all_data: Dictionary of sentiment data by symbol
            bank_names: Mapping of symbols to bank names
        
        Returns:
            Plotly figure object
        """
        try:
            symbols = []
            scores = []
            confidences = []
            colors = []
            
            data_points = 0
            
            for symbol, data in all_data.items():
                if not data:
                    continue
                
                # Get latest analysis
                latest = self._get_latest_from_data(data)
                if not latest:
                    continue
                
                symbols.append(bank_names.get(symbol, symbol))
                score = latest.get('overall_sentiment', 0)
                confidence = latest.get('confidence', 0)
                
                scores.append(score)
                confidences.append(confidence)
                colors.append(get_color_for_sentiment(score))
                data_points += 1
            
            fig = go.Figure()
            
            if data_points > 0:
                # Add sentiment bars
                fig.add_trace(go.Bar(
                    x=symbols,
                    y=scores,
                    name='Sentiment Score',
                    marker=dict(
                        color=colors,
                        line=dict(color='white', width=1)
                    ),
                    text=[f"{s:.3f}" for s in scores],
                    textposition='auto',
                    textfont=dict(size=12, family="Inter"),
                    hovertemplate='<b>%{x}</b><br>' +
                                 'Sentiment: %{y:.3f}<br>' +
                                 'Confidence: %{customdata:.2f}<br>' +
                                 '<extra></extra>',
                    customdata=confidences
                ))
                
                fig.update_layout(
                    title=dict(
                        text="Bank Sentiment Overview",
                        font=dict(size=18, family="Inter", weight=600, color="#2c3e50")
                    ),
                    xaxis=dict(
                        title=dict(text="Banks", font=dict(size=14, family="Inter")),
                        tickfont=dict(size=12, family="Inter"),
                        gridcolor="#f1f1f1",
                        linecolor="#dee2e6"
                    ),
                    yaxis=dict(
                        title=dict(text="Sentiment Score", font=dict(size=14, family="Inter")),
                        tickfont=dict(size=12, family="Inter"),
                        range=[-1, 1],
                        gridcolor="#f1f1f1",
                        linecolor="#dee2e6",
                        zeroline=True,
                        zerolinecolor="#dee2e6",
                        zerolinewidth=2
                    ),
                    height=400,
                    showlegend=False,
                    **self.layout_style
                )
            else:
                self._add_no_data_message(fig, "No sentiment data available")
            
            log_chart_generation(logger, "sentiment_overview", "ALL", data_points)
            return fig
            
        except Exception as e:
            log_error_with_context(logger, e, "creating sentiment overview chart")
            return self._create_error_chart("Error creating sentiment overview chart")
    
    def create_confidence_distribution_chart(self, all_data: Dict, bank_names: Dict) -> go.Figure:
        """
        Create professional confidence distribution chart
        
        Args:
            all_data: Dictionary of sentiment data by symbol
            bank_names: Mapping of symbols to bank names
        
        Returns:
            Plotly figure object
        """
        try:
            symbols = []
            confidences = []
            colors = []
            data_points = 0
            
            for symbol, data in all_data.items():
                if not data:
                    continue
                
                latest = self._get_latest_from_data(data)
                if not latest:
                    continue
                
                symbols.append(bank_names.get(symbol, symbol))
                confidence = latest.get('confidence', 0)
                confidences.append(confidence)
                
                # Color mapping for confidence
                if confidence >= 0.8:
                    colors.append(self.default_colors['positive'])
                elif confidence >= 0.6:
                    colors.append(self.default_colors['warning'])
                else:
                    colors.append(self.default_colors['negative'])
                
                data_points += 1
            
            fig = go.Figure()
            
            if data_points > 0:
                fig.add_trace(go.Bar(
                    x=symbols,
                    y=confidences,
                    marker=dict(
                        color=colors,
                        line=dict(color='white', width=1)
                    ),
                    text=[f"{c:.2f}" for c in confidences],
                    textposition='auto',
                    textfont=dict(size=12, family="Inter"),
                    hovertemplate='<b>%{x}</b><br>' +
                                 'Confidence: %{y:.3f}<br>' +
                                 '<extra></extra>'
                ))
                
                fig.update_layout(
                    title=dict(
                        text="Analysis Confidence Levels",
                        font=dict(size=18, family="Inter", weight=600, color="#2c3e50")
                    ),
                    xaxis=dict(
                        title=dict(text="Banks", font=dict(size=14, family="Inter")),
                        tickfont=dict(size=12, family="Inter"),
                        gridcolor="#f1f1f1",
                        linecolor="#dee2e6"
                    ),
                    yaxis=dict(
                        title=dict(text="Confidence Score", font=dict(size=14, family="Inter")),
                        tickfont=dict(size=12, family="Inter"),
                        range=[0, 1],
                        gridcolor="#f1f1f1",
                        linecolor="#dee2e6"
                    ),
                    height=400,
                    showlegend=False,
                    **self.layout_style
                )
            else:
                self._add_no_data_message(fig, "No confidence data available")
            
            log_chart_generation(logger, "confidence_distribution", "ALL", data_points)
            return fig
            
        except Exception as e:
            log_error_with_context(logger, e, "creating confidence distribution chart")
            return self._create_error_chart("Error creating confidence distribution chart")
    
    def create_historical_trends_chart(self, symbol: str, data: List[Dict], bank_names: Dict) -> go.Figure:
        """
        Create professional historical trends chart for sentiment
        
        Args:
            symbol: Stock symbol
            data: Historical sentiment data
            bank_names: Mapping of symbols to bank names
        
        Returns:
            Plotly figure object
        """
        try:
            if not data:
                return self._create_no_data_chart("No historical data available")
            
            # Prepare data
            dates = []
            sentiments = []
            confidences = []
            
            for entry in data[-30:]:  # Last 30 entries
                try:
                    timestamp = entry.get('timestamp', '')
                    if not timestamp:
                        continue
                    
                    # Parse timestamp
                    if 'T' in timestamp:
                        date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    
                    dates.append(date)
                    sentiments.append(entry.get('overall_sentiment', 0))
                    confidences.append(entry.get('confidence', 0))
                    
                except Exception:
                    continue
            
            fig = go.Figure()
            
            if dates:
                # Add sentiment trace
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=sentiments,
                    mode='lines+markers',
                    name='Sentiment Score',
                    line=dict(color=self.default_colors['primary'], width=2),
                    marker=dict(size=8, color=self.default_colors['primary']),
                    text=[f"Sentiment: {s:.3f}<br>Confidence: {c:.2f}" 
                          for s, c in zip(sentiments, confidences)],
                    hovertemplate='%{text}<br>Date: %{x}<extra></extra>'
                ))
                
                # Add confidence trace on secondary y-axis
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=confidences,
                    mode='lines',
                    name='Confidence',
                    line=dict(color=self.default_colors['warning'], width=2, dash='dash'),
                    yaxis='y2',
                    hovertemplate='Date: %{x}<br>Confidence: %{y:.3f}<extra></extra>'
                ))
                
                bank_name = bank_names.get(symbol, symbol)
                fig.update_layout(
                    title=dict(
                        text=f"Historical Trends - {bank_name}",
                        font=dict(size=18, family="Inter", weight=600, color="#2c3e50")
                    ),
                    xaxis=dict(
                        title=dict(text="Date", font=dict(size=14, family="Inter")),
                        tickfont=dict(size=12, family="Inter"),
                        gridcolor="#f1f1f1",
                        linecolor="#dee2e6"
                    ),
                    yaxis=dict(
                        title=dict(text="Sentiment Score", font=dict(size=14, family="Inter")),
                        tickfont=dict(size=12, family="Inter"),
                        range=[-1, 1],
                        gridcolor="#f1f1f1",
                        linecolor="#dee2e6"
                    ),
                    yaxis2=dict(
                        title=dict(text="Confidence", font=dict(size=14, family="Inter")),
                        overlaying='y',
                        side='right',
                        range=[0, 1]
                    ),
                    height=500,
                    showlegend=True,
                    **self.layout_style
                )
            else:
                self._add_no_data_message(fig, "No valid timestamp data found")
            
            log_chart_generation(logger, "historical_trends", symbol, len(dates))
            return fig
            
        except Exception as e:
            log_error_with_context(logger, e, f"creating historical trends chart for {symbol}")
            return self._create_error_chart("Error creating historical trends chart")
    
    def create_correlation_chart(self, symbol: str, correlation_data: List[Dict], bank_names: Dict) -> go.Figure:
        """
        Create professional correlation analysis chart
        
        Args:
            symbol: Stock symbol
            correlation_data: Correlation data points
            bank_names: Mapping of symbols to bank names
        
        Returns:
            Plotly figure object
        """
        try:
            if not correlation_data:
                return self._create_no_data_chart("Insufficient data for correlation analysis")
            
            sentiments = [p['sentiment'] for p in correlation_data]
            price_changes = [p['price_change'] for p in correlation_data]
            confidences = [p['confidence'] for p in correlation_data]
            dates = [p['date'].strftime('%Y-%m-%d') for p in correlation_data]
            
            fig = go.Figure()
            
            # Create scatter plot with confidence as size
            fig.add_trace(go.Scatter(
                x=sentiments,
                y=price_changes,
                mode='markers',
                marker=dict(
                    size=[c * 30 + 5 for c in confidences],
                    color=confidences,
                    colorscale='Viridis',
                    colorbar=dict(title="Confidence Level"),
                    line=dict(width=1, color='white')
                ),
                text=dates,
                hovertemplate='<b>Correlation Point</b><br>' +
                             'Sentiment: %{x:.3f}<br>' +
                             'Price Change: %{y:.2f}%<br>' +
                             'Confidence: %{marker.color:.2f}<br>' +
                             'Date: %{text}<extra></extra>'
            ))
            
            # Add trend line if enough data points
            if len(correlation_data) >= 3:
                try:
                    z = np.polyfit(sentiments, price_changes, 1)
                    p = np.poly1d(z)
                    
                    x_trend = np.linspace(min(sentiments), max(sentiments), 100)
                    y_trend = p(x_trend)
                    
                    fig.add_trace(go.Scatter(
                        x=x_trend,
                        y=y_trend,
                        mode='lines',
                        name='Trend Line',
                        line=dict(color=self.default_colors['negative'], width=2, dash='dash'),
                        hovertemplate='Trend Line<extra></extra>'
                    ))
                except Exception as e:
                    logger.debug(f"Could not add trend line: {e}")
            
            bank_name = bank_names.get(symbol, symbol)
            fig.update_layout(
                title=dict(
                    text=f"Sentiment vs Price Movement Correlation - {bank_name}",
                    font=dict(size=18, family="Inter", weight=600, color="#2c3e50")
                ),
                xaxis=dict(
                    title=dict(text="Sentiment Score", font=dict(size=14, family="Inter")),
                    tickfont=dict(size=12, family="Inter"),
                    gridcolor="#f1f1f1",
                    linecolor="#dee2e6"
                ),
                yaxis=dict(
                    title=dict(text="Price Change (%)", font=dict(size=14, family="Inter")),
                    tickfont=dict(size=12, family="Inter"),
                    gridcolor="#f1f1f1",
                    linecolor="#dee2e6",
                    zeroline=True,
                    zerolinecolor="#dee2e6",
                    zerolinewidth=2
                ),
                height=500,
                **self.layout_style
            )
            
            log_chart_generation(logger, "correlation", symbol, len(correlation_data))
            return fig
            
        except Exception as e:
            log_error_with_context(logger, e, f"creating correlation chart for {symbol}")
            return self._create_error_chart("Error creating correlation chart")
    
    def create_news_impact_chart(self, news_data: List[Dict]) -> go.Figure:
        """
        Create professional chart showing news impact on sentiment
        
        Args:
            news_data: List of news articles with sentiment analysis
        
        Returns:
            Plotly figure object
        """
        try:
            if not news_data:
                return self._create_no_data_chart("No news impact data available")
            
            # Analyze news sentiment impact
            impact_data = []
            
            for news in news_data[:10]:  # Top 10 recent news
                title = news.get('title', 'Unknown')[:50] + "..."
                sentiment_impact = 0
                
                # Extract sentiment if available
                if 'sentiment_analysis' in news:
                    sentiment_impact = news['sentiment_analysis'].get('composite', 0)
                
                impact_data.append({
                    'title': title,
                    'impact': sentiment_impact,
                    'source': news.get('source', 'Unknown'),
                    'relevance': news.get('relevance', 'medium')
                })
            
            if not impact_data:
                return self._create_no_data_chart("No news impact data available")
            
            df = pd.DataFrame(impact_data)
            
            # Professional color mapping
            colors = [get_color_for_sentiment(i) for i in df['impact']]
            
            fig = go.Figure(go.Bar(
                x=df['title'],
                y=df['impact'],
                marker=dict(
                    color=colors,
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>%{x}</b><br>' +
                             'Impact: %{y:.3f}<br>' +
                             'Source: %{customdata}<br>' +
                             '<extra></extra>',
                customdata=df['source']
            ))
            
            fig.update_layout(
                title=dict(
                    text="News Impact on Sentiment",
                    font=dict(size=18, family="Inter", weight=600, color="#2c3e50")
                ),
                xaxis=dict(
                    title=dict(text="News Articles", font=dict(size=14, family="Inter")),
                    tickfont=dict(size=10, family="Inter"),
                    tickangle=-45,
                    gridcolor="#f1f1f1",
                    linecolor="#dee2e6"
                ),
                yaxis=dict(
                    title=dict(text="Sentiment Impact", font=dict(size=14, family="Inter")),
                    tickfont=dict(size=12, family="Inter"),
                    gridcolor="#f1f1f1",
                    linecolor="#dee2e6"
                ),
                height=400,
                showlegend=False,
                **self.layout_style
            )
            
            log_chart_generation(logger, "news_impact", "ALL", len(impact_data))
            return fig
            
        except Exception as e:
            log_error_with_context(logger, e, "creating news impact chart")
            return self._create_error_chart("Error creating news impact chart")
    
    def _get_latest_from_data(self, data: List[Dict]) -> Dict:
        """Get latest analysis from data list"""
        if not data:
            return {}
        
        try:
            sorted_data = sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)
            return sorted_data[0] if sorted_data else {}
        except:
            return data[-1] if data else {}
    
    def _create_error_chart(self, error_message: str) -> go.Figure:
        """Create a chart displaying an error message"""
        fig = go.Figure()
        fig.add_annotation(
            text=f"⚠️ {error_message}",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, family="Inter", color="#e74c3c")
        )
        fig.update_layout(
            height=300,
            showlegend=False,
            **self.layout_style
        )
        return fig
    
    def _create_no_data_chart(self, message: str) -> go.Figure:
        """Create a chart for no data scenarios"""
        fig = go.Figure()
        fig.add_annotation(
            text=f"📊 {message}",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, family="Inter", color="#6c757d")
        )
        fig.update_layout(
            height=300,
            showlegend=False,
            **self.layout_style
        )
        return fig
    
    def _add_no_data_message(self, fig: go.Figure, message: str):
        """Add no data message to existing figure"""
        fig.add_annotation(
            text=message,
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, family="Inter", color="#6c757d")
        )
