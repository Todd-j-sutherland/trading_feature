#!/usr/bin/env python3

import http.server
import socketserver
import json
import logging
from datetime import datetime, timedelta
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
        
        select, button {
            padding: 8px 12px;
            border: 1px solid #404040;
            border-radius: 4px;
            background: #1e1e1e;
            color: #ffffff;
            font-size: 14px;
        }
        
        button {
            background: #0078d4;
            cursor: pointer;
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
        
        .status-panel {
            background: #2d2d2d;
            border-radius: 8px;
            padding: 15px;
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
        
        .chart-container {
            flex: 1;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        
        .chart-placeholder {
            width: 100%;
            height: 100%;
            background: #2d2d2d;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 2px dashed #404040;
        }
        
        .chart-title {
            font-size: 24px;
            margin-bottom: 20px;
            color: #0078d4;
        }
        
        .data-display {
            background: #1e1e1e;
            padding: 20px;
            border-radius: 8px;
            min-width: 300px;
        }
        
        .data-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px;
            background: #404040;
            border-radius: 4px;
        }
        
        .loading {
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
                <div id="legend-items">
                    <div class="legend-item" onclick="toggleElement('candlesticks')">
                        <div class="legend-color" style="background-color: #2196F3"></div>
                        <div class="legend-label">Price Candlesticks</div>
                    </div>
                    <div class="legend-item" onclick="toggleElement('volume')">
                        <div class="legend-color" style="background-color: #9C27B0"></div>
                        <div class="legend-label">Volume</div>
                    </div>
                    <div class="legend-item" onclick="toggleElement('sma20')">
                        <div class="legend-color" style="background-color: #FF9800"></div>
                        <div class="legend-label">SMA 20</div>
                    </div>
                    <div class="legend-item" onclick="toggleElement('sma50')">
                        <div class="legend-color" style="background-color: #FF5722"></div>
                        <div class="legend-label">SMA 50</div>
                    </div>
                </div>
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
            </div>
            
            <div class="chart-container">
                <div class="chart-placeholder">
                    <div class="chart-title">Trading Dashboard - Data View</div>
                    <div class="data-display" id="chart-data">
                        <div id="loading" class="loading">Loading chart data...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentData = null;
        let visibleElements = {
            candlesticks: true,
            volume: true,
            sma20: true,
            sma50: true
        };

        function toggleElement(element) {
            visibleElements[element] = !visibleElements[element];
            
            // Update legend item appearance
            const items = document.querySelectorAll('.legend-item');
            items.forEach(item => {
                const label = item.querySelector('.legend-label').textContent;
                if ((element === 'candlesticks' && label.includes('Candlesticks')) ||
                    (element === 'volume' && label.includes('Volume')) ||
                    (element === 'sma20' && label.includes('SMA 20')) ||
                    (element === 'sma50' && label.includes('SMA 50'))) {
                    
                    if (visibleElements[element]) {
                        item.classList.remove('disabled');
                    } else {
                        item.classList.add('disabled');
                    }
                }
            });
            
            displayChartData();
        }

        async function loadChartData() {
            try {
                const symbol = document.getElementById('symbol').value;
                const hours = document.getElementById('timeframe-select').value;
                
                document.getElementById('loading').textContent = 'Loading...';
                
                const response = await fetch(`/api/chart-data?symbol=${symbol}&hours=${hours}`);
                currentData = await response.json();
                
                // Update status
                document.getElementById('data-points').textContent = currentData.dataPoints;
                document.getElementById('timeframe').textContent = hours + ' hours';
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                
                if (currentData.candlesticks && currentData.candlesticks.length > 0) {
                    const lastPrice = currentData.candlesticks[currentData.candlesticks.length - 1];
                    document.getElementById('current-price').textContent = '$' + lastPrice.close.toFixed(2);
                }
                
                displayChartData();
                
            } catch (error) {
                console.error('Error loading chart data:', error);
                document.getElementById('loading').textContent = 'Error loading data: ' + error.message;
            }
        }

        function displayChartData() {
            if (!currentData || !currentData.candlesticks) return;
            
            const container = document.getElementById('chart-data');
            container.innerHTML = '';
            
            let displayCount = 0;
            const maxDisplay = 10; // Show last 10 data points
            
            if (visibleElements.candlesticks) {
                const title = document.createElement('h3');
                title.textContent = 'Recent Price Data';
                title.style.color = '#2196F3';
                title.style.marginBottom = '10px';
                container.appendChild(title);
                
                const recentData = currentData.candlesticks.slice(-maxDisplay);
                recentData.forEach(candle => {
                    const row = document.createElement('div');
                    row.className = 'data-row';
                    row.innerHTML = `
                        <span>${new Date(candle.time * 1000).toLocaleTimeString()}</span>
                        <span>O: $${candle.open} H: $${candle.high} L: $${candle.low} C: $${candle.close}</span>
                    `;
                    container.appendChild(row);
                });
                displayCount++;
            }
            
            if (visibleElements.volume) {
                const title = document.createElement('h3');
                title.textContent = 'Volume Information';
                title.style.color = '#9C27B0';
                title.style.marginTop = displayCount > 0 ? '20px' : '0';
                title.style.marginBottom = '10px';
                container.appendChild(title);
                
                const row = document.createElement('div');
                row.className = 'data-row';
                row.innerHTML = `<span>Average Volume:</span><span>1,234,567</span>`;
                container.appendChild(row);
                displayCount++;
            }
            
            if (visibleElements.sma20 || visibleElements.sma50) {
                const title = document.createElement('h3');
                title.textContent = 'Technical Indicators';
                title.style.color = '#FF9800';
                title.style.marginTop = displayCount > 0 ? '20px' : '0';
                title.style.marginBottom = '10px';
                container.appendChild(title);
                
                if (visibleElements.sma20) {
                    const row = document.createElement('div');
                    row.className = 'data-row';
                    const sma20 = calculateSMA(currentData.candlesticks, 20);
                    row.innerHTML = `<span>SMA 20:</span><span>$${sma20.toFixed(2)}</span>`;
                    container.appendChild(row);
                }
                
                if (visibleElements.sma50) {
                    const row = document.createElement('div');
                    row.className = 'data-row';
                    const sma50 = calculateSMA(currentData.candlesticks, 50);
                    row.innerHTML = `<span>SMA 50:</span><span>$${sma50.toFixed(2)}</span>`;
                    container.appendChild(row);
                }
            }
            
            if (!visibleElements.candlesticks && !visibleElements.volume && !visibleElements.sma20 && !visibleElements.sma50) {
                container.innerHTML = '<div class="loading">All elements hidden. Click legend items to show data.</div>';
            }
        }

        function calculateSMA(data, period) {
            if (data.length < period) return 0;
            const recent = data.slice(-period);
            const sum = recent.reduce((acc, candle) => acc + candle.close, 0);
            return sum / period;
        }

        function refreshChart() {
            loadChartData();
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {
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
            
            # Generate realistic mock data with proper density
            data = self.get_realistic_price_data(symbol, hours)
            
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

    def get_realistic_price_data(self, symbol, hours):
        """Generate realistic price data with proper density"""
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        # Determine interval for proper data density
        if hours <= 0.5:        # 30 minutes
            interval_minutes = 1    # ~30 points
        elif hours <= 4:        # 4 hours  
            interval_minutes = 5    # ~48 points
        elif hours <= 24:       # 1 day
            interval_minutes = 15   # ~96 points
        elif hours <= 72:       # 3 days
            interval_minutes = 60   # ~72 points
        else:                   # 7+ days
            interval_minutes = 60   # ~168 points for 7 days
        
        # Generate realistic price movement
        candlesticks = []
        current_time = start_time
        base_price = 100.0
        
        # Create some market trends
        trend_changes = random.randint(2, 5)
        trend_duration = hours / trend_changes
        current_trend = random.choice([-1, 1]) * random.uniform(0.001, 0.005)
        
        price = base_price
        trend_counter = 0
        
        while current_time <= now:
            # Change trend occasionally
            if trend_counter > trend_duration * 60 / interval_minutes:
                current_trend = random.choice([-1, 1]) * random.uniform(0.001, 0.005)
                trend_counter = 0
            
            # Apply trend and noise
            trend_move = current_trend * interval_minutes
            noise = random.uniform(-0.3, 0.3)
            price_change = trend_move + noise
            
            price += price_change
            price = max(80, min(120, price))  # Keep realistic bounds
            
            # Generate OHLC
            volatility = random.uniform(0.2, 0.8)
            open_price = price
            high_price = price + random.uniform(0, volatility)
            low_price = price - random.uniform(0, volatility)
            close_price = random.uniform(low_price, high_price)
            
            candlesticks.append({
                'time': int(current_time.timestamp()),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2)
            })
            
            price = close_price
            current_time += timedelta(minutes=interval_minutes)
            trend_counter += 1
        
        logger.info(f"Generated {len(candlesticks)} data points for {hours} hours with {interval_minutes}min intervals")
        return candlesticks

def main():
    PORT = 8082  # Changed from 8081 to avoid conflicts
    
    try:
        with socketserver.TCPServer(("", PORT), TradingDashboardHandler) as httpd:
            logger.info(f"Simple Trading Dashboard started on port {PORT}")
            logger.info(f"Dashboard URL: http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
