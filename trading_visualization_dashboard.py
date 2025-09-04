#!/usr/bin/env python3
"""
Real-time Trading Visualization Dashboard
Shows 1-minute price data with overlaid prediction metrics
"""

import sqlite3
import json
from datetime import datetime, timedelta
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import os

class TradingVisualizationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"DEBUG: Received GET request: {self.path}")
        
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/data':
            self.serve_data()
        elif self.path.startswith('/api/symbol/'):
            # Parse URL properly to extract symbol and query parameters
            # Remove '/api/symbol/' prefix
            symbol_part = self.path[12:]  # Remove '/api/symbol/'
            
            # Split on '?' to separate symbol from query parameters
            if '?' in symbol_part:
                symbol = symbol_part.split('?')[0]
            else:
                symbol = symbol_part
            
            print(f"DEBUG: Extracted symbol: '{symbol}' from path: '{self.path}'")
            self.serve_symbol_data(symbol)
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Visualization Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #0a0a0a;
            color: #ffffff;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            border-radius: 10px;
        }
        .controls {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .control-group {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        select, button {
            padding: 10px 15px;
            border: none;
            border-radius: 5px;
            background-color: #2d3748;
            color: white;
            cursor: pointer;
            margin: 5px;
        }
        select:hover, button:hover {
            background-color: #4a5568;
        }
        .chart-container {
            margin: 20px 0;
            background-color: #1a1a1a;
            border-radius: 10px;
            padding: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-card {
            background: linear-gradient(135deg, #2d3748, #4a5568);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            margin: 5px 0;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            text-align: center;
        }
        .status.connected {
            background-color: #22543d;
            border: 1px solid #38a169;
        }
        .status.loading {
            background-color: #744210;
            border: 1px solid #d69e2e;
        }
        .status.error {
            background-color: #742a2a;
            border: 1px solid #e53e3e;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 Trading Visualization Dashboard</h1>
        <p>Real-time price movements with prediction metrics overlay</p>
        <div id="status" class="status loading">Loading data...</div>
    </div>

    <div class="controls">
        <div class="control-group">
            <label>Symbol:</label>
            <select id="symbolSelect">
                <option value="CBA.AX">CBA.AX</option>
                <option value="WBC.AX">WBC.AX</option>
                <option value="ANZ.AX">ANZ.AX</option>
                <option value="NAB.AX">NAB.AX</option>
                <option value="MQG.AX">MQG.AX</option>
                <option value="SUN.AX">SUN.AX</option>
                <option value="QBE.AX">QBE.AX</option>
                <option value="BHP.AX">BHP.AX</option>
            </select>
        </div>
        <div class="control-group">
            <label>Time Range:</label>
            <select id="timeRange">
                <option value="1">Last 1 hour</option>
                <option value="4" selected>Last 4 hours</option>
                <option value="24">Last 24 hours</option>
                <option value="168">Last 7 days</option>
            </select>
        </div>
        <div class="control-group">
            <button onclick="refreshData()">🔄 Refresh</button>
            <button onclick="toggleAutoRefresh()" id="autoRefreshBtn">▶️ Auto Refresh</button>
        </div>
    </div>

    <div class="metrics-grid" id="metricsGrid"></div>
    
    <div class="chart-container">
        <div id="priceChart" style="height: 500px;"></div>
    </div>
    
    <div class="chart-container">
        <div id="sentimentChart" style="height: 300px;"></div>
    </div>
    
    <div class="chart-container">
        <div id="technicalChart" style="height: 300px;"></div>
    </div>

    <script>
        let autoRefreshInterval = null;
        let isAutoRefreshing = false;

        function updateStatus(message, type = 'loading') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
        }

        function formatTimestamp(timestamp) {
            return new Date(timestamp).toLocaleString();
        }

        async function loadSymbolData(symbol = 'CBA.AX', hours = 4) {
            try {
                updateStatus('Loading data...', 'loading');
                const response = await fetch(`/api/symbol/${symbol}?hours=${hours}`);
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                updateMetrics(data.metrics);
                plotPriceChart(data.price_data, symbol);
                plotSentimentChart(data.sentiment_data, symbol);
                plotTechnicalChart(data.technical_data, symbol);
                
                updateStatus(`Last updated: ${formatTimestamp(new Date())}`, 'connected');
            } catch (error) {
                console.error('Error loading data:', error);
                updateStatus(`Error: ${error.message}`, 'error');
            }
        }

        function updateMetrics(metrics) {
            const grid = document.getElementById('metricsGrid');
            grid.innerHTML = '';
            
            Object.entries(metrics).forEach(([key, value]) => {
                const card = document.createElement('div');
                card.className = 'metric-card';
                card.innerHTML = `
                    <div class="metric-label">${key.replace(/_/g, ' ').toUpperCase()}</div>
                    <div class="metric-value">${typeof value === 'number' ? value.toFixed(3) : value}</div>
                `;
                grid.appendChild(card);
            });
        }

        function plotPriceChart(data, symbol) {
            const traces = [];
            
            // Main price line - only show if we have actual price variation
            if (data.timestamps.length > 0 && data.prices.length > 0) {
                // Filter out consecutive identical values for cleaner visualization
                const filteredData = data.timestamps.map((ts, i) => ({
                    timestamp: ts,
                    price: data.prices[i]
                })).filter((point, i, arr) => {
                    if (i === 0 || i === arr.length - 1) return true; // Always include first and last
                    return point.price !== arr[i-1].price; // Only include if price changed
                });

                // If we still have reasonable data points, show the line
                if (filteredData.length > 1) {
                    traces.push({
                        x: filteredData.map(p => p.timestamp),
                        y: filteredData.map(p => p.price),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: `${symbol} Price`,
                        line: { color: '#00ff41', width: 3 },
                        marker: { size: 6, color: '#00ff41' }
                    });
                }
            }

            // Add prediction markers with action-based colors
            if (data.entry_prices && data.entry_prices.length > 0) {
                // Group predictions by action
                const buyPoints = { x: [], y: [], text: [] };
                const holdPoints = { x: [], y: [], text: [] };
                const sellPoints = { x: [], y: [], text: [] };
                
                data.prediction_times.forEach((time, i) => {
                    const action = data.actions[i];
                    const price = data.entry_prices[i];
                    const text = `${action}: $${price.toFixed(2)}`;
                    
                    if (action === 'BUY') {
                        buyPoints.x.push(time);
                        buyPoints.y.push(price);
                        buyPoints.text.push(text);
                    } else if (action === 'HOLD') {
                        holdPoints.x.push(time);
                        holdPoints.y.push(price);
                        holdPoints.text.push(text);
                    } else if (action === 'SELL') {
                        sellPoints.x.push(time);
                        sellPoints.y.push(price);
                        sellPoints.text.push(text);
                    }
                });
                
                // Add BUY markers
                if (buyPoints.x.length > 0) {
                    traces.push({
                        x: buyPoints.x,
                        y: buyPoints.y,
                        type: 'scatter',
                        mode: 'markers',
                        name: 'BUY Signals',
                        marker: { 
                            color: '#00ff00', 
                            size: 12,
                            symbol: 'triangle-up'
                        },
                        text: buyPoints.text,
                        hovertemplate: '%{text}<extra></extra>'
                    });
                }
                
                // Add HOLD markers
                if (holdPoints.x.length > 0) {
                    traces.push({
                        x: holdPoints.x,
                        y: holdPoints.y,
                        type: 'scatter',
                        mode: 'markers',
                        name: 'HOLD Signals',
                        marker: { 
                            color: '#ffaa00', 
                            size: 10,
                            symbol: 'circle'
                        },
                        text: holdPoints.text,
                        hovertemplate: '%{text}<extra></extra>'
                    });
                }
                
                // Add SELL markers
                if (sellPoints.x.length > 0) {
                    traces.push({
                        x: sellPoints.x,
                        y: sellPoints.y,
                        type: 'scatter',
                        mode: 'markers',
                        name: 'SELL Signals',
                        marker: { 
                            color: '#ff0000', 
                            size: 12,
                            symbol: 'triangle-down'
                        },
                        text: sellPoints.text,
                        hovertemplate: '%{text}<extra></extra>'
                    });
                }
            }

            const layout = {
                title: `${symbol} Price Movement with Trading Signals`,
                xaxis: { title: 'Time', color: '#ffffff' },
                yaxis: { title: 'Price ($)', color: '#ffffff' },
                plot_bgcolor: '#1a1a1a',
                paper_bgcolor: '#1a1a1a',
                font: { color: '#ffffff' },
                grid: { color: '#333333' },
                hovermode: 'x unified',
                annotations: [
                    {
                        x: 0.02,
                        y: 0.98,
                        xref: 'paper',
                        yref: 'paper',
                        text: `${data.timestamps.length} data points, ${data.entry_prices ? data.entry_prices.length : 0} predictions`,
                        showarrow: false,
                        font: { color: '#888888', size: 10 }
                    }
                ]
            };

            Plotly.newPlot('priceChart', traces, layout, {responsive: true});
        }

        function plotSentimentChart(data, symbol) {
            const traces = [];
            
            // Filter data to show only meaningful changes in sentiment
            if (data.timestamps.length > 0) {
                // Create filtered datasets for sentiment and confidence
                const sentimentData = data.timestamps.map((ts, i) => ({
                    timestamp: ts,
                    sentiment: data.sentiment_scores[i],
                    confidence: data.confidence_scores ? data.confidence_scores[i] : 0
                })).filter((point, i, arr) => {
                    if (i === 0 || i === arr.length - 1) return true; // Always include first and last
                    return Math.abs(point.sentiment - arr[i-1].sentiment) > 0.001 || 
                           Math.abs(point.confidence - arr[i-1].confidence) > 0.001; // Include if meaningful change
                });

                if (sentimentData.length > 1) {
                    // Show as lines if we have variation
                    traces.push({
                        x: sentimentData.map(p => p.timestamp),
                        y: sentimentData.map(p => p.sentiment),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'Sentiment Score',
                        line: { color: '#ffa500', width: 2 },
                        marker: { size: 8, color: '#ffa500' }
                    });
                } else {
                    // Show as single point if no variation
                    traces.push({
                        x: data.timestamps,
                        y: data.sentiment_scores,
                        type: 'scatter',
                        mode: 'markers',
                        name: 'Sentiment Score',
                        marker: { size: 10, color: '#ffa500' }
                    });
                }
            }

            // Confidence level
            if (data.confidence_scores && data.confidence_scores.length > 0) {
                // Filter confidence data similar to sentiment
                const confData = data.timestamps.map((ts, i) => ({
                    timestamp: ts,
                    confidence: data.confidence_scores[i]
                })).filter((point, i, arr) => {
                    if (i === 0 || i === arr.length - 1) return true;
                    return Math.abs(point.confidence - arr[i-1].confidence) > 0.001;
                });

                if (confData.length > 1) {
                    traces.push({
                        x: confData.map(p => p.timestamp),
                        y: confData.map(p => p.confidence),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'Confidence Level',
                        line: { color: '#9370db', width: 1 },
                        marker: { size: 6, color: '#9370db' },
                        yaxis: 'y2'
                    });
                } else {
                    traces.push({
                        x: data.timestamps,
                        y: data.confidence_scores,
                        type: 'scatter',
                        mode: 'markers',
                        name: 'Confidence Level',
                        marker: { size: 8, color: '#9370db' },
                        yaxis: 'y2'
                    });
                }
            }
            
            // Add sentiment reference lines
            const timeRange = data.timestamps.length > 0 ? data.timestamps : ['2025-09-03T00:00:00'];
            
            // Positive sentiment line
            traces.push({
                x: timeRange,
                y: Array(timeRange.length).fill(0.5),
                type: 'scatter',
                mode: 'lines',
                name: 'Positive Threshold',
                line: { color: '#00ff00', width: 1, dash: 'dash' },
                showlegend: false
            });
            
            // Negative sentiment line
            traces.push({
                x: timeRange,
                y: Array(timeRange.length).fill(-0.5),
                type: 'scatter',
                mode: 'lines',
                name: 'Negative Threshold',
                line: { color: '#ff0000', width: 1, dash: 'dash' },
                showlegend: false
            });

            const layout = {
                title: `${symbol} Sentiment Analysis & Confidence`,
                xaxis: { title: 'Time', color: '#ffffff' },
                yaxis: { 
                    title: 'Sentiment Score', 
                    color: '#ffffff',
                    range: [-1, 1]
                },
                yaxis2: {
                    title: 'Confidence Level',
                    overlaying: 'y',
                    side: 'right',
                    color: '#ffffff',
                    range: [0, 1]
                },
                plot_bgcolor: '#1a1a1a',
                paper_bgcolor: '#1a1a1a',
                font: { color: '#ffffff' },
                annotations: [
                    {
                        x: 0.02,
                        y: 0.98,
                        xref: 'paper',
                        yref: 'paper',
                        text: data.timestamps.length === 1 ? 'Single Data Point' : `${data.timestamps.length} Data Points`,
                        showarrow: false,
                        font: { color: '#888888', size: 10 }
                    }
                ]
            };

            Plotly.newPlot('sentimentChart', traces, layout, {responsive: true});
        }

        function plotTechnicalChart(data, symbol) {
            const traces = [];
            
            // Filter RSI data to show meaningful changes
            if (data.timestamps.length > 0) {
                const rsiData = data.timestamps.map((ts, i) => ({
                    timestamp: ts,
                    rsi: data.rsi_values[i],
                    macd: data.macd_values ? data.macd_values[i] : 0
                })).filter((point, i, arr) => {
                    if (i === 0 || i === arr.length - 1) return true; // Always include first and last
                    return Math.abs(point.rsi - arr[i-1].rsi) > 0.5 || 
                           Math.abs(point.macd - arr[i-1].macd) > 0.001; // Include if meaningful change
                });

                if (rsiData.length > 1) {
                    traces.push({
                        x: rsiData.map(p => p.timestamp),
                        y: rsiData.map(p => p.rsi),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'RSI',
                        line: { color: '#00bfff', width: 2 },
                        marker: { size: 8, color: '#00bfff' }
                    });
                } else {
                    traces.push({
                        x: data.timestamps,
                        y: data.rsi_values,
                        type: 'scatter',
                        mode: 'markers',
                        name: 'RSI',
                        marker: { size: 10, color: '#00bfff' }
                    });
                }
            }

            // MACD line/point (on secondary axis)
            if (data.macd_values && data.macd_values.length > 0) {
                const macdData = data.timestamps.map((ts, i) => ({
                    timestamp: ts,
                    macd: data.macd_values[i]
                })).filter((point, i, arr) => {
                    if (i === 0 || i === arr.length - 1) return true;
                    return Math.abs(point.macd - arr[i-1].macd) > 0.001;
                });

                if (macdData.length > 1) {
                    traces.push({
                        x: macdData.map(p => p.timestamp),
                        y: macdData.map(p => p.macd),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'MACD',
                        line: { color: '#ff69b4', width: 2 },
                        marker: { size: 6, color: '#ff69b4' },
                        yaxis: 'y2'
                    });
                } else {
                    traces.push({
                        x: data.timestamps,
                        y: data.macd_values,
                        type: 'scatter',
                        mode: 'markers',
                        name: 'MACD',
                        marker: { size: 8, color: '#ff69b4' },
                        yaxis: 'y2'
                    });
                }
            }

            // RSI reference lines (always show these for context)
            const timeRange = data.timestamps.length > 0 ? data.timestamps : ['2025-09-03T00:00:00'];
            
            // RSI Overbought (70)
            traces.push({
                x: timeRange,
                y: Array(timeRange.length).fill(70),
                type: 'scatter',
                mode: 'lines',
                name: 'RSI Overbought (70)',
                line: { color: '#ff0000', width: 1, dash: 'dash' },
                showlegend: false
            });

            // RSI Oversold (30)
            traces.push({
                x: timeRange,
                y: Array(timeRange.length).fill(30),
                type: 'scatter',
                mode: 'lines',
                name: 'RSI Oversold (30)',
                line: { color: '#00ff00', width: 1, dash: 'dash' },
                showlegend: false
            });
            
            // RSI Neutral (50)
            traces.push({
                x: timeRange,
                y: Array(timeRange.length).fill(50),
                type: 'scatter',
                mode: 'lines',
                name: 'RSI Neutral (50)',
                line: { color: '#888888', width: 1, dash: 'dot' },
                showlegend: false
            });

            // MACD zero line
            traces.push({
                x: timeRange,
                y: Array(timeRange.length).fill(0),
                type: 'scatter',
                mode: 'lines',
                name: 'MACD Zero',
                line: { color: '#666666', width: 1, dash: 'dot' },
                yaxis: 'y2',
                showlegend: false
            });

            const layout = {
                title: `${symbol} Technical Indicators`,
                xaxis: { title: 'Time', color: '#ffffff' },
                yaxis: { 
                    title: 'RSI', 
                    color: '#ffffff', 
                    range: [0, 100],
                    side: 'left'
                },
                yaxis2: {
                    title: 'MACD',
                    overlaying: 'y',
                    side: 'right',
                    color: '#ffffff'
                },
                plot_bgcolor: '#1a1a1a',
                paper_bgcolor: '#1a1a1a',
                font: { color: '#ffffff' },
                annotations: [
                    {
                        x: 0.02,
                        y: 0.02,
                        xref: 'paper',
                        yref: 'paper',
                        text: data.rsi_values.length > 0 ? 
                            `RSI: ${data.rsi_values[data.rsi_values.length-1].toFixed(1)} ${data.rsi_values[data.rsi_values.length-1] > 70 ? '(Overbought)' : data.rsi_values[data.rsi_values.length-1] < 30 ? '(Oversold)' : '(Neutral)'}` :
                            'No RSI data',
                        showarrow: false,
                        font: { color: '#888888', size: 10 }
                    }
                ]
            };

            Plotly.newPlot('technicalChart', traces, layout, {responsive: true});
        }

        function refreshData() {
            const symbol = document.getElementById('symbolSelect').value;
            const hours = parseInt(document.getElementById('timeRange').value);
            loadSymbolData(symbol, hours);
        }

        function toggleAutoRefresh() {
            const btn = document.getElementById('autoRefreshBtn');
            
            if (isAutoRefreshing) {
                clearInterval(autoRefreshInterval);
                btn.textContent = '▶️ Auto Refresh';
                isAutoRefreshing = false;
            } else {
                autoRefreshInterval = setInterval(refreshData, 30000); // Refresh every 30 seconds
                btn.textContent = '⏸️ Stop Auto';
                isAutoRefreshing = true;
            }
        }

        // Event listeners
        document.getElementById('symbolSelect').addEventListener('change', refreshData);
        document.getElementById('timeRange').addEventListener('change', refreshData);

        // Load initial data
        loadSymbolData();
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_symbol_data(self, symbol):
        """Serve data for a specific symbol"""
        try:
            # Validate symbol format
            if not symbol or not symbol.endswith('.AX'):
                raise ValueError(f"Invalid symbol format: '{symbol}'. Expected format: 'XXX.AX'")
            
            # Parse query parameters correctly
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            hours = int(query_params.get('hours', [4])[0])
            
            print(f"DEBUG: Processing symbol='{symbol}', hours={hours}")
            
            # Validate hours parameter
            if hours <= 0 or hours > 8760:  # Max 1 year
                hours = 24  # Default to 24 hours
            
            data = get_symbol_visualization_data(symbol, hours)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            
        except Exception as e:
            print(f"ERROR in serve_symbol_data: {e}")
            import traceback
            traceback.print_exc()
            error_data = {
                "error": str(e), 
                "symbol_received": symbol,
                "path_received": self.path,
                "debug_info": f"Symbol parsing issue - check URL format"
            }
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_data).encode())

def get_symbol_visualization_data(symbol, hours=4):
    """Get comprehensive data for symbol visualization"""
    
    print(f"DEBUG: Getting data for symbol='{symbol}', hours={hours}")
    
    # Connect to database
    conn = sqlite3.connect('trading_predictions.db')
    
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        print(f"DEBUG: Time range: {start_time.isoformat()} to {end_time.isoformat()}")
        
        # Get enhanced features data (this contains price, sentiment, technical data)
        # Get enhanced features data
        features_query = """
        SELECT 
            timestamp,
            current_price,
            sentiment_score,
            confidence,
            rsi,
            macd_line,
            macd_signal,
            price_change_1h,
            price_change_4h,
            volume_ratio,
            bollinger_upper,
            bollinger_lower,
            sma_20,
            sma_50
        FROM enhanced_features 
        WHERE symbol = ? AND timestamp >= ?
        ORDER BY timestamp ASC
        """
        
        cursor = conn.execute(features_query, (symbol, start_time.isoformat()))
        features_data = cursor.fetchall()
        
        print(f"DEBUG: Found {len(features_data)} feature records with time filter")
        
        # If no data found with time filter or very few records, expand the search
        if len(features_data) < 5:
            print(f"DEBUG: Found only {len(features_data)} records with time filter, expanding search for {symbol}")
            
            # Try progressively larger time windows
            expanded_hours = [hours * 2, hours * 7, hours * 30, 8760]  # Up to 1 year
            
            for expanded in expanded_hours:
                expanded_start = end_time - timedelta(hours=expanded)
                cursor = conn.execute(features_query, (symbol, expanded_start.isoformat()))
                features_data = cursor.fetchall()
                print(f"DEBUG: Trying {expanded} hours: found {len(features_data)} records")
                
                if len(features_data) >= 5:
                    break
            
            # If still no data, get all available records for this symbol
            if len(features_data) < 5:
                print(f"DEBUG: Still limited data, getting all records for {symbol}")
                fallback_query = """
                SELECT 
                    timestamp,
                    current_price,
                    sentiment_score,
                    confidence,
                    rsi,
                    macd_line,
                    macd_signal,
                    price_change_1h,
                    price_change_4h,
                    volume_ratio,
                    bollinger_upper,
                    bollinger_lower,
                    sma_20,
                    sma_50
                FROM enhanced_features 
                WHERE symbol = ?
                ORDER BY timestamp ASC
                """
                cursor = conn.execute(fallback_query, (symbol,))
                features_data = cursor.fetchall()
                print(f"DEBUG: All-time fallback found {len(features_data)} records")
        
        # Get prediction data
        predictions_query = """
        SELECT 
            prediction_timestamp,
            predicted_action,
            action_confidence,
            entry_price,
            predicted_direction
        FROM predictions 
        WHERE symbol = ? AND prediction_timestamp >= ?
        ORDER BY prediction_timestamp ASC
        """
        
        # Get prediction data with expanded time range if needed
        cursor = conn.execute(predictions_query, (symbol, start_time.isoformat()))
        predictions_data = cursor.fetchall()
        
        # Expand prediction search if we have few predictions but many features
        if len(predictions_data) < len(features_data) and len(features_data) > 1:
            print(f"DEBUG: Expanding prediction search to match {len(features_data)} feature records")
            
            # Get all predictions for this symbol and match by timestamp proximity
            all_predictions_query = """
            SELECT 
                prediction_timestamp,
                predicted_action,
                action_confidence,
                entry_price,
                predicted_direction
            FROM predictions 
            WHERE symbol = ?
            ORDER BY prediction_timestamp ASC
            """
            cursor = conn.execute(all_predictions_query, (symbol,))
            predictions_data = cursor.fetchall()
        
        print(f"DEBUG: Final data - Features: {len(features_data)}, Predictions: {len(predictions_data)}")
        
        # Process the data for visualization
        timestamps = []
        prices = []
        sentiment_scores = []
        confidence_scores = []
        rsi_values = []
        macd_values = []
        
        prediction_times = []
        entry_prices = []
        actions = []
        
        # Process features data - create unified timeline linking predictions and features
        feature_timestamps = []
        feature_prices = []
        feature_sentiment = []
        feature_confidence = []
        feature_rsi = []
        feature_macd = []
        
        for row in features_data:
            timestamp, price, sentiment, confidence, rsi, macd_line, macd_signal, \
            price_1h, price_4h, volume_ratio, bb_upper, bb_lower, sma20, sma50 = row
            
            feature_timestamps.append(timestamp)
            feature_prices.append(price if price is not None else 0)
            feature_sentiment.append(sentiment if sentiment is not None else 0)
            feature_confidence.append(confidence if confidence is not None else 0)
            feature_rsi.append(rsi if rsi is not None else 50)
            feature_macd.append(macd_line if macd_line is not None else 0)
        
        # Process predictions data
        prediction_times = []
        entry_prices = []
        actions = []
        action_confidences = []
        
        for row in predictions_data:
            pred_time, action, action_conf, entry_price, direction = row
            
            prediction_times.append(pred_time)
            entry_prices.append(entry_price if entry_price is not None else 0)
            actions.append(action if action is not None else 'HOLD')
            action_confidences.append(action_conf if action_conf is not None else 0)
        
        # Create unified timeline by combining feature and prediction timestamps
        all_timestamps = sorted(set(feature_timestamps + prediction_times))
        
        # Interpolate data to create continuous series
        timestamps = []
        prices = []
        sentiment_scores = []
        confidence_scores = []
        rsi_values = []
        macd_values = []
        
        # For each timestamp, find or interpolate feature values
        for ts in all_timestamps:
            timestamps.append(ts)
            
            # Find closest feature data point
            if ts in feature_timestamps:
                idx = feature_timestamps.index(ts)
                prices.append(feature_prices[idx])
                sentiment_scores.append(feature_sentiment[idx])
                confidence_scores.append(feature_confidence[idx])
                rsi_values.append(feature_rsi[idx])
                macd_values.append(feature_macd[idx])
            else:
                # Use most recent feature data (carry forward)
                if feature_timestamps:
                    recent_features = [(ft, i) for i, ft in enumerate(feature_timestamps) if ft <= ts]
                    if recent_features:
                        _, idx = max(recent_features, key=lambda x: x[0])
                        prices.append(feature_prices[idx])
                        sentiment_scores.append(feature_sentiment[idx])
                        confidence_scores.append(feature_confidence[idx])
                        rsi_values.append(feature_rsi[idx])
                        macd_values.append(feature_macd[idx])
                    else:
                        # Use first available data if timestamp is before all features
                        prices.append(feature_prices[0] if feature_prices else 0)
                        sentiment_scores.append(feature_sentiment[0] if feature_sentiment else 0)
                        confidence_scores.append(feature_confidence[0] if feature_confidence else 0)
                        rsi_values.append(feature_rsi[0] if feature_rsi else 50)
                        macd_values.append(feature_macd[0] if feature_macd else 0)
                else:
                    # No feature data available, use defaults
                    prices.append(0)
                    sentiment_scores.append(0)
                    confidence_scores.append(0)
                    rsi_values.append(50)
                    macd_values.append(0)
        
        # Debug information
        print(f"DEBUG: {symbol} - Features: {len(features_data)}, Predictions: {len(predictions_data)}")
        print(f"DEBUG: {symbol} - Unified timeline: {len(timestamps)} points")
        print(f"DEBUG: {symbol} - Prediction times: {len(prediction_times)}, Entry prices: {len(entry_prices)}")
        print(f"DEBUG: Time range: {start_time.isoformat()} to {end_time.isoformat()}")
        
        # Calculate current metrics
        latest_features = features_data[-1] if features_data else None
        latest_prediction = predictions_data[-1] if predictions_data else None
        
        metrics = {}
        if latest_features:
            _, price, sentiment, confidence, rsi, macd_line, macd_signal, \
            price_1h, price_4h, volume_ratio, bb_upper, bb_lower, sma20, sma50 = latest_features
            
            metrics = {
                'current_price': price,
                'sentiment_score': sentiment,
                'confidence': confidence,
                'rsi': rsi,
                'macd_line': macd_line,
                'price_change_1h': price_1h,
                'price_change_4h': price_4h,
                'volume_ratio': volume_ratio,
                'sma_20': sma20,
                'sma_50': sma50
            }
        
        if latest_prediction:
            pred_time, action, action_conf, entry_price, direction = latest_prediction
            metrics.update({
                'last_action': action,
                'action_confidence': action_conf,
                'predicted_direction': direction
            })
        
        return {
            'symbol': symbol,
            'timerange_hours': hours,
            'data_points': len(timestamps),
            'feature_records': len(features_data),
            'prediction_records': len(predictions_data),
            'metrics': metrics,
            'price_data': {
                'timestamps': timestamps,
                'prices': prices,
                'prediction_times': prediction_times,
                'entry_prices': entry_prices,
                'actions': actions,
                'action_confidences': action_confidences
            },
            'sentiment_data': {
                'timestamps': timestamps,
                'sentiment_scores': sentiment_scores,
                'confidence_scores': confidence_scores
            },
            'technical_data': {
                'timestamps': timestamps,
                'rsi_values': rsi_values,
                'macd_values': macd_values
            }
        }
        
    finally:
        conn.close()

def start_dashboard_server(port=8080):
    """Start the visualization dashboard server"""
    server = HTTPServer(('0.0.0.0', port), TradingVisualizationHandler)
    print(f"🚀 Trading Visualization Dashboard starting on port {port}")
    print(f"📊 Access dashboard at: http://localhost:{port}")
    print(f"🌐 Remote access at: http://YOUR_SERVER_IP:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()

if __name__ == "__main__":
    # Change to directory where database is located
    if os.path.exists('/root/test/trading_predictions.db'):
        os.chdir('/root/test')
    elif os.path.exists('./data/trading_predictions.db'):
        os.chdir('./data')
    
    start_dashboard_server(8080)
