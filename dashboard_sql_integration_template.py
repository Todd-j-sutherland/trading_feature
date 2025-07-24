
# Dashboard Integration Template
# Add this to your dashboard files:

from app.dashboard.utils.sql_data_manager import DashboardDataManagerSQL

# Replace:
# dashboard = DataManager()

# With:
dashboard = DashboardDataManagerSQL()

# All existing method calls work the same:
# - dashboard.load_sentiment_data()
# - dashboard.get_latest_analysis() 
# - dashboard.get_prediction_log()

# But now they use live SQL database instead of stale JSON!
