#!/usr/bin/env python3
"""
Check Moomoo account API status
"""

def check_opend_logs():
    """Look for OpenD error messages"""
    import subprocess
    import os
    
    print("🔍 Checking for OpenD error messages...")
    
    # Check if OpenD is outputting anything
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        opend_lines = [line for line in result.stdout.split('\n') if 'OpenD' in line and 'opendirectoryd' not in line]
        
        print(f"Found {len(opend_lines)} OpenD processes:")
        for line in opend_lines:
            print(f"  {line}")
        
        # Check if there are any recent log files
        log_paths = [
            os.path.expanduser("~/Library/Application Support/cn.futu.FutuOpenDGUI"),
            os.path.expanduser("~/Library/Logs"),
            "/tmp"
        ]
        
        print("\n📁 Looking for OpenD log files...")
        for path in log_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if any(term in file.lower() for term in ['opend', 'futu', 'log']):
                            full_path = os.path.join(root, file)
                            print(f"  Found: {full_path}")
                            
                            # Try to read recent log entries
                            try:
                                with open(full_path, 'r') as f:
                                    lines = f.readlines()[-10:]  # Last 10 lines
                                    if any('api' in line.lower() or 'error' in line.lower() for line in lines):
                                        print(f"    Recent entries from {file}:")
                                        for line in lines[-5:]:
                                            if line.strip():
                                                print(f"      {line.strip()}")
                            except:
                                pass
        
    except Exception as e:
        print(f"Error checking logs: {e}")

def main():
    print("Moomoo Account API Status Checker")
    print("=" * 35)
    
    check_opend_logs()
    
    print("\n💡 Next Steps to Enable API Access:")
    print("1. In Moomoo App/Website:")
    print("   - Go to Settings → Account → API Settings")
    print("   - Enable 'OpenAPI Access'")
    print("   - Accept Terms and Conditions")
    print("   - Set API trading permissions")
    print()
    print("2. Common locations for API settings:")
    print("   - Account Settings → Security → API")
    print("   - Trading → API Trading")
    print("   - Profile → Developer Settings")
    print()
    print("3. If you can't find these options:")
    print("   - Contact Moomoo Support")
    print("   - Ask for 'OpenAPI access enablement'")
    print("   - Mention you want paper trading API access")

if __name__ == '__main__':
    main()