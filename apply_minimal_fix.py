import re

# Read current file
with open('corrected_outcome_evaluator_updated.py', 'r') as f:
    content = f.read()

# Add timezone helper method after __init__
init_end = '        self.utc = pytz.UTC'
helper_method = '''
    def ensure_timezone_aware(self, dt):
        """Ensure datetime is timezone-aware (UTC if naive)"""
        if dt.tzinfo is None:
            return self.utc.localize(dt)
        return dt'''

content = content.replace(init_end, init_end + helper_method)

# Fix first datetime comparison
old_pattern1 = r'time_diff = abs\(\(idx\.to_pydatetime\(\) - target_time\)\.total_seconds\(\)\)'
new_pattern1 = '''idx_dt = self.ensure_timezone_aware(idx.to_pydatetime())
                    target_dt = self.ensure_timezone_aware(target_time)
                    time_diff = abs((idx_dt - target_dt).total_seconds())'''

content = re.sub(old_pattern1, new_pattern1, content)

# Write fixed file
with open('corrected_outcome_evaluator_updated.py', 'w') as f:
    f.write(content)

print("Applied minimal timezone fix")
