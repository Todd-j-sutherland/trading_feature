# 📚 MCP Server Context Update Guide

## 🔧 **How to Add More Context as Your Project Evolves**

### **1. Adding New File Purposes**

Edit `/mcp_server/src/index.ts` and update the `FILE_PURPOSES` object:

```typescript
const FILE_PURPOSES: Record<string, string> = {
  // Existing entries...
  
  // ADD NEW FILES HERE:
  "new_feature/analyzer.py": "New feature analyzer for XYZ functionality",
  "scripts/new_deployment.sh": "Automated deployment script for production",
  "data/new_models/": "Storage for new ML model implementations",
  
  // Pattern examples:
  "prefix/*.py": "All Python files in prefix/ directory do XYZ",
  "some_specific_file.ts": "Specific purpose of this TypeScript file"
};
```

### **2. Adding New Command References**

Update the `QUICK_REFERENCES` object to add new operational commands:

```typescript
const QUICK_REFERENCES: Record<string, any> = {
  commands: {
    // Existing commands...
    
    // ADD NEW COMMAND CATEGORIES:
    new_feature: {
      start: "python -m app.new_feature start",
      status: "python -m app.new_feature status", 
      deploy: "./scripts/deploy_new_feature.sh"
    },
    
    production_ops: {
      backup: "./scripts/backup_production.sh",
      restore: "./scripts/restore_production.sh",
      monitor: "python -m app.monitoring check"
    }
  },
  
  // ADD NEW REFERENCE CATEGORIES:
  new_architecture: {
    component1: "Description of new architectural component",
    component2: "How this fits into the overall system"
  }
};
```

### **3. Adding New System Architecture Context**

Update the `SYSTEM_ARCHITECTURE` object for major system changes:

```typescript
const SYSTEM_ARCHITECTURE = {
  core_components: {
    // Existing components...
    
    // ADD NEW COMPONENTS:
    "new_module/": "Purpose and role of new module",
    "enhanced_feature/": "Enhanced feature implementation details"
  },
  
  // ADD NEW ARCHITECTURE SECTIONS:
  new_backend: {
    "port_9000": "New service on port 9000",
    "description": "What this new backend does"
  },
  
  integrations: {
    "external_api": "Integration with external service",
    "new_database": "Purpose of new database component"
  }
};
```

## 🚀 **Quick Update Process**

### **Step 1: Edit the Context**
```bash
cd mcp_server
# Edit src/index.ts with your changes
code src/index.ts
```

### **Step 2: Rebuild and Deploy**
```bash
# Rebuild the TypeScript
npm run build

# Restart VS Code to load changes
# Or restart the MCP server if running separately
```

### **Step 3: Test New Context**
```bash
# Test that new context is working
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "explain_file_purpose", "arguments": {"filepath": "your_new_file.py"}}}' | npm run dev
```

## 📝 **Common Update Scenarios**

### **New Feature Added:**
```typescript
// 1. Add file purposes
"features/new_trading_strategy/": "Implementation of new trading strategy with ML integration",
"features/new_trading_strategy/analyzer.py": "Main analyzer for new strategy",
"features/new_trading_strategy/models.py": "ML models specific to new strategy",

// 2. Add commands
new_strategy: {
  train: "python -m features.new_trading_strategy train",
  backtest: "python -m features.new_trading_strategy backtest",
  deploy: "python -m features.new_trading_strategy deploy"
}
```

### **New API Endpoint:**
```typescript
// 1. Update architecture
"port_9001": "New API service for real-time alerts",

// 2. Add commands  
alerts: {
  start: "./start_alerts_service.sh",
  status: "curl http://localhost:9001/health",
  config: "python -m app.alerts configure"
}
```

### **New Data Source:**
```typescript
// 1. Add data context
"data/external_feeds/": "External market data feeds and processing",
"scripts/sync_external_data.sh": "Synchronization script for external data",

// 2. Add operational commands
data_sync: {
  manual: "./scripts/sync_external_data.sh",
  schedule: "crontab -l | grep sync_external",
  validate: "python validate_external_data.py"
}
```

## 🔄 **Automated Context Updates**

### **Create Update Scripts:**
```bash
# Create helper script for common updates
cat > mcp_server/update_context.sh << 'EOF'
#!/bin/bash
echo "🔄 Updating MCP Server Context..."

# Rebuild
npm run build

# Restart if needed  
if pgrep -f "tsx.*index.ts" > /dev/null; then
    echo "🔄 Restarting MCP server..."
    pkill -f "tsx.*index.ts"
    npm run dev &
fi

echo "✅ Context updated!"
EOF

chmod +x mcp_server/update_context.sh
```

### **Version Control Integration:**
```bash
# Add context updates to your git workflow
git add mcp_server/src/index.ts
git commit -m "Update MCP context: Add new feature XYZ"
```

## 📊 **Best Practices for Context Management**

### **1. Keep Context Current**
- Update when adding new major features
- Remove context for deprecated/removed files
- Keep command references accurate

### **2. Organize by Categories**
```typescript
const FILE_PURPOSES: Record<string, string> = {
  // === CORE APPLICATION ===
  "app/main.py": "...",
  
  // === ML PIPELINE ===  
  "enhanced_ml_system/": "...",
  
  // === NEW FEATURES ===
  "features/new_feature/": "...",
  
  // === UTILITIES ===
  "utils/": "..."
};
```

### **3. Use Descriptive Context**
```typescript
// ❌ Bad - too generic
"new_file.py": "Python file for trading"

// ✅ Good - specific and helpful  
"new_file.py": "ML model validator that checks prediction accuracy and exports performance metrics to dashboard"
```

## 🎯 **Context Update Checklist**

When adding new functionality:

- [ ] Add file purposes to `FILE_PURPOSES`
- [ ] Add relevant commands to `QUICK_REFERENCES.commands`
- [ ] Update architecture if adding new components
- [ ] Add troubleshooting steps if complex
- [ ] Rebuild: `npm run build`
- [ ] Test with Copilot to verify context is working
- [ ] Document the change in your project docs

This keeps your MCP server context accurate and ensures AI assistants always have up-to-date knowledge of your evolving trading system! 🚀
