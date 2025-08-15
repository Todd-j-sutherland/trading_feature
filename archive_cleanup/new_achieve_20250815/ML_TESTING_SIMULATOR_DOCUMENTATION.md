# ML Testing Simulator Documentation

## 🤖 Frontend ML Testing Simulator

The **ML Testing Simulator** is a built-in frontend component that allows you to test and validate the Enhanced ML system's predictions in real-time. It's designed to simulate and test the results from the evening `app.main` analysis with a comprehensive, user-friendly interface.

---

## 🎯 **What Is The ML Testing Simulator?**

The ML Testing Simulator is the **SimpleMLDashboard** component that provides:

- **Real-time testing** of all 11 Australian banks
- **ML prediction validation** with confidence scores
- **Interactive interface** to test Enhanced ML API responses
- **Comprehensive metrics display** for validation
- **Evening analysis simulation** in the browser

### **Key Purpose**
This simulator was built to test and validate the Enhanced ML system during development and to provide a way to interactively explore the ML predictions without running the full evening analysis workflow.

---

## 🚀 **How to Access the ML Testing Simulator**

### **Method 1: Frontend View Switcher (Recommended)**

1. **Start the complete system:**
   ```bash
   ./start_complete_ml_system.sh
   ```

2. **Navigate to the frontend:**
   ```
   http://localhost:3000
   ```

3. **Click the "🤖 ML Test" button** in the top-right header to switch to the ML Testing view

4. **The simulator will load automatically** and start fetching real-time data

### **Method 2: Direct Access to SimpleMLDashboard**

The ML Test view is powered by the `SimpleMLDashboard` component which connects directly to the Enhanced ML API.

---

## 📊 **What The Simulator Shows**

### **Market Summary Section**
- **Total Banks Analyzed**: Count of successfully analyzed banks
- **Average 1D Change**: Overall market performance 
- **Average Sentiment**: Market sentiment overview
- **Signal Distribution**: BUY/SELL/HOLD signal counts
- **Best/Worst Performers**: Top and bottom performers with details

### **Individual Bank Analysis**
For each of the 11 banks, the simulator displays:

```tsx
interface BankPrediction {
  symbol: string;           // e.g., "CBA.AX"
  bank_name: string;        // e.g., "Commonwealth Bank"
  sector: string;           // e.g., "Major Banks"
  current_price: number;    // Current stock price
  price_change_1d: number;  // 1-day % change
  price_change_5d: number;  // 5-day % change
  rsi: number;              // RSI technical indicator
  sentiment_score: number;  // Sentiment analysis (-1 to +1)
  sentiment_confidence: number; // Confidence in sentiment
  predicted_direction: string;  // "UP" or "DOWN"
  predicted_magnitude: number;  // Expected % change
  prediction_confidence: number; // ML confidence (0-1)
  optimal_action: string;   // "BUY", "SELL", "STRONG_BUY", etc.
  timestamp: string;        // When prediction was made
}
```

### **Visual Indicators**
- **Color-coded signals**: Green (BUY), Red (SELL), Yellow (HOLD)
- **Confidence meters**: Visual confidence scoring
- **Sentiment indicators**: Positive/negative sentiment display
- **Performance metrics**: Price change visualization
- **Real-time updates**: Auto-refresh every 30 seconds

---

## 🏗️ **Technical Architecture**

### **Data Flow**
```
SimpleMLDashboard → Enhanced ML API (Port 8001) → Real-time Predictions
                 ↓
            Display Results
```

### **API Endpoints Used**
```typescript
// Market summary data
GET http://localhost:8001/api/market-summary

// Individual bank predictions  
GET http://localhost:8001/api/bank-predictions

// Real-time updates via polling every 30 seconds
```

### **Component Structure**
```tsx
SimpleMLDashboard
├── Market Summary Cards
├── Bank Prediction Grid
├── Loading States
├── Error Handling
└── Auto-refresh Logic
```

---

## 🔧 **How to Use for Testing**

### **Testing Evening Analysis Results**

1. **Run Evening Analysis:**
   ```bash
   python -m app.main evening
   ```

2. **Start the Enhanced ML API:**
   ```bash
   # This should already be running from start_complete_ml_system.sh
   python enhanced_ml_system/realtime_ml_api.py
   ```

3. **Open the ML Testing Simulator:**
   ```
   http://localhost:3000
   Click "🤖 ML Test" button
   ```

4. **Validate Results:**
   - Check that all 11 banks appear
   - Verify prediction confidence scores
   - Compare with evening analysis logs
   - Test signal distribution makes sense

### **Real-time Testing Workflow**

```bash
# 1. Generate fresh ML data
python enhanced_ml_system/multi_bank_data_collector.py

# 2. The simulator will automatically pick up new data
# (Refreshes every 30 seconds)

# 3. Test specific scenarios:
#    - Check high-confidence predictions
#    - Verify sentiment alignment
#    - Validate technical indicators
```

### **Validation Checklist**

When using the simulator to test evening analysis results:

✅ **Data Completeness**
- All 11 banks should appear
- No missing price data
- All sentiment scores present
- Technical indicators calculated

✅ **Prediction Quality**  
- Confidence scores > 60% for most predictions
- Sentiment and technical alignment
- Reasonable action recommendations
- No extreme outliers

✅ **System Performance**
- Loading time < 5 seconds
- Auto-refresh working
- No error messages
- Responsive interface

---

## 🎯 **Testing Scenarios**

### **Scenario 1: Bullish Market**
- Look for multiple BUY signals
- High average sentiment scores
- RSI values in healthy ranges (30-70)
- Strong prediction confidence

### **Scenario 2: Bearish Market**
- Multiple SELL signals
- Negative sentiment scores
- RSI showing oversold conditions
- Clear directional signals

### **Scenario 3: Mixed Market**
- Balanced signal distribution
- Varying sentiment scores
- Some HOLD recommendations
- Mixed confidence levels

### **Scenario 4: High Volatility**
- Strong signals (STRONG_BUY/STRONG_SELL)
- High sentiment confidence
- Clear directional predictions
- RSI at extremes

---

## 🔍 **Troubleshooting the Simulator**

### **Common Issues**

**1. "Connection Error" Message**
```bash
# Check if Enhanced ML API is running
curl http://localhost:8001/api/market-summary

# If not running, start it:
python enhanced_ml_system/realtime_ml_api.py
```

**2. "Loading ML Dashboard..." Stuck**
```bash
# Check API server logs
# Usually means API is not responding

# Restart the complete system:
./start_complete_ml_system.sh
```

**3. Missing Bank Data**
```bash
# Run data collection first:
python enhanced_ml_system/multi_bank_data_collector.py

# Then refresh the simulator
```

**4. Outdated Predictions**
```bash
# Check timestamp in simulator
# If old, run fresh analysis:
python -m app.main evening
```

### **Debug Mode**

Add debug information to the simulator:
```tsx
// In SimpleMLDashboard.tsx, add console logging:
console.log('API Response:', predictions);
console.log('Market Summary:', marketSummary);
```

---

## 🚀 **Advanced Usage**

### **Custom Testing Scenarios**

You can modify the simulator for specific testing:

```tsx
// Test specific banks only
const testBanks = ['CBA.AX', 'ANZ.AX', 'WBC.AX'];
const filteredPredictions = predictions.filter(p => 
  testBanks.includes(p.symbol)
);
```

### **Performance Benchmarking**

Use the simulator to benchmark system performance:
```tsx
// Add timing measurements
const startTime = performance.now();
// ... fetch data ...
const endTime = performance.now();
console.log(`API Response Time: ${endTime - startTime}ms`);
```

### **Integration with Testing Scripts**

You can programmatically test the simulator:
```javascript
// Automated testing
fetch('http://localhost:8001/api/market-summary')
  .then(response => response.json())
  .then(data => {
    console.log('Market Summary Test:', data);
    // Add assertions here
  });
```

---

## 📁 **Related Files**

### **Core Simulator Files**
- `frontend/src/components/SimpleMLDashboard.tsx` - Main simulator component
- `frontend/src/pages/MLTestPage.tsx` - Standalone test page
- `frontend/src/App.tsx` - Main app with view switcher

### **Backend API Files**
- `enhanced_ml_system/realtime_ml_api.py` - ML API server (port 8001)
- `enhanced_ml_system/multi_bank_data_collector.py` - Data generation

### **Startup Scripts**
- `start_complete_ml_system.sh` - Starts entire system including simulator

---

## 🎯 **Summary**

The **ML Testing Simulator** (`SimpleMLDashboard`) is your go-to tool for:

1. **Testing evening analysis results** in a visual interface
2. **Validating ML predictions** with real-time data
3. **Debugging the Enhanced ML system** interactively  
4. **Monitoring system performance** during development
5. **Simulating trading scenarios** with live data

**Quick Access:** Start the system with `./start_complete_ml_system.sh`, go to `http://localhost:3000`, and click "🤖 ML Test" to begin testing!

This simulator makes it easy to validate your ML system's performance and test the results from your evening analysis workflow in an intuitive, visual way.
