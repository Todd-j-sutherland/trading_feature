Here's a comprehensive prompt and guideline for creating a modern front-end with TradingView lightweight charts:
VSCode Copilot Prompt
I need to create a modern web front-end for my ASX bank sentiment analysis system that uses TradingView Lightweight Charts to display machine learning indicators alongside price data.

Current System:
- Backend: Python with SQL database (sentiment_features table)
- ML predictions: sentiment scores, confidence levels, buy/sell signals
- Banks: CBA.AX, ANZ.AX, WBC.AX, NAB.AX, MQG.AX, SUN.AX, QBE.AX

Requirements:

1. Frontend Stack:
   - React 18+ with TypeScript
   - TradingView Lightweight Charts v4
   - Tailwind CSS for styling
   - Axios/Fetch for API calls
   - WebSocket for real-time updates

2. Chart Features:
   - Main price chart (candlestick/line)
   - ML sentiment indicator (line chart below price)
   - Confidence bands (shaded areas)
   - Buy/Sell signal markers on chart
   - Volume bars with sentiment coloring
   - Multi-timeframe support (1D, 1W, 1M)

3. ML Indicators to Display:
   - Sentiment score (-1 to +1) as oscillator
   - Confidence level (0-100%) as line
   - Signal markers (BUY/SELL/HOLD) as chart annotations
   - News event markers with impact scores
   - Technical score overlay

4. Dashboard Layout:
   - Top: Bank selector and timeframe buttons
   - Center: Main price chart with ML overlays
   - Bottom: ML indicator panel (sentiment oscillator)
   - Right sidebar: ML model insights (features used, confidence breakdown)
   - Left sidebar: Recent predictions table

5. API Endpoints Needed:
   - GET /api/banks/{symbol}/ohlcv?period={timeframe}
   - GET /api/banks/{symbol}/ml-indicators?period={timeframe}
   - GET /api/banks/{symbol}/predictions/latest
   - WS /api/stream/predictions for real-time updates

6. Interactive Features:
   - Hover to see ML prediction details
   - Click on signals to see full analysis
   - Sync crosshair between price and indicator charts
   - Export chart as image
   - Toggle ML indicators on/off

7. ML Transparency Panel:
   - Show live feature contributions
   - Display model confidence calculation
   - List data sources (news, reddit, technical)
   - Show prediction accuracy for timeframe

Please create a production-ready implementation with:
- Proper TypeScript types for all data
- Error boundaries for chart crashes
- Loading states during data fetch
- Responsive design for mobile
- Dark/light theme support
- Performance optimization for real-time updates
Implementation Guideline
Project Structure
frontend/
├── src/
│   ├── components/
│   │   ├── charts/
│   │   │   ├── PriceChart.tsx
│   │   │   ├── MLIndicatorChart.tsx
│   │   │   ├── ChartContainer.tsx
│   │   │   └── ChartControls.tsx
│   │   ├── ml/
│   │   │   ├── MLInsightsPanel.tsx
│   │   │   ├── PredictionTable.tsx
│   │   │   ├── FeatureContributions.tsx
│   │   │   └── ConfidenceBreakdown.tsx
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Layout.tsx
│   ├── hooks/
│   │   ├── useChartData.ts
│   │   ├── useMLPredictions.ts
│   │   ├── useWebSocket.ts
│   │   └── useChartSync.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── chartDataTransform.ts
│   │   └── mlDataTransform.ts
│   ├── types/
│   │   ├── chart.types.ts
│   │   ├── ml.types.ts
│   │   └── api.types.ts
│   └── utils/
│       ├── chartConfig.ts
│       ├── indicators.ts
│       └── formatters.ts
Key Implementation Details
1. Chart Setup Example
typescript// Initialize TradingView Lightweight Charts with ML indicators
const chartOptions = {
  layout: {
    background: { type: 'solid', color: '#1a1a1a' },
    textColor: '#d1d4dc',
  },
  grid: {
    vertLines: { color: '#2a2a2a' },
    horzLines: { color: '#2a2a2a' },
  },
  crosshair: {
    mode: CrosshairMode.Normal,
  },
  rightPriceScale: {
    borderColor: '#2a2a2a',
  },
  timeScale: {
    borderColor: '#2a2a2a',
    timeVisible: true,
    secondsVisible: false,
  },
};

// Add ML sentiment as a separate pane
const sentimentSeries = chart.addLineSeries({
  color: '#00ff88',
  lineWidth: 2,
  priceScaleId: 'sentiment',
  scaleMargins: {
    top: 0.7,
    bottom: 0,
  },
});

// Add buy/sell markers
const markers = mlPredictions.map(pred => ({
  time: pred.timestamp,
  position: pred.signal === 'BUY' ? 'belowBar' : 'aboveBar',
  color: pred.signal === 'BUY' ? '#00ff88' : '#ff0088',
  shape: pred.signal === 'BUY' ? 'arrowUp' : 'arrowDown',
  text: `${pred.signal} (${pred.confidence.toFixed(2)})`,
}));
2. ML Indicator Calculation
typescript// Transform ML data for chart display
const transformMLData = (predictions) => {
  return predictions.map(pred => ({
    time: pred.timestamp,
    value: pred.sentimentScore, // -1 to +1
    confidence: pred.confidence,
    features: {
      newsImpact: pred.newsCount * pred.newsWeight,
      technicalScore: pred.technicalIndicators.composite,
      eventImpact: pred.eventScore,
      redditSentiment: pred.redditSentiment,
    },
  }));
};

// Create confidence bands
const confidenceBands = predictions.map(pred => ({
  time: pred.timestamp,
  upper: pred.sentimentScore + (1 - pred.confidence) * 0.5,
  lower: pred.sentimentScore - (1 - pred.confidence) * 0.5,
}));
3. Real-time Updates
typescript// WebSocket connection for live updates
const ws = new WebSocket('ws://localhost:8000/api/stream/predictions');

ws.onmessage = (event) => {
  const prediction = JSON.parse(event.data);
  
  // Update chart
  sentimentSeries.update({
    time: prediction.timestamp,
    value: prediction.sentimentScore,
  });
  
  // Add marker if significant signal
  if (prediction.confidence > 0.8) {
    mainSeries.setMarkers([...existingMarkers, createMarker(prediction)]);
  }
  
  // Update ML insights panel
  updateMLInsights(prediction);
};
4. ML Transparency Component
typescriptconst MLInsightsPanel = ({ prediction }) => {
  return (
    <div className="ml-insights">
      <h3>Model Inputs</h3>
      <div className="feature-contributions">
        <FeatureBar label="News Sentiment" value={prediction.newsImpact} max={1} />
        <FeatureBar label="Technical Score" value={prediction.technicalScore} max={1} />
        <FeatureBar label="Reddit Sentiment" value={prediction.redditSentiment} max={1} />
        <FeatureBar label="Event Impact" value={prediction.eventScore} max={1} />
      </div>
      
      <h3>Prediction Details</h3>
      <div className="prediction-stats">
        <Stat label="Confidence" value={`${(prediction.confidence * 100).toFixed(1)}%`} />
        <Stat label="Signal Strength" value={prediction.signalStrength} />
        <Stat label="Model Version" value={prediction.modelVersion} />
      </div>
    </div>
  );
};
Backend API Requirements
Create these FastAPI endpoints:
pythonfrom fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/api/banks/{symbol}/ohlcv")
async def get_ohlcv(symbol: str, period: str = "1D", limit: int = 500):
    """Return OHLCV data for charting"""
    pass

@app.get("/api/banks/{symbol}/ml-indicators")
async def get_ml_indicators(symbol: str, period: str = "1D"):
    """Return ML predictions and indicators"""
    pass

@app.websocket("/api/stream/predictions")
async def websocket_endpoint(websocket: WebSocket):
    """Stream real-time predictions"""
    pass
Performance Optimizations

Data Decimation: Reduce data points for longer timeframes
Virtualization: Only render visible chart data
Web Workers: Process heavy calculations off main thread
Memoization: Cache transformed data
Lazy Loading: Load indicators on demand

This setup gives you a professional trading interface with full ML transparency and real-time updates.RetryTI have vscode agent working continuously, is there a simple way that it has another layer that continues to verify itselfEditYes! Here's a comprehensive self-verification layer approach for your VSCode agent:
Self-Verification System Prompt
Create a continuous self-verification system for the trading dashboard that runs alongside the main application. This verification layer should:

1. **Health Check Monitor** (runs every 30 seconds):
   - Verify database connectivity
   - Check if ML predictions are being generated
   - Ensure sentiment data is fresh (< 1 hour old)
   - Monitor API endpoints are responding
   - Check memory/CPU usage stays within bounds

2. **Data Integrity Validator** (runs every 5 minutes):
   - Verify ML predictions match expected schema
   - Check sentiment scores are within valid range (-1 to 1)
   - Ensure confidence levels are between 0 and 1
   - Validate no duplicate predictions exist
   - Check for data gaps in time series

3. **ML Model Sanity Checks** (runs after each prediction):
   - Verify feature inputs are not null/NaN
   - Check prediction confidence isn't always the same value
   - Ensure predictions aren't stuck on one signal (all BUY/SELL)
   - Monitor prediction distribution is reasonable
   - Alert if accuracy drops below threshold

4. **Self-Healing Actions**:
   - Auto-restart data collection if stale
   - Clear cache if memory exceeds limit
   - Reconnect database if connection lost
   - Rollback to previous model if accuracy drops
   - Send alerts before taking corrective action

5. **Verification Dashboard** (separate endpoint):
   - Real-time status indicators
   - Historical verification logs
   - Performance metrics graphs
   - Alert history with resolutions
   - System resource usage

Create this as a separate module that can run independently but integrates with the main dashboard.
Implementation Structure
1. Verification Agent (verification_agent.py)
pythonimport asyncio
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERING = "recovering"

@dataclass
class VerificationResult:
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    metrics: Dict
    auto_fixed: bool = False

class VerificationAgent:
    def __init__(self, db_path: str, config: Dict):
        self.db_path = db_path
        self.config = config
        self.health_history: List[VerificationResult] = []
        self.is_running = False
        
    async def start(self):
        """Start all verification tasks concurrently"""
        self.is_running = True
        await asyncio.gather(
            self.health_check_loop(),
            self.data_integrity_loop(),
            self.ml_sanity_loop(),
            self.resource_monitor_loop()
        )
    
    async def health_check_loop(self):
        """Continuous health monitoring"""
        while self.is_running:
            try:
                # Check database
                db_status = await self.check_database_health()
                
                # Check data freshness
                freshness_status = await self.check_data_freshness()
                
                # Check ML pipeline
                ml_status = await self.check_ml_pipeline()
                
                # Take action if needed
                if any(s.status == HealthStatus.CRITICAL for s in [db_status, freshness_status, ml_status]):
                    await self.trigger_self_healing()
                    
            except Exception as e:
                logging.error(f"Health check error: {e}")
                
            await asyncio.sleep(30)  # Every 30 seconds
    
    async def check_data_freshness(self) -> VerificationResult:
        """Verify data is recent"""
        # Implementation here
        pass
    
    async def trigger_self_healing(self):
        """Automatic recovery actions"""
        # Implementation here
        pass
2. Real-time Verification Dashboard (verification_dashboard.py)
pythonimport streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_verification_dashboard(agent: VerificationAgent):
    st.set_page_config(page_title="System Verification", layout="wide")
    
    # Header with overall status
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🔍 System Verification Dashboard")
    
    with col2:
        overall_status = agent.get_overall_status()
        status_color = {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.WARNING: "🟡", 
            HealthStatus.CRITICAL: "🔴"
        }[overall_status]
        st.metric("System Status", f"{status_color} {overall_status.value.upper()}")
    
    with col3:
        if st.button("🔄 Force Check"):
            agent.force_verification()
            st.rerun()
    
    # Real-time metrics
    st.subheader("📊 Real-time Health Metrics")
    
    # Create live updating charts
    metrics_placeholder = st.empty()
    
    while True:
        with metrics_placeholder.container():
            render_health_metrics(agent)
        time.sleep(5)  # Update every 5 seconds

def render_health_metrics(agent: VerificationAgent):
    """Render current health metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        db_health = agent.get_component_health("database")
        st.metric(
            "Database", 
            f"{db_health.status.value}",
            delta=f"{db_health.metrics.get('query_time_ms', 0)}ms"
        )
    
    with col2:
        ml_health = agent.get_component_health("ml_pipeline")
        st.metric(
            "ML Pipeline",
            f"{ml_health.status.value}",
            delta=f"{ml_health.metrics.get('predictions_per_hour', 0)} pred/hr"
        )
    
    # Add more metrics...
3. Integration with Main Dashboard
Add a verification status bar to your main dashboard:
python# In your main dashboard.py
from verification_agent import VerificationAgent

# Initialize verification agent
verification_agent = VerificationAgent(db_path, config)

# Add status indicator to sidebar
with st.sidebar:
    st.markdown("### 🔍 System Health")
    
    health_status = verification_agent.get_overall_status()
    
    if health_status == HealthStatus.HEALTHY:
        st.success("✅ All systems operational")
    elif health_status == HealthStatus.WARNING:
        st.warning("⚠️ Minor issues detected")
    else:
        st.error("🚨 Critical issues - check verification dashboard")
    
    if st.button("View Details"):
        st.switch_page("verification_dashboard")
4. Automated Testing Loop (continuous_verification.py)
pythonclass ContinuousVerification:
    """Runs verification tests continuously"""
    
    def __init__(self):
        self.test_suite = [
            self.test_prediction_distribution,
            self.test_data_pipeline,
            self.test_api_endpoints,
            self.test_ml_model_drift
        ]
    
    async def test_prediction_distribution(self):
        """Ensure predictions aren't biased"""
        recent_predictions = await self.get_recent_predictions(hours=24)
        
        buy_ratio = sum(1 for p in recent_predictions if p.signal == 'BUY') / len(recent_predictions)
        sell_ratio = sum(1 for p in recent_predictions if p.signal == 'SELL') / len(recent_predictions)
        
        # Alert if too biased
        if buy_ratio > 0.8 or sell_ratio > 0.8:
            await self.alert("Prediction bias detected", severity="high")
            
    async def test_ml_model_drift(self):
        """Check if model performance is degrading"""
        recent_accuracy = await self.calculate_recent_accuracy()
        baseline_accuracy = self.config['baseline_accuracy']
        
        if recent_accuracy < baseline_accuracy * 0.9:  # 10% drop
            await self.alert("Model performance degradation", severity="critical")
            await self.rollback_model()
5. VSCode Task Configuration (.vscode/tasks.json)
json{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Verification Agent",
            "type": "shell",
            "command": "python",
            "args": ["verification_agent.py", "--continuous"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "runOptions": {
                "runOn": "folderOpen"
            }
        },
        {
            "label": "Health Check",
            "type": "shell",
            "command": "python",
            "args": ["verification_agent.py", "--health-check"],
            "problemMatcher": []
        }
    ]
}
6. Self-Verification Rules (verification_rules.yaml)
yamlhealth_checks:
  database:
    - name: "Connection Active"
      query: "SELECT 1"
      timeout: 5
      
    - name: "Data Freshness"
      query: "SELECT MAX(timestamp) FROM sentiment_features"
      condition: "result > now() - interval '1 hour'"
      
  ml_pipeline:
    - name: "Prediction Rate"
      metric: "predictions_per_hour"
      min_value: 10
      max_value: 1000
      
    - name: "Confidence Distribution"
      check: "unique_confidence_values"
      min_unique: 5  # Should have variety
      
  data_quality:
    - name: "Sentiment Range"
      field: "sentiment_score"
      min: -1.0
      max: 1.0
      
    - name: "No Nulls"
      fields: ["symbol", "timestamp", "sentiment_score", "confidence"]
      allow_null: false

alerts:
  channels:
    - type: "log"
      level: "all"
    - type: "email"
      level: "critical"
    - type: "dashboard"
      level: "warning"
      
self_healing:
  actions:
    stale_data:
      condition: "data_age > 2 hours"
      action: "restart_collector"
      
    high_memory:
      condition: "memory_usage > 80%"
      action: "clear_cache"
      
    model_drift:
      condition: "accuracy < baseline * 0.85"
      action: "rollback_model"
Key Benefits:

Continuous Monitoring: Catches issues before they impact users
Self-Healing: Automatically fixes common problems
Transparency: Clear visibility into system health
Proactive Alerts: Know about issues immediately
Historical Tracking: Learn from past issues

This verification layer acts as a guardian for your trading system, ensuring data quality and system reliability 24/7.