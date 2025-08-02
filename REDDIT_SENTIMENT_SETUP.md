# Reddit Sentiment Analysis Setup Guide

## 🔍 **Current Status: BROKEN** ❌

Reddit sentiment analysis is currently **not working** because Reddit API credentials are not configured.

**Evidence:**
- All 145 records in database have `reddit_sentiment = 0.0`
- Reddit client is never initialized (`self.reddit = None`)
- News sentiment works fine (varying values 0.02-0.04)

## 🛠️ **How to Fix Reddit Sentiment**

### Step 1: Get Reddit API Credentials

1. **Go to Reddit Apps**: https://www.reddit.com/prefs/apps
2. **Create a new app**:
   - Name: `TradingAnalysisBot`
   - Type: `script`
   - Description: `ASX bank sentiment analysis`
   - About URL: (leave blank)
   - Redirect URI: `http://localhost:8080`

3. **Save the credentials**:
   - `client_id`: The string under your app name (14 characters)
   - `client_secret`: The secret string (27 characters)

### Step 2: Add Credentials to Environment

Create or update `.env` file in project root:

```bash
# Reddit API credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USER_AGENT=TradingAnalysisBot/1.0
```

### Step 3: Test Reddit Connection

```bash
# Test Reddit setup
python3 -c "
from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
analyzer = NewsSentimentAnalyzer()
print('Reddit available:', analyzer.reddit is not None)
if analyzer.reddit:
    result = analyzer._get_reddit_sentiment('CBA.AX')
    print('Reddit posts found:', result['posts_analyzed'])
"
```

## 📊 **Expected Impact After Fix**

Currently missing from all predictions:
- Reddit community sentiment (bullish/bearish/neutral counts)
- Social media momentum indicators  
- Retail investor sentiment trends
- Subreddit-specific sentiment breakdown (ASX_Bets, AusFinance, etc.)

**Database Impact:**
- `reddit_sentiment` will change from `0.0` to actual values (-1.0 to +1.0)
- Feature completeness will improve from ~90% to 100%
- ML model accuracy should improve with additional sentiment signal

## 🚨 **Quick Status Check**

```bash
# Check current reddit sentiment status
sqlite3 data/ml_models/enhanced_training_data.db "
SELECT 
    'Total records:' as metric, COUNT(*) as value 
FROM enhanced_features
UNION ALL
SELECT 
    'Reddit sentiment = 0.0:', COUNT(*) 
FROM enhanced_features 
WHERE reddit_sentiment = 0.0
UNION ALL  
SELECT 
    'News sentiment working:', COUNT(*) 
FROM enhanced_features 
WHERE sentiment_score != 0.0
"
```

## 📈 **Reddit Subreddits Monitored**

When working, the system monitors these subreddits for ASX bank mentions:
- `ASX_Bets` - Active trading discussions
- `AusFinance` - Australian finance community  
- `fiaustralia` - Financial independence community
- `ASX` - Official ASX discussions
- `investing` - General investing community

**Keywords per bank:**
- CBA.AX: ["CBA", "Commonwealth Bank", "CommBank"]
- WBC.AX: ["WBC", "Westpac", "WestPac"]  
- ANZ.AX: ["ANZ", "ANZ Bank"]
- NAB.AX: ["NAB", "National Australia Bank"]
- MQG.AX: ["MQG", "Macquarie", "Macquarie Group"]
- SUN.AX: ["SUN", "Suncorp", "Suncorp Group"]
- QBE.AX: ["QBE", "QBE Insurance"]

## 🔧 **Alternative: Mock Reddit Data**

If Reddit API access is not desired, we could implement mock Reddit sentiment:
- Use historical patterns to generate realistic sentiment values
- Base on news sentiment with some variance
- Add time-based and volatility-based adjustments
- Still improve model training over current 0.0 values

This would require updating the `_get_reddit_sentiment` method to return mock data instead of empty results.
