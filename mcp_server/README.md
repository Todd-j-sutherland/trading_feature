# ASX Trading System MCP Server

A Model Context Protocol (MCP) server that provides comprehensive context about the ASX Trading System to VS Code Copilot and AI agents.

## 🎯 Purpose

This MCP server gives AI assistants deep understanding of your trading system by providing:

- **System Architecture**: Complete overview of components, data flow, and ML pipeline
- **File Context**: Purpose and role of every file in the project
- **Operations Guide**: Commands, troubleshooting, and maintenance procedures
- **Quick References**: Essential commands and system status checks

## 🚀 Setup

1. **Install and configure:**
   ```bash
   cd mcp_server
   ./setup.sh
   ```

2. **Restart VS Code** to load the new MCP server

3. **Verify setup:**
   ```bash
   npm run dev
   ```

## 🛠️ Available Tools

### Core Tools
- `read_project_file` - Read any file from the trading system
- `list_directory` - Browse project structure with purpose explanations
- `get_system_status` - Check current system health and component status
- `get_quick_reference` - Access command references by category
- `explain_file_purpose` - Understand what any file does in your system
- `get_system_architecture` - Get comprehensive architecture overview

### Resource URIs
- `trading://system/architecture` - Complete system architecture
- `trading://system/documentation` - Golden Standard Documentation  
- `trading://system/quick-reference` - Essential commands and operations

## 📊 System Context Provided

### Architecture Overview
- **Dual Backend**: Port 8000 (original) + Port 8001 (enhanced ML)
- **Frontend**: React dashboard on Port 3002
- **ML Pipeline**: Two-stage sentiment analysis with 54+ features
- **Data Flow**: Morning collection → Evening training → Real-time predictions

### File Categories
- **Core Application** (`app/`): Main CLI, sentiment engine, dashboard
- **ML Pipeline** (`enhanced_ml_system/`): Advanced ML with ensemble models
- **Frontend** (`frontend/`): React with interactive charts
- **Data** (`data/`): ML models, cache, historical data
- **Scripts**: Automation, deployment, monitoring
- **Documentation**: Guides, references, troubleshooting

### Operations Context
- **Daily Commands**: morning, evening, dashboard, status
- **System Management**: startup, shutdown, monitoring
- **Troubleshooting**: Port conflicts, memory issues, data validation
- **Remote Deployment**: Server management, cron jobs, monitoring

## 🔧 Development

```bash
# Development mode
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 📁 Structure

```
mcp_server/
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── setup.sh             # Installation and VS Code setup
├── src/
│   └── index.ts         # Main MCP server implementation
└── dist/                # Compiled JavaScript (generated)
```

## 🎯 Integration Benefits

With this MCP server, AI assistants can:

1. **Understand Context**: Know what every file does and how components relate
2. **Provide Accurate Help**: Reference actual system architecture and commands
3. **Troubleshoot Effectively**: Access real troubleshooting guides and status checks
4. **Maintain Consistency**: Use authoritative documentation as reference
5. **Navigate Complexity**: Handle the large codebase with proper context

## 🔗 Related Documentation

- `../GOLDEN_STANDARD_DOCUMENTATION.md` - Authoritative technical reference
- `../README.md` - Project overview and architecture
- `../ML_INTEGRATION_SUCCESS.md` - ML system implementation details

---

*This MCP server provides the foundation for AI-assisted development and maintenance of the ASX Trading System.*
