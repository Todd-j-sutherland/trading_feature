# 🌐 Remote Testing Guide for ASX Trading System

## 🎯 **Remote Server Testing Workflow**

Based on your Golden Standard Documentation, here's how to test all application features remotely:

---

## 🚀 **Step 1: Connect to Remote Server**

```bash
# Connect to your remote server
ssh root@170.64.199.151
```

## 📁 **Step 2: Navigate to Test Directory & Activate Environment**

```bash
# Navigate to the test directory
cd /path/to/test/directory  # Update with actual path

# Activate the remote Python environment
source ../trading_venv/bin/activate

# Verify environment is active
which python
python --version
```

---

## 🧪 **Step 3: Test Core Application Features**

### **Morning Analysis Test**
```bash
# Test morning analysis workflow
echo "🌅 Testing Morning Analysis..."
python -m app.main morning

# Expected output: Trading signals for 11 banks
# Check for: CBA.AX, ANZ.AX, WBC.AX, NAB.AX, etc.
```

### **Evening Analysis Test**
```bash
# Test evening analysis workflow  
echo "🌆 Testing Evening Analysis..."
python -m app.main evening

# Expected output: Model training, validation metrics
# Check for: validation files in metrics_exports/
```

### **Enhanced ML System Test**
```bash
# Test Enhanced ML data collection
echo "🤖 Testing Enhanced ML System..."
python enhanced_ml_system/multi_bank_data_collector.py

# Expected output: 11 banks analyzed, predictions generated
# Check for: data/multi_bank_analysis.db created
```

---

## 🔧 **Step 4: Test API Endpoints**

### **Start ML Backend**
```bash
# Start the ML API server
echo "🚀 Starting ML Backend..."
python enhanced_ml_system/realtime_ml_api.py &
ML_PID=$!

# Wait for startup
sleep 5

# Test API endpoints
echo "🧪 Testing API Endpoints..."
```

### **Test Predictions API**
```bash
# Test predictions endpoint
echo "📊 Testing Predictions API..."
curl -s "http://localhost:8001/api/predictions" | head -20

# Expected: JSON array with bank predictions
```

### **Test Market Summary API**
```bash
# Test market summary endpoint
echo "📈 Testing Market Summary API..."
curl -s "http://localhost:8001/api/market-summary" | python -m json.tool

# Expected: Market summary with totals and averages
```

---

## 📊 **Step 5: Test Validation Framework**

### **Generate Validation Metrics**
```bash
# Test validation metrics export
echo "✅ Testing Validation Framework..."
python export_and_validate_metrics.py

# Check generated files
ls -la metrics_exports/validation_*$(date +%Y%m%d)*

# View latest validation summary
cat metrics_exports/validation_summary_$(date +%Y%m%d)*.txt
```

### **Test Data Validation**
```bash
# Test ML data validator
echo "🔍 Testing Data Validation..."
python ml_data_validator.py

# Expected: Validation results for all components
```

---

## 🎨 **Step 6: Test Dashboard Generation**

### **Generate HTML Dashboard**
```bash
# Test HTML dashboard generation
echo "📊 Testing HTML Dashboard..."
python enhanced_ml_system/html_dashboard_generator.py

# Check generated dashboard
ls -la enhanced_ml_system/bank_performance_dashboard.html

# View file size (should be ~50-100KB)
du -h enhanced_ml_system/bank_performance_dashboard.html
```

### **Test Python Dashboard**
```bash
# Test Streamlit dashboard (if available)
echo "🖥️ Testing Python Dashboard..."
streamlit run dashboard.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

# Wait and test
sleep 10
curl -s "http://localhost:8501" | head -10
```

---

## 🔄 **Step 7: Test Complete System Integration**

### **Full System Test**
```bash
# Create comprehensive test script
cat > remote_system_test.sh << 'EOF'
#!/bin/bash
echo "🏦 ASX Trading System - Remote Integration Test"
echo "=============================================="

# Test morning analysis
echo "1. Testing Morning Analysis..."
python -m app.main morning > /tmp/morning_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Morning analysis: PASSED"
else
    echo "   ❌ Morning analysis: FAILED"
    cat /tmp/morning_test.log
fi

# Test enhanced ML collection
echo "2. Testing Enhanced ML Collection..."
python enhanced_ml_system/multi_bank_data_collector.py > /tmp/ml_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ ML collection: PASSED"
else
    echo "   ❌ ML collection: FAILED"
    cat /tmp/ml_test.log
fi

# Test validation framework
echo "3. Testing Validation Framework..."
python export_and_validate_metrics.py > /tmp/validation_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Validation: PASSED"
else
    echo "   ❌ Validation: FAILED"
    cat /tmp/validation_test.log
fi

# Test HTML dashboard
echo "4. Testing HTML Dashboard..."
python enhanced_ml_system/html_dashboard_generator.py > /tmp/dashboard_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ HTML Dashboard: PASSED"
else
    echo "   ❌ HTML Dashboard: FAILED"
    cat /tmp/dashboard_test.log
fi

# Start ML API and test
echo "5. Testing ML API..."
python enhanced_ml_system/realtime_ml_api.py &
API_PID=$!
sleep 8

# Test API endpoints
PREDICTIONS=$(curl -s "http://localhost:8001/api/predictions" | wc -c)
SUMMARY=$(curl -s "http://localhost:8001/api/market-summary" | wc -c)

if [ $PREDICTIONS -gt 100 ] && [ $SUMMARY -gt 50 ]; then
    echo "   ✅ ML API: PASSED"
else
    echo "   ❌ ML API: FAILED"
fi

# Cleanup
kill $API_PID 2>/dev/null

echo ""
echo "🎯 Remote Testing Complete!"
echo "Check individual logs in /tmp/ for detailed results"
EOF

# Make executable and run
chmod +x remote_system_test.sh
./remote_system_test.sh
```

---

## 📈 **Step 8: Performance & Resource Testing**

### **Memory Usage Test**
```bash
# Monitor memory usage during operations
echo "💾 Testing Memory Usage..."
free -h

# Run memory-intensive operation
SKIP_TRANSFORMERS=1 python -m app.main evening &
EVENING_PID=$!

# Monitor during execution
while kill -0 $EVENING_PID 2>/dev/null; do
    ps -p $EVENING_PID -o pid,ppid,cmd,%mem,%cpu
    sleep 10
done
```

### **Database Performance Test**
```bash
# Test database operations
echo "🗄️ Testing Database Performance..."
time sqlite3 data/ml_models/training_data.db "SELECT COUNT(*) FROM enhanced_predictions;"

# Test data integrity
python -c "
import sqlite3
conn = sqlite3.connect('data/ml_models/training_data.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM enhanced_predictions')
count = cursor.fetchone()[0]
print(f'✅ Database records: {count}')
conn.close()
"
```

---

## 🔍 **Step 9: Troubleshooting Common Remote Issues**

### **Port Availability Check**
```bash
# Check if required ports are available
echo "🔌 Checking Port Availability..."
netstat -tuln | grep -E ":800[01]"

# If ports are busy, find processes
lsof -i :8000
lsof -i :8001
```

### **Environment Validation**
```bash
# Validate Python environment
echo "🐍 Validating Python Environment..."
python -c "
import sys
print(f'Python version: {sys.version}')
print(f'Python path: {sys.executable}')

# Test critical imports
try:
    import pandas as pd
    print('✅ Pandas available')
except ImportError:
    print('❌ Pandas missing')

try:
    import yfinance as yf
    print('✅ YFinance available')
except ImportError:
    print('❌ YFinance missing')

try:
    from fastapi import FastAPI
    print('✅ FastAPI available')
except ImportError:
    print('❌ FastAPI missing')
"
```

### **File System Check**
```bash
# Check disk space and permissions
echo "📁 Checking File System..."
df -h .
ls -la data/
ls -la enhanced_ml_system/
ls -la metrics_exports/ 2>/dev/null || mkdir -p metrics_exports
```

---

## 🎯 **Step 10: Remote Access Testing**

### **Test External Access (if needed)**
```bash
# If testing external access to APIs
echo "🌐 Testing External Access..."

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)
echo "Server IP: $SERVER_IP"

# Start API with external binding
python enhanced_ml_system/realtime_ml_api.py --host 0.0.0.0 --port 8001 &
API_PID=$!

# Test from external (replace with your local IP)
# curl "http://$SERVER_IP:8001/api/market-summary"
```

---

## 📋 **Quick Remote Test Summary**

```bash
# One-liner comprehensive test
echo "🚀 Quick Remote Test..." && \
python -m app.main morning && \
python enhanced_ml_system/multi_bank_data_collector.py && \
python export_and_validate_metrics.py && \
python enhanced_ml_system/html_dashboard_generator.py && \
echo "✅ All core features tested successfully!"
```

---

## 🔧 **Cleanup After Testing**

```bash
# Stop any background processes
pkill -f "realtime_ml_api"
pkill -f "streamlit"

# Check system resources
echo "💾 Final System Status:"
free -h
df -h
ps aux | grep python | grep -v grep
```

---

## 📊 **Expected Results Summary**

After successful remote testing, you should see:

✅ **Morning Analysis**: Trading signals for 11 Australian banks  
✅ **Evening Analysis**: Model training and validation metrics  
✅ **Enhanced ML**: Real-time predictions and data collection  
✅ **API Endpoints**: Functional /api/predictions and /api/market-summary  
✅ **Validation Framework**: Generated metrics in metrics_exports/  
✅ **HTML Dashboard**: bank_performance_dashboard.html created  
✅ **Database Operations**: SQLite database with prediction data  
✅ **System Resources**: Acceptable memory and CPU usage  

Use this guide to systematically test all features of your ASX Trading System on the remote server!
