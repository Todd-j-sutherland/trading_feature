#!/usr/bin/env python3
"""
Simple Local Trading Data Viewer
Creates static HTML visualization of trading data
"""

import sqlite3
import json
from datetime import datetime, timedelta
import os

def generate_static_visualization(symbol='CBA.AX', hours=24):
    """Generate a static HTML visualization"""
    
    # Connect to database
    db_path = 'data/trading_predictions.db' if os.path.exists('data/trading_predictions.db') else 'trading_predictions.db'
    conn = sqlite3.connect(db_path)
    
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get enhanced features data
        features_query = """
        SELECT 
            timestamp,
            current_price,
            sentiment_score,
            confidence,
            rsi,
            macd_line,
            price_change_1h,
            volume_ratio
        FROM enhanced_features 
        WHERE symbol = ? AND timestamp >= ?
        ORDER BY timestamp ASC
        """
        
        cursor = conn.execute(features_query, (symbol, start_time.isoformat()))
        features_data = cursor.fetchall()
        
        # Get predictions
        predictions_query = """
        SELECT 
            prediction_timestamp,
            predicted_action,
            action_confidence,
            entry_price
        FROM predictions 
        WHERE symbol = ? AND prediction_timestamp >= ?
        ORDER BY prediction_timestamp ASC
        """
        
        cursor = conn.execute(predictions_query, (symbol, start_time.isoformat()))
        predictions_data = cursor.fetchall()
        
        # Process data
        chart_data = {
            'timestamps': [],
            'prices': [],
            'sentiment': [],
            'rsi': [],
            'macd': [],
            'prediction_times': [],
            'entry_prices': [],
            'actions': []
        }
        
        for row in features_data:
            timestamp, price, sentiment, confidence, rsi, macd_line, price_1h, volume_ratio = row
            
            if price is not None:
                chart_data['timestamps'].append(timestamp)
                chart_data['prices'].append(price)
                chart_data['sentiment'].append(sentiment if sentiment is not None else 0)
                chart_data['rsi'].append(rsi if rsi is not None else 50)
                chart_data['macd'].append(macd_line if macd_line is not None else 0)
        
        for row in predictions_data:
            pred_time, action, action_conf, entry_price = row
            if entry_price is not None:
                chart_data['prediction_times'].append(pred_time)
                chart_data['entry_prices'].append(entry_price)
                chart_data['actions'].append(action)
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Data Visualization - {symbol}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #0a0a0a;
            color: white;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            border-radius: 10px;
        }}
        .chart-container {{
            margin: 20px 0;
            background-color: #1a1a1a;
            border-radius: 10px;
            padding: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #2d3748, #4a5568);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 {symbol} Trading Visualization</h1>
        <p>Last {hours} hours of trading data with prediction overlays</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <h3>Data Points</h3>
            <p>{len(chart_data['timestamps'])}</p>
        </div>
        <div class="stat-card">
            <h3>Predictions</h3>
            <p>{len(chart_data['prediction_times'])}</p>
        </div>
        <div class="stat-card">
            <h3>Latest Price</h3>
            <p>${chart_data['prices'][-1]:.2f}</p>
        </div>
        <div class="stat-card">
            <h3>Latest RSI</h3>
            <p>{chart_data['rsi'][-1]:.1f}</p>
        </div>
    </div>

    <div class="chart-container">
        <div id="priceChart" style="height: 500px;"></div>
    </div>
    
    <div class="chart-container">
        <div id="indicatorsChart" style="height: 400px;"></div>
    </div>

    <script>
        const data = {json.dumps(chart_data)};

        // Price Chart with Predictions
        const priceTraces = [{{
            x: data.timestamps,
            y: data.prices,
            type: 'scatter',
            mode: 'lines',
            name: '{symbol} Price',
            line: {{ color: '#00ff41', width: 3 }}
        }}];

        if (data.entry_prices.length > 0) {{
            priceTraces.push({{
                x: data.prediction_times,
                y: data.entry_prices,
                type: 'scatter',
                mode: 'markers',
                name: 'Predictions',
                marker: {{ 
                    color: '#ff6b6b', 
                    size: 10,
                    symbol: 'diamond'
                }}
            }});
        }}

        const priceLayout = {{
            title: '{symbol} Price Movement with Predictions',
            xaxis: {{ title: 'Time', color: '#ffffff' }},
            yaxis: {{ title: 'Price ($)', color: '#ffffff' }},
            plot_bgcolor: '#1a1a1a',
            paper_bgcolor: '#1a1a1a',
            font: {{ color: '#ffffff' }}
        }};

        Plotly.newPlot('priceChart', priceTraces, priceLayout, {{responsive: true}});

        // Technical Indicators Chart
        const indicatorTraces = [{{
            x: data.timestamps,
            y: data.sentiment,
            type: 'scatter',
            mode: 'lines',
            name: 'Sentiment Score',
            line: {{ color: '#ffa500', width: 2 }},
            yaxis: 'y1'
        }}, {{
            x: data.timestamps,
            y: data.rsi,
            type: 'scatter',
            mode: 'lines',
            name: 'RSI',
            line: {{ color: '#00bfff', width: 2 }},
            yaxis: 'y2'
        }}, {{
            x: data.timestamps,
            y: data.macd,
            type: 'scatter',
            mode: 'lines',
            name: 'MACD',
            line: {{ color: '#ff69b4', width: 2 }},
            yaxis: 'y3'
        }}];

        // Add RSI reference lines
        indicatorTraces.push({{
            x: data.timestamps,
            y: Array(data.timestamps.length).fill(70),
            type: 'scatter',
            mode: 'lines',
            name: 'RSI Overbought',
            line: {{ color: '#ff0000', width: 1, dash: 'dash' }},
            yaxis: 'y2'
        }});

        indicatorTraces.push({{
            x: data.timestamps,
            y: Array(data.timestamps.length).fill(30),
            type: 'scatter',
            mode: 'lines',
            name: 'RSI Oversold',
            line: {{ color: '#00ff00', width: 1, dash: 'dash' }},
            yaxis: 'y2'
        }});

        const indicatorLayout = {{
            title: '{symbol} Technical Indicators & Sentiment',
            xaxis: {{ title: 'Time', color: '#ffffff' }},
            yaxis: {{ 
                title: 'Sentiment Score', 
                color: '#ffffff',
                side: 'left',
                position: 0
            }},
            yaxis2: {{ 
                title: 'RSI', 
                color: '#ffffff',
                overlaying: 'y',
                side: 'right',
                position: 1,
                range: [0, 100]
            }},
            yaxis3: {{ 
                title: 'MACD', 
                color: '#ffffff',
                overlaying: 'y',
                side: 'left',
                position: 0.15
            }},
            plot_bgcolor: '#1a1a1a',
            paper_bgcolor: '#1a1a1a',
            font: {{ color: '#ffffff' }}
        }};

        Plotly.newPlot('indicatorsChart', indicatorTraces, indicatorLayout, {{responsive: true}});
    </script>
</body>
</html>"""
        
        return html
        
    finally:
        conn.close()

def create_visualization_file(symbol='CBA.AX', hours=24):
    """Create a static HTML file with trading visualization"""
    
    print(f"📊 Generating visualization for {symbol} (last {hours} hours)...")
    
    try:
        html_content = generate_static_visualization(symbol, hours)
        
        filename = f'trading_visualization_{symbol.replace(".", "_")}_{hours}h.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Visualization created: {filename}")
        print(f"🌐 Open {filename} in your browser to view the charts")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error creating visualization: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import sys
    
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'CBA.AX'
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    
    create_visualization_file(symbol, hours)
