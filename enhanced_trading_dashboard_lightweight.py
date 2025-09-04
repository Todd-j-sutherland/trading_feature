#!/usr/bin/env python3
"""
Enhanced Trading Visualization Dashboard with TradingView Lightweight Charts
Provides professional-grade financial charting with candlestick charts, volume, and technical indicators
"""

import sqlite3
import json
import os
import math
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Try to import yfinance for real market data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("yfinance not available - install with: pip install yfinance")

# Try to import requests for alternative data sources
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class EnhancedTradingVisualizationHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # Suppress default logging
    
    def do_GET(self):
        print(f"DEBUG: Received GET request: {self.path}")
        
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_dashboard()
        elif parsed_path.path.startswith('/api/symbol/'):
            self.serve_api_data(parsed_path)
        elif parsed_path.path.startswith('/api/candlestick/'):
            self.serve_candlestick_data(parsed_path)
        else:
            self.send_error(404)
    
    def serve_candlestick_data(self, parsed_path):
        """Serve OHLCV candlestick data for TradingView charts"""
        try:
            # Extract symbol from path like /api/candlestick/WBC.AX
            path_parts = parsed_path.path.split('/')
            symbol = path_parts[-1] if len(path_parts) > 2 else 'CBA.AX'
            
            query_params = parse_qs(parsed_path.query)
            hours = int(query_params.get('hours', [24])[0])
            
            print(f"DEBUG: Candlestick data request for {symbol}, {hours} hours")
            
            data = self.get_candlestick_data(symbol, hours)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            
        except Exception as e:
            print(f"ERROR: Failed to serve candlestick data: {e}")
            self.send_error(500)
    
    def serve_api_data(self, parsed_path):
        """Serve enhanced API data for indicators and volume"""
        try:
            # Extract symbol from path
            path_parts = parsed_path.path.split('/')
            symbol = path_parts[-1] if len(path_parts) > 2 else 'CBA.AX'
            
            query_params = parse_qs(parsed_path.query)
            hours = int(query_params.get('hours', [24])[0])
            
            print(f"DEBUG: API data request for {symbol}, {hours} hours")
            
            data = self.get_enhanced_symbol_data(symbol, hours)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            
        except Exception as e:
            print(f"ERROR: Failed to serve API data: {e}")
            self.send_error(500)

    def serve_dashboard(self):
        """Serve the enhanced dashboard with TradingView Lightweight Charts"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📈 Enhanced Trading Dashboard</title>
    <script src="https://unpkg.com/lightweight-charts@4.2.1/dist/lightweight-charts.standalone.production.js"></script>
    <script>
        // Fallback to newer version if v4 doesn't work
        if (typeof LightweightCharts === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js';
            document.head.appendChild(script);
        }
    </script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        console.log('Chart libraries loaded:');
        console.log('TradingView Charts:', typeof LightweightCharts !== 'undefined' ? 'Available' : 'Not Available');
        console.log('Chart.js:', typeof Chart !== 'undefined' ? 'Available' : 'Not Available');
        
        // Use Chart.js as fallback if TradingView fails
        const USE_CHARTJS_FALLBACK = typeof LightweightCharts === 'undefined';
        if (USE_CHARTJS_FALLBACK) {
            console.log('Using Chart.js fallback');
        }
    </script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #00ff41, #0099ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            color: #cccccc;
            font-size: 1.1rem;
        }
        
        .controls {
            display: flex;
            justify-content: center;
            gap: 20px;
            padding: 20px;
            flex-wrap: wrap;
            background: rgba(255, 255, 255, 0.05);
        }
        
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
            align-items: center;
        }
        
        .control-group label {
            font-weight: 600;
            color: #cccccc;
            font-size: 0.9rem;
        }
        
        .legend-panel {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .legend-title {
            font-size: 1rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding-bottom: 5px;
        }
        
        .legend-items {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 8px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 5px;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        
        .legend-item:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .legend-checkbox {
            width: 16px;
            height: 16px;
            accent-color: #00ff41;
        }
        
        .legend-color {
            width: 16px;
            height: 3px;
            border-radius: 2px;
        }
        
        .legend-label {
            color: #ffffff;
            font-size: 0.85rem;
            flex: 1;
        }
        
        select, button {
            padding: 10px 15px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        select:hover, button:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: #00ff41;
        }
        
        .status {
            text-align: center;
            padding: 10px;
            margin: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
        }
        
        .status.connected {
            background-color: rgba(0, 255, 65, 0.2);
            border: 1px solid #00ff41;
            color: #00ff41;
        }
        
        .status.loading {
            background-color: rgba(255, 170, 0, 0.2);
            border: 1px solid #ffaa00;
            color: #ffaa00;
        }
        
        .status.error {
            background-color: rgba(255, 0, 0, 0.2);
            border: 1px solid #ff0000;
            color: #ff0000;
        }
        
        .charts-container {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .chart-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .chart-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #ffffff;
        }
        
        .chart-info {
            font-size: 0.9rem;
            color: #888888;
        }
        
        .main-chart {
            height: 500px;
            margin-bottom: 10px;
        }
        
        .volume-chart {
            height: 150px;
            margin-bottom: 20px;
        }
        
        .indicators-chart {
            height: 200px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .metric-label {
            font-size: 0.8rem;
            color: #cccccc;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-value {
            font-size: 1.3rem;
            font-weight: 600;
            color: #ffffff;
        }
        
        .predictions-overlay {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            max-width: 300px;
        }
        
        .prediction-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }
        
        .buy-signal { color: #00ff41; }
        .sell-signal { color: #ff4444; }
        .hold-signal { color: #ffaa00; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 Enhanced Trading Dashboard</h1>
        <p>Professional-grade financial charting with real-time indicators</p>
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
            </select>
        </div>
        <div class="control-group">
            <label>Timeframe:</label>
            <select id="timeRange">
                <option value="0.0167">1 Minute</option>
                <option value="0.25">15 Minutes</option>
                <option value="1">1 Hour</option>
                <option value="4" selected>4 Hours</option>
                <option value="24">1 Day</option>
                <option value="168">7 Days</option>
            </select>
        </div>
        <div class="control-group">
            <label>Chart Type:</label>
            <select id="chartType">
                <option value="candlestick" selected>Candlestick</option>
                <option value="line">Line</option>
                <option value="area">Area</option>
            </select>
        </div>
        <div class="control-group">
            <button onclick="refreshData()">🔄 Refresh</button>
            <button onclick="toggleAutoRefresh()" id="autoRefreshBtn">▶️ Auto Refresh</button>
        </div>
    </div>

    <div id="status" class="status loading">Initializing dashboard...</div>

    <div class="legend-panel">
        <div class="legend-title">📊 Chart Elements</div>
        <div class="legend-items">
            <div class="legend-item">
                <input type="checkbox" id="showCandlesticks" class="legend-checkbox" checked>
                <div class="legend-color" style="background: linear-gradient(to right, #00ff41, #ff4444);"></div>
                <label for="showCandlesticks" class="legend-label">Price Data</label>
            </div>
            <div class="legend-item">
                <input type="checkbox" id="showVolume" class="legend-checkbox" checked>
                <div class="legend-color" style="background: rgba(0, 255, 65, 0.6);"></div>
                <label for="showVolume" class="legend-label">Volume</label>
            </div>
            <div class="legend-item">
                <input type="checkbox" id="showPredictions" class="legend-checkbox" checked>
                <div class="legend-color" style="background: #00ff41;"></div>
                <label for="showPredictions" class="legend-label">ML Predictions</label>
            </div>
            <div class="legend-item">
                <input type="checkbox" id="showRSI" class="legend-checkbox" checked>
                <div class="legend-color" style="background: #ff6b35;"></div>
                <label for="showRSI" class="legend-label">RSI Technical</label>
            </div>
            <div class="legend-item">
                <input type="checkbox" id="showMACD" class="legend-checkbox" checked>
                <div class="legend-color" style="background: #4fc3f7;"></div>
                <label for="showMACD" class="legend-label">MACD Technical</label>
            </div>
            <div class="legend-item">
                <input type="checkbox" id="showSentiment" class="legend-checkbox" checked>
                <div class="legend-color" style="background: #ab47bc;"></div>
                <label for="showSentiment" class="legend-label">News Sentiment</label>
            </div>
            <div class="legend-item">
                <input type="checkbox" id="showMLConfidence" class="legend-checkbox" checked>
                <div class="legend-color" style="background: #ffc107;"></div>
                <label for="showMLConfidence" class="legend-label">ML Confidence</label>
            </div>
            <div class="legend-item">
                <input type="checkbox" id="showMovingAvg" class="legend-checkbox" checked>
                <div class="legend-color" style="background: #26a69a;"></div>
                <label for="showMovingAvg" class="legend-label">Moving Averages</label>
            </div>
        </div>
    </div>

    <div class="charts-container">
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title" id="chartTitle">Loading...</div>
                <div class="chart-info" id="chartInfo">Preparing data...</div>
            </div>
            <div class="metrics-grid" id="metricsGrid"></div>
            <div id="mainChart" class="main-chart"></div>
            <div id="volumeChart" class="volume-chart"></div>
        </div>
        
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title">Technical Indicators</div>
                <div class="chart-info">RSI & MACD</div>
            </div>
            <div id="indicatorsChart" class="indicators-chart"></div>
        </div>
    </div>

    <script>
        let mainChart = null;
        let volumeChart = null;
        let indicatorsChart = null;
        let candlestickSeries = null;
        let volumeSeries = null;
        let rsiSeries = null;
        let rsiRef70Series = null;
        let rsiRef30Series = null;
        let macdSeries = null;
        let sma20Series = null;
        let sma50Series = null;
        let sentimentSeries = null;
        let confidenceSeries = null;
        let autoRefreshInterval = null;
        let isAutoRefreshing = false;
        let currentData = null;
        
        // Legend state management
        let legendState = {
            showCandlesticks: true,
            showVolume: true,
            showPredictions: true,
            showRSI: true,
            showMACD: true,
            showSentiment: true,
            showMLConfidence: true,
            showMovingAvg: true
        };
        
        // Initialize legend event handlers
        function initializeLegend() {
            const checkboxes = document.querySelectorAll('.legend-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const key = this.id.replace('show', 'show');
                    legendState[key] = this.checked;
                    updateChartsVisibility();
                });
            });
        }
        
        function updateChartsVisibility() {
            if (!currentData) return;
            
            // Update main chart elements
            if (candlestickSeries && legendState.showCandlesticks) {
                // Candlesticks are handled by chart type
            }
            
            // Update volume chart visibility
            if (volumeChart && volumeSeries) {
                volumeChart.timeScale().setVisibleLogicalRange(null);
            }
            
            // Update technical indicators
            if (rsiSeries) {
                // RSI visibility handled by separate chart
            }
            
            // Re-plot charts with current visibility settings
            plotCharts(currentData, document.getElementById('symbolSelect').value);
        }

        // Initialize charts
        function initializeCharts() {
            // Check if LightweightCharts is available
            if (typeof LightweightCharts === 'undefined') {
                console.error('LightweightCharts library not loaded');
                updateStatus('Error: Chart library not loaded', 'error');
                return;
            }
            
            console.log('Initializing charts with LightweightCharts:', typeof LightweightCharts);
            
            try {
                // Main price chart
                mainChart = LightweightCharts.createChart(document.getElementById('mainChart'), {
                    width: document.getElementById('mainChart').clientWidth,
                    height: 500,
                    layout: {
                        background: {
                            type: 'solid',
                            color: 'transparent',
                        },
                        textColor: '#ffffff',
                    },
                    grid: {
                        vertLines: {
                            color: 'rgba(255, 255, 255, 0.1)',
                        },
                        horzLines: {
                            color: 'rgba(255, 255, 255, 0.1)',
                        },
                    },
                    crosshair: {
                        mode: LightweightCharts.CrosshairMode.Normal,
                    },
                    rightPriceScale: {
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        textColor: '#ffffff',
                    },
                    timeScale: {
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        textColor: '#ffffff',
                    },
                });

                // Volume chart
                volumeChart = LightweightCharts.createChart(document.getElementById('volumeChart'), {
                    width: document.getElementById('volumeChart').clientWidth,
                    height: 150,
                    layout: {
                        background: {
                            type: 'solid',
                            color: 'transparent',
                        },
                        textColor: '#ffffff',
                    },
                    grid: {
                        vertLines: {
                            color: 'rgba(255, 255, 255, 0.1)',
                        },
                        horzLines: {
                            color: 'rgba(255, 255, 255, 0.1)',
                        },
                    },
                    rightPriceScale: {
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        textColor: '#ffffff',
                    },
                    timeScale: {
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        textColor: '#ffffff',
                    },
                });

                // Indicators chart
                indicatorsChart = LightweightCharts.createChart(document.getElementById('indicatorsChart'), {
                    width: document.getElementById('indicatorsChart').clientWidth,
                    height: 200,
                    layout: {
                        background: {
                            type: 'solid',
                            color: 'transparent',
                        },
                        textColor: '#ffffff',
                    },
                    grid: {
                        vertLines: {
                            color: 'rgba(255, 255, 255, 0.1)',
                        },
                        horzLines: {
                            color: 'rgba(255, 255, 255, 0.1)',
                        },
                    },
                    rightPriceScale: {
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        textColor: '#ffffff',
                    },
                    timeScale: {
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        textColor: '#ffffff',
                    },
                });

                console.log('Charts initialized successfully');
                updateStatus('Charts initialized', 'connected');
                
                // Initialize legend controls
                initializeLegend();
                
            } catch (error) {
                console.error('Error initializing charts:', error);
                updateStatus('Chart initialization failed', 'error');
            }

            // Handle window resize
            window.addEventListener('resize', () => {
                if (mainChart && volumeChart && indicatorsChart) {
                    const containerWidth = document.getElementById('mainChart').clientWidth;
                    mainChart.applyOptions({ width: containerWidth });
                    volumeChart.applyOptions({ width: containerWidth });
                    indicatorsChart.applyOptions({ width: containerWidth });
                }
            });
        }

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
                
                // Ensure charts are initialized
                if (!mainChart || !volumeChart || !indicatorsChart) {
                    console.warn('Charts not initialized, reinitializing...');
                    initializeCharts();
                    await new Promise(resolve => setTimeout(resolve, 100)); // Small delay for initialization
                }
                
                // Load both candlestick and indicator data
                const [candlestickResponse, indicatorResponse] = await Promise.all([
                    fetch(`/api/candlestick/${symbol}?hours=${hours}`),
                    fetch(`/api/symbol/${symbol}?hours=${hours}`)
                ]);
                
                if (!candlestickResponse.ok || !indicatorResponse.ok) {
                    throw new Error(`HTTP Error: ${candlestickResponse.status} / ${indicatorResponse.status}`);
                }
                
                const candlestickData = await candlestickResponse.json();
                const indicatorData = await indicatorResponse.json();
                
                if (candlestickData.error || indicatorData.error) {
                    throw new Error(candlestickData.error || indicatorData.error);
                }
                
                console.log('Data loaded:', {
                    candlestick: candlestickData.data_points,
                    indicators: indicatorData.data_points
                });
                
                updateChartTitle(symbol, candlestickData.data_points, hours);
                updateMetrics(indicatorData.metrics || {});
                
                // Plot charts with error handling
                try {
                    plotMainChart(candlestickData, symbol);
                } catch (error) {
                    console.error('Error plotting main chart:', error);
                }
                
                try {
                    plotVolumeChart(candlestickData, symbol);
                } catch (error) {
                    console.error('Error plotting volume chart:', error);
                }
                
                try {
                    plotIndicatorsChart(indicatorData, symbol);
                } catch (error) {
                    console.error('Error plotting indicators chart:', error);
                }
                
                updateStatus(`Last updated: ${formatTimestamp(new Date())}`, 'connected');
            } catch (error) {
                console.error('Error loading data:', error);
                updateStatus(`Error: ${error.message}`, 'error');
            }
        }

        function updateChartTitle(symbol, dataPoints, hours) {
            document.getElementById('chartTitle').textContent = `${symbol} Price Chart`;
            document.getElementById('chartInfo').textContent = `${dataPoints} data points (${hours}h timeframe)`;
        }

        function updateMetrics(metrics) {
            const grid = document.getElementById('metricsGrid');
            grid.innerHTML = '';
            
            Object.entries(metrics).forEach(([key, value]) => {
                const card = document.createElement('div');
                card.className = 'metric-card';
                
                let displayValue = value;
                if (typeof value === 'number') {
                    displayValue = value.toFixed(3);
                }
                
                card.innerHTML = `
                    <div class="metric-label">${key.replace(/_/g, ' ').toUpperCase()}</div>
                    <div class="metric-value">${displayValue}</div>
                `;
                grid.appendChild(card);
            });
        }

        function plotMainChart(data, symbol) {
            if (!mainChart) {
                console.error('Main chart not initialized');
                return;
            }
            
            // Clear existing series
            if (candlestickSeries) {
                try {
                    mainChart.removeSeries(candlestickSeries);
                } catch (error) {
                    console.warn('Error removing series:', error);
                }
                candlestickSeries = null;
            }
            
            const chartType = document.getElementById('chartType').value;
            
            try {
                if (chartType === 'candlestick' && data.candlestick_data && data.candlestick_data.length > 0) {
                    // Try modern API first (v4.0+)
                    try {
                        candlestickSeries = mainChart.addCandlestickSeries({
                            upColor: '#00ff41',
                            downColor: '#ff4444',
                            borderDownColor: '#ff4444',
                            borderUpColor: '#00ff41',
                            wickDownColor: '#ff4444',
                            wickUpColor: '#00ff41',
                        });
                        candlestickSeries.setData(data.candlestick_data);
                    } catch (error) {
                        console.warn('Standard candlestick API failed, trying alternative approach:', error);
                        throw new Error('Candlestick not supported');
                    }
                } else {
                    throw new Error('Using line chart fallback');
                }
            } catch (error) {
                console.log('Falling back to line chart:', error.message);
                // Use line chart as fallback
                candlestickSeries = mainChart.addLineSeries({
                    color: '#00ff41',
                    lineWidth: 2,
                });
                
                if (data.line_data && data.line_data.length > 0) {
                    // Filter valid line data
                    const validLineData = data.line_data.filter(item => 
                        item && 
                        item.time !== null && item.time !== undefined &&
                        item.value !== null && item.value !== undefined && 
                        !isNaN(item.value)
                    );
                    if (validLineData.length > 0) {
                        candlestickSeries.setData(validLineData);
                    }
                } else if (data.candlestick_data && data.candlestick_data.length > 0) {
                    // Convert candlestick to line data and validate
                    const lineData = data.candlestick_data
                        .filter(candle => 
                            candle && 
                            candle.time !== null && candle.time !== undefined &&
                            candle.close !== null && candle.close !== undefined && 
                            !isNaN(candle.close)
                        )
                        .map(candle => ({
                            time: candle.time,
                            value: candle.close
                        }));
                    if (lineData.length > 0) {
                        candlestickSeries.setData(lineData);
                    }
                }
            }
            
            // Add prediction markers
            if (data.predictions && data.predictions.length > 0) {
                try {
                    console.log('Processing prediction markers:', data.predictions.length);
                    
                    const validPredictions = data.predictions.filter(pred => {
                        const isValid = pred &&
                            pred.time !== null && pred.time !== undefined &&
                            pred.color !== null && pred.color !== undefined &&
                            pred.shape !== null && pred.shape !== undefined;
                        
                        if (!isValid) {
                            console.warn('Invalid prediction marker:', pred);
                        }
                        return isValid;
                    });
                    
                    if (validPredictions.length > 0) {
                        console.log('Setting markers on chart:', validPredictions.length);
                        
                        // Map the prediction data to TradingView marker format
                        const markers = validPredictions.map(pred => ({
                            time: pred.time,
                            position: pred.position || 'aboveBar',
                            color: pred.color,
                            shape: pred.shape,
                            text: pred.text || 'Prediction',
                            size: pred.size || 1.0
                        }));
                        
                        candlestickSeries.setMarkers(markers);
                        console.log('✅ Markers set successfully:', markers.length);
                    } else {
                        console.warn('No valid prediction markers found');
                    }
                } catch (error) {
                    console.error('Error setting markers:', error);
                }
            } else {
                console.log('No prediction data available');
            }
        }

        function plotVolumeChart(data, symbol) {
            if (!volumeChart) {
                console.error('Volume chart not initialized');
                return;
            }
            
            // Clear existing series properly
            if (volumeSeries) {
                try {
                    volumeChart.removeSeries(volumeSeries);
                } catch (error) {
                    console.warn('Error removing volume series:', error);
                }
                volumeSeries = null;
            }
            
            if (data.volume_data && data.volume_data.length > 0) {
                try {
                    // Try standard API for volume histogram
                    volumeSeries = volumeChart.addHistogramSeries({
                        color: 'rgba(0, 255, 65, 0.6)',
                        priceFormat: {
                            type: 'volume',
                        },
                        priceScaleId: '',
                    });
                    
                    // Filter and validate volume data
                    const validVolumeData = data.volume_data.filter(item => 
                        item && 
                        item.time !== null && item.time !== undefined &&
                        item.value !== null && item.value !== undefined && 
                        !isNaN(item.value) && 
                        item.value > 0
                    );
                    
                    if (validVolumeData.length > 0) {
                        volumeSeries.setData(validVolumeData);
                    }
                } catch (error) {
                    console.error('Error creating volume chart:', error);
                }
            }
        }

        function plotIndicatorsChart(data, symbol) {
            if (!indicatorsChart) {
                console.error('Indicators chart not initialized');
                return;
            }
            
            // Clear existing series properly with better error handling
            try {
                if (rsiSeries && typeof rsiSeries === 'object') {
                    try {
                        indicatorsChart.removeSeries(rsiSeries);
                    } catch (e) {
                        console.warn('Error removing RSI series:', e);
                    }
                    rsiSeries = null;
                }
                if (rsiRef70Series && typeof rsiRef70Series === 'object') {
                    try {
                        indicatorsChart.removeSeries(rsiRef70Series);
                    } catch (e) {
                        console.warn('Error removing RSI 70 ref series:', e);
                    }
                    rsiRef70Series = null;
                }
                if (rsiRef30Series && typeof rsiRef30Series === 'object') {
                    try {
                        indicatorsChart.removeSeries(rsiRef30Series);
                    } catch (e) {
                        console.warn('Error removing RSI 30 ref series:', e);
                    }
                    rsiRef30Series = null;
                }
            } catch (error) {
                console.warn('Error during series cleanup:', error);
                // Reset all series variables
                rsiSeries = null;
                rsiRef70Series = null;
                rsiRef30Series = null;
            }
            
            // Validate input data
            if (!data || !data.technical_data || !data.technical_data.rsi_values || !Array.isArray(data.technical_data.rsi_values)) {
                console.warn('Invalid technical data format for indicators');
                return;
            }
            
            // Add RSI line
            if (data.technical_data.rsi_values.length > 0) {
                try {
                    rsiSeries = indicatorsChart.addLineSeries({
                        color: '#0099ff',
                        lineWidth: 2,
                        priceScaleId: 'rsi',
                    });
                    
                    // Filter and prepare RSI data with stricter validation
                    const rsiData = data.technical_data.timestamps
                        .map((time, i) => ({
                            time: time,
                            value: data.technical_data.rsi_values[i]
                        }))
                        .filter(point => {
                            // More thorough validation
                            if (!point || point.time === null || point.time === undefined) return false;
                            if (point.value === null || point.value === undefined || isNaN(point.value)) return false;
                            if (point.value < 0 || point.value > 100) return false; // RSI range check
                            return true;
                        });
                    
                    console.log('RSI data points:', rsiData.length, 'of', data.technical_data.rsi_values.length);
                    
                    if (rsiData.length > 0) {
                        rsiSeries.setData(rsiData);
                        
                        // Add RSI reference lines
                        rsiRef70Series = indicatorsChart.addLineSeries({
                            color: '#ff4444',
                            lineWidth: 1,
                            lineStyle: LightweightCharts.LineStyle.Dashed,
                            priceScaleId: 'rsi',
                        });
                        rsiRef30Series = indicatorsChart.addLineSeries({
                            color: '#00ff41',
                            lineWidth: 1,
                            lineStyle: LightweightCharts.LineStyle.Dashed,
                            priceScaleId: 'rsi',
                        });
                        
                        // Set reference line data
                        const refData70 = rsiData.map(d => ({ time: d.time, value: 70 }));
                        const refData30 = rsiData.map(d => ({ time: d.time, value: 30 }));
                        
                        if (rsiRef70Series) rsiRef70Series.setData(refData70);
                        if (rsiRef30Series) rsiRef30Series.setData(refData30);
                    } else {
                        console.warn('No valid RSI data points after filtering');
                    }
                } catch (error) {
                    console.error('Error creating RSI indicators:', error);
                    // Clean up on error
                    rsiSeries = null;
                    rsiRef70Series = null;
                    rsiRef30Series = null;
                }
            }
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
                btn.style.background = 'rgba(255, 255, 255, 0.1)';
                isAutoRefreshing = false;
            } else {
                autoRefreshInterval = setInterval(refreshData, 30000); // 30 seconds
                btn.textContent = '⏸️ Stop Auto';
                btn.style.background = 'rgba(0, 255, 65, 0.2)';
                isAutoRefreshing = true;
            }
        }

        // Event listeners
        document.getElementById('symbolSelect').addEventListener('change', refreshData);
        document.getElementById('timeRange').addEventListener('change', refreshData);
        document.getElementById('chartType').addEventListener('change', refreshData);

        // Initialize dashboard
        function initializeDashboard() {
            // Try TradingView first, fallback to Chart.js
            if (typeof LightweightCharts !== 'undefined') {
                console.log('Using TradingView Lightweight Charts');
                initializeCharts();
            } else {
                console.log('TradingView not available, using Chart.js fallback');
                initializeChartJSFallback();
            }
            loadSymbolData();
        }

        function initializeChartJSFallback() {
            // Create Chart.js charts as fallback
            const mainCtx = document.createElement('canvas');
            document.getElementById('mainChart').appendChild(mainCtx);
            
            const volumeCtx = document.createElement('canvas');
            document.getElementById('volumeChart').appendChild(volumeCtx);
            
            const indicatorsCtx = document.createElement('canvas');
            document.getElementById('indicatorsChart').appendChild(indicatorsCtx);
            
            updateStatus('Using Chart.js fallback', 'connected');
        }

        // Initialize dashboard
        initializeCharts();
        loadSymbolData();
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def get_historical_price_data(self, symbol, hours):
        """Fetch real historical price data from yfinance with multiple intervals"""
        try:
            if YFINANCE_AVAILABLE:
                # Use yfinance for ASX data
                ticker = symbol.replace('.AX', '') + '.AX' if not symbol.endswith('.AX') else symbol
                stock = yf.Ticker(ticker)
                
                # Determine the best interval based on timeframe
                if hours <= 0.5:  # 30 minutes or less
                    interval = "1m"
                    period = "1d"  # 1 minute data for 1 day
                elif hours <= 4:  # 4 hours or less
                    interval = "5m"
                    period = "5d"  # 5 minute data for 5 days
                elif hours <= 24:  # 1 day or less
                    interval = "15m"
                    period = "7d"  # 15 minute data for 7 days
                elif hours <= 168:  # 1 week or less
                    interval = "1h"
                    period = "30d"  # 1 hour data for 30 days
                else:
                    interval = "1d"
                    period = "1y"  # Daily data for 1 year
                
                print(f"📊 Fetching {interval} data for {ticker} (period: {period})")
                
                # Get historical data
                hist = stock.history(period=period, interval=interval)
                
                if hist.empty:
                    print(f"No {interval} yfinance data for {ticker}, trying daily fallback")
                    hist = stock.history(period="30d", interval="1d")
                
                if not hist.empty:
                    candlestick_data = []
                    volume_data = []
                    
                    for timestamp, row in hist.iterrows():
                        unix_time = int(timestamp.timestamp())
                        
                        # Validate OHLCV data
                        if (not math.isnan(row['Open']) and not math.isnan(row['High']) and 
                            not math.isnan(row['Low']) and not math.isnan(row['Close']) and
                            row['Open'] > 0 and row['High'] > 0 and row['Low'] > 0 and row['Close'] > 0):
                            
                            candlestick_data.append({
                                'time': unix_time,
                                'open': round(float(row['Open']), 4),
                                'high': round(float(row['High']), 4),
                                'low': round(float(row['Low']), 4),
                                'close': round(float(row['Close']), 4)
                            })
                            
                            volume_data.append({
                                'time': unix_time,
                                'value': float(row['Volume']) if not math.isnan(row['Volume']) else 0,
                                'color': '#00ff41' if len(candlestick_data) == 1 or row['Close'] >= row['Open'] else '#ff4444'
                            })
                    
                    print(f"✅ Retrieved {len(candlestick_data)} real {interval} price points for {symbol}")
                    return candlestick_data, volume_data
            
            # Fallback: generate sample data based on latest prediction data
            print(f"Using sample data for {symbol} (yfinance not available)")
            return self.generate_sample_candlestick_data(symbol, max(1, int(hours / 24)))
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return self.generate_sample_candlestick_data(symbol, max(1, int(hours / 24)))

    def generate_sample_candlestick_data(self, symbol, days):
        """Generate sample candlestick data when real data is unavailable"""
        conn = sqlite3.connect('trading_predictions.db')
        try:
            # Get latest prediction data for baseline price
            query = """
            SELECT current_price, timestamp
            FROM enhanced_features 
            WHERE symbol = ?
            ORDER BY timestamp DESC LIMIT 1
            """
            
            cursor = conn.execute(query, (symbol,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                # Use default price if no data
                base_price = 35.0 if 'WBC' in symbol else 30.0
                start_time = datetime.now() - timedelta(days=days)
            else:
                base_price = float(result[0]) if result[0] and result[0] > 0 else 30.0
                start_time = datetime.now() - timedelta(days=days)
            
            candlestick_data = []
            volume_data = []
            
            # Generate hourly sample data
            current_time = start_time
            current_price = base_price
            
            for i in range(days * 24):  # Hourly data for specified days
                unix_time = int(current_time.timestamp())
                
                # Simulate realistic price movement
                price_change = (hash(str(unix_time)) % 200 - 100) / 10000  # Random-ish movement
                current_price *= (1 + price_change)
                current_price = max(current_price, base_price * 0.8)  # Floor
                current_price = min(current_price, base_price * 1.2)  # Ceiling
                
                # Generate OHLC from current price with realistic spread
                variation = current_price * 0.005  # 0.5% variation
                open_price = current_price + (hash(str(unix_time + 1)) % 100 - 50) / 100000
                close_price = current_price + (hash(str(unix_time + 2)) % 100 - 50) / 100000
                high_price = max(open_price, close_price) + abs(hash(str(unix_time + 3)) % 50) / 100000
                low_price = min(open_price, close_price) - abs(hash(str(unix_time + 4)) % 50) / 100000
                
                candlestick_data.append({
                    'time': unix_time,
                    'open': round(open_price, 4),
                    'high': round(high_price, 4),
                    'low': round(low_price, 4),
                    'close': round(close_price, 4)
                })
                
                volume_data.append({
                    'time': unix_time,
                    'value': abs(hash(str(unix_time + 5)) % 1000000)  # Sample volume
                })
                
                current_time += timedelta(hours=1)
            
            return candlestick_data, volume_data
            
        finally:
            conn.close()

    def get_prediction_markers(self, symbol, hours):
        """Get prediction data to overlay as markers on the chart"""
        conn = sqlite3.connect('trading_predictions.db')
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get predictions with associated technical data
            query = """
            SELECT 
                p.prediction_timestamp,
                p.predicted_action,
                p.action_confidence,
                p.entry_price,
                ef.current_price,
                ef.rsi,
                ef.macd_line,
                ef.sentiment_score,
                ef.volume_ratio,
                ef.confidence
            FROM predictions p
            LEFT JOIN enhanced_features ef ON p.symbol = ef.symbol 
                AND datetime(p.prediction_timestamp) = datetime(ef.timestamp)
            WHERE p.symbol = ? AND p.prediction_timestamp >= ?
            ORDER BY p.prediction_timestamp ASC
            """
            
            cursor = conn.execute(query, (symbol, start_time.isoformat()))
            predictions = cursor.fetchall()
            
            print(f"🔍 Query returned {len(predictions)} predictions for {symbol}")
            if predictions:
                print(f"📊 Sample prediction: {predictions[0]}")
            
            markers = []
            technical_data = {
                'timestamps': [],
                'rsi_values': [],
                'macd_values': [],
                'sentiment_scores': []
            }
            
            for pred in predictions:
                try:
                    timestamp, action, confidence, entry_price, current_price, rsi, macd, sentiment, volume_ratio, ef_confidence = pred
                    
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    unix_time = int(dt.timestamp())
                    
                    # Create prediction marker with more robust formatting
                    marker_color = '#00ff41' if action == 'BUY' else '#ff4444' if action == 'SELL' else '#ffaa00'
                    marker_shape = 'arrowUp' if action == 'BUY' else 'arrowDown' if action == 'SELL' else 'circle'
                    
                    confidence_val = confidence if confidence else ef_confidence if ef_confidence else 0.5
                    
                    marker = {
                        'time': unix_time,
                        'position': 'aboveBar' if action == 'BUY' else 'belowBar',
                        'color': marker_color,
                        'shape': marker_shape,
                        'text': f"{action} {confidence_val:.2f}" if confidence_val else action,
                        'size': max(0.8, min(2.0, confidence_val * 2)) if confidence_val else 1.0
                    }
                    
                    markers.append(marker)
                    print(f"📍 Added marker: {action} at {unix_time} with confidence {confidence_val}")
                    
                    # Collect technical data for overlay charts
                    if rsi is not None:
                        technical_data['timestamps'].append(timestamp)
                        technical_data['rsi_values'].append(float(rsi))
                        technical_data['macd_values'].append(float(macd) if macd else 0)
                        technical_data['sentiment_scores'].append(float(sentiment) if sentiment else 0)
                
                except Exception as e:
                    print(f"Error processing prediction marker: {e}")
                    continue
            
            return markers, technical_data
            
        finally:
            conn.close()

    def generate_technical_analysis(self, candlestick_data, technical_data):
        """Generate comprehensive technical analysis overlays"""
        try:
            analysis = {
                'rsi_data': [],
                'macd_data': [],
                'sma_data': [],
                'sentiment_data': [],
                'confidence_data': []
            }
            
            if not candlestick_data:
                return analysis
            
            # Generate RSI overlay from existing technical data or calculate from prices
            if technical_data['timestamps'] and technical_data['rsi_values']:
                for i, timestamp in enumerate(technical_data['timestamps']):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        unix_time = int(dt.timestamp())
                        if i < len(technical_data['rsi_values']):
                            analysis['rsi_data'].append({
                                'time': unix_time,
                                'value': technical_data['rsi_values'][i]
                            })
                    except:
                        continue
            else:
                # Calculate simple RSI from price data
                analysis['rsi_data'] = self.calculate_rsi_from_prices(candlestick_data)
            
            # Generate MACD overlay
            if technical_data['timestamps'] and technical_data['macd_values']:
                for i, timestamp in enumerate(technical_data['timestamps']):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        unix_time = int(dt.timestamp())
                        if i < len(technical_data['macd_values']):
                            analysis['macd_data'].append({
                                'time': unix_time,
                                'value': technical_data['macd_values'][i],
                                'signal': technical_data['macd_values'][i] * 0.9  # Simple signal line
                            })
                    except:
                        continue
            else:
                # Calculate MACD from price data
                analysis['macd_data'] = self.calculate_macd_from_prices(candlestick_data)
            
            # Generate Moving Averages overlay
            analysis['sma_data'] = self.calculate_moving_averages(candlestick_data)
            
            # Generate Sentiment overlay
            if technical_data['timestamps'] and technical_data['sentiment_scores']:
                for i, timestamp in enumerate(technical_data['timestamps']):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        unix_time = int(dt.timestamp())
                        if i < len(technical_data['sentiment_scores']):
                            # Normalize sentiment to 0-100 scale for visualization
                            sentiment_normalized = (technical_data['sentiment_scores'][i] + 1) * 50
                            analysis['sentiment_data'].append({
                                'time': unix_time,
                                'value': max(0, min(100, sentiment_normalized))
                            })
                    except:
                        continue
            
            # Generate ML Confidence overlay (dummy data for now)
            analysis['confidence_data'] = self.generate_confidence_overlay(candlestick_data)
            
            return analysis
            
        except Exception as e:
            print(f"Error generating technical analysis: {e}")
            return {
                'rsi_data': [],
                'macd_data': [],
                'sma_data': [],
                'sentiment_data': [],
                'confidence_data': []
            }

    def calculate_rsi_from_prices(self, candlestick_data, period=14):
        """Calculate RSI from price data"""
        if len(candlestick_data) < period + 1:
            return []
        
        rsi_data = []
        gains = []
        losses = []
        
        # Calculate price changes
        for i in range(1, len(candlestick_data)):
            change = candlestick_data[i]['close'] - candlestick_data[i-1]['close']
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        
        # Calculate RSI
        for i in range(period - 1, len(gains)):
            avg_gain = sum(gains[i-period+1:i+1]) / period
            avg_loss = sum(losses[i-period+1:i+1]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_data.append({
                'time': candlestick_data[i+1]['time'],
                'value': round(rsi, 2)
            })
        
        return rsi_data

    def calculate_macd_from_prices(self, candlestick_data):
        """Calculate MACD from price data"""
        if len(candlestick_data) < 26:
            return []
        
        macd_data = []
        closes = [candle['close'] for candle in candlestick_data]
        
        # Simple MACD calculation (EMA12 - EMA26)
        for i in range(25, len(closes)):
            ema12 = sum(closes[i-11:i+1]) / 12  # Simplified EMA
            ema26 = sum(closes[i-25:i+1]) / 26  # Simplified EMA
            macd = ema12 - ema26
            
            macd_data.append({
                'time': candlestick_data[i]['time'],
                'value': round(macd, 4),
                'signal': round(macd * 0.9, 4)  # Simple signal line
            })
        
        return macd_data

    def calculate_moving_averages(self, candlestick_data):
        """Calculate moving averages"""
        if len(candlestick_data) < 50:
            return []
        
        sma_data = []
        closes = [candle['close'] for candle in candlestick_data]
        
        for i in range(49, len(closes)):
            sma20 = sum(closes[i-19:i+1]) / 20
            sma50 = sum(closes[i-49:i+1]) / 50
            
            sma_data.append({
                'time': candlestick_data[i]['time'],
                'sma20': round(sma20, 4),
                'sma50': round(sma50, 4)
            })
        
        return sma_data

    def generate_confidence_overlay(self, candlestick_data):
        """Generate ML confidence overlay data"""
        confidence_data = []
        
        for i, candle in enumerate(candlestick_data):
            # Generate pseudo-confidence based on volatility
            if i > 0:
                volatility = abs(candle['close'] - candlestick_data[i-1]['close']) / candlestick_data[i-1]['close']
                confidence = max(0.3, min(1.0, 1.0 - volatility * 10))  # Inverse of volatility
            else:
                confidence = 0.7
            
            confidence_data.append({
                'time': candle['time'],
                'value': round(confidence * 100, 1)  # Convert to percentage
            })
        
        return confidence_data

    def get_candlestick_data(self, symbol, hours):
        """Main function to get real historical price data with prediction overlays"""
        try:
            print(f"🔍 Fetching data for {symbol} ({hours} hours)")
            
            # Get real historical price data with proper timeframe
            candlestick_data, volume_data = self.get_historical_price_data(symbol, hours)
            
            # Get prediction markers and technical data
            markers, technical_data = self.get_prediction_markers(symbol, hours)
            print(f"📍 Found {len(markers)} prediction markers for {symbol}")
            
            # Debug: Print first few markers
            if markers:
                print(f"📍 Sample markers: {markers[:2]}")
            
            # Add a test marker to verify the system works
            if candlestick_data and len(candlestick_data) > 10:
                test_time = candlestick_data[len(candlestick_data)//2]['time']
                test_marker = {
                    'time': test_time,
                    'position': 'aboveBar',
                    'color': '#00ff41',
                    'shape': 'arrowUp',
                    'text': 'TEST MARKER',
                    'size': 1.5
                }
                markers.append(test_marker)
                print(f"📍 Added test marker at time {test_time}")
            
            # Filter data to requested timeframe
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            start_unix = int(start_time.timestamp())
            
            # Filter candlestick data
            candlestick_data = [d for d in candlestick_data if d['time'] >= start_unix]
            volume_data = [d for d in volume_data if d['time'] >= start_unix]
            
            # Create line data from candlestick close prices
            line_data = [{'time': d['time'], 'value': d['close']} for d in candlestick_data]
            
            # Generate RSI data for technical indicator overlay
            rsi_data = []
            if technical_data['timestamps'] and technical_data['rsi_values']:
                for i, timestamp in enumerate(technical_data['timestamps']):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        unix_time = int(dt.timestamp())
                        if unix_time >= start_unix and i < len(technical_data['rsi_values']):
                            rsi_data.append({
                                'time': unix_time,
                                'value': technical_data['rsi_values'][i]
                            })
                    except:
                        continue
            
            # Generate comprehensive technical analysis data
            technical_analysis_data = self.generate_technical_analysis(candlestick_data, technical_data)
            
            print(f"📊 Chart data prepared: {len(candlestick_data)} candles, {len(markers)} predictions")
            
            return {
                'symbol': symbol,
                'timeframe_hours': hours,
                'data_points': len(candlestick_data),
                'candlestick_data': candlestick_data,
                'line_data': line_data,
                'volume_data': volume_data,
                'rsi_data': technical_analysis_data.get('rsi_data', []),
                'macd_data': technical_analysis_data.get('macd_data', []),
                'sma_data': technical_analysis_data.get('sma_data', []),
                'sentiment_data': technical_analysis_data.get('sentiment_data', []),
                'confidence_data': technical_analysis_data.get('confidence_data', []),
                'predictions': markers,
                'technical_data': technical_data,
                'metrics': {
                    'current_price': candlestick_data[-1]['close'] if candlestick_data else 0,
                    'rsi': technical_data['rsi_values'][-1] if technical_data['rsi_values'] else 50,
                    'macd': technical_data['macd_values'][-1] if technical_data['macd_values'] else 0,
                    'sentiment': technical_data['sentiment_scores'][-1] if technical_data['sentiment_scores'] else 0,
                    'volume': volume_data[-1]['value'] if volume_data else 0
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating chart data for {symbol}: {e}")
            return {
                'symbol': symbol,
                'timeframe_hours': hours,
                'data_points': 0,
                'candlestick_data': [],
                'line_data': [],
                'volume_data': [],
                'rsi_data': [],
                'predictions': [],
                'technical_data': {'timestamps': [], 'rsi_values': [], 'macd_values': [], 'sentiment_scores': []},
                'metrics': {'current_price': 0, 'rsi': 50, 'macd': 0, 'sentiment': 0}
            }

    def get_enhanced_symbol_data(self, symbol, hours):
        """Get enhanced data for indicators and metrics"""
        conn = sqlite3.connect('trading_predictions.db')
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get technical indicators
            query = """
            SELECT 
                timestamp,
                current_price,
                sentiment_score,
                confidence,
                rsi,
                macd_line,
                macd_signal,
                volume_ratio,
                sma_20,
                sma_50
            FROM enhanced_features 
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp ASC
            """
            
            cursor = conn.execute(query, (symbol, start_time.isoformat()))
            data = cursor.fetchall()
            
            if not data:
                cursor = conn.execute("""
                    SELECT timestamp, current_price, sentiment_score, confidence, rsi, 
                           macd_line, macd_signal, volume_ratio, sma_20, sma_50
                    FROM enhanced_features 
                    WHERE symbol = ?
                    ORDER BY timestamp DESC LIMIT 10
                """, (symbol,))
                data = cursor.fetchall()
            
            # Process technical data
            timestamps = []
            rsi_values = []
            macd_values = []
            sentiment_scores = []
            
            for row in data:
                timestamp, price, sentiment, confidence, rsi, macd_line, macd_signal, volume_ratio, sma20, sma50 = row
                
                timestamps.append(timestamp)
                rsi_values.append(rsi if rsi is not None else 50)
                macd_values.append(macd_line if macd_line is not None else 0)
                sentiment_scores.append(sentiment if sentiment is not None else 0)
            
            # Calculate metrics
            latest = data[-1] if data else None
            metrics = {}
            
            if latest:
                _, price, sentiment, confidence, rsi, macd_line, macd_signal, volume_ratio, sma20, sma50 = latest
                metrics = {
                    'current_price': price,
                    'rsi': rsi,
                    'macd': macd_line,
                    'sentiment': sentiment,
                    'confidence': confidence,
                    'volume_ratio': volume_ratio,
                    'sma_20': sma20,
                    'sma_50': sma50
                }
            
            return {
                'symbol': symbol,
                'timeframe_hours': hours,
                'data_points': len(data),
                'metrics': metrics,
                'technical_data': {
                    'timestamps': timestamps,
                    'rsi_values': rsi_values,
                    'macd_values': macd_values,
                    'sentiment_scores': sentiment_scores
                }
            }
            
        finally:
            conn.close()

def start_enhanced_dashboard_server(port=8081):
    """Start the enhanced visualization dashboard server"""
    server = HTTPServer(('0.0.0.0', port), EnhancedTradingVisualizationHandler)
    print(f"🚀 Enhanced Trading Dashboard starting on port {port}")
    print(f"📊 Access dashboard at: http://localhost:{port}")
    print(f"🌐 Remote access at: http://YOUR_SERVER_IP:{port}")
    print("🎯 Features: TradingView charts, candlesticks, volume, indicators")
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
    
    start_enhanced_dashboard_server(8081)
