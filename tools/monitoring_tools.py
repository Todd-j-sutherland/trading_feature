#!/usr/bin/env python3
"""
Advanced Monitoring Tools and Utilities

Collection of advanced monitoring tools for system administration, troubleshooting,
and performance analysis of the trading microservices architecture.

Tools included:
- Real-time log analyzer and aggregator
- Performance profiler and bottleneck detector
- Service dependency mapper
- Alert simulator for testing
- Metrics export utilities
- Health check validator

Author: Trading System Monitoring Tools
Date: September 14, 2025
"""

import asyncio
import json
import time
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
import threading
import queue
import psutil
import re
from collections import defaultdict, deque
import statistics

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class LogAnalyzer:
    """Real-time log analysis and aggregation tool"""
    
    def __init__(self, log_paths: List[str]):
        self.log_paths = log_paths
        self.patterns = {
            'error': re.compile(r'ERROR|CRITICAL|FATAL', re.IGNORECASE),
            'warning': re.compile(r'WARNING|WARN', re.IGNORECASE),
            'service_call': re.compile(r'service.*call|method.*call', re.IGNORECASE),
            'response_time': re.compile(r'execution_time["\']?\s*:\s*([0-9.]+)', re.IGNORECASE),
            'prediction': re.compile(r'prediction.*generated|buy.*signal', re.IGNORECASE)
        }
        
        self.stats = defaultdict(int)
        self.recent_events = deque(maxlen=1000)
        
    def analyze_logs(self, tail_lines: int = 100) -> Dict[str, Any]:
        """Analyze recent log entries"""
        events = []
        
        for log_path in self.log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                        recent_lines = lines[-tail_lines:] if len(lines) > tail_lines else lines
                        
                        for line in recent_lines:
                            event = self._parse_log_line(line, log_path)
                            if event:
                                events.append(event)
                                self.recent_events.append(event)
                                
                except Exception as e:
                    print(f"Error reading log {log_path}: {e}")
                    
        # Aggregate statistics
        error_count = sum(1 for e in events if e['level'] == 'ERROR')
        warning_count = sum(1 for e in events if e['level'] == 'WARNING')
        service_calls = sum(1 for e in events if e.get('type') == 'service_call')
        
        response_times = [e['response_time'] for e in events if e.get('response_time')]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        return {
            'total_events': len(events),
            'error_count': error_count,
            'warning_count': warning_count,
            'service_calls': service_calls,
            'avg_response_time': avg_response_time,
            'recent_events': events[-20:],  # Last 20 events
            'analysis_timestamp': datetime.now().isoformat()
        }
        
    def _parse_log_line(self, line: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse individual log line"""
        line = line.strip()
        if not line:
            return None
            
        event = {
            'timestamp': datetime.now().isoformat(),
            'source': os.path.basename(source),
            'raw_line': line
        }
        
        # Determine log level
        if self.patterns['error'].search(line):
            event['level'] = 'ERROR'
        elif self.patterns['warning'].search(line):
            event['level'] = 'WARNING'
        else:
            event['level'] = 'INFO'
            
        # Check for service calls
        if self.patterns['service_call'].search(line):
            event['type'] = 'service_call'
            
        # Extract response time if present
        response_match = self.patterns['response_time'].search(line)
        if response_match:
            try:
                event['response_time'] = float(response_match.group(1))
            except ValueError:
                pass
                
        # Check for prediction events
        if self.patterns['prediction'].search(line):
            event['type'] = 'prediction'
            
        return event
        
    def watch_logs_realtime(self, callback):
        """Watch logs in real-time"""
        print("🔍 Starting real-time log monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                analysis = self.analyze_logs(50)  # Check last 50 lines
                callback(analysis)
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            print("\n📊 Log monitoring stopped")

class PerformanceProfiler:
    """Performance profiling and bottleneck detection"""
    
    def __init__(self):
        self.services = [
            "market-data", "sentiment", "prediction", 
            "scheduler", "paper-trading", "ml-model"
        ]
        self.performance_data = defaultdict(list)
        
    async def profile_services(self, duration: int = 300) -> Dict[str, Any]:
        """Profile service performance over time"""
        print(f"🔬 Profiling services for {duration} seconds...")
        
        start_time = time.time()
        end_time = start_time + duration
        
        results = {
            'profile_duration': duration,
            'services': {},
            'bottlenecks': [],
            'recommendations': []
        }
        
        while time.time() < end_time:
            # Test each service
            for service in self.services:
                perf_data = await self._profile_single_service(service)
                self.performance_data[service].append(perf_data)
                
            # Progress indicator
            elapsed = time.time() - start_time
            progress = (elapsed / duration) * 100
            print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            
            await asyncio.sleep(10)  # Sample every 10 seconds
            
        print("\n📊 Analysis complete")
        
        # Analyze results
        for service in self.services:
            service_data = self.performance_data[service]
            if service_data:
                results['services'][service] = self._analyze_service_performance(service_data)
                
        # Detect bottlenecks
        results['bottlenecks'] = self._detect_bottlenecks(results['services'])
        results['recommendations'] = self._generate_recommendations(results['services'])
        
        return results
        
    async def _profile_single_service(self, service: str) -> Dict[str, Any]:
        """Profile individual service performance"""
        start_time = time.time()
        
        try:
            socket_path = f"/tmp/trading_{service}.sock"
            
            # Test health endpoint
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path),
                timeout=10.0
            )
            
            request = {'method': 'health', 'params': {}}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(8192), timeout=10.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            response_time = time.time() - start_time
            
            return {
                'timestamp': time.time(),
                'service': service,
                'response_time': response_time,
                'success': response.get('status') == 'success',
                'error': None
            }
            
        except Exception as e:
            return {
                'timestamp': time.time(),
                'service': service,
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
            
    def _analyze_service_performance(self, service_data: List[Dict]) -> Dict[str, Any]:
        """Analyze performance data for a single service"""
        if not service_data:
            return {'error': 'No performance data available'}
            
        response_times = [d['response_time'] for d in service_data if d['success']]
        success_rate = sum(1 for d in service_data if d['success']) / len(service_data)
        
        if response_times:
            return {
                'total_samples': len(service_data),
                'success_rate': success_rate,
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'median_response_time': statistics.median(response_times),
                'p95_response_time': self._percentile(response_times, 95),
                'p99_response_time': self._percentile(response_times, 99),
                'performance_grade': self._calculate_performance_grade(statistics.mean(response_times), success_rate)
            }
        else:
            return {
                'total_samples': len(service_data),
                'success_rate': success_rate,
                'error': 'No successful responses to analyze',
                'performance_grade': 'F'
            }
            
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
        
    def _calculate_performance_grade(self, avg_response_time: float, success_rate: float) -> str:
        """Calculate performance grade A-F"""
        if success_rate < 0.9:
            return 'F'
        elif avg_response_time > 10:
            return 'F'
        elif avg_response_time > 5:
            return 'D'
        elif avg_response_time > 2:
            return 'C'
        elif avg_response_time > 1:
            return 'B'
        else:
            return 'A'
            
    def _detect_bottlenecks(self, services_data: Dict[str, Dict]) -> List[Dict]:
        """Detect performance bottlenecks"""
        bottlenecks = []
        
        for service, data in services_data.items():
            if 'error' in data:
                continue
                
            # High response time bottleneck
            if data['avg_response_time'] > 5.0:
                bottlenecks.append({
                    'type': 'high_response_time',
                    'service': service,
                    'severity': 'high' if data['avg_response_time'] > 10 else 'medium',
                    'value': data['avg_response_time'],
                    'description': f"Service {service} has high average response time: {data['avg_response_time']:.2f}s"
                })
                
            # Low success rate bottleneck
            if data['success_rate'] < 0.95:
                bottlenecks.append({
                    'type': 'low_success_rate',
                    'service': service,
                    'severity': 'high' if data['success_rate'] < 0.8 else 'medium',
                    'value': data['success_rate'],
                    'description': f"Service {service} has low success rate: {data['success_rate']:.1%}"
                })
                
            # High response time variance
            if 'p99_response_time' in data and 'avg_response_time' in data:
                variance_ratio = data['p99_response_time'] / data['avg_response_time']
                if variance_ratio > 3:
                    bottlenecks.append({
                        'type': 'high_variance',
                        'service': service,
                        'severity': 'medium',
                        'value': variance_ratio,
                        'description': f"Service {service} has inconsistent response times (P99/avg ratio: {variance_ratio:.1f})"
                    })
                    
        return bottlenecks
        
    def _generate_recommendations(self, services_data: Dict[str, Dict]) -> List[Dict]:
        """Generate performance recommendations"""
        recommendations = []
        
        for service, data in services_data.items():
            if 'error' in data:
                recommendations.append({
                    'service': service,
                    'priority': 'high',
                    'type': 'service_issue',
                    'recommendation': f"Service {service} is not responding - check service status and logs"
                })
                continue
                
            grade = data['performance_grade']
            
            if grade in ['D', 'F']:
                recommendations.append({
                    'service': service,
                    'priority': 'high',
                    'type': 'performance_optimization',
                    'recommendation': f"Service {service} needs immediate performance optimization (Grade: {grade})"
                })
            elif grade == 'C':
                recommendations.append({
                    'service': service,
                    'priority': 'medium',
                    'type': 'performance_improvement',
                    'recommendation': f"Service {service} could benefit from performance tuning (Grade: {grade})"
                })
                
            # Specific recommendations based on metrics
            if data['avg_response_time'] > 2:
                recommendations.append({
                    'service': service,
                    'priority': 'medium',
                    'type': 'response_time',
                    'recommendation': f"Consider optimizing {service} response time (current: {data['avg_response_time']:.2f}s)"
                })
                
        return recommendations

class ServiceDependencyMapper:
    """Map and analyze service dependencies"""
    
    def __init__(self):
        self.dependencies = {
            "prediction": ["market-data", "sentiment"],
            "paper-trading": ["prediction"],
            "scheduler": ["prediction", "paper-trading"],
            "ml-model": [],
            "market-data": [],
            "sentiment": []
        }
        
    async def map_dependencies(self) -> Dict[str, Any]:
        """Map current service dependencies and health"""
        dependency_map = {
            'services': {},
            'health_propagation': {},
            'critical_path': [],
            'risk_analysis': {}
        }
        
        # Check each service and its dependencies
        for service in self.dependencies:
            service_info = await self._analyze_service_dependencies(service)
            dependency_map['services'][service] = service_info
            
        # Analyze health propagation
        dependency_map['health_propagation'] = self._analyze_health_propagation(dependency_map['services'])
        
        # Find critical path
        dependency_map['critical_path'] = self._find_critical_path()
        
        # Risk analysis
        dependency_map['risk_analysis'] = self._analyze_risks(dependency_map['services'])
        
        return dependency_map
        
    async def _analyze_service_dependencies(self, service: str) -> Dict[str, Any]:
        """Analyze dependencies for a single service"""
        deps = self.dependencies.get(service, [])
        
        service_info = {
            'service': service,
            'dependencies': deps,
            'dependency_count': len(deps),
            'health_status': 'unknown',
            'dependent_services': [],
            'dependency_health': {}
        }
        
        # Find services that depend on this one
        for svc, svc_deps in self.dependencies.items():
            if service in svc_deps:
                service_info['dependent_services'].append(svc)
                
        # Check health of dependencies
        for dep in deps:
            try:
                socket_path = f"/tmp/trading_{dep}.sock"
                reader, writer = await asyncio.wait_for(
                    asyncio.open_unix_connection(socket_path),
                    timeout=5.0
                )
                
                request = {'method': 'health', 'params': {}}
                writer.write(json.dumps(request).encode())
                await writer.drain()
                
                response_data = await asyncio.wait_for(reader.read(8192), timeout=5.0)
                response = json.loads(response_data.decode())
                
                writer.close()
                await writer.wait_closed()
                
                if response.get('status') == 'success':
                    service_info['dependency_health'][dep] = 'healthy'
                else:
                    service_info['dependency_health'][dep] = 'unhealthy'
                    
            except Exception:
                service_info['dependency_health'][dep] = 'unreachable'
                
        # Check own health
        try:
            socket_path = f"/tmp/trading_{service}.sock"
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path),
                timeout=5.0
            )
            
            request = {'method': 'health', 'params': {}}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(8192), timeout=5.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response.get('status') == 'success':
                service_info['health_status'] = 'healthy'
            else:
                service_info['health_status'] = 'unhealthy'
                
        except Exception:
            service_info['health_status'] = 'unreachable'
            
        return service_info
        
    def _analyze_health_propagation(self, services: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze how health issues propagate through dependencies"""
        propagation = {
            'healthy_services': [],
            'unhealthy_services': [],
            'at_risk_services': [],
            'cascade_risks': []
        }
        
        for service, info in services.items():
            status = info['health_status']
            
            if status == 'healthy':
                propagation['healthy_services'].append(service)
            else:
                propagation['unhealthy_services'].append(service)
                
                # Check cascade impact
                dependent_services = info['dependent_services']
                if dependent_services:
                    propagation['cascade_risks'].append({
                        'failed_service': service,
                        'affected_services': dependent_services,
                        'impact_severity': 'high' if len(dependent_services) > 2 else 'medium'
                    })
                    
            # Check if service is at risk due to unhealthy dependencies
            unhealthy_deps = [
                dep for dep, health in info['dependency_health'].items() 
                if health != 'healthy'
            ]
            
            if unhealthy_deps and status == 'healthy':
                propagation['at_risk_services'].append({
                    'service': service,
                    'unhealthy_dependencies': unhealthy_deps,
                    'risk_level': 'high' if len(unhealthy_deps) > 1 else 'medium'
                })
                
        return propagation
        
    def _find_critical_path(self) -> List[str]:
        """Find critical path through service dependencies"""
        # Start from services with no dependencies and traverse
        critical_path = []
        
        # Market data and sentiment are leaf nodes
        critical_path.extend(['market-data', 'sentiment'])
        
        # Prediction depends on both
        critical_path.append('prediction')
        
        # Paper trading depends on prediction
        critical_path.append('paper-trading')
        
        # Scheduler coordinates everything
        critical_path.append('scheduler')
        
        return critical_path
        
    def _analyze_risks(self, services: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze dependency risks"""
        risks = {
            'single_points_of_failure': [],
            'highly_depended_services': [],
            'isolated_services': [],
            'risk_score': 0
        }
        
        dependency_counts = defaultdict(int)
        
        # Count how many services depend on each service
        for service, info in services.items():
            for dep in info['dependencies']:
                dependency_counts[dep] += 1
                
        # Identify highly depended services
        for service, count in dependency_counts.items():
            if count >= 3:
                risks['highly_depended_services'].append({
                    'service': service,
                    'dependent_count': count,
                    'risk_level': 'high'
                })
            elif count >= 2:
                risks['highly_depended_services'].append({
                    'service': service,
                    'dependent_count': count,
                    'risk_level': 'medium'
                })
                
        # Find isolated services (no dependencies or dependents)
        for service, info in services.items():
            if not info['dependencies'] and not info['dependent_services']:
                risks['isolated_services'].append(service)
                
        # Calculate overall risk score
        risk_score = 0
        risk_score += len(risks['highly_depended_services']) * 20
        risk_score += len([s for s in services.values() if s['health_status'] != 'healthy']) * 30
        risk_score -= len(risks['isolated_services']) * 5  # Isolation reduces risk
        
        risks['risk_score'] = max(0, min(100, risk_score))
        
        return risks

class MonitoringToolsCLI:
    """Command-line interface for monitoring tools"""
    
    def __init__(self):
        self.log_analyzer = LogAnalyzer([
            "/var/log/trading/market-data.log",
            "/var/log/trading/sentiment.log", 
            "/var/log/trading/prediction.log",
            "/var/log/trading/scheduler.log",
            "/var/log/trading/paper-trading.log",
            "/var/log/trading/ml-model.log",
            "/var/log/trading/monitoring.log"
        ])
        
        self.profiler = PerformanceProfiler()
        self.dependency_mapper = ServiceDependencyMapper()
        
    async def analyze_logs(self, args):
        """Run log analysis"""
        print("📜 TRADING SYSTEM LOG ANALYSIS")
        print("=" * 50)
        
        if args.watch:
            def print_analysis(analysis):
                print(f"\n🕐 {analysis['analysis_timestamp']}")
                print(f"📊 Events: {analysis['total_events']} | Errors: {analysis['error_count']} | Warnings: {analysis['warning_count']}")
                print(f"🔄 Service Calls: {analysis['service_calls']} | Avg Response: {analysis['avg_response_time']:.2f}s")
                
                if analysis['recent_events']:
                    print("\n🔍 Recent Events:")
                    for event in analysis['recent_events'][-5:]:
                        level_icon = "🚨" if event['level'] == 'ERROR' else "⚠️" if event['level'] == 'WARNING' else "ℹ️"
                        print(f"  {level_icon} [{event['source']}] {event['raw_line'][:80]}...")
                        
            self.log_analyzer.watch_logs_realtime(print_analysis)
        else:
            analysis = self.log_analyzer.analyze_logs(args.lines)
            
            print(f"📊 Total Events: {analysis['total_events']}")
            print(f"🚨 Errors: {analysis['error_count']}")
            print(f"⚠️  Warnings: {analysis['warning_count']}")
            print(f"🔄 Service Calls: {analysis['service_calls']}")
            print(f"⏱️  Avg Response Time: {analysis['avg_response_time']:.2f}s")
            
            if analysis['recent_events']:
                print(f"\n🔍 Recent Events:")
                for event in analysis['recent_events'][-10:]:
                    level_icon = "🚨" if event['level'] == 'ERROR' else "⚠️" if event['level'] == 'WARNING' else "ℹ️"
                    print(f"  {level_icon} [{event['source']}] {event['raw_line'][:100]}...")
                    
    async def profile_performance(self, args):
        """Run performance profiling"""
        print("🔬 TRADING SYSTEM PERFORMANCE PROFILING")
        print("=" * 50)
        
        results = await self.profiler.profile_services(args.duration)
        
        print(f"\n📊 Performance Analysis Results ({args.duration}s profile)")
        print("=" * 50)
        
        for service, data in results['services'].items():
            if 'error' in data:
                print(f"❌ {service}: {data['error']}")
            else:
                grade_icon = "🟢" if data['performance_grade'] in ['A', 'B'] else "🟡" if data['performance_grade'] == 'C' else "🔴"
                print(f"{grade_icon} {service} (Grade: {data['performance_grade']})")
                print(f"   📈 Success Rate: {data['success_rate']:.1%}")
                print(f"   ⏱️  Avg Response: {data['avg_response_time']:.2f}s")
                print(f"   📊 P95: {data.get('p95_response_time', 0):.2f}s | P99: {data.get('p99_response_time', 0):.2f}s")
                
        if results['bottlenecks']:
            print(f"\n🚫 Detected Bottlenecks:")
            for bottleneck in results['bottlenecks']:
                severity_icon = "🚨" if bottleneck['severity'] == 'high' else "⚠️"
                print(f"   {severity_icon} {bottleneck['description']}")
                
        if results['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in results['recommendations']:
                priority_icon = "🔥" if rec['priority'] == 'high' else "📈"
                print(f"   {priority_icon} {rec['recommendation']}")
                
    async def map_dependencies(self, args):
        """Run dependency mapping"""
        print("🗺️  TRADING SYSTEM DEPENDENCY MAPPING")
        print("=" * 50)
        
        dependency_map = await self.dependency_mapper.map_dependencies()
        
        print("📋 Service Dependencies:")
        for service, info in dependency_map['services'].items():
            status_icon = "🟢" if info['health_status'] == 'healthy' else "🔴" if info['health_status'] == 'unhealthy' else "⚪"
            print(f"  {status_icon} {service}")
            
            if info['dependencies']:
                print(f"    ⬅️  Depends on: {', '.join(info['dependencies'])}")
                
            if info['dependent_services']:
                print(f"    ➡️  Used by: {', '.join(info['dependent_services'])}")
                
            unhealthy_deps = [dep for dep, health in info['dependency_health'].items() if health != 'healthy']
            if unhealthy_deps:
                print(f"    ⚠️  Unhealthy dependencies: {', '.join(unhealthy_deps)}")
                
        propagation = dependency_map['health_propagation']
        print(f"\n💊 Health Status:")
        print(f"  🟢 Healthy: {len(propagation['healthy_services'])} services")
        print(f"  🔴 Unhealthy: {len(propagation['unhealthy_services'])} services")
        
        if propagation['at_risk_services']:
            print(f"  ⚠️  At Risk: {len(propagation['at_risk_services'])} services")
            
        if propagation['cascade_risks']:
            print(f"\n🔗 Cascade Risks:")
            for risk in propagation['cascade_risks']:
                print(f"   📉 {risk['failed_service']} failure affects: {', '.join(risk['affected_services'])}")
                
        risks = dependency_map['risk_analysis']
        print(f"\n⚡ Risk Analysis:")
        print(f"  📊 Overall Risk Score: {risks['risk_score']}/100")
        
        if risks['highly_depended_services']:
            print(f"  🎯 Critical Services:")
            for service_risk in risks['highly_depended_services']:
                print(f"     {service_risk['service']} ({service_risk['dependent_count']} dependencies)")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Trading System Monitoring Tools")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Log analysis command
    log_parser = subparsers.add_parser('logs', help='Analyze system logs')
    log_parser.add_argument('--lines', type=int, default=100, help='Number of recent lines to analyze')
    log_parser.add_argument('--watch', action='store_true', help='Watch logs in real-time')
    
    # Performance profiling command
    perf_parser = subparsers.add_parser('profile', help='Profile service performance')
    perf_parser.add_argument('--duration', type=int, default=300, help='Profiling duration in seconds')
    
    # Dependency mapping command
    dep_parser = subparsers.add_parser('dependencies', help='Map service dependencies')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # Initialize CLI
    cli = MonitoringToolsCLI()
    
    # Run appropriate command
    if args.command == 'logs':
        asyncio.run(cli.analyze_logs(args))
    elif args.command == 'profile':
        asyncio.run(cli.profile_performance(args))
    elif args.command == 'dependencies':
        asyncio.run(cli.map_dependencies(args))

if __name__ == "__main__":
    main()
