# MCP Server Configuration Guide

## Local Workspace Configuration (Recommended)
The MCP server is now configured in `.vscode/settings.json` for this workspace.

## Global Configuration (Alternative)
If you want to use this MCP server in all VS Code workspaces, add this to your global settings:

1. Open VS Code Command Palette (Cmd+Shift+P)
2. Type "Preferences: Open User Settings (JSON)"
3. Add this configuration:

```json
{
  "github.copilot.chat.mcp.servers": {
    "asx-trading-system": {
      "command": "node",
      "args": ["/Users/toddsutherland/Repos/trading_feature/mcp_server/dist/index.js"],
      "env": {}
    }
  }
}
```

## Steps to Activate

1. **Restart VS Code** - MCP server configurations require a restart
2. **Open Copilot Chat** - Use Cmd+Shift+I or click the chat icon
3. **Check for Tools** - Your MCP server tools should appear in the tool selection

## Available Tools from Your MCP Server

- `get_trading_system_info` - Get comprehensive trading system information
- `get_validation_framework_info` - Get validation framework details
- `get_ml_system_status` - Get ML system status and metrics
- `get_system_health` - Get overall system health check

## Troubleshooting

If the MCP server doesn't appear:
1. Check the build completed: `cd mcp_server && npm run build`
2. Test the server manually: `cd mcp_server && npm start`
3. Restart VS Code completely
4. Check VS Code output panel for MCP-related errors

## Testing the Connection

Once configured, you should be able to ask Copilot Chat:
- "What is the current trading system status?"
- "Show me the validation framework information"
- "Check the ML system health"
