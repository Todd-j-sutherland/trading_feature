#!/usr/bin/env python3
"""
Advanced Daily Collection - Automated daily data collection with progress tracking
Runs comprehensive daily collection with notifications and milestone tracking
"""
import time
import json
import os
from datetime import datetime, timedelta
from news_trading_analyzer import NewsTradingAnalyzer
from app.core.ml.training.pipeline import MLTrainingPipeline
from smart_collector import SmartCollector

class AdvancedDailyCollector:
    def __init__(self):
        self.analyzer = NewsTradingAnalyzer()
        self.ml_pipeline = MLTrainingPipeline()
        self.smart_collector = SmartCollector()
        self.daily_stats = self.load_daily_stats()
        self.milestones = [25, 50, 100, 200, 500]
        
    def load_daily_stats(self):
        """Load daily collection statistics"""
        stats_file = 'data/ml_models/daily_collection_stats.json'
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                return json.load(f)
        return {'total_samples': 0, 'daily_progress': {}}
    
    def save_daily_stats(self):
        """Save daily collection statistics"""
        os.makedirs('data/ml_models', exist_ok=True)
        with open('data/ml_models/daily_collection_stats.json', 'w') as f:
            json.dump(self.daily_stats, f, indent=2)
    
    def run_comprehensive_collection(self):
        """Run comprehensive daily collection"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        print(f"🚀 Starting comprehensive collection for {today}")
        
        # Initialize daily stats
        if today not in self.daily_stats['daily_progress']:
            self.daily_stats['daily_progress'][today] = {
                'samples_start': self.get_current_sample_count(),
                'signals_collected': 0,
                'outcomes_recorded': 0,
                'high_quality_signals': 0,
                'start_time': datetime.now().isoformat()
            }
        
        daily_stats = self.daily_stats['daily_progress'][today]
        
        # Run multiple collection cycles throughout the day
        cycle_count = 0
        max_cycles = 24  # Run for up to 24 hours
        
        while cycle_count < max_cycles:
            try:
                print(f"\n🔄 Collection cycle {cycle_count + 1}/{max_cycles}")
                
                # Run smart collector cycle
                self.smart_collector.run_collection_cycle()
                
                # Update daily stats
                current_samples = self.get_current_sample_count()
                daily_stats['samples_collected'] = current_samples - daily_stats['samples_start']
                daily_stats['signals_collected'] += self.smart_collector.collection_stats['signals_today']
                daily_stats['outcomes_recorded'] += self.smart_collector.collection_stats['outcomes_recorded']
                
                # Check for milestones
                self.check_milestones(current_samples)
                
                # Print progress
                self.print_daily_progress(daily_stats)
                
                # Reset smart collector daily stats
                self.smart_collector.collection_stats = {'signals_today': 0, 'outcomes_recorded': 0}
                
                cycle_count += 1
                
                # Wait between cycles (1 hour)
                if cycle_count < max_cycles:
                    print("💤 Sleeping for 1 hour...")
                    time.sleep(3600)  # 1 hour
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping daily collection...")
                break
            except Exception as e:
                print(f"❌ Error in collection cycle: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
        
        # Finalize daily stats
        daily_stats['end_time'] = datetime.now().isoformat()
        daily_stats['samples_end'] = self.get_current_sample_count()
        daily_stats['total_samples_collected'] = daily_stats['samples_end'] - daily_stats['samples_start']
        
        self.save_daily_stats()
        self.generate_daily_report(today, daily_stats)
    
    def get_current_sample_count(self):
        """Get current total sample count"""
        try:
            X, y = self.ml_pipeline.prepare_training_dataset(min_samples=1)
            return len(X) if X is not None else 0
        except:
            return 0
    
    def check_milestones(self, current_samples):
        """Check if we've hit any milestones"""
        for milestone in self.milestones:
            if current_samples >= milestone and milestone not in self.daily_stats.get('milestones_reached', []):
                self.celebrate_milestone(milestone)
                
                if 'milestones_reached' not in self.daily_stats:
                    self.daily_stats['milestones_reached'] = []
                self.daily_stats['milestones_reached'].append(milestone)
    
    def celebrate_milestone(self, milestone):
        """Celebrate reaching a milestone"""
        print(f"\n🎉 MILESTONE REACHED: {milestone} SAMPLES! 🎉")
        print("=" * 50)
        
        if milestone == 25:
            print("✅ Basic training dataset ready!")
        elif milestone == 50:
            print("✅ Ready for initial model training!")
            print("Run: python scripts/retrain_ml_models.py --min-samples 50")
        elif milestone == 100:
            print("✅ Solid training dataset!")
            print("Models should show good performance now.")
        elif milestone == 200:
            print("✅ Excellent dataset for advanced models!")
        elif milestone == 500:
            print("✅ Production-ready dataset!")
            print("Time to implement full automated trading!")
        
        print("=" * 50)
    
    def print_daily_progress(self, daily_stats):
        """Print daily progress summary"""
        print(f"\n📊 Daily Progress Summary:")
        print(f"   Samples collected today: {daily_stats.get('samples_collected', 0)}")
        print(f"   Signals collected: {daily_stats.get('signals_collected', 0)}")
        print(f"   Outcomes recorded: {daily_stats.get('outcomes_recorded', 0)}")
        print(f"   Total samples: {daily_stats.get('samples_end', daily_stats.get('samples_start', 0))}")
        
        # Calculate collection rate
        start_time = datetime.fromisoformat(daily_stats['start_time'])
        hours_running = (datetime.now() - start_time).total_seconds() / 3600
        
        if hours_running > 0:
            rate = daily_stats.get('samples_collected', 0) / hours_running
            print(f"   Collection rate: {rate:.1f} samples/hour")
    
    def generate_daily_report(self, date, daily_stats):
        """Generate detailed daily report"""
        report_file = f'reports/daily_ml_collection_{date}.json'
        os.makedirs('reports', exist_ok=True)
        
        report = {
            'date': date,
            'collection_stats': daily_stats,
            'milestones_reached': self.daily_stats.get('milestones_reached', []),
            'total_samples': daily_stats.get('samples_end', 0),
            'performance_metrics': self.get_performance_metrics(),
            'recommendations': self.get_recommendations(daily_stats)
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Daily report saved: {report_file}")
        
        # Print summary
        print(f"\n📋 Daily Collection Summary ({date}):")
        print(f"   Total samples collected: {daily_stats.get('samples_collected', 0)}")
        print(f"   New total samples: {daily_stats.get('samples_end', 0)}")
        print(f"   Collection efficiency: {self.calculate_efficiency(daily_stats):.1%}")
        
        # Print recommendations
        for rec in report['recommendations']:
            print(f"   💡 {rec}")
    
    def get_performance_metrics(self):
        """Get ML performance metrics"""
        try:
            X, y = self.ml_pipeline.prepare_training_dataset(min_samples=1)
            if X is not None:
                class_balance = y.value_counts().to_dict()
                return {
                    'total_samples': len(X),
                    'class_balance': class_balance,
                    'features_count': len(X.columns),
                    'data_quality': 'Good' if len(X) > 50 else 'Developing'
                }
        except:
            pass
        return {'status': 'No data available'}
    
    def get_recommendations(self, daily_stats):
        """Get recommendations based on daily performance"""
        recommendations = []
        
        samples_collected = daily_stats.get('samples_collected', 0)
        total_samples = daily_stats.get('samples_end', 0)
        
        if samples_collected < 5:
            recommendations.append("Low collection rate - consider running more frequently")
        
        if total_samples < 50:
            recommendations.append("Need more samples for training - continue daily collection")
        elif total_samples < 100:
            recommendations.append("Consider initial model training")
        else:
            recommendations.append("Excellent dataset - ready for advanced ML strategies")
        
        return recommendations
    
    def calculate_efficiency(self, daily_stats):
        """Calculate collection efficiency"""
        signals = daily_stats.get('signals_collected', 0)
        outcomes = daily_stats.get('outcomes_recorded', 0)
        
        if signals == 0:
            return 0
        
        return outcomes / signals
    
    def run_notification_system(self):
        """Run simple notification system"""
        print("🔔 Notification system active")
        
        # Check for important events
        current_samples = self.get_current_sample_count()
        
        # Check if we're close to a milestone
        for milestone in self.milestones:
            if milestone not in self.daily_stats.get('milestones_reached', []):
                if current_samples >= milestone * 0.9:  # 90% of milestone
                    remaining = milestone - current_samples
                    print(f"🎯 Close to milestone: {remaining} samples until {milestone}!")
                break

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced daily ML collection')
    parser.add_argument('--report-only', action='store_true', help='Generate report only')
    parser.add_argument('--notifications', action='store_true', help='Run notification system')
    
    args = parser.parse_args()
    
    collector = AdvancedDailyCollector()
    
    if args.report_only:
        today = datetime.now().strftime('%Y-%m-%d')
        if today in collector.daily_stats['daily_progress']:
            collector.generate_daily_report(today, collector.daily_stats['daily_progress'][today])
        else:
            print("No data for today")
    elif args.notifications:
        collector.run_notification_system()
    else:
        collector.run_comprehensive_collection()
