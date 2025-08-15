#!/usr/bin/env python3
"""
Check Remote Trading Prediction Outcomes
Query the remote server for recent prediction outcomes and accuracy
"""

import subprocess
import json
from datetime import datetime, timedelta


def run_remote_command(command, server="root@170.64.199.151", remote_path="/root/test"):
    """Execute command on remote server"""
    full_command = f"ssh {server} 'cd {remote_path} && {command}'"
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Exception: {e}"


def check_remote_database_status():
    """Check if remote database exists and has data"""
    print("🔍 CHECKING REMOTE DATABASE STATUS")
    print("=" * 50)
    
    # Check if database exists
    db_check = run_remote_command("ls -la data/*.db 2>/dev/null || echo 'No databases found'")
    print(f"📁 Database Files:\n{db_check}\n")
    
    # Check main database tables
    db_path = "data/trading_predictions.db"
    table_check = run_remote_command(f'sqlite3 {db_path} "SELECT name FROM sqlite_master WHERE type=\'table\';" 2>/dev/null || echo "Database not accessible"')
    
    if "predictions" in table_check:
        print("✅ Database accessible with tables:")
        for table in table_check.split('\n'):
            if table.strip():
                print(f"   • {table}")
    else:
        print("❌ Database not accessible or no tables found")
        return False
    
    return True


def get_recent_prediction_outcomes():
    """Get recent prediction outcomes from remote server"""
    print("\n📊 RECENT PREDICTION OUTCOMES")
    print("=" * 50)
    
    # Get recent predictions with outcomes
    query = '''
    SELECT 
        symbol,
        date,
        time,
        signal,
        confidence,
        sentiment_score,
        status,
        outcome
    FROM predictions 
    WHERE status = "completed"
    ORDER BY date DESC, time DESC 
    LIMIT 20;
    '''
    
    result = run_remote_command(f'sqlite3 data/trading_predictions.db "{query}" 2>/dev/null')
    
    if "Error" in result or not result.strip():
        print("❌ No prediction data found or database error")
        return None
    
    print("Recent Completed Predictions:")
    print("-" * 80)
    print("Symbol   | Date       | Time  | Signal | Conf.  | Outcome")
    print("-" * 80)
    
    outcomes = []
    for line in result.split('\n'):
        if line.strip():
            parts = line.split('|')
            if len(parts) >= 8:
                symbol = parts[0]
                date = parts[1]
                time = parts[2]
                signal = parts[3]
                confidence = parts[4]
                outcome = parts[7]
                
                print(f"{symbol:8} | {date} | {time} | {signal:6} | {confidence:6} | {outcome}")
                outcomes.append({
                    'symbol': symbol,
                    'signal': signal,
                    'outcome': outcome,
                    'confidence': confidence
                })
    
    return outcomes


def calculate_success_metrics(outcomes):
    """Calculate success metrics from outcomes"""
    if not outcomes:
        return None
    
    print(f"\n📈 SUCCESS METRICS")
    print("=" * 50)
    
    total = len(outcomes)
    successful = sum(1 for o in outcomes if 'successful' in o['outcome'].lower())
    neutral = sum(1 for o in outcomes if 'neutral' in o['outcome'].lower())
    
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"Total Predictions: {total}")
    print(f"Successful: {successful}")
    print(f"Neutral/Pending: {neutral}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Break down by signal type
    print(f"\n📊 SUCCESS BY SIGNAL TYPE")
    print("-" * 30)
    
    for signal_type in ['BUY', 'SELL', 'HOLD']:
        signal_outcomes = [o for o in outcomes if o['signal'] == signal_type]
        if signal_outcomes:
            signal_total = len(signal_outcomes)
            signal_successful = sum(1 for o in signal_outcomes if 'successful' in o['outcome'].lower())
            signal_rate = (signal_successful / signal_total * 100) if signal_total > 0 else 0
            print(f"{signal_type:4}: {signal_successful:2}/{signal_total:2} ({signal_rate:5.1f}%)")
    
    return {
        'total': total,
        'successful': successful,
        'success_rate': success_rate
    }


def check_enhanced_outcomes():
    """Check enhanced outcomes table for more detailed results"""
    print(f"\n🎯 ENHANCED OUTCOMES ANALYSIS")
    print("=" * 50)
    
    # Query enhanced outcomes with returns
    query = '''
    SELECT 
        symbol,
        DATE(prediction_timestamp) as date,
        optimal_action,
        confidence_score,
        return_pct,
        CASE 
            WHEN optimal_action = "BUY" AND return_pct > 0 THEN "CORRECT"
            WHEN optimal_action = "SELL" AND return_pct < 0 THEN "CORRECT"
            WHEN optimal_action = "HOLD" AND ABS(return_pct) < 1.0 THEN "CORRECT"
            ELSE "WRONG"
        END as accuracy
    FROM enhanced_outcomes 
    WHERE return_pct != 0 
    AND prediction_timestamp >= date("now", "-7 days")
    ORDER BY prediction_timestamp DESC 
    LIMIT 15;
    '''
    
    result = run_remote_command(f'sqlite3 data/trading_predictions.db "{query}" 2>/dev/null')
    
    if "Error" in result or not result.strip():
        print("❌ No enhanced outcomes data found")
        return None
    
    print("Recent Enhanced Outcomes (Last 7 Days):")
    print("-" * 80)
    print("Symbol   | Date       | Action | Conf. | Return | Accuracy")
    print("-" * 80)
    
    correct_count = 0
    total_count = 0
    
    for line in result.split('\n'):
        if line.strip():
            parts = line.split('|')
            if len(parts) >= 6:
                symbol = parts[0]
                date = parts[1]
                action = parts[2]
                confidence = float(parts[3]) if parts[3] else 0
                return_pct = float(parts[4]) if parts[4] else 0
                accuracy = parts[5]
                
                print(f"{symbol:8} | {date} | {action:6} | {confidence:4.1f}% | {return_pct:+5.2f}% | {accuracy}")
                
                total_count += 1
                if accuracy == "CORRECT":
                    correct_count += 1
    
    if total_count > 0:
        accuracy_rate = (correct_count / total_count * 100)
        print("-" * 80)
        print(f"Enhanced Accuracy: {correct_count}/{total_count} ({accuracy_rate:.1f}%)")
        
        return {
            'total': total_count,
            'correct': correct_count,
            'accuracy_rate': accuracy_rate
        }
    
    return None


def get_overall_statistics():
    """Get overall historical statistics"""
    print(f"\n📊 OVERALL HISTORICAL STATISTICS")
    print("=" * 50)
    
    # Get total counts
    stats_query = '''
    SELECT 
        COUNT(*) as total_predictions,
        COUNT(CASE WHEN status = "completed" THEN 1 END) as completed_predictions,
        COUNT(CASE WHEN outcome LIKE "%Successful%" THEN 1 END) as successful_count
    FROM predictions;
    '''
    
    result = run_remote_command(f'sqlite3 data/trading_predictions.db "{stats_query}" 2>/dev/null')
    
    if result and not "Error" in result:
        parts = result.strip().split('|')
        if len(parts) >= 3:
            total = int(parts[0])
            completed = int(parts[1])
            successful = int(parts[2])
            
            completion_rate = (completed / total * 100) if total > 0 else 0
            success_rate = (successful / completed * 100) if completed > 0 else 0
            
            print(f"Total Predictions Made: {total:,}")
            print(f"Completed Predictions: {completed:,}")
            print(f"Successful Trades: {successful:,}")
            print(f"Completion Rate: {completion_rate:.1f}%")
            print(f"Success Rate: {success_rate:.1f}%")
            
            return {
                'total': total,
                'completed': completed,
                'successful': successful,
                'success_rate': success_rate
            }
    
    print("❌ Unable to get overall statistics")
    return None


def main():
    """Main function to check remote outcomes"""
    print("🌐 REMOTE TRADING PREDICTION OUTCOMES CHECK")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check database status
    if not check_remote_database_status():
        print("❌ Cannot access remote database. Exiting.")
        return
    
    # Get recent outcomes
    recent_outcomes = get_recent_prediction_outcomes()
    
    if recent_outcomes:
        # Calculate success metrics
        metrics = calculate_success_metrics(recent_outcomes)
        
        # Check enhanced outcomes
        enhanced_metrics = check_enhanced_outcomes()
        
        # Get overall statistics
        overall_stats = get_overall_statistics()
        
        # Summary
        print(f"\n🏆 SUMMARY")
        print("=" * 50)
        
        if metrics:
            print(f"Recent Success Rate: {metrics['success_rate']:.1f}%")
        
        if enhanced_metrics:
            print(f"Enhanced Accuracy: {enhanced_metrics['accuracy_rate']:.1f}%")
        
        if overall_stats:
            print(f"Historical Success Rate: {overall_stats['success_rate']:.1f}%")
            print(f"Total System Predictions: {overall_stats['total']:,}")
        
        print(f"\n✅ Remote outcomes analysis complete!")
    
    else:
        print("❌ No recent prediction outcomes found")


if __name__ == "__main__":
    main()
