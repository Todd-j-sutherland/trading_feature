#!/usr/bin/env bash

# ASX Trading System MCP Server Setup Script

set -e

echo "🚀 Setting up ASX Trading System MCP Server..."

# Change to MCP server directory
cd "$(dirname "$0")"

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Build the TypeScript project
echo "🔨 Building TypeScript project..."
npm run build

# Create VS Code MCP settings file
echo "⚙️ Creating VS Code MCP configuration..."

# VS Code settings directory
VSCODE_SETTINGS_DIR="$HOME/.vscode"
MCP_CONFIG_FILE="$VSCODE_SETTINGS_DIR/mcp_servers.json"

# Create .vscode directory if it doesn't exist
mkdir -p "$VSCODE_SETTINGS_DIR"

# Create or update MCP servers configuration
cat > "$MCP_CONFIG_FILE" << 'EOF'
{
  "mcpServers": {
    "asx-trading-system": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "mcp_server",
      "env": {}
    }
  }
}
EOF

echo "✅ MCP Server setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Restart VS Code to load the new MCP server"
echo "2. Open your trading system project in VS Code"
echo "3. The MCP server will provide context about your system to Copilot"
echo ""
echo "🔧 Available MCP tools:"
echo "  - read_project_file: Read any file from the trading system"
echo "  - list_directory: Browse project structure with purpose explanations"
echo "  - get_system_status: Check current system health and component status"
echo "  - get_quick_reference: Access command references and troubleshooting"
echo "  - explain_file_purpose: Understand what any file does in your system"
echo "  - get_system_architecture: Get comprehensive architecture overview"
echo ""
echo "📚 Resources available:"
echo "  - trading://system/architecture: Complete system architecture"
echo "  - trading://system/documentation: Golden Standard Documentation"
echo "  - trading://system/quick-reference: Essential commands and operations"
echo ""
echo "🔍 To test the setup:"
echo "  cd mcp_server && npm run dev"
