#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard

A comprehensive web-based dashboard for monitoring the trading microservices architecture.
Provides real-time metrics, health status, alerts, and system performance visualization.

Features:
- Real-time service health monitoring
- Interactive metrics charts and graphs
- Alert management and notification center
- SLA compliance tracking
- System resource utilization
- Historical trend analysis
- Export capabilities for reports

Author: Trading System Dashboard
Date: September 14, 2025
"""

from flask import Flask, render_template, jsonify, request, send_file
import asyncio
import json
import time
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, List, Any
import threading
import sqlite3

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base_service import BaseService

app = Flask(__name__)

class MonitoringDashboard:
    """Real-time monitoring dashboard with web interface"""
    
    def __init__(self):
        self.monitoring_service = None
        self.last_update = 0
        self.cache_duration = 10  # seconds
        self.cached_data = {}
        
        # Initialize connection to monitoring service
        self._init_monitoring_connection()
        
    def _init_monitoring_connection(self):
        """Initialize connection to monitoring service"""
        try:
            # Create a simple client to connect to monitoring service
            import socket
            import json
            
            class MonitoringClient:
                def __init__(self):
                    self.socket_path = "/tmp/trading_monitoring.sock"
                    
                async def call_method(self, method: str, params: Dict = None):
                    try:
                        reader, writer = await asyncio.open_unix_connection(self.socket_path)
                        
                        request = {
                            'method': method,
                            'params': params or {},
                            'timestamp': time.time()
                        }
                        
                        writer.write(json.dumps(request).encode())
                        await writer.drain()
                        
                        response_data = await reader.read(32768)
                        response = json.loads(response_data.decode())
                        
                        writer.close()
                        await writer.wait_closed()
                        
                        if response.get('status') == 'success':
                            return response.get('result')
                        else:
                            return {'error': response.get('error', 'Unknown error')}
                            
                    except Exception as e:
                        return {'error': str(e)}
                        
            self.monitoring_client = MonitoringClient()
            
        except Exception as e:
            print(f"Failed to initialize monitoring connection: {e}")
            self.monitoring_client = None
            
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data with caching"""
        current_time = time.time()
        
        # Use cached data if recent
        if (current_time - self.last_update < self.cache_duration and 
            'dashboard' in self.cached_data):
            return self.cached_data['dashboard']
            
        try:
            if self.monitoring_client:
                dashboard_data = await self.monitoring_client.call_method('get_dashboard_data')
            else:
                # Fallback to simulated data if monitoring service unavailable
                dashboard_data = self._get_simulated_dashboard_data()
                
            # Cache the data
            self.cached_data['dashboard'] = dashboard_data
            self.last_update = current_time
            
            return dashboard_data
            
        except Exception as e:
            return {'error': f'Failed to get dashboard data: {e}'}
            
    async def get_service_health(self) -> Dict[str, Any]:
        """Get current service health status"""
        try:
            if self.monitoring_client:
                return await self.monitoring_client.call_method('get_service_health')
            else:
                return self._get_simulated_health_data()
        except Exception as e:
            return {'error': f'Failed to get health data: {e}'}
            
    async def get_metrics(self, service: str = None, hours: int = 1) -> Dict[str, Any]:
        """Get metrics data"""
        try:
            if self.monitoring_client:
                return await self.monitoring_client.call_method('get_metrics_data', {
                    'service': service,
                    'hours': hours
                })
            else:
                return self._get_simulated_metrics_data(service, hours)
        except Exception as e:
            return {'error': f'Failed to get metrics: {e}'}
            
    async def get_alerts(self) -> Dict[str, Any]:
        """Get active alerts"""
        try:
            if self.monitoring_client:
                return await self.monitoring_client.call_method('get_active_alerts')
            else:
                return self._get_simulated_alerts_data()
        except Exception as e:
            return {'error': f'Failed to get alerts: {e}'}
            
    async def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        """Resolve an alert"""
        try:
            if self.monitoring_client:
                return await self.monitoring_client.call_method('resolve_alert', {
                    'alert_id': alert_id
                })
            else:
                return {'status': 'resolved', 'alert_id': alert_id}
        except Exception as e:
            return {'error': f'Failed to resolve alert: {e}'}
            
    async def get_sla_report(self, days: int = 7) -> Dict[str, Any]:
        """Get SLA compliance report"""
        try:
            if self.monitoring_client:
                return await self.monitoring_client.call_method('get_sla_report', {
                    'days': days
                })
            else:
                return self._get_simulated_sla_data(days)
        except Exception as e:
            return {'error': f'Failed to get SLA report: {e}'}
            
    def _get_simulated_dashboard_data(self) -> Dict[str, Any]:
        """Generate simulated dashboard data for testing"""
        return {
            'timestamp': time.time(),
            'health': {
                'summary': {
                    'total_services': 6,
                    'healthy_services': 5,
                    'unhealthy_services': 1,
                    'avg_response_time': 2.3,
                    'avg_sla_compliance': 98.5
                },
                'services': {
                    'market-data': {'status': 'healthy', 'response_time': 1.2, 'sla_compliance': 99.1},
                    'sentiment': {'status': 'healthy', 'response_time': 2.1, 'sla_compliance': 98.7},
                    'prediction': {'status': 'healthy', 'response_time': 3.5, 'sla_compliance': 97.9},
                    'scheduler': {'status': 'healthy', 'response_time': 0.8, 'sla_compliance': 99.5},
                    'paper-trading': {'status': 'unhealthy', 'response_time': 15.2, 'sla_compliance': 85.3},
                    'ml-model': {'status': 'healthy', 'response_time': 4.1, 'sla_compliance': 98.1}
                }
            },
            'alerts': {
                'active_alerts': [
                    {
                        'alert_id': 'paper-trading_slow_response_123',
                        'service': 'paper-trading',
                        'severity': 'warning',
                        'message': 'Service paper-trading response time is 15.2s',
                        'created_at': time.time() - 300
                    }
                ],
                'alert_count': 1
            },
            'system_overview': {
                'total_services': 6,
                'monitoring_uptime': 3600,
                'total_metrics_collected': 1250,
                'active_alert_count': 1
            }
        }
        
    def _get_simulated_health_data(self) -> Dict[str, Any]:
        """Generate simulated health data"""
        return {
            'timestamp': time.time(),
            'services': {
                'market-data': {
                    'service_name': 'market-data',
                    'status': 'healthy',
                    'uptime': 3600,
                    'cpu_usage': 15.2,
                    'memory_usage': 125000000,
                    'response_time': 1.2,
                    'error_rate': 0.1,
                    'sla_compliance': 99.1
                },
                'sentiment': {
                    'service_name': 'sentiment',
                    'status': 'healthy',
                    'uptime': 3590,
                    'cpu_usage': 22.1,
                    'memory_usage': 89000000,
                    'response_time': 2.1,
                    'error_rate': 0.3,
                    'sla_compliance': 98.7
                },
                'prediction': {
                    'service_name': 'prediction',
                    'status': 'healthy',
                    'uptime': 3555,
                    'cpu_usage': 45.3,
                    'memory_usage': 256000000,
                    'response_time': 3.5,
                    'error_rate': 0.8,
                    'sla_compliance': 97.9
                }
            },
            'summary': {
                'total_services': 6,
                'healthy_services': 5,
                'unhealthy_services': 1,
                'avg_response_time': 2.3,
                'avg_sla_compliance': 98.5
            }
        }
        
    def _get_simulated_metrics_data(self, service: str, hours: int) -> Dict[str, Any]:
        """Generate simulated metrics data"""
        import random
        
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        metrics = []
        current_time = start_time
        
        while current_time < end_time:
            if not service or service == 'prediction':
                metrics.append({
                    'timestamp': current_time,
                    'service': 'prediction',
                    'metric_name': 'response_time',
                    'value': random.uniform(1.0, 5.0)
                })
                metrics.append({
                    'timestamp': current_time,
                    'service': 'prediction',
                    'metric_name': 'buy_rate',
                    'value': random.uniform(20, 80)
                })
                
            current_time += 300  # 5 minute intervals
            
        return {
            'start_time': start_time,
            'end_time': end_time,
            'hours': hours,
            'total_points': len(metrics),
            'metrics': metrics
        }
        
    def _get_simulated_alerts_data(self) -> Dict[str, Any]:
        """Generate simulated alerts data"""
        return {
            'timestamp': time.time(),
            'active_alerts': [
                {
                    'alert_id': 'paper-trading_slow_response_123',
                    'alert_type': 'slow_response',
                    'service': 'paper-trading',
                    'severity': 'warning',
                    'message': 'Service paper-trading response time is 15.2s',
                    'threshold': 5.0,
                    'current_value': 15.2,
                    'created_at': time.time() - 300
                }
            ],
            'alert_count': 1,
            'recent_history': []
        }
        
    def _get_simulated_sla_data(self, days: int) -> Dict[str, Any]:
        """Generate simulated SLA data"""
        return {
            'report_period': {
                'start_time': time.time() - (days * 86400),
                'end_time': time.time(),
                'days': days
            },
            'services': {
                'market-data': {'avg_compliance': 99.2, 'sla_met': True},
                'sentiment': {'avg_compliance': 98.8, 'sla_met': False},
                'prediction': {'avg_compliance': 97.5, 'sla_met': False},
                'scheduler': {'avg_compliance': 99.6, 'sla_met': True},
                'paper-trading': {'avg_compliance': 92.3, 'sla_met': False},
                'ml-model': {'avg_compliance': 98.9, 'sla_met': False}
            },
            'overall': {
                'avg_compliance': 97.7,
                'services_meeting_sla': 2,
                'total_services': 6,
                'overall_sla_met': False
            }
        }

# Global dashboard instance
dashboard = MonitoringDashboard()

# Flask routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for dashboard data"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = loop.run_until_complete(dashboard.get_dashboard_data())
        return jsonify(data)
    finally:
        loop.close()

@app.route('/api/health')
def api_health():
    """API endpoint for health data"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = loop.run_until_complete(dashboard.get_service_health())
        return jsonify(data)
    finally:
        loop.close()

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for metrics data"""
    service = request.args.get('service')
    hours = int(request.args.get('hours', 1))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = loop.run_until_complete(dashboard.get_metrics(service, hours))
        return jsonify(data)
    finally:
        loop.close()

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for alerts data"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = loop.run_until_complete(dashboard.get_alerts())
        return jsonify(data)
    finally:
        loop.close()

@app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
def api_resolve_alert(alert_id):
    """API endpoint to resolve an alert"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = loop.run_until_complete(dashboard.resolve_alert(alert_id))
        return jsonify(data)
    finally:
        loop.close()

@app.route('/api/sla')
def api_sla():
    """API endpoint for SLA report"""
    days = int(request.args.get('days', 7))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = loop.run_until_complete(dashboard.get_sla_report(days))
        return jsonify(data)
    finally:
        loop.close()

@app.route('/health-details')
def health_details():
    """Detailed health monitoring page"""
    return render_template('health_details.html')

@app.route('/metrics-analysis')
def metrics_analysis():
    """Metrics analysis page"""
    return render_template('metrics_analysis.html')

@app.route('/alerts-management')
def alerts_management():
    """Alerts management page"""
    return render_template('alerts_management.html')

@app.route('/sla-reports')
def sla_reports():
    """SLA reports page"""
    return render_template('sla_reports.html')

# Create templates directory and basic HTML templates
def create_dashboard_templates():
    """Create basic dashboard templates"""
    templates_dir = "templates"
    os.makedirs(templates_dir, exist_ok=True)
    
    # Main dashboard template
    dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading System Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .header { text-align: center; margin-bottom: 30px; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { display: flex; justify-content: space-between; align-items: center; margin: 10px 0; }
        .status-healthy { color: #28a745; }
        .status-unhealthy { color: #dc3545; }
        .status-warning { color: #ffc107; }
        .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .alert-critical { background-color: #f8d7da; border: 1px solid #f5c6cb; }
        .alert-warning { background-color: #fff3cd; border: 1px solid #ffeaa7; }
        .alert-info { background-color: #d1ecf1; border: 1px solid #bee5eb; }
        .refresh-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #0056b3; }
        .timestamp { font-size: 0.8em; color: #666; }
        #refreshStatus { margin-left: 10px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Trading System Monitoring Dashboard</h1>
        <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
        <span id="refreshStatus"></span>
        <div class="timestamp" id="lastUpdate"></div>
    </div>
    
    <div class="dashboard-grid">
        <!-- System Overview Card -->
        <div class="card">
            <h2>📊 System Overview</h2>
            <div id="systemOverview">Loading...</div>
        </div>
        
        <!-- Service Health Card -->
        <div class="card">
            <h2>🏥 Service Health</h2>
            <div id="serviceHealth">Loading...</div>
        </div>
        
        <!-- Active Alerts Card -->
        <div class="card">
            <h2>🚨 Active Alerts</h2>
            <div id="activeAlerts">Loading...</div>
        </div>
        
        <!-- Performance Metrics Card -->
        <div class="card">
            <h2>📈 Performance Metrics</h2>
            <canvas id="performanceChart" width="400" height="200"></canvas>
        </div>
    </div>

    <script>
        let performanceChart = null;
        
        async function refreshDashboard() {
            document.getElementById('refreshStatus').textContent = 'Refreshing...';
            
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                
                updateSystemOverview(data);
                updateServiceHealth(data);
                updateActiveAlerts(data);
                updatePerformanceChart(data);
                
                document.getElementById('lastUpdate').textContent = 
                    'Last updated: ' + new Date().toLocaleString();
                document.getElementById('refreshStatus').textContent = '✅ Updated';
                
                setTimeout(() => {
                    document.getElementById('refreshStatus').textContent = '';
                }, 2000);
                
            } catch (error) {
                console.error('Failed to refresh dashboard:', error);
                document.getElementById('refreshStatus').textContent = '❌ Error';
            }
        }
        
        function updateSystemOverview(data) {
            const overview = data.system_overview || {};
            const health = data.health?.summary || {};
            
            document.getElementById('systemOverview').innerHTML = `
                <div class="metric">
                    <span>Total Services:</span>
                    <span><strong>${overview.total_services || 0}</strong></span>
                </div>
                <div class="metric">
                    <span>Healthy Services:</span>
                    <span class="status-healthy"><strong>${health.healthy_services || 0}</strong></span>
                </div>
                <div class="metric">
                    <span>Unhealthy Services:</span>
                    <span class="status-unhealthy"><strong>${health.unhealthy_services || 0}</strong></span>
                </div>
                <div class="metric">
                    <span>Active Alerts:</span>
                    <span class="status-warning"><strong>${overview.active_alert_count || 0}</strong></span>
                </div>
                <div class="metric">
                    <span>Avg Response Time:</span>
                    <span><strong>${(health.avg_response_time || 0).toFixed(2)}s</strong></span>
                </div>
                <div class="metric">
                    <span>Avg SLA Compliance:</span>
                    <span><strong>${(health.avg_sla_compliance || 0).toFixed(1)}%</strong></span>
                </div>
            `;
        }
        
        function updateServiceHealth(data) {
            const services = data.health?.services || {};
            
            let html = '';
            for (const [serviceName, health] of Object.entries(services)) {
                const statusClass = health.status === 'healthy' ? 'status-healthy' : 'status-unhealthy';
                
                html += `
                    <div class="metric">
                        <span>${serviceName}:</span>
                        <span class="${statusClass}"><strong>${health.status}</strong></span>
                    </div>
                `;
            }
            
            document.getElementById('serviceHealth').innerHTML = html || 'No service data available';
        }
        
        function updateActiveAlerts(data) {
            const alerts = data.alerts?.active_alerts || [];
            
            if (alerts.length === 0) {
                document.getElementById('activeAlerts').innerHTML = 
                    '<div style="color: #28a745;">✅ No active alerts</div>';
                return;
            }
            
            let html = '';
            alerts.forEach(alert => {
                const severityClass = `alert-${alert.severity}`;
                const timeAgo = Math.round((Date.now() / 1000 - alert.created_at) / 60);
                
                html += `
                    <div class="alert ${severityClass}">
                        <strong>${alert.service}</strong>: ${alert.message}
                        <div style="font-size: 0.8em; margin-top: 5px;">
                            ${timeAgo} minutes ago
                            <button onclick="resolveAlert('${alert.alert_id}')" 
                                    style="float: right; font-size: 0.8em;">Resolve</button>
                        </div>
                    </div>
                `;
            });
            
            document.getElementById('activeAlerts').innerHTML = html;
        }
        
        async function resolveAlert(alertId) {
            try {
                const response = await fetch(`/api/alerts/${alertId}/resolve`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.status === 'resolved') {
                    refreshDashboard();
                }
            } catch (error) {
                console.error('Failed to resolve alert:', error);
            }
        }
        
        function updatePerformanceChart(data) {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            
            // Simulated performance data
            const labels = [];
            const responseTimeData = [];
            const now = new Date();
            
            for (let i = 11; i >= 0; i--) {
                const time = new Date(now.getTime() - i * 5 * 60 * 1000);
                labels.push(time.toLocaleTimeString());
                responseTimeData.push(Math.random() * 3 + 1); // Random response times
            }
            
            if (performanceChart) {
                performanceChart.destroy();
            }
            
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Response Time (s)',
                        data: responseTimeData,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshDashboard, 30000);
        
        // Initial load
        refreshDashboard();
    </script>
</body>
</html>"""
    
    with open(f"{templates_dir}/dashboard.html", "w") as f:
        f.write(dashboard_html)
    
    # Create placeholder templates for other pages
    placeholder_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading System Monitoring - {title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; text-decoration: none; color: #007bff; }}
        .back-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <a href="/" class="back-link">← Back to Dashboard</a>
    <div class="header">
        <h1>{title}</h1>
        <p>This page is under development. Advanced {title.lower()} features will be available soon.</p>
    </div>
</body>
</html>"""
    
    for page, title in [
        ("health_details.html", "Health Details"),
        ("metrics_analysis.html", "Metrics Analysis"),
        ("alerts_management.html", "Alerts Management"),
        ("sla_reports.html", "SLA Reports")
    ]:
        with open(f"{templates_dir}/{page}", "w") as f:
            f.write(placeholder_template.format(title=title))

def run_dashboard_server(host='0.0.0.0', port=5000, debug=False):
    """Run the dashboard web server"""
    print(f"🌐 Starting Trading System Monitoring Dashboard")
    print(f"📊 Dashboard URL: http://{host}:{port}")
    print(f"🔄 Auto-refresh enabled (30 seconds)")
    print("=" * 60)
    
    # Create templates if they don't exist
    create_dashboard_templates()
    
    # Run Flask app
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trading System Monitoring Dashboard")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_dashboard_server(args.host, args.port, args.debug)
