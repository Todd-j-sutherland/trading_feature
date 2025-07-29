# 🎯 MCP Server Usage Examples

## How Copilot Will Now Help You

### **Before MCP Server:**
```
You: "How do I start the system?"
Copilot: "Try running python main.py or npm start"
```

### **After MCP Server:**
```
You: "How do I start the system?"
Copilot: "Use the complete system startup:
1. pkill -f python && pkill -f node
2. ./start_complete_ml_system.sh
3. Verify with: ps aux | grep -E '(api_server|realtime_ml_api|node.*serve)'"
```

### **File Context Examples:**
```
You: "What does enhanced_evening_analyzer_with_ml.py do?"
Copilot: "This is the evening ML training routine that:
- Processes collected sentiment data
- Trains ensemble models with 54+ features  
- Exports validation metrics
- Updates the ML performance database
- Runs comprehensive backtesting"
```

### **System Knowledge:**
```
You: "Why am I getting 'insufficient training data' warnings?"
Copilot: "You have 75 features but 0 outcomes. This means:
- Predictions have been made but not enough time passed
- Need 10+ outcomes for basic training (3-5 days)
- Need 50+ outcomes for reliable models (2-3 weeks)
- Run the outcome recording check command to monitor progress"
```

## 🚀 **Direct MCP Server Commands**

You can also interact with the MCP server directly for development:

### Get System Architecture:
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_system_architecture", "arguments": {}}}' | npm run dev
```

### Get Quick Commands Reference:
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_quick_reference", "arguments": {"category": "commands"}}}' | npm run dev
```

### Explain Any File:
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "explain_file_purpose", "arguments": {"filepath": "app/main.py"}}}' | npm run dev
```

## ✅ **Verification**

Your MCP server is working when:
1. VS Code restarts without errors
2. Copilot gives specific, accurate answers about your trading system  
3. AI assistants reference your actual file names and commands
4. Responses include your specific ports (8000, 8001, 3002)
5. Troubleshooting suggestions match your Golden Standard docs
