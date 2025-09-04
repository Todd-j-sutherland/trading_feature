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
        elif self.path.startswith('/api/chart-data'):
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
    <title>Fixed Trading Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: #1e1e1e; 
            color: #fff; 
            height: 100vh; 
            display: flex; 
        }
        .sidebar {
            width: 300px; 
            background: #2d2d2d; 
            padding: 20px; 
            border-right: 1px solid #404040;
        }
        .main { 
            flex: 1; 
            display: flex; 
            flex-direction: column; 
        }
        .controls { 
            padding: 20px; 
            background: #2d2d2d; 
            display: flex; 
            gap: 15px; 
            align-items: center; 
        }
        select, button { 
            padding: 8px 12px; 
            border: 1px solid #404040; 
            border-radius: 4px; 
            background: #1e1e1e; 
            color: #fff; 
        }
        button { background: #0078d4; cursor: pointer; }
        button:hover { background: #106ebe; }
        .legend-panel { 
            background: #2d2d2d; 
            border-radius: 8px; 
            padding: 15px; 
            margin-bottom: 15px; 
        }
        .legend-item { 
            display: flex; 
            align-items: center; 
            margin-bottom: 8px; 
            cursor: pointer; 
            padding: 5px; 
            border-radius: 4px; 
        }
        .legend-item:hover { background: #404040; }
        .legend-item.disabled { opacity: 0.5; }
        .legend-color { 
            width: 16px; 
            height: 16px; 
            margin-right: 8px; 
            border-radius: 3px; 
        }
        .content { 
            flex: 1; 
            padding: 20px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .data-display { 
            background: #2d2d2d; 
            padding: 30px; 
            border-radius: 8px; 
            min-width: 500px; 
            max-height: 70vh; 
            overflow-y: auto; 
        }
        .data-row { 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 8px; 
            padding: 8px; 
            background: #404040; 
            border-radius: 4px; 
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
        }
        .status-value { 
            color: #0078d4; 
            font-weight: bold; 
        }
        h2 { 
            color: #0078d4; 
            margin-bottom: 20px; 
        }
        h3 { 
            margin: 15px 0 10px 0; 
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="legend-panel">
            <h3>Chart Elements</h3>
            <div class="legend-item" onclick="toggleElement('candlesticks')" id="legend-candlesticks">
                <div class="legend-color" style="background: #2196F3;"></div>
                <span>Price Data</span>
            </div>
            <div class="legend-item" onclick="toggleElement('volume')" id="legend-volume">
                <div class="legend-color" style="background: #9C27B0;"></div>
                <span>Volume</span>
            </div>
            <div class="legend-item" onclick="toggleElement('sma20')" id="legend-sma20">
                <div class="legend-color" style="background: #FF9800;"></div>
                <span>SMA 20</span>
            </div>
            <div class="legend-item" onclick="toggleElement('sma50')" id="legend-sma50">
                <div class="legend-color" style="background: #FF5722;"></div>
                <span>SMA 50</span>
            </div>
        </div>
        
        <div class="status-panel">
            <h3>Status</h3>
            <div class="status-item">
                <span>Data Points:</span>
                <span class="status-value" id="data-points">0</span>
            </div>
            <div class="status-item">
                <span>Timeframe:</span>
                <span class="status-value" id="timeframe">7 days</span>
            </div>
            <div class="status-item">
                <span>Last Update:</span>
                <span class="status-value" id="last-update">Never</span>
            </div>
        </div>
    </div>
    
    <div class="main">
        <div class="controls">
            <label>Symbol:</label>
            <select id="symbol">
                <option value="CBA.AX">CBA</option>
                <option value="ANZ.AX">ANZ</option>
                <option value="WBC.AX">WBC</option>
                <option value="NAB.AX">NAB</option>
            </select>
            
            <label>Timeframe:</label>
            <select id="timeframe-select">
                <option value="0.5">30 Minutes</option>
                <option value="2">2 Hours</option>
                <option value="8">8 Hours</option>
                <option value="24">1 Day</option>
                <option value="72">3 Days</option>
                <option value="168" selected>7 Days</option>
            </select>
            
            <button onclick="loadData()">Refresh Data</button>
        </div>
        
        <div class="content">
            <div class="data-display">
                <h2>Trading Data Dashboard</h2>
                <div id="chart-data">
                    <p>Click "Refresh Data" to load chart information</p>
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
            
            const legendItem = document.getElementById('legend-' + element);
            if (visibleElements[element]) {
                legendItem.classList.remove('disabled');
            } else {
                legendItem.classList.add('disabled');
            }
            
            displayData();
        }

        async function loadData() {
            try {
                const symbol = document.getElementById('symbol').value;
                const hours = document.getElementById('timeframe-select').value;
                
                console.log('Loading data for:', symbol, hours);
                
                const response = await fetch(`/api/chart-data?symbol=${symbol}&hours=${hours}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                currentData = await response.json();
                console.log('Data loaded:', currentData);
                
                // Update status
                document.getElementById('data-points').textContent = currentData.dataPoints || 0;
                document.getElementById('timeframe').textContent = hours + ' hours';
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                
                displayData();
                
            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('chart-data').innerHTML = `
                    <h3 style="color: #f44336;">Error Loading Data</h3>
                    <p>Error: ${error.message}</p>
                    <p>Check the browser console for more details.</p>
                `;
            }
        }

        function displayData() {
            if (!currentData || !currentData.candlesticks) {
                return;
            }
            
            const container = document.getElementById('chart-data');
            container.innerHTML = '';
            
            if (visibleElements.candlesticks) {
                const section = document.createElement('div');
                section.innerHTML = `
                    <h3 style="color: #2196F3;">Recent Price Data (Last 10 Points)</h3>
                `;
                
                const recent = currentData.candlesticks.slice(-10);
                recent.forEach(candle => {
                    const row = document.createElement('div');
                    row.className = 'data-row';
                    row.innerHTML = `
                        <span>${new Date(candle.time * 1000).toLocaleString()}</span>
                        <span>$${candle.close.toFixed(2)}</span>
                    `;
                    section.appendChild(row);
                });
                
                container.appendChild(section);
            }
            
            if (visibleElements.volume) {
                const section = document.createElement('div');
                section.innerHTML = `
                    <h3 style="color: #9C27B0;">Volume Analysis</h3>
                    <div class="data-row">
                        <span>Average Volume:</span>
                        <span>1,234,567 shares</span>
                    </div>
                `;
                container.appendChild(section);
            }
            
            if (visibleElements.sma20 || visibleElements.sma50) {
                const section = document.createElement('div');
                section.innerHTML = '<h3 style="color: #FF9800;">Technical Indicators</h3>';
                
                if (visibleElements.sma20) {
                    const sma20 = calculateSMA(currentData.candlesticks, 20);
                    const row = document.createElement('div');
                    row.className = 'data-row';
                    row.innerHTML = `<span>SMA 20:</span><span>$${sma20.toFixed(2)}</span>`;
                    section.appendChild(row);
                }
                
                if (visibleElements.sma50) {
                    const sma50 = calculateSMA(currentData.candlesticks, 50);
                    const row = document.createElement('div');
                    row.className = 'data-row';
                    row.innerHTML = `<span>SMA 50:</span><span>$${sma50.toFixed(2)}</span>`;
                    section.appendChild(row);
                }
                
                container.appendChild(section);
            }
            
            if (!visibleElements.candlesticks && !visibleElements.volume && !visibleElements.sma20 && !visibleElements.sma50) {
                container.innerHTML = '<p>All elements hidden. Click legend items to show data.</p>';
            }
        }

        function calculateSMA(data, period) {
            if (data.length < period) return 0;
            const recent = data.slice(-period);
            const sum = recent.reduce((acc, candle) => acc + candle.close, 0);
            return sum / period;
        }

        // Auto-load data on page load
        document.addEventListener('DOMContentLoaded', () => {
            loadData();
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
            
            logger.info(f"API: Generating data for {symbol} over {hours} hours")
            
            # Generate realistic data with proper density
            data = self.generate_realistic_data(symbol, hours)
            
            response_data = {
                'candlesticks': data,
                'symbol': symbol,
                'timeframe': hours,
                'dataPoints': len(data),
                'lastUpdate': datetime.now().isoformat()
            }
            
            logger.info(f"API: Returning {len(data)} data points")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            logger.error(f"API Error: {e}")
            self.send_error(500, str(e))

    def generate_realistic_data(self, symbol, hours):
        """Generate realistic trading data with proper density"""
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        # Determine interval for proper data density
        if hours <= 0.5:
            interval_minutes = 1    # ~30 points
        elif hours <= 4:
            interval_minutes = 5    # ~48 points
        elif hours <= 24:
            interval_minutes = 15   # ~96 points
        elif hours <= 72:
            interval_minutes = 60   # ~72 points
        else:
            interval_minutes = 60   # ~168 points for 7 days
        
        candlesticks = []
        current_time = start_time
        price = 100.0
        
        while current_time <= now:
            # Realistic price movement
            price_change = random.uniform(-0.5, 0.5)
            price += price_change
            price = max(90, min(110, price))
            
            # Generate OHLC
            volatility = random.uniform(0.1, 0.5)
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
        
        return candlesticks

def main():
    PORT = 8083  # Using a fresh port
    
    try:
        with socketserver.TCPServer(("", PORT), TradingDashboardHandler) as httpd:
            logger.info(f"Fixed Trading Dashboard started on port {PORT}")
            logger.info(f"Access at: http://170.64.199.151:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
