#!/usr/bin/env bash

# ASX Trading System MCP Server Setup Script

set -e

echo "🚀 Setting up ASX Trading System MCP Server..."

# Get the absolute path of the MCP server directory
MCP_SERVER_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "📂 MCP Server directory: $MCP_SERVER_DIR"

# For your specific setup, we know the exact path
if [ -d "/Users/toddsutherland/Repos/trading_feature/mcp_server" ]; then
    MCP_SERVER_DIR="/Users/toddsutherland/Repos/trading_feature/mcp_server"
    echo "📂 Using known MCP Server path: $MCP_SERVER_DIR"
fi

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Build the TypeScript project
echo "🔨 Building TypeScript project..."
npm run build

# Verify build
if [ ! -f "dist/index.js" ]; then
    echo "❌ Build failed: dist/index.js not found"
    exit 1
fi

# Detect OS and set VS Code settings path
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    VSCODE_SETTINGS_DIR="$HOME/Library/Application Support/Code/User"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows
    VSCODE_SETTINGS_DIR="$APPDATA/Code/User"
else
    # Linux
    VSCODE_SETTINGS_DIR="$HOME/.config/Code/User"
fi

SETTINGS_FILE="$VSCODE_SETTINGS_DIR/settings.json"

echo "⚙️ Configuring VS Code settings at: $SETTINGS_FILE"

# Create VS Code settings directory if it doesn't exist
mkdir -p "$VSCODE_SETTINGS_DIR"

# Check if settings.json exists
if [ -f "$SETTINGS_FILE" ]; then
    # Backup existing settings
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📋 Backed up existing settings.json"
    
    # Use jq to add/update the MCP configuration if available
    if command -v jq &> /dev/null; then
        jq --arg mcp_path "$MCP_SERVER_DIR" \
           '.["github.copilot.chat.contextProviders"]["asx-trading-system"] = {
              "command": "node",
              "args": ["dist/index.js"],
              "cwd": $mcp_path,
              "env": {}
            }' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
        echo "✅ Updated settings.json with MCP configuration"
    else
        echo "⚠️  jq not found. Please manually add the following to your VS Code settings.json:"
        echo ""
        echo "Location: $SETTINGS_FILE"
        echo ""
        cat << EOF
"github.copilot.chat.contextProviders": {
  "asx-trading-system": {
    "command": "node",
    "args": ["dist/index.js"],
    "cwd": "/Users/toddsutherland/Repos/trading_feature/mcp_server",
    "env": {}
  }
}
EOF
    fi
else
    # Create new settings.json
    cat > "$SETTINGS_FILE" << EOF
{
  "github.copilot.chat.contextProviders": {
    "asx-trading-system": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "/Users/toddsutherland/Repos/trading_feature/mcp_server",
      "env": {}
    }
  }
}
EOF
    echo "✅ Created new settings.json with MCP configuration"
fi

# Test the MCP server
echo ""
echo "🧪 Testing MCP server..."
timeout 5s node dist/index.js 2>&1 | head -n 5 || true

echo ""
echo "✅ MCP Server setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Restart VS Code completely (not just reload window)"
echo "2. Open your trading system project in VS Code"
echo "3. In GitHub Copilot Chat, type @ and look for 'asx-trading-system'"
echo "4. If it doesn't appear, check VS Code settings (Cmd/Ctrl+,) and search for 'copilot.chat.contextProviders'"
echo ""
echo "🔧 Troubleshooting:"
echo "- Check VS Code Developer Tools (Help > Toggle Developer Tools) for errors"
echo "- Verify settings at: $SETTINGS_FILE"
echo "- Test server manually: cd /Users/toddsutherland/Repos/trading_feature/mcp_server && node dist/index.js"
echo ""
echo "📚 Available MCP tools once connected:"
echo "  - read_project_file: Read any file from the trading system"
echo "  - list_directory: Browse project structure"
echo "  - get_system_status: Check system health"
echo "  - get_quick_reference: Access command references"
echo "  - explain_file_purpose: Understand file purposes"
echo "  - get_system_architecture: Get architecture overview"