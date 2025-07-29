#!/usr/bin/env bash

# MCP Server Context Update Helper Script

set -e

echo "🔄 MCP Server Context Update Helper"
echo ""

# Check if we're in the MCP server directory
if [[ ! -f "src/index.ts" ]]; then
    echo "❌ Error: Run this script from the mcp_server directory"
    echo "Usage: cd mcp_server && ./update_context.sh"
    exit 1
fi

echo "📝 Current context update options:"
echo "1. Rebuild existing context"
echo "2. Add new file purpose"
echo "3. Add new command reference"
echo "4. View current context"
echo "5. Test MCP server"
echo ""

read -p "Choose option (1-5): " choice

case $choice in
    1)
        echo "🔨 Rebuilding MCP server..."
        npm run build
        echo "✅ Rebuild complete!"
        ;;
    
    2)
        echo "📁 Adding new file purpose..."
        read -p "Enter file path (e.g., 'new_feature/analyzer.py'): " filepath
        read -p "Enter purpose description: " purpose
        
        echo ""
        echo "Add this to FILE_PURPOSES in src/index.ts:"
        echo "\"$filepath\": \"$purpose\","
        echo ""
        echo "Then run option 1 to rebuild."
        ;;
    
    3)
        echo "⚡ Adding new command reference..."
        read -p "Enter command category (e.g., 'new_feature'): " category
        read -p "Enter command name (e.g., 'start'): " cmd_name
        read -p "Enter command (e.g., 'python -m app.new_feature start'): " command
        
        echo ""
        echo "Add this to QUICK_REFERENCES.commands in src/index.ts:"
        echo "$category: {"
        echo "  $cmd_name: \"$command\""
        echo "},"
        echo ""
        echo "Then run option 1 to rebuild."
        ;;
    
    4)
        echo "📊 Current context overview:"
        echo ""
        echo "🔧 Available tools:"
        echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | npm run dev 2>/dev/null | grep -o '"name":"[^"]*"' | sed 's/"name":"//; s/"//; s/^/  - /'
        ;;
    
    5)
        echo "🧪 Testing MCP server..."
        echo ""
        echo "Testing tool list..."
        echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | npm run dev 2>/dev/null | jq '.result.tools | length' | xargs echo "Available tools:"
        
        echo ""
        echo "Testing system architecture..."
        echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_system_architecture", "arguments": {}}}' | npm run dev 2>/dev/null | jq -r '.result.content[0].text' | head -5
        
        echo ""
        echo "✅ MCP server test complete!"
        ;;
    
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "📚 For detailed update instructions, see:"
echo "  - CONTEXT_UPDATE_GUIDE.md"
echo "  - README.md"
