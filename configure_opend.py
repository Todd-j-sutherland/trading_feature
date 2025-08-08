#!/usr/bin/env python3
"""
Helper script to configure OpenD connection
This will help diagnose OpenD connection issues
"""

import time
import socket
from moomoo import *

def check_opend_status():
    """Check if OpenD is running and accepting connections"""
    print("🔍 Checking OpenD Status...")
    
    # Check if port is open
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 11111))
        sock.close()
        
        if result == 0:
            print("✅ Port 11111 is open")
            return True
        else:
            print("❌ Port 11111 is not open")
            return False
    except Exception as e:
        print(f"❌ Error checking port: {e}")
        return False

def try_different_ports():
    """Try connecting to different common OpenD ports"""
    print("\n🔍 Trying different ports...")
    common_ports = [11111, 11112, 11113, 11110]
    
    for port in common_ports:
        try:
            print(f"Trying port {port}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                print(f"✅ Found OpenD on port {port}")
                return port
            else:
                print(f"❌ Port {port} not available")
        except Exception as e:
            print(f"❌ Error checking port {port}: {e}")
    
    return None

def test_moomoo_connection(port=11111):
    """Test Moomoo API connection"""
    print(f"\n🧪 Testing Moomoo connection on port {port}...")
    
    try:
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=port, timeout=5)
        
        # Try to get server version
        print("Attempting to connect...")
        ret, data = quote_ctx.get_market_snapshot(['HK.00700'])  # Tencent as test
        
        if ret == RET_OK:
            print("✅ Connection successful!")
            print(f"Sample data: {data.head(1) if not data.empty else 'No data'}")
        else:
            print(f"❌ Connection failed: {data}")
        
        quote_ctx.close()
        return ret == RET_OK
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    print("OpenD Configuration Helper")
    print("=" * 30)
    
    # Step 1: Check basic port availability
    port_open = check_opend_status()
    
    if not port_open:
        # Step 2: Try different ports
        available_port = try_different_ports()
        
        if available_port:
            print(f"\n💡 Try using port {available_port} instead of 11111")
            test_moomoo_connection(available_port)
        else:
            print("\n❌ No OpenD ports found. OpenD might not be fully started.")
            print("\n🔧 Troubleshooting steps:")
            print("1. Make sure OpenD app is running")
            print("2. Check if there's a login screen visible")
            print("3. Try restarting OpenD")
            print("4. Look for OpenD in system tray/menu bar")
    else:
        # Step 3: Test connection
        test_moomoo_connection()

if __name__ == '__main__':
    main()