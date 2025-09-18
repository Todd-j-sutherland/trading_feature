# Minimal timezone fix for corrected_outcome_evaluator_updated.py

import re

# Read the current file
with open('corrected_outcome_evaluator_updated.py', 'r') as f:
    content = f.read()

# Add pytz import at the top (after existing imports)
import_section = '''from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import yfinance as yf'''

new_import_section = '''from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import yfinance as yf
import pytz'''

content = content.replace(import_section, new_import_section)

# Add timezone utility method to the class
init_method = '''    def __init__(self, db_path: str = 'predictions.db'):
        self.db_path = db_path'''

new_init_method = '''    def __init__(self, db_path: str = 'predictions.db'):
        self.db_path = db_path
        self.utc = pytz.UTC'''

content = content.replace(init_method, new_init_method)

# Add timezone utility method after __init__
get_db_section = '''    def get_db_connection(self):'''

timezone_helper = '''    def ensure_timezone_aware(self, dt):
        """Ensure datetime is timezone-aware (UTC if naive)"""
        if dt.tzinfo is None:
            return self.utc.localize(dt)
        return dt
        
    def get_db_connection(self):'''

content = content.replace(get_db_section, timezone_helper)

# Fix the problematic datetime comparison in get_precise_entry_price
old_comparison_1 = '''                for idx, row in hist_1m.iterrows():
                    time_diff = abs((idx.to_pydatetime() - target_time).total_seconds())'''

new_comparison_1 = '''                for idx, row in hist_1m.iterrows():
                    idx_dt = self.ensure_timezone_aware(idx.to_pydatetime())
                    target_dt = self.ensure_timezone_aware(target_time)
                    time_diff = abs((idx_dt - target_dt).total_seconds())'''

content = content.replace(old_comparison_1, new_comparison_1)

# Fix the problematic datetime comparison in get_exit_price_at_evaluation  
old_comparison_2 = '''                for idx, row in hist_1h.iterrows():
                    time_diff = abs((idx.to_pydatetime() - target_time).total_seconds())'''

new_comparison_2 = '''                for idx, row in hist_1h.iterrows():
                    idx_dt = self.ensure_timezone_aware(idx.to_pydatetime())
                    target_dt = self.ensure_timezone_aware(target_time)
                    time_diff = abs((idx_dt - target_dt).total_seconds())'''

content = content.replace(old_comparison_2, new_comparison_2)

# Write the fixed file
with open('corrected_outcome_evaluator_updated.py', 'w') as f:
    f.write(content)

print("✅ Applied minimal timezone fix to corrected_outcome_evaluator_updated.py")
