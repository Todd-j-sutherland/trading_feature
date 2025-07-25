---
applyTo: '**'
---
I need to rebuild a trading sentiment analysis dashboard for ASX banks. The current implementation is overly complex with multiple views and components. I want a simplified single-page dashboard that displays everything at once.

Requirements:
1. Single page layout showing:
   - Machine Learning performance metrics (accuracy, success rate, predictions)
   - Current/latest sentiment scores for all banks (CBA, ANZ, WBC, NAB, MQG, SUN, QBE)
   - Technical analysis indicators
   - Dynamic description of ML features being used for predictions

2. Technical specifications:
   - Use Python 3.12 virtual environment
   - Streamlit for the UI
   - Direct SQL database queries (no JSON files)
   - Real-time data only (no mock/static data)
   - Error handling that raises exceptions (not just logging)
   - Each component must be independently runnable

3. ML transparency:
   - Show what features the ML model is using (news count, reddit sentiment, event scores, technical indicators)
   - Display these dynamically based on actual model inputs
   - Show confidence levels and how they're calculated

4. Data source:
   - Primary data from: data/ml_models/training_data.db
   - Tables: sentiment_features, ml_predictions
   - No dependency on JSON history files

5. Error handling:
   - All database queries wrapped in try/except
   - Raise exceptions with clear messages
   - No silent failures or fallback to empty data

6. Modular design:
   - Each section (ML metrics, sentiment, technical) in separate functions
   - Can run individually for testing
   - Clean separation of data fetching and UI rendering

Please create a simplified dashboard.py file that:
- Loads all data on page load
- Shows everything in a clean grid layout
- Updates automatically when refreshed
- Has clear visual indicators for buy/sell signals
- Shows ML model performance over time
- Explains what data feeds into predictions

The dashboard should be production-ready with proper error handling and no placeholder data.