#!/usr/bin/env python3

import http.server
import socketserver
import json
import sqlite3
import logging
from datetime import datetime, timedelta
import os
import sys
import random

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingDashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/chart-data':
            self.serve_chart_data()
        elif self.path == '/api/predictions':
            self.serve_predictions()
        elif self.path.startswith('/static/'):
            self.serve_static_file()
        else:
            self.send_error(404)

    def serve_dashboard(self):
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Trading Dashboard</title>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1e1e1e;
            color: #ffffff;
            overflow: hidden;
        }
        
        .dashboard-container {
            display: flex;
            height: 100vh;
        }
        
        .sidebar {
            width: 300px;
            background: #2d2d2d;
            padding: 20px;
            border-right: 1px solid #404040;
            overflow-y: auto;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .chart-container {
            flex: 1;
            position: relative;
            padding: 20px;
        }
        
        .controls {
            padding: 20px;
            background: #2d2d2d;
            border-bottom: 1px solid #404040;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .control-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .control-group label {
            font-size: 14px;
            color: #cccccc;
        }
        
        select, input {
            padding: 8px 12px;
            border: 1px solid #404040;
            border-radius: 4px;
            background: #1e1e1e;
            color: #ffffff;
            font-size: 14px;
        }
        
        button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background: #0078d4;
            color: white;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        
        button:hover {
            background: #106ebe;
        }
        
        .legend-panel {
            background: #2d2d2d;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .legend-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #ffffff;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            cursor: pointer;
            padding: 5px;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        
        .legend-item:hover {
            background: #404040;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 3px;
            margin-right: 8px;
            border: 1px solid #404040;
        }
        
        .legend-label {
            font-size: 14px;
            color: #cccccc;
        }
        
        .legend-item.disabled {
            opacity: 0.5;
        }
        
        .legend-item.disabled .legend-label {
            text-decoration: line-through;
        }
        
        .status-panel {
            background: #2d2d2d;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .status-value {
            color: #0078d4;
            font-weight: bold;
        }
        
        .chart-wrapper {
            width: 100%;
            height: 100%;
            position: relative;
        }
        
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #cccccc;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="sidebar">
            <div class="legend-panel">
                <div class="legend-title">Chart Elements</div>
                <div id="legend-items"></div>
            </div>
            
            <div class="status-panel">
                <div class="legend-title">Market Status</div>
                <div class="status-item">
                    <span>Data Points:</span>
                    <span class="status-value" id="data-points">Loading...</span>
                </div>
                <div class="status-item">
                    <span>Timeframe:</span>
                    <span class="status-value" id="timeframe">7 days</span>
                </div>
                <div class="status-item">
                    <span>Last Update:</span>
                    <span class="status-value" id="last-update">Loading...</span>
                </div>
                <div class="status-item">
                    <span>Current Price:</span>
                    <span class="status-value" id="current-price">Loading...</span>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="controls">
                <div class="control-group">
                    <label for="symbol">Symbol:</label>
                    <select id="symbol">
                        <option value="CBA.AX">CBA</option>
                        <option value="ANZ.AX">ANZ</option>
                        <option value="WBC.AX">WBC</option>
                        <option value="NAB.AX">NAB</option>
                        <option value="BHP.AX">BHP</option>
                        <option value="CSL.AX">CSL</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label for="timeframe">Timeframe:</label>
                    <select id="timeframe-select">
                        <option value="0.5">30 Minutes</option>
                        <option value="2">2 Hours</option>
                        <option value="8">8 Hours</option>
                        <option value="24">1 Day</option>
                        <option value="72">3 Days</option>
                        <option value="168" selected>7 Days</option>
                    </select>
                </div>
                
                <button onclick="refreshChart()">Refresh Chart</button>
                <button onclick="exportData()">Export Data</button>
            </div>
            
            <div class="chart-container">
                <div class="chart-wrapper">
                    <div id="chart"></div>
                    <div id="loading" class="loading">Loading chart data...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let chart = null;
        let candlestickSeries = null;
        let legendState = {
            candlesticks: true,
            volume: true,
            sma20: true,
            sma50: true,
            rsi: true,
            macd: true,
            predictions: true,
            sentiment: true
        };
        
        const legendConfig = {
            candlesticks: { color: '#2196F3', label: 'Price Candlesticks' },
            volume: { color: '#9C27B0', label: 'Volume' },
            sma20: { color: '#FF9800', label: 'SMA 20' },
            sma50: { color: '#FF5722', label: 'SMA 50' },
            rsi: { color: '#4CAF50', label: 'RSI' },
            macd: { color: '#E91E63', label: 'MACD' },
            predictions: { color: '#00BCD4', label: 'ML Predictions' },
            sentiment: { color: '#FFEB3B', label: 'News Sentiment' }
        };

        function initChart() {
            const chartContainer = document.getElementById('chart');
            
            chart = LightweightCharts.createChart(chartContainer, {
                width: chartContainer.clientWidth,
                height: chartContainer.clientHeight,
                layout: {
                    backgroundColor: '#1e1e1e',
                    textColor: '#ffffff',
                },
                grid: {
                    vertLines: {
                        color: '#404040',
                    },
                    horzLines: {
                        color: '#404040',
                    },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#404040',
                },
                timeScale: {
                    borderColor: '#404040',
                    timeVisible: true,
                    secondsVisible: false,
                },
            });

            candlestickSeries = chart.addCandlestickSeries({
                upColor: '#4CAF50',
                downColor: '#F44336',
                borderUpColor: '#4CAF50',
                borderDownColor: '#F44336',
                wickUpColor: '#4CAF50',
                wickDownColor: '#F44336',
            });

            // Create legend
            createLegend();
            
            window.addEventListener('resize', () => {
                chart.applyOptions({ 
                    width: chartContainer.clientWidth,
                    height: chartContainer.clientHeight 
                });
            });
        }

        function createLegend() {
            const legendContainer = document.getElementById('legend-items');
            legendContainer.innerHTML = '';
            
            Object.entries(legendConfig).forEach(([key, config]) => {
                const legendItem = document.createElement('div');
                legendItem.className = `legend-item ${legendState[key] ? '' : 'disabled'}`;
                legendItem.onclick = () => toggleLegendItem(key);
                
                legendItem.innerHTML = `
                    <div class="legend-color" style="background-color: ${config.color}"></div>
                    <div class="legend-label">${config.label}</div>
                `;
                
                legendContainer.appendChild(legendItem);
            });
        }

        function toggleLegendItem(key) {
            legendState[key] = !legendState[key];
            createLegend();
            refreshChart();
        }

        async function loadChartData() {
            try {
                const symbol = document.getElementById('symbol').value;
                const hours = document.getElementById('timeframe-select').value;
                
                document.getElementById('loading').style.display = 'block';
                
                const response = await fetch(`/api/chart-data?symbol=${symbol}&hours=${hours}`);
                const data = await response.json();
                
                if (data.candlesticks && data.candlesticks.length > 0) {
                    // Update candlesticks
                    if (legendState.candlesticks) {
                        candlestickSeries.setData(data.candlesticks);
                    } else {
                        candlestickSeries.setData([]);
                    }
                    
                    // Update status
                    document.getElementById('data-points').textContent = data.candlesticks.length;
                    document.getElementById('timeframe').textContent = hours + ' hours';
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                    
                    const lastPrice = data.candlesticks[data.candlesticks.length - 1];
                    if (lastPrice) {
                        document.getElementById('current-price').textContent = '$' + lastPrice.close.toFixed(2);
                    }
                }
                
                document.getElementById('loading').style.display = 'none';
                
            } catch (error) {
                console.error('Error loading chart data:', error);
                document.getElementById('loading').textContent = 'Error loading data';
            }
        }

        function refreshChart() {
            loadChartData();
        }

        function exportData() {
            const symbol = document.getElementById('symbol').value;
            const timeframe = document.getElementById('timeframe-select').value;
            alert(`Exporting ${symbol} data for ${timeframe} hours...`);
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {
            initChart();
            loadChartData();
        });
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())

    def serve_chart_data(self):
        try:
            # Parse query parameters
            query = self.path.split('?')[1] if '?' in self.path else ''
            params = {}
            for param in query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
            
            symbol = params.get('symbol', 'CBA.AX')
            hours = float(params.get('hours', 168))
            
            logger.info(f"Generating chart data for {symbol} over {hours} hours")
            
            # Try to use yfinance first, fallback to mock data
            try:
                import yfinance as yf
                data = self.get_real_price_data(symbol, hours)
                logger.info(f"Using real yfinance data: {len(data)} points")
            except Exception as e:
                logger.warning(f"yfinance not available ({e}), using mock data")
                data = self.get_mock_price_data(symbol, hours)
                logger.info(f"Using mock data: {len(data)} points")
            
            response_data = {
                'candlesticks': data,
                'symbol': symbol,
                'timeframe': hours,
                'dataPoints': len(data),
                'lastUpdate': datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            logger.error(f"Error serving chart data: {e}")
            self.send_error(500, str(e))

    def get_real_price_data(self, symbol, hours):
        """Get real price data using yfinance"""
        import yfinance as yf
        import pandas as pd
        
        # Convert symbol to yfinance format
        ticker = symbol.replace('.AX', '') + '.AX' if not symbol.endswith('.AX') else symbol
        stock = yf.Ticker(ticker)
        
        # Determine the best interval based on timeframe
        if hours <= 0.5:  # 30 minutes or less
            interval = "1m"
            period = "1d"
        elif hours <= 4:  # 4 hours or less
            interval = "5m"
            period = "5d"
        elif hours <= 24:  # 1 day or less
            interval = "15m"
            period = "5d"
        elif hours <= 72:  # 3 days or less
            interval = "1h"
            period = "5d"
        else:  # More than 3 days
            interval = "1h"
            period = "1mo"
        
        # Get historical data
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            raise Exception("No data returned from yfinance")
        
        # Convert to our format
        candlesticks = []
        for index, row in hist.iterrows():
            # Convert timestamp to Unix timestamp for TradingView
            timestamp = int(index.timestamp())
            
            candlesticks.append({
                'time': timestamp,
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close'])
            })
        
        # Filter to the requested timeframe
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)
        cutoff_timestamp = int(cutoff.timestamp())
        
        filtered_data = [c for c in candlesticks if c['time'] >= cutoff_timestamp]
        
        return filtered_data

    def get_mock_price_data(self, symbol, hours):
        """Generate mock price data when yfinance is not available"""
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        # Determine interval based on timeframe
        if hours <= 1:
            interval_minutes = 1
        elif hours <= 4:
            interval_minutes = 5
        elif hours <= 24:
            interval_minutes = 15
        elif hours <= 72:
            interval_minutes = 60
        else:
            interval_minutes = 60
        
        # Generate data points
        candlesticks = []
        current_time = start_time
        current_price = 100.0  # Base price
        
        while current_time <= now:
            # Add some random movement
            price_change = random.uniform(-2, 2)
            current_price += price_change
            current_price = max(50, min(200, current_price))  # Keep within bounds
            
            # Generate OHLC
            open_price = current_price
            high_price = current_price + random.uniform(0, 1)
            low_price = current_price - random.uniform(0, 1)
            close_price = current_price + random.uniform(-0.5, 0.5)
            
            candlesticks.append({
                'time': int(current_time.timestamp()),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2)
            })
            
            current_time += timedelta(minutes=interval_minutes)
        
        return candlesticks

    def serve_predictions(self):
        """Serve ML predictions data"""
        try:
            predictions = []
            
            # Try to get predictions from database
            try:
                db_path = '/root/test/enhanced_trading_data.db'
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT symbol, prediction_timestamp, predicted_price, confidence
                        FROM predictions 
                        WHERE prediction_timestamp > datetime('now', '-7 days')
                        ORDER BY prediction_timestamp DESC
                        LIMIT 100
                    """)
                    
                    for row in cursor.fetchall():
                        predictions.append({
                            'symbol': row[0],
                            'timestamp': row[1],
                            'predicted_price': row[2],
                            'confidence': row[3]
                        })
                    
                    conn.close()
            except Exception as e:
                logger.warning(f"Could not load predictions from database: {e}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(predictions).encode())
            
        except Exception as e:
            logger.error(f"Error serving predictions: {e}")
            self.send_error(500, str(e))

    def serve_static_file(self):
        self.send_error(404)

def main():
    PORT = 8081
    
    try:
        with socketserver.TCPServer(("", PORT), TradingDashboardHandler) as httpd:
            logger.info(f"Enhanced Trading Dashboard with fallback started on port {PORT}")
            logger.info(f"Dashboard URL: http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
