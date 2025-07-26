#!/usr/bin/env python3
"""
Enhanced Multi-Bank Performance Dashboard (HTML Version)

Generates a static HTML dashboard showcasing real-time performance of Australian bank symbols
with ML predictions, sentiment analysis, and comprehensive analytics.

Features:
- Real-time price performance
- Sentiment analysis visualization  
- ML prediction tracking
- Sector comparison
- Interactive HTML output
"""

import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

class HTMLBankDashboard:
    """HTML-based dashboard for bank performance analysis"""
    
    def __init__(self):
        self.db_path = 'data/multi_bank_analysis.db'
        
    def load_data(self):
        """Load data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load main performance data
                performance_df = pd.read_sql_query('''
                    SELECT * FROM bank_performance 
                    ORDER BY timestamp DESC
                ''', conn)
                
                # Load sentiment data
                sentiment_df = pd.read_sql_query('''
                    SELECT * FROM news_sentiment_analysis
                    ORDER BY timestamp DESC
                    LIMIT 50
                ''', conn)
                
                return performance_df, sentiment_df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def generate_dashboard_html(self):
        """Generate complete HTML dashboard"""
        performance_df, sentiment_df = self.load_data()
        
        if performance_df.empty:
            return self.generate_no_data_html()
        
        # Get latest data for each bank
        latest_data = performance_df.groupby('symbol').first().reset_index()
        
        # Calculate summary statistics
        total_banks = len(latest_data)
        avg_change = latest_data['price_change_1d'].mean()
        avg_sentiment = latest_data['sentiment_score'].mean()
        buy_signals = len(latest_data[latest_data['optimal_action'].isin(['BUY', 'STRONG_BUY'])])
        
        # Top and bottom performers
        top_performer = latest_data.loc[latest_data['price_change_1d'].idxmax()]
        bottom_performer = latest_data.loc[latest_data['price_change_1d'].idxmin()]
        
        # Sentiment extremes
        most_positive = latest_data.loc[latest_data['sentiment_score'].idxmax()]
        most_negative = latest_data.loc[latest_data['sentiment_score'].idxmin()]
        
        # Action distribution
        action_counts = latest_data['optimal_action'].value_counts().to_dict()
        
        # Sector performance
        sector_performance = latest_data.groupby('sector')['price_change_1d'].mean().to_dict()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Australian Banks ML Performance Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .neutral {{ color: #ffc107; }}
        .section {{
            padding: 30px;
            border-bottom: 1px solid #eee;
        }}
        .section h2 {{
            margin: 0 0 20px 0;
            color: #2a5298;
            font-size: 1.8em;
        }}
        .banks-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .bank-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #2a5298;
        }}
        .bank-name {{
            font-weight: bold;
            font-size: 1.2em;
            color: #2a5298;
        }}
        .bank-symbol {{
            background: #2a5298;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        .bank-details {{
            margin-top: 10px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}
        .detail-item {{
            font-size: 0.9em;
        }}
        .action-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .action-strong-buy {{ background: #28a745; color: white; }}
        .action-buy {{ background: #6f42c1; color: white; }}
        .action-hold {{ background: #ffc107; color: black; }}
        .action-sell {{ background: #fd7e14; color: white; }}
        .action-strong-sell {{ background: #dc3545; color: white; }}
        .sentiment-headlines {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        .headline-item {{
            padding: 15px;
            margin: 10px 0;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #ddd;
        }}
        .headline-positive {{ border-left-color: #28a745; }}
        .headline-negative {{ border-left-color: #dc3545; }}
        .headline-neutral {{ border-left-color: #ffc107; }}
        .timestamp {{
            color: #666;
            font-size: 0.8em;
            margin-top: 10px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #2a5298;
            color: white;
        }}
        .chart-container {{
            margin: 20px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏦 Australian Banks ML Dashboard</h1>
            <p>Real-time Performance Analysis with Machine Learning Predictions</p>
            <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Banks Analyzed</div>
                <div class="metric-value">{total_banks}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg 1D Change</div>
                <div class="metric-value {'positive' if avg_change > 0 else 'negative' if avg_change < 0 else 'neutral'}">{avg_change:+.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Sentiment</div>
                <div class="metric-value {'positive' if avg_sentiment > 0.1 else 'negative' if avg_sentiment < -0.1 else 'neutral'}">{avg_sentiment:.3f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Buy Signals</div>
                <div class="metric-value positive">{buy_signals}/{total_banks}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🏆 Top Performers</h2>
            <div class="banks-grid">
                <div class="bank-card">
                    <div class="bank-name">📈 Best Performer</div>
                    <div style="margin-top: 10px;">
                        <span class="bank-name">{top_performer['bank_name']}</span>
                        <span class="bank-symbol">{top_performer['symbol']}</span>
                    </div>
                    <div class="bank-details">
                        <div class="detail-item">Price: <strong>${top_performer['current_price']:.2f}</strong></div>
                        <div class="detail-item positive">Change: <strong>{top_performer['price_change_1d']:+.2f}%</strong></div>
                        <div class="detail-item">RSI: <strong>{top_performer['rsi']:.1f}</strong></div>
                        <div class="detail-item">
                            <span class="action-badge action-{top_performer['optimal_action'].lower().replace('_', '-')}">{top_performer['optimal_action']}</span>
                        </div>
                    </div>
                </div>
                
                <div class="bank-card">
                    <div class="bank-name">📉 Biggest Decline</div>
                    <div style="margin-top: 10px;">
                        <span class="bank-name">{bottom_performer['bank_name']}</span>
                        <span class="bank-symbol">{bottom_performer['symbol']}</span>
                    </div>
                    <div class="bank-details">
                        <div class="detail-item">Price: <strong>${bottom_performer['current_price']:.2f}</strong></div>
                        <div class="detail-item negative">Change: <strong>{bottom_performer['price_change_1d']:+.2f}%</strong></div>
                        <div class="detail-item">RSI: <strong>{bottom_performer['rsi']:.1f}</strong></div>
                        <div class="detail-item">
                            <span class="action-badge action-{bottom_performer['optimal_action'].lower().replace('_', '-')}">{bottom_performer['optimal_action']}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>💭 Sentiment Analysis</h2>
            <div class="banks-grid">
                <div class="bank-card">
                    <div class="bank-name">😊 Most Positive Sentiment</div>
                    <div style="margin-top: 10px;">
                        <span class="bank-name">{most_positive['bank_name']}</span>
                        <span class="bank-symbol">{most_positive['symbol']}</span>
                    </div>
                    <div class="bank-details">
                        <div class="detail-item positive">Sentiment: <strong>{most_positive['sentiment_score']:.3f}</strong></div>
                        <div class="detail-item">Confidence: <strong>{most_positive['sentiment_confidence']:.3f}</strong></div>
                    </div>
                </div>
                
                <div class="bank-card">
                    <div class="bank-name">😟 Most Negative Sentiment</div>
                    <div style="margin-top: 10px;">
                        <span class="bank-name">{most_negative['bank_name']}</span>
                        <span class="bank-symbol">{most_negative['symbol']}</span>
                    </div>
                    <div class="bank-details">
                        <div class="detail-item negative">Sentiment: <strong>{most_negative['sentiment_score']:.3f}</strong></div>
                        <div class="detail-item">Confidence: <strong>{most_negative['sentiment_confidence']:.3f}</strong></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🏢 Sector Performance</h2>
            <div class="banks-grid">
"""
        
        # Add sector performance cards
        for sector, performance in sector_performance.items():
            performance_class = 'positive' if performance > 0 else 'negative' if performance < 0 else 'neutral'
            html_content += f"""
                <div class="bank-card">
                    <div class="bank-name">{sector}</div>
                    <div class="bank-details">
                        <div class="detail-item {performance_class}">Avg Change: <strong>{performance:+.2f}%</strong></div>
                        <div class="detail-item">Banks: <strong>{len(latest_data[latest_data['sector'] == sector])}</strong></div>
                    </div>
                </div>
"""
        
        html_content += """
            </div>
        </div>
        
        <div class="section">
            <h2>🤖 ML Predictions Distribution</h2>
            <div class="banks-grid">
"""
        
        # Add ML predictions distribution
        for action, count in action_counts.items():
            action_class = action.lower().replace('_', '-')
            html_content += f"""
                <div class="bank-card">
                    <div class="bank-name">{action.replace('_', ' ').title()}</div>
                    <div class="bank-details">
                        <div class="detail-item">Banks: <strong>{count}</strong></div>
                        <div class="detail-item">
                            <span class="action-badge action-{action_class}">{action}</span>
                        </div>
                    </div>
                </div>
"""
        
        html_content += """
            </div>
        </div>
        
        <div class="section">
            <h2>📊 All Banks Overview</h2>
            <div class="banks-grid">
"""
        
        # Add all banks
        for _, bank in latest_data.iterrows():
            change_class = 'positive' if bank['price_change_1d'] > 0 else 'negative' if bank['price_change_1d'] < 0 else 'neutral'
            sentiment_class = 'positive' if bank['sentiment_score'] > 0.1 else 'negative' if bank['sentiment_score'] < -0.1 else 'neutral'
            action_class = bank['optimal_action'].lower().replace('_', '-')
            
            html_content += f"""
                <div class="bank-card">
                    <div class="bank-name">{bank['bank_name']} <span class="bank-symbol">{bank['symbol']}</span></div>
                    <div class="bank-details">
                        <div class="detail-item">Price: <strong>${bank['current_price']:.2f}</strong></div>
                        <div class="detail-item {change_class}">1D: <strong>{bank['price_change_1d']:+.2f}%</strong></div>
                        <div class="detail-item {change_class}">5D: <strong>{bank['price_change_5d']:+.2f}%</strong></div>
                        <div class="detail-item">RSI: <strong>{bank['rsi']:.1f}</strong></div>
                        <div class="detail-item {sentiment_class}">Sentiment: <strong>{bank['sentiment_score']:.3f}</strong></div>
                        <div class="detail-item">
                            <span class="action-badge action-{action_class}">{bank['optimal_action']}</span>
                        </div>
                    </div>
                </div>
"""
        
        html_content += """
            </div>
        </div>
"""
        
        # Add sentiment headlines if available
        if not sentiment_df.empty:
            html_content += """
        <div class="section">
            <h2>📰 Recent Sentiment Headlines</h2>
            <div class="sentiment-headlines">
"""
            
            for _, news in sentiment_df.head(10).iterrows():
                sentiment_class = 'positive' if news['sentiment_score'] > 0.1 else 'negative' if news['sentiment_score'] < -0.1 else 'neutral'
                
                html_content += f"""
                <div class="headline-item headline-{sentiment_class}">
                    <div class="bank-name">{news['symbol']} - {news['category'].title()}</div>
                    <div style="margin: 10px 0;">"{news['headline']}"</div>
                    <div class="bank-details">
                        <div class="detail-item {sentiment_class}">Sentiment: <strong>{news['sentiment_score']:.3f}</strong></div>
                        <div class="detail-item">Confidence: <strong>{news['confidence']:.3f}</strong></div>
                    </div>
                    <div class="timestamp">{news['timestamp']}</div>
                </div>
"""
            
            html_content += """
            </div>
        </div>
"""
        
        html_content += f"""
        <div class="footer">
            <p>Enhanced Multi-Bank ML Analysis System</p>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Data includes {total_banks} Australian financial institutions</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def generate_no_data_html(self):
        """Generate HTML for when no data is available"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Australian Banks ML Dashboard - No Data</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            text-align: center;
        }}
        .container {{
            max-width: 600px;
            margin: 100px auto;
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        }}
        .error-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #2a5298;
            margin-bottom: 20px;
        }}
        .instructions {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
        }}
        code {{
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="error-icon">📊</div>
        <h1>No Data Available</h1>
        <p>The dashboard cannot be generated because no data is available in the database.</p>
        
        <div class="instructions">
            <h3>To generate data, run:</h3>
            <code>python enhanced_ml_system/multi_bank_data_collector.py</code>
            
            <h3>Then regenerate the dashboard:</h3>
            <code>python enhanced_ml_system/html_dashboard_generator.py</code>
        </div>
        
        <p><em>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    </div>
</body>
</html>
"""
    
    def save_dashboard(self, filename='enhanced_ml_system/bank_performance_dashboard.html'):
        """Save the dashboard to an HTML file"""
        html_content = self.generate_dashboard_html()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename

def main():
    """Main execution function"""
    print("🏦 Generating Enhanced Bank Performance Dashboard")
    print("=" * 60)
    
    dashboard = HTMLBankDashboard()
    
    try:
        filename = dashboard.save_dashboard()
        print(f"✅ Dashboard generated successfully!")
        print(f"📄 File: {filename}")
        print(f"🌐 Open in browser: file://{os.path.abspath(filename)}")
        
    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")

if __name__ == "__main__":
    main()
