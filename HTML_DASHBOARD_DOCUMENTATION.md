# HTML Dashboard Generator Documentation

## 📊 HTML Dashboard Generator (`html_dashboard_generator.py`)

The HTML Dashboard Generator creates a beautiful, static HTML dashboard that showcases the performance of all 11 Australian bank symbols with comprehensive ML predictions, sentiment analysis, and market insights.

---

## 🎯 **Purpose & Features**

### **What It Does**
- Generates a **static HTML dashboard** from SQLite database data
- Displays **real-time performance** of all 11 Australian banks
- Shows **ML predictions**, **sentiment analysis**, and **technical indicators**
- Creates **responsive, interactive visualizations** with modern CSS styling
- Provides **sector performance comparison** and **signal distribution**

### **Key Features**
- 🏦 **11 Bank Analysis**: CBA, ANZ, WBC, NAB, MQG, SUN, BOQ, BEN, AMP, IFL, MPG
- 🤖 **ML Predictions**: BUY/SELL signals with confidence scores
- 💭 **Sentiment Analysis**: News sentiment scoring and confidence
- 📈 **Performance Metrics**: Price changes, RSI, sector comparison
- 🎨 **Beautiful Design**: Modern gradient styling with responsive layout
- 📱 **Mobile Friendly**: Responsive design that works on all devices

---

## 🏗️ **Architecture & Data Sources**

### **Data Source**
```python
Database: data/multi_bank_analysis.db
Tables:
  - bank_performance       # Main ML predictions and metrics
  - news_sentiment_analysis # News headlines and sentiment scores
```

### **Core Class Structure**
```python
class HTMLBankDashboard:
    def __init__(self):
        self.db_path = 'data/multi_bank_analysis.db'
    
    def load_data(self):
        # Load performance and sentiment data from SQLite
        
    def generate_dashboard_html(self):
        # Create complete HTML with CSS styling
        
    def generate_no_data_html(self):
        # Fallback when no data available
        
    def save_dashboard(self, filename):
        # Save HTML to file
```

---

## 🚀 **How to Use**

### **Quick Start**
```bash
# Generate the dashboard
python enhanced_ml_system/html_dashboard_generator.py

# Output file
enhanced_ml_system/bank_performance_dashboard.html

# Open in browser
open enhanced_ml_system/bank_performance_dashboard.html
```

### **Integration with Data Collection**
```bash
# 1. First collect data
python enhanced_ml_system/multi_bank_data_collector.py

# 2. Then generate dashboard  
python enhanced_ml_system/html_dashboard_generator.py

# 3. View the results
open enhanced_ml_system/bank_performance_dashboard.html
```

### **Automated Workflow**
```bash
# The data collector automatically generates the dashboard
# Just run the collector and the HTML dashboard is created:
python enhanced_ml_system/multi_bank_data_collector.py
# ↳ This will also generate bank_performance_dashboard.html
```

---

## 📊 **Dashboard Sections**

### **1. Header Summary**
- Total banks analyzed
- Average 1-day price change
- Average sentiment score  
- Number of buy signals

### **2. Top Performers Section**
- **Best Performer**: Highest price change with details
- **Biggest Decline**: Lowest price change with context
- Price, change %, RSI, and ML action for each

### **3. Sentiment Analysis Section**
- **Most Positive Sentiment**: Bank with highest sentiment score
- **Most Negative Sentiment**: Bank with lowest sentiment score
- Sentiment confidence levels

### **4. Sector Performance**
- Average performance by sector
- Number of banks per sector
- Color-coded performance indicators

### **5. ML Predictions Distribution**
- Count of each action type (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
- Visual distribution of trading signals

### **6. All Banks Overview**
- Complete grid of all 11 banks
- Key metrics for each bank:
  - Current price
  - 1-day and 5-day changes
  - RSI value
  - Sentiment score
  - ML action recommendation

### **7. Recent News Headlines** (if available)
- Latest sentiment-analyzed news articles
- Sentiment classification (positive/negative/neutral)
- Confidence scores

---

## 🎨 **Visual Design Features**

### **Modern Styling**
- **Gradient backgrounds**: Blue/purple gradient header
- **Card-based layout**: Clean white cards with shadows
- **Responsive grid**: Adapts to different screen sizes
- **Color coding**: Green (positive), Red (negative), Yellow (neutral)
- **Action badges**: Color-coded trading signals
- **Hover effects**: Cards lift on hover for interactivity

### **Typography**
- **Main font**: 'Segoe UI' for clean, modern look
- **Large metrics**: 2.5em font size for key numbers
- **Hierarchical text**: Clear information hierarchy

### **Color Scheme**
```css
Primary: #2a5298 (Blue)
Success: #28a745 (Green) 
Danger: #dc3545 (Red)
Warning: #ffc107 (Yellow)
Background: Linear gradient #667eea to #764ba2
```

---

## 🔧 **Customization Options**

### **Modify Output Location**
```python
# Change the output filename
dashboard = HTMLBankDashboard()
dashboard.save_dashboard('custom_path/my_dashboard.html')
```

### **Database Path Configuration**
```python
# Use different database
dashboard = HTMLBankDashboard()
dashboard.db_path = 'path/to/your/database.db'
```

### **Styling Customization**
The HTML includes embedded CSS that can be modified:
- Change color schemes in the `<style>` section
- Modify grid layouts (currently uses CSS Grid)
- Adjust responsive breakpoints
- Update typography settings

---

## 🛠️ **Troubleshooting**

### **No Data Available**
If the database is empty, the generator creates a helpful "No Data" page with instructions:

```html
📊 No Data Available
To generate data, run:
python enhanced_ml_system/multi_bank_data_collector.py
```

### **Database Connection Issues**
```python
# Check if database exists
import os
if not os.path.exists('data/multi_bank_analysis.db'):
    print("Database not found. Run data collector first.")
```

### **Missing Tables**
The generator handles missing tables gracefully and shows available data only.

---

## 📁 **File Dependencies**

### **Required Files**
- `data/multi_bank_analysis.db` - SQLite database with bank data
- `enhanced_ml_system/html_dashboard_generator.py` - Main generator script

### **Optional Dependencies**
- `pandas` - Data manipulation
- `sqlite3` - Database access (built-in)
- Modern web browser for viewing

### **Output Files**
- `enhanced_ml_system/bank_performance_dashboard.html` - Generated dashboard

---

## 🚀 **Integration Points**

### **With Data Collection**
```python
# multi_bank_data_collector.py automatically calls:
from html_dashboard_generator import HTMLBankDashboard
dashboard = HTMLBankDashboard()
dashboard.save_dashboard()
```

### **With Morning/Evening Analysis**
```bash
# Can be integrated into daily workflows:
python -m app.main evening  # Collects data
python enhanced_ml_system/html_dashboard_generator.py  # Generates dashboard
```

### **With Web Servers**
```python
# Serve the static HTML file
from http.server import HTTPServer, SimpleHTTPRequestHandler
# Navigate to enhanced_ml_system/ and run:
# python -m http.server 8080
# Then visit: http://localhost:8080/bank_performance_dashboard.html
```

---

## 📈 **Performance Characteristics**

- **Generation Time**: ~2-5 seconds for full dashboard
- **File Size**: ~50-100KB depending on data volume
- **Browser Compatibility**: Works in all modern browsers
- **Mobile Responsive**: Adapts to phone/tablet screens
- **No JavaScript Required**: Pure HTML/CSS for maximum compatibility

---

## 🎯 **Best Practices**

1. **Regular Updates**: Run after each data collection cycle
2. **Archive Previous Versions**: Keep dated copies for historical analysis
3. **Mobile Testing**: Verify dashboard works on mobile devices
4. **Performance Monitoring**: Check file size if adding more features
5. **Backup Generation**: Include in automated backup scripts

This HTML dashboard provides a beautiful, comprehensive view of your ML trading system's performance that can be easily shared, archived, or displayed on any device!
