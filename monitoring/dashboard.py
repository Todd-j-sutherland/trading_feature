#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard
Web-based dashboard for production monitoring system
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import subprocess
import sys

# Simple web server imports
try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse
except ImportError:
    print("HTTP server modules not available")
    sys.exit(1)

class MonitoringDashboard:
    """Web-based monitoring dashboard"""
    
    def __init__(self, monitor_db: str = "monitoring/monitoring_metrics.db", port: int = 8080):
        self.db_path = monitor_db
        self.port = port
        self.server = None

    def get_system_metrics(self, hours: int = 24) -> List[Dict]:
        """Get system metrics for the last N hours"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, cpu_percent, memory_percent, disk_usage_percent
                FROM system_metrics 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 1000
            ''', (cutoff.isoformat(),))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "timestamp": row[0],
                    "cpu_percent": row[1],
                    "memory_percent": row[2], 
                    "disk_usage_percent": row[3]
                }
                for row in results
            ]
            
        except Exception as e:
            print(f"Error getting system metrics: {e}")
            return []

    def get_service_metrics(self, hours: int = 24) -> List[Dict]:
        """Get service metrics for the last N hours"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT service_name, region, status, response_time, error_rate, timestamp
                FROM service_metrics 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 1000
            ''', (cutoff.isoformat(),))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "service_name": row[0],
                    "region": row[1],
                    "status": row[2],
                    "response_time": row[3],
                    "error_rate": row[4],
                    "timestamp": row[5]
                }
                for row in results
            ]
            
        except Exception as e:
            print(f"Error getting service metrics: {e}")
            return []

    def get_alerts(self, days: int = 7) -> List[Dict]:
        """Get alerts for the last N days"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, severity, service, metric, value, threshold, message, region, resolved
                FROM alerts 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 500
            ''', (cutoff.isoformat(),))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "timestamp": row[0],
                    "severity": row[1],
                    "service": row[2],
                    "metric": row[3],
                    "value": row[4],
                    "threshold": row[5],
                    "message": row[6],
                    "region": row[7],
                    "resolved": bool(row[8])
                }
                for row in results
            ]
            
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return []

    def get_dashboard_summary(self) -> Dict:
        """Get dashboard summary data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Current system status
            cursor.execute('''
                SELECT cpu_percent, memory_percent, disk_usage_percent
                FROM system_metrics 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            current_system = cursor.fetchone()
            
            # Service status counts
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM (
                    SELECT DISTINCT service_name, region, 
                           FIRST_VALUE(status) OVER (
                               PARTITION BY service_name, region 
                               ORDER BY timestamp DESC
                           ) as status
                    FROM service_metrics 
                    WHERE timestamp > datetime('now', '-1 hour')
                ) 
                GROUP BY status
            ''')
            service_counts = cursor.fetchall()
            
            # Active alerts by severity
            cursor.execute('''
                SELECT severity, COUNT(*) as count
                FROM alerts 
                WHERE resolved = FALSE
                GROUP BY severity
            ''')
            alert_counts = cursor.fetchall()
            
            # Recent error count
            cursor.execute('''
                SELECT COUNT(*) 
                FROM alerts 
                WHERE timestamp > datetime('now', '-24 hours')
            ''')
            recent_alerts = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "current_system": {
                    "cpu": current_system[0] if current_system else 0,
                    "memory": current_system[1] if current_system else 0,
                    "disk": current_system[2] if current_system else 0
                },
                "service_status": {row[0]: row[1] for row in service_counts},
                "alert_counts": {row[0]: row[1] for row in alert_counts},
                "recent_alerts": recent_alerts,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting dashboard summary: {e}")
            return {"error": str(e)}

    def generate_html_dashboard(self) -> str:
        """Generate HTML dashboard"""
        summary = self.get_dashboard_summary()
        system_metrics = self.get_system_metrics(6)  # Last 6 hours
        service_metrics = self.get_service_metrics(6)
        alerts = self.get_alerts(1)  # Last day
        
        html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading System Monitoring Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            margin-top: 0;
            color: #444;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-value {{
            font-weight: bold;
            font-size: 1.2em;
        }}
        .status-healthy {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-error {{ color: #dc3545; }}
        .status-critical {{ color: #6f42c1; }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 5px;
        }}
        .progress-fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
        .progress-cpu {{ background-color: #17a2b8; }}
        .progress-memory {{ background-color: #28a745; }}
        .progress-disk {{ background-color: #ffc107; }}
        .alert {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }}
        .alert-critical {{
            background-color: #f8d7da;
            border-color: #dc3545;
        }}
        .alert-high {{
            background-color: #fff3cd;
            border-color: #ffc107;
        }}
        .alert-medium {{
            background-color: #d1ecf1;
            border-color: #17a2b8;
        }}
        .alert-low {{
            background-color: #d4edda;
            border-color: #28a745;
        }}
        .service-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
        }}
        .service-item {{
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
        }}
        .refresh-info {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            text-align: left;
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .timestamp {{
            font-size: 0.8em;
            color: #666;
        }}
    </style>
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() {{
            window.location.reload();
        }}, 30000);
    </script>
</head>
<body>
    <div class="header">
        <h1>🏦 Trading System Monitoring Dashboard</h1>
        <p>Multi-Region Microservices Status - {summary.get('timestamp', 'Unknown')}</p>
    </div>

    <div class="dashboard-grid">
        <!-- System Overview -->
        <div class="card">
            <h3>📊 System Overview</h3>
            <div class="metric">
                <span>CPU Usage</span>
                <span class="metric-value">{summary['current_system']['cpu']:.1f}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill progress-cpu" style="width: {summary['current_system']['cpu']:.1f}%"></div>
            </div>
            
            <div class="metric">
                <span>Memory Usage</span>
                <span class="metric-value">{summary['current_system']['memory']:.1f}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill progress-memory" style="width: {summary['current_system']['memory']:.1f}%"></div>
            </div>
            
            <div class="metric">
                <span>Disk Usage</span>
                <span class="metric-value">{summary['current_system']['disk']:.1f}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill progress-disk" style="width: {summary['current_system']['disk']:.1f}%"></div>
            </div>
        </div>

        <!-- Service Status -->
        <div class="card">
            <h3>🔧 Service Status</h3>
            <div class="service-grid">
        '''
        
        # Add service status items
        service_status = summary.get('service_status', {})
        for status, count in service_status.items():
            status_class = f"status-{status}" if status in ['healthy', 'warning', 'error', 'critical'] else "status-warning"
            html += f'''
                <div class="service-item {status_class}">
                    {status.title()}<br>
                    <span style="font-size: 1.5em;">{count}</span>
                </div>
            '''
        
        html += '''
            </div>
        </div>

        <!-- Alert Summary -->
        <div class="card">
            <h3>🚨 Alert Summary</h3>
        '''
        
        alert_counts = summary.get('alert_counts', {})
        total_alerts = sum(alert_counts.values())
        
        if total_alerts > 0:
            for severity, count in alert_counts.items():
                html += f'''
                <div class="metric">
                    <span>{severity.title()} Alerts</span>
                    <span class="metric-value status-{severity}">{count}</span>
                </div>
                '''
        else:
            html += '<div class="metric"><span class="status-healthy">✅ No Active Alerts</span></div>'
        
        html += f'''
            <div class="metric">
                <span>Recent Alerts (24h)</span>
                <span class="metric-value">{summary.get('recent_alerts', 0)}</span>
            </div>
        </div>
    </div>

    <!-- Recent Alerts -->
    <div class="card">
        <h3>🔔 Recent Alerts</h3>
        '''
        
        if alerts:
            html += '''
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Severity</th>
                        <th>Service</th>
                        <th>Region</th>
                        <th>Message</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
            '''
            
            for alert in alerts[:20]:  # Show last 20 alerts
                severity_class = f"status-{alert['severity']}"
                resolved_status = "✅ Resolved" if alert['resolved'] else "🔴 Active"
                timestamp = datetime.fromisoformat(alert['timestamp']).strftime("%H:%M:%S")
                
                html += f'''
                <tr>
                    <td class="timestamp">{timestamp}</td>
                    <td class="{severity_class}">{alert['severity'].title()}</td>
                    <td>{alert['service']}</td>
                    <td>{alert['region']}</td>
                    <td>{alert['message'][:100]}...</td>
                    <td>{resolved_status}</td>
                </tr>
                '''
            
            html += '</tbody></table>'
        else:
            html += '<p class="status-healthy">No recent alerts</p>'
        
        html += '''
    </div>

    <!-- Service Performance -->
    <div class="card">
        <h3>⚡ Service Performance (Last Hour)</h3>
        '''
        
        # Group service metrics by service and region
        recent_services = {}
        for metric in service_metrics:
            key = f"{metric['service_name']}@{metric['region']}"
            if key not in recent_services:
                recent_services[key] = metric
        
        if recent_services:
            html += '''
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Status</th>
                        <th>Response Time</th>
                        <th>Error Rate</th>
                    </tr>
                </thead>
                <tbody>
            '''
            
            for service_key, metric in recent_services.items():
                status_class = "status-healthy" if metric['status'] == 'healthy' else "status-error"
                response_time = f"{metric['response_time']:.2f}s" if metric['response_time'] != float('inf') else "∞"
                
                html += f'''
                <tr>
                    <td>{service_key}</td>
                    <td class="{status_class}">{metric['status'].title()}</td>
                    <td>{response_time}</td>
                    <td>{metric['error_rate']:.1f}%</td>
                </tr>
                '''
            
            html += '</tbody></table>'
        else:
            html += '<p>No recent service data available</p>'
        
        html += '''
    </div>

    <div class="refresh-info">
        🔄 Dashboard auto-refreshes every 30 seconds<br>
        📊 Data includes metrics from the last 6 hours
    </div>

</body>
</html>
        '''
        
        return html

class DashboardHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, dashboard, *args, **kwargs):
        self.dashboard = dashboard
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            # Serve dashboard HTML
            html = self.dashboard.generate_html_dashboard()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
            
        elif self.path == '/api/summary':
            # Serve JSON summary
            summary = self.dashboard.get_dashboard_summary()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(summary, indent=2).encode())
            
        elif self.path == '/api/metrics':
            # Serve metrics data
            system_metrics = self.dashboard.get_system_metrics(24)
            service_metrics = self.dashboard.get_service_metrics(24)
            
            data = {
                "system_metrics": system_metrics,
                "service_metrics": service_metrics
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())
            
        elif self.path == '/api/alerts':
            # Serve alerts data
            alerts = self.dashboard.get_alerts(7)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(alerts, indent=2).encode())
            
        else:
            # 404 for other paths
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass

def create_handler(dashboard):
    """Create HTTP handler with dashboard instance"""
    def handler(*args, **kwargs):
        return DashboardHTTPHandler(dashboard, *args, **kwargs)
    return handler

async def main():
    """Main dashboard function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitoring dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve dashboard")
    parser.add_argument("--db", default="monitoring/monitoring_metrics.db", help="Monitoring database path")
    
    args = parser.parse_args()
    
    # Check if database exists
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Warning: Monitoring database not found at {args.db}")
        print("Make sure the production monitor is running and has created metrics.")
    
    dashboard = MonitoringDashboard(args.db, args.port)
    
    # Create HTTP server
    handler = create_handler(dashboard)
    httpd = HTTPServer(('', args.port), handler)
    
    print(f"🚀 Starting monitoring dashboard on http://localhost:{args.port}")
    print("📊 Dashboard will show:")
    print("   - Real-time system metrics")
    print("   - Service health status")
    print("   - Active alerts")
    print("   - Performance data")
    print("\\n📡 API endpoints available:")
    print(f"   - http://localhost:{args.port}/api/summary")
    print(f"   - http://localhost:{args.port}/api/metrics")
    print(f"   - http://localhost:{args.port}/api/alerts")
    print("\\nPress Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 Dashboard stopped")
        httpd.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
