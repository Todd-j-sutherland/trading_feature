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
- `get_quick_reference` - Access command references by category (commands, architecture, troubleshooting, maintenance, validation_framework)
- `explain_file_purpose` - Understand what any file does in your system
- `get_system_architecture` - Get comprehensive architecture overview
- `get_validation_framework_info` - Get detailed validation framework information

### Resource URIs
- `trading://system/architecture` - Complete system architecture
- `trading://system/documentation` - Golden Standard Documentation  
- `trading://system/quick-reference` - Essential commands and operations
- `trading://system/validation-framework` - Comprehensive validation framework details

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
- **Validation Framework**: Comprehensive data integrity validation for dashboard, database, and ML components

### Validation Framework Context
- **Dashboard Validation**: MetricsValidator class validates ML performance, sentiment data, feature analysis
- **Database Validation**: Test suite validates sentiment scores, confidence ranges, RSI values, trading signals
- **ML Data Validation**: DataValidator class prevents data leakage, validates features and training data
- **Frontend Validation**: React dashboard displays validation status with visual indicators
- **Automated Reports**: Generates validation summaries, metrics exports, and quality assessments

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
6. **Validate Data Quality**: Access comprehensive validation framework information and commands

## 📊 Validation Framework Integration

The MCP server provides detailed access to the validation framework through:

### Validation Framework Tool
```bash
# Get complete validation framework overview
get_validation_framework_info()

# Get specific component information
get_validation_framework_info(component: "overview" | "components" | "commands" | "files" | "thresholds" | "examples")
```

### Quick Reference
```bash
# Access validation commands and procedures
get_quick_reference(category: "validation_framework")
```

### Validation Framework Coverage
- **4 Validation Components**: Dashboard metrics, database structure, ML data, frontend integration
- **Quality Thresholds**: Data quality (85%), confidence (60%), news coverage (70%), sentiment reliability (75%)
- **Automated Reports**: JSON metrics, validation results, human-readable summaries
- **File Locations**: `helpers/export_and_validate_metrics.py`, `tests/test_data_validation.py`, `app/core/ml/enhanced_training_pipeline.py`
- **Generated Files**: `metrics_exports/` with timestamped validation reports

## 🔗 Related Documentation

- `../GOLDEN_STANDARD_DOCUMENTATION.md` - Authoritative technical reference
- `../README.md` - Project overview and architecture
- `../ML_INTEGRATION_SUCCESS.md` - ML system implementation details

---

*This MCP server provides the foundation for AI-assisted development and maintenance of the ASX Trading System.*
