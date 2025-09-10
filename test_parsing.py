import json
import sqlite3

def format_ml_components(confidence_breakdown):
    if not confidence_breakdown:
        return N/A
    
    try:
        # Try JSON format first
        data = json.loads(confidence_breakdown)
        news = data.get('news_component', 0) * 100
        tech = data.get('technical_component', 0) * 100
        return f"N:{news:.1f} T:{tech:.1f}"
    except:
        # Fall back to string format
        try:
            news = 0
            tech = 0
            if 'News:' in confidence_breakdown:
                news = float(confidence_breakdown.split('News:')[1].split()[0]) * 100
            if 'Tech:' in confidence_breakdown:
                tech = float(confidence_breakdown.split('Tech:')[1].split()[0]) * 100
            return f"N:{news:.1f} T:{tech:.1f}"
        except:
            return "N/A"

# Test with sample data
conn = sqlite3.connect('data/trading_predictions.db')
cursor = conn.cursor()

print('Testing ML component parsing:')
print('-' * 40)

# Get samples of both formats
cursor.execute('SELECT confidence_breakdown FROM predictions WHERE confidence_breakdown LIKE "{%" LIMIT 3')
json_samples = cursor.fetchall()

cursor.execute('SELECT confidence_breakdown FROM predictions WHERE confidence_breakdown LIKE "Tech:%" LIMIT 3')
string_samples = cursor.fetchall()

print('JSON format samples:')
for i, (breakdown,) in enumerate(json_samples, 1):
    result = format_ml_components(breakdown)
    print(f'{i}. {result}')

print()
print('String format samples:')
for i, (breakdown,) in enumerate(string_samples, 1):
    result = format_ml_components(breakdown)
    print(f'{i}. {result}')

conn.close()
