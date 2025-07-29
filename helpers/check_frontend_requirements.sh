#!/bin/bash
echo "🔍 Remote Frontend Diagnostics"
echo "============================="

echo "📁 Current directory: $(pwd)"
echo "📁 Frontend directory exists: $([ -d "frontend" ] && echo "YES" || echo "NO")"
echo "📁 Package.json exists: $([ -f "frontend/package.json" ] && echo "YES" || echo "NO")"
echo "📦 Node.js version: $(node --version 2>/dev/null || echo "NOT INSTALLED")"
echo "📦 NPM version: $(npm --version 2>/dev/null || echo "NOT INSTALLED")"

if [ -d "frontend" ]; then
    echo "📁 Frontend directory contents:"
    ls -la frontend/ | head -10
    
    if [ -f "frontend/package.json" ]; then
        echo "📋 Package.json scripts:"
        grep -A 10 '"scripts"' frontend/package.json || echo "No scripts section found"
    fi
fi

echo ""
echo "🔧 Node.js Installation Check:"
which node || echo "Node.js not found in PATH"
which npm || echo "NPM not found in PATH"

echo ""
echo "🌐 Port availability check:"
netstat -ln | grep -E ":3000|:3001|:3002" || echo "Ports 3000-3002 are available"
