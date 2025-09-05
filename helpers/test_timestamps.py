#!/usr/bin/env python3
"""
Test script to simulate rapid data updates and check for timestamp ordering issues
"""
import time
import requests
import json

def test_timestamp_ordering():
    """Test that our API returns consistent timestamp ordering"""
    base_url = "http://localhost:8000"
    
    print("Testing timestamp ordering...")
    
    # Test multiple rapid calls to see timestamp consistency
    timestamps = []
    for i in range(5):
        try:
            response = requests.get(f"{base_url}/api/live/price/CBA.AX")
            if response.status_code == 200:
                data = response.json()
                if data['success'] and 'data' in data:
                    timestamp = data['data']['timestamp']
                    timestamps.append(timestamp)
                    print(f"Call {i+1}: timestamp = {timestamp} ({time.ctime(timestamp/1000)})")
            time.sleep(1)  # Wait 1 second between calls
        except Exception as e:
            print(f"Error on call {i+1}: {e}")
    
    # Check if timestamps are in order
    if len(timestamps) > 1:
        is_ordered = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
        print(f"\nTimestamps are {'properly ordered' if is_ordered else 'NOT properly ordered'}")
        
        # Show differences
        for i in range(1, len(timestamps)):
            diff = timestamps[i] - timestamps[i-1]
            print(f"Diff {i}: {diff}ms ({diff/1000:.1f} seconds)")
    else:
        print("Not enough data points to check ordering")

def test_historical_vs_live():
    """Test historical data timestamps vs live data timestamps"""
    base_url = "http://localhost:8000"
    
    print("\nTesting historical vs live timestamp compatibility...")
    
    try:
        # Get historical data
        hist_response = requests.get(f"{base_url}/api/banks/CBA.AX/ohlcv?period=1D")
        if hist_response.status_code == 200:
            hist_data = hist_response.json()
            if hist_data['success'] and hist_data['data']:
                last_hist_timestamp = hist_data['data'][-1]['timestamp']
                print(f"Last historical timestamp: {last_hist_timestamp} ({time.ctime(last_hist_timestamp)})")
                
                # Get live data
                live_response = requests.get(f"{base_url}/api/live/price/CBA.AX")
                if live_response.status_code == 200:
                    live_data = live_response.json()
                    if live_data['success'] and 'data' in live_data:
                        live_timestamp = live_data['data']['timestamp'] // 1000  # Convert to seconds
                        print(f"Live timestamp: {live_timestamp} ({time.ctime(live_timestamp)})")
                        
                        if live_timestamp > last_hist_timestamp:
                            print("✅ Live timestamp is newer than historical - OK")
                        else:
                            print("⚠️  Live timestamp is older than historical - POTENTIAL ISSUE")
                            print(f"   Difference: {last_hist_timestamp - live_timestamp} seconds")
    except Exception as e:
        print(f"Error testing timestamps: {e}")

if __name__ == "__main__":
    test_timestamp_ordering()
    test_historical_vs_live()
