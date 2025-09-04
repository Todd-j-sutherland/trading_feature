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
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Database and Data Generation ---

def get_db_connection():
    """Establish a connection to the SQLite database."""
    db_path = 'enhanced_trading_data.db'
    if not os.path.exists(db_path):
        logger.warning(f"Database not found at {db_path}. Creating a new one.")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                prediction_timestamp DATETIME NOT NULL,
                predicted_price REAL,
                confidence REAL,
                prediction_type TEXT
            );
        """)
        conn.commit()
        return conn
    return sqlite3.connect(db_path)

def get_price_data(symbol, hours):
    """Get price data, trying yfinance first and falling back to mock data."""
    try:
        import yfinance as yf
        ticker = symbol.replace('.AX', '') + '.AX'
        stock = yf.Ticker(ticker)
        
        if hours <= 1:
            interval, period = "1m", "1d"
        elif hours <= 8:
            interval, period = "5m", "5d"
        elif hours <= 72:
            interval, period = "15m", "60d"
        else:
            interval, period = "1h", "730d"
            
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            raise ValueError("No data from yfinance")
            
        hist = hist.reset_index()
        
        # Ensure correct column names
        hist.rename(columns={'Datetime': 'Timestamp', 'Date': 'Timestamp'}, inplace=True)
        
        # Convert timezone-aware to timezone-naive then to unix timestamp
        if pd.api.types.is_datetime64_any_dtype(hist['Timestamp']):
             if hist['Timestamp'].dt.tz is not None:
                hist['Timestamp'] = hist['Timestamp'].dt.tz_convert('UTC').dt.tz_localize(None)

        candlesticks = [{
            'time': int(row['Timestamp'].timestamp()),
            'open': row['Open'],
            'high': row['High'],
            'low': row['Low'],
            'close': row['Close'],
            'volume': row['Volume']
        } for _, row in hist.iterrows()]
        
        cutoff = int((datetime.now() - timedelta(hours=hours)).timestamp())
        filtered_data = [c for c in candlesticks if c['time'] >= cutoff]
        
        logger.info(f"Successfully fetched {len(filtered_data)} data points from yfinance for {symbol}")
        return filtered_data
        
    except Exception as e:
        logger.warning(f"yfinance failed ({e}), generating mock data.")
        return generate_mock_price_data(hours)

def generate_mock_price_data(hours):
    """Generate realistic mock data."""
    now = datetime.now()
    if hours <= 1: interval_minutes = 1
    elif hours <= 8: interval_minutes = 5
    else: interval_minutes = 15
    
    start_time = now - timedelta(hours=hours)
    candlesticks = []
    price = 100.0
    
    current_time = start_time
    while current_time <= now:
        price_change = random.uniform(-0.5, 0.5)
        price = max(90, min(110, price) + price_change)
        
        open_price = price
        high = price + random.uniform(0, 0.5)
        low = price - random.uniform(0, 0.5)
        close = random.uniform(low, high)
        
        candlesticks.append({
            'time': int(current_time.timestamp()),
            'open': open_price, 'high': high, 'low': low, 'close': close,
            'volume': random.randint(10000, 50000)
        })
        current_time += timedelta(minutes=interval_minutes)
        
    return candlesticks

def get_predictions(symbol, hours):
    """Get BUY/SELL predictions from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    cursor.execute("""
        SELECT prediction_timestamp, prediction_type, confidence 
        FROM predictions 
        WHERE symbol = ? AND prediction_timestamp >= ? AND prediction_type = 'BUY'
    """, (symbol, cutoff_time))
    
    predictions = [{
        'time': int(datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').timestamp()),
        'type': row[1],
        'confidence': row[2]
    } for row in cursor.fetchall()]
    
    conn.close()
    logger.info(f"Found {len(predictions)} BUY predictions for {symbol}")
    return predictions

def get_news_sentiment(hours):
    """Generate mock news sentiment data."""
    sentiments = []
    now = datetime.now()
    start_time = now - timedelta(hours=hours)
    
    for _ in range(random.randint(5, 20)):
        event_time = start_time + timedelta(seconds=random.randint(0, int(hours * 3600)))
        sentiments.append({
            'time': int(event_time.timestamp()),
            'sentiment': random.choice(['positive', 'negative', 'neutral'])
        })
    return sentiments

# --- HTTP Handler ---

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == '/':
                self.serve_dashboard()
            elif self.path.startswith('/api/data'):
                self.serve_api_data()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"Server Error: {e}", exc_info=True)
            self.send_error(500, f"Server Error: {e}")

    def serve_dashboard(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(self.get_html_content().encode('utf-8'))

    def serve_api_data(self):
        try:
            params = dict(p.split('=') for p in self.path.split('?')[1].split('&'))
            symbol = params.get('symbol', 'CBA.AX')
            hours = float(params.get('hours', 24))
            
            price_data = get_price_data(symbol, hours)
            prediction_data = get_predictions(symbol, hours)
            sentiment_data = get_news_sentiment(hours)
            
            response = {
                'price_data': price_data,
                'prediction_data': prediction_data,
                'sentiment_data': sentiment_data
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            logger.error(f"API Data Error: {e}", exc_info=True)
            self.send_error(500, f"API Error: {e}")

    def get_html_content(self):
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Comprehensive Trading Dashboard</title>
    <script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; font-family: sans-serif; background: #131722; color: #d1d4dc; }
        .container { display: flex; height: 100%; }
        .sidebar { width: 280px; padding: 15px; background: #1e222d; border-right: 1px solid #2a2e39; }
        .main-content { flex: 1; display: flex; flex-direction: column; }
        .controls { padding: 10px; background: #1e222d; border-bottom: 1px solid #2a2e39; display: flex; gap: 20px; align-items: center; }
        .chart-container { flex: 1; position: relative; }
        #chart { width: 100%; height: 100%; }
        .legend-item { display: flex; align-items: center; margin-bottom: 10px; cursor: pointer; font-size: 14px; }
        .legend-item.disabled { opacity: 0.5; }
        .legend-color { width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; }
        select, button { padding: 8px; background: #2a2e39; color: #fff; border: 1px solid #404553; border-radius: 4px; }
        h3 { margin-top: 20px; margin-bottom: 10px; color: #0078d4; }
        .loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h3>Controls</h3>
            <div class="controls-group" style="margin-bottom: 20px;">
                <label>Symbol:</label>
                <select id="symbol">
                    <option value="CBA.AX">CBA</option>
                    <option value="ANZ.AX">ANZ</option>
                    <option value="WBC.AX">WBC</option>
                    <option value="NAB.AX">NAB</option>
                </select>
            </div>
            <div class="controls-group">
                <label>Timeframe:</label>
                <select id="timeframe">
                    <option value="1">1 Hour</option>
                    <option value="8" selected>8 Hours</option>
                    <option value="24">1 Day</option>
                    <option value="168">7 Days</option>
                </select>
            </div>
            
            <h3>Chart Layers</h3>
            <div id="legend"></div>
        </div>
        <div class="main-content">
            <div class="chart-container">
                <div id="chart"></div>
                <div id="loading" class="loading">Loading...</div>
            </div>
        </div>
    </div>

    <script>
        let chart;
        const series = {};
        const legendState = {
            candlesticks: { label: 'Price', color: '#2196F3', visible: true, type: 'candlestick' },
            volume: { label: 'Volume', color: '#9C27B0', visible: true, type: 'histogram', scale: 'volume' },
            sma20: { label: 'SMA 20', color: '#FF9800', visible: true, type: 'line' },
            sma50: { label: 'SMA 50', color: '#FF5722', visible: true, type: 'line' },
            predictions: { label: 'BUY Predictions', color: '#00BCD4', visible: true, type: 'marker' },
            sentiment: { label: 'News Sentiment', color: '#FFEB3B', visible: true, type: 'marker' },
            rsi: { label: 'RSI', color: '#4CAF50', visible: true, type: 'line', scale: 'rsi' },
            macd: { label: 'MACD', color: '#E91E63', visible: true, type: 'histogram', scale: 'macd' }
        };

        function init() {
            if (typeof LightweightCharts === 'undefined') {
                document.getElementById('loading').innerText = 'Error: Charting library failed to load.';
                return;
            }
            
            chart = LightweightCharts.createChart(document.getElementById('chart'), {
                layout: { backgroundColor: '#131722', textColor: '#d1d4dc' },
                grid: { vertLines: { color: '#2a2e39' }, horzLines: { color: '#2a2e39' } },
                timeScale: { timeVisible: true, secondsVisible: true }
            });

            // Setup scales
            chart.priceScale('right').applyOptions({ scaleMargins: { top: 0.1, bottom: 0.4 } });
            chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.7, bottom: 0 } });
            chart.priceScale('rsi').applyOptions({ scaleMargins: { top: 0.5, bottom: 0.25 } });
            chart.priceScale('macd').applyOptions({ scaleMargins: { top: 0.25, bottom: 0 } });

            createLegend();
            loadData();

            document.getElementById('symbol').addEventListener('change', loadData);
            document.getElementById('timeframe').addEventListener('change', loadData);
        }

        function createLegend() {
            const container = document.getElementById('legend');
            container.innerHTML = '';
            for (const key in legendState) {
                const item = legendState[key];
                const el = document.createElement('div');
                el.className = 'legend-item';
                el.innerHTML = `<div class="legend-color" style="background:${item.color}"></div><span>${item.label}</span>`;
                el.onclick = () => {
                    item.visible = !item.visible;
                    el.classList.toggle('disabled', !item.visible);
                    toggleSeriesVisibility(key, item.visible);
                };
                container.appendChild(el);
            }
        }

        function toggleSeriesVisibility(key, visible) {
            if (series[key]) {
                series[key].applyOptions({ visible });
            }
        }

        async function loadData() {
            document.getElementById('loading').style.display = 'block';
            
            const symbol = document.getElementById('symbol').value;
            const hours = document.getElementById('timeframe').value;
            
            const response = await fetch(`/api/data?symbol=${symbol}&hours=${hours}`);
            const data = await response.json();

            // Clear old series
            for (const key in series) {
                chart.removeSeries(series[key]);
                delete series[key];
            }

            if (!data.price_data || data.price_data.length === 0) {
                document.getElementById('loading').innerText = 'No data available for this timeframe.';
                return;
            }

            // Add new series
            series.candlesticks = chart.addCandlestickSeries({ title: 'Price' });
            series.volume = chart.addHistogramSeries({ title: 'Volume', priceScaleId: 'volume', priceFormat: { type: 'volume' } });
            series.sma20 = chart.addLineSeries({ color: legendState.sma20.color, lineWidth: 2, crosshairMarkerVisible: false });
            series.sma50 = chart.addLineSeries({ color: legendState.sma50.color, lineWidth: 2, crosshairMarkerVisible: false });
            series.rsi = chart.addLineSeries({ title: 'RSI', priceScaleId: 'rsi', color: legendState.rsi.color });
            series.macd = chart.addHistogramSeries({ title: 'MACD', priceScaleId: 'macd', color: legendState.macd.color });

            // Process data
            const taData = calculateTA(data.price_data);
            
            series.candlesticks.setData(data.price_data);
            series.volume.setData(data.price_data.map(d => ({ time: d.time, value: d.volume, color: d.close > d.open ? 'rgba(0, 150, 136, 0.5)' : 'rgba(255, 82, 82, 0.5)' })));
            series.sma20.setData(taData.sma20);
            series.sma50.setData(taData.sma50);
            series.rsi.setData(taData.rsi);
            series.macd.setData(taData.macd);

            // Set markers
            const predictionMarkers = data.prediction_data.map(p => ({
                time: p.time,
                position: 'belowBar',
                color: legendState.predictions.color,
                shape: 'arrowUp',
                text: `BUY @ ${p.confidence.toFixed(2)}`
            }));
            series.candlesticks.setMarkers(predictionMarkers);
            
            const sentimentMarkers = data.sentiment_data.map(s => ({
                time: s.time,
                position: 'aboveBar',
                color: s.sentiment === 'positive' ? '#4caf50' : (s.sentiment === 'negative' ? '#f44336' : '#ffeb3b'),
                shape: 'circle',
                text: s.sentiment.charAt(0).toUpperCase()
            }));
            series.candlesticks.setMarkers([...predictionMarkers, ...sentimentMarkers]);

            // Update visibility based on legend
            for (const key in legendState) {
                toggleSeriesVisibility(key, legendState[key].visible);
            }

            chart.timeScale().fitContent();
            document.getElementById('loading').style.display = 'none';
        }

        function calculateTA(data) {
            const closePrices = data.map(d => d.close);
            
            const sma = (period) => {
                const result = [];
                for (let i = period - 1; i < data.length; i++) {
                    const slice = closePrices.slice(i - period + 1, i + 1);
                    const sum = slice.reduce((a, b) => a + b, 0);
                    result.push({ time: data[i].time, value: sum / period });
                }
                return result;
            };

            const rsi = (period = 14) => {
                const result = [];
                let gains = 0, losses = 0;
                for (let i = 1; i < data.length; i++) {
                    const diff = data[i].close - data[i-1].close;
                    if (i <= period) {
                        gains += Math.max(0, diff);
                        losses += Math.max(0, -diff);
                    } else {
                        gains = (gains * (period - 1) + Math.max(0, diff)) / period;
                        losses = (losses * (period - 1) + Math.max(0, -diff)) / period;
                    }
                    if (i >= period) {
                        const rs = losses > 0 ? gains / losses : 100;
                        result.push({ time: data[i].time, value: 100 - (100 / (1 + rs)) });
                    }
                }
                return result;
            };
            
            const ema = (source, period) => {
                const result = [];
                let ema = source.slice(0, period).reduce((a, b) => a + b, 0) / period;
                const multiplier = 2 / (period + 1);
                for (let i = period; i < source.length; i++) {
                    ema = (source[i] - ema) * multiplier + ema;
                    result.push({ time: data[i].time, value: ema });
                }
                return result;
            };

            const macd = (fast = 12, slow = 26, signal = 9) => {
                const emaFast = ema(closePrices, fast).map(d => d.value);
                const emaSlow = ema(closePrices, slow).map(d => d.value);
                const macdLine = emaFast.slice(emaFast.length - emaSlow.length).map((f, i) => f - emaSlow[i]);
                const signalLine = ema(macdLine, signal);
                
                const histogram = signalLine.map((s, i) => {
                    const macdVal = macdLine[macdLine.length - signalLine.length + i];
                    const histVal = macdVal - s.value;
                    return { time: s.time, value: histVal, color: histVal > 0 ? 'rgba(0, 150, 136, 0.5)' : 'rgba(255, 82, 82, 0.5)' };
                });
                return histogram;
            };

            return {
                sma20: sma(20),
                sma50: sma(50),
                rsi: rsi(),
                macd: macd()
            };
        }

        // Run after the script is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    </script>
</body>
</html>
        """

# --- Main Execution ---

def main():
    PORT = 8084  # Using a new port to avoid conflicts
    
    try:
        # Ensure we have a database
        if not os.path.exists('enhanced_trading_data.db'):
            get_db_connection().close()
            
        httpd = socketserver.TCPServer(("", PORT), DashboardHandler)
        logger.info(f"Comprehensive dashboard starting on port {PORT}")
        logger.info(f"Access at: http://170.64.199.151:{PORT}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
