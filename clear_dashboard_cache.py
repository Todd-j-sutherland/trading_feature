#!/usr/bin/env python3
"""
Clear dashboard and Python caches for fresh runs
"""

import os
import shutil
import subprocess
import sys

def clear_all_caches():
    """Clear streamlit, Python, and browser caches"""
    
    print('🧹 CLEARING ALL CACHES')
    print('=' * 40)
    
    # Clear streamlit cache directories
    cache_dirs = [
        os.path.expanduser('~/.streamlit'),
        '/tmp/.streamlit',
        '/root/.streamlit',
        '.streamlit'
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f'✅ Cleared streamlit cache: {cache_dir}')
            except Exception as e:
                print(f'⚠️ Could not clear {cache_dir}: {e}')
    
    # Clear Python bytecode cache
    try:
        subprocess.run(['find', '/root/test', '-name', '*.pyc', '-delete'], 
                      capture_output=True, check=True)
        print('✅ Cleared Python .pyc files')
    except Exception as e:
        print(f'⚠️ Could not clear .pyc files: {e}')
    
    try:
        subprocess.run(['find', '/root/test', '-name', '__pycache__', '-type', 'd', 
                       '-exec', 'rm', '-rf', '{}', '+'], capture_output=True)
        print('✅ Cleared __pycache__ directories')
    except Exception as e:
        print(f'⚠️ Could not clear __pycache__: {e}')
    
    # Clear any existing streamlit processes
    try:
        subprocess.run(['pkill', '-f', 'streamlit'], capture_output=True)
        print('✅ Stopped existing streamlit processes')
    except Exception as e:
        pass  # It's OK if no processes are running
    
    print('\n🎉 Cache clearing complete!')
    print('📝 Recommendation: Refresh your browser to clear browser cache too')

if __name__ == '__main__':
    clear_all_caches()
