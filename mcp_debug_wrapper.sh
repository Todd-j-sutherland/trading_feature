#!/bin/bash

# MCP Server Debug Wrapper
# This wrapper logs when VS Code tries to start the MCP server

echo "$(date): MCP Server starting..." >> /tmp/mcp_debug.log
echo "Args: $@" >> /tmp/mcp_debug.log
echo "Working directory: $(pwd)" >> /tmp/mcp_debug.log

# Run the actual MCP server
node ./mcp_server/dist/index.js "$@" 2>&1 | tee -a /tmp/mcp_debug.log
