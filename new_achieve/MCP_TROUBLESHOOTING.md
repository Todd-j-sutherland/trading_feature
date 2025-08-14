# MCP Troubleshooting Steps

## Current Status
Your MCP server is built and ready, but not appearing in Copilot Chat.

## Step 1: Enable Experimental MCP Support
I've updated `.vscode/settings.json` to include:
```json
"github.copilot.chat.experimental.mcp.enabled": true
```

## Step 2: Add to Global Settings (Alternative)
If workspace settings don't work, add this to your global VS Code settings:

1. Open VS Code
2. Press Cmd+Shift+P 
3. Type "Preferences: Open User Settings (JSON)"
4. Add this configuration:

```json
{
  "github.copilot.chat.experimental.mcp.enabled": true,
  "github.copilot.chat.mcp.servers": {
    "asx-trading-system": {
      "command": "node",
      "args": ["/Users/toddsutherland/Repos/trading_feature/mcp_server/dist/index.js"],
      "env": {}
    }
  }
}
```

## Step 3: Restart VS Code Completely
- Close ALL VS Code windows
- Reopen VS Code
- Open this workspace

## Step 4: Check Copilot Chat
1. Open Copilot Chat (Cmd+Shift+I)
2. Look for:
   - Tool selection dropdown
   - @ symbol for mentioning tools
   - MCP server status in settings

## Step 5: Check VS Code Output Panel
1. View → Output
2. Select "GitHub Copilot Chat" from dropdown
3. Look for MCP-related messages or errors

## Step 6: Alternative - Test with Claude Desktop
If VS Code MCP isn't working, you can test with Claude Desktop:

1. Install Claude Desktop app
2. Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "asx-trading-system": {
      "command": "node",
      "args": ["/Users/toddsutherland/Repos/trading_feature/mcp_server/dist/index.js"]
    }
  }
}
```

## Troubleshooting Commands

Test MCP server manually:
```bash
cd /Users/toddsutherland/Repos/trading_feature/mcp_server
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}' | node dist/index.js
```

## Common Issues
- MCP is experimental - feature flag needed
- VS Code version too old
- Path issues in configuration
- Copilot Chat extension not updated
- Need complete VS Code restart

Try these steps in order and let me know what happens!
