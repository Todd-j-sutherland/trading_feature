Evening Routine Machine Learning Training - Simple Explanation
What Data Goes In (Training Inputs):
📊 Primary Training Data from sentiment_features table:

News Analysis: Count of news articles, sentiment scores from financial news
Reddit Sentiment: Social media sentiment from trading communities
Event Scores: Important market events (earnings, announcements, etc.)
Technical Indicators: Price movement patterns, RSI, volume analysis
Confidence Levels: How certain the system is about each prediction
💰 Trading Outcomes from trading_outcomes table:

Entry/Exit Prices: When trades were made and closed
Return Percentage: Did the trade make or lose money?
Success Labels: 1 = profitable trade, 0 = losing trade
What the ML System Learns (Training Process):
🧠 The system learns to predict:

Should I BUY this bank stock? (when sentiment + technical indicators look good)
Should I SELL this bank stock? (when indicators suggest decline)
Should I HOLD/wait? (when signals are unclear)
📈 Training Examples:

"When CBA has 15+ positive news articles + high Reddit sentiment + technical score >25 → BUY signal was 85% successful"
"When ANZ has negative event score + low confidence → SELL signal was 70% successful"
"When sentiment is neutral + low news volume → HOLD was the safest choice"
What Comes Out (Predictions):
🎯 The trained models output:

Trading Signal: BUY/SELL/HOLD for each bank (CBA, ANZ, WBC, NAB, etc.)
Confidence Score: How sure the system is (0-100%)
Expected Success Rate: Based on similar past situations
📊 Real Example from Your Dashboard:

CBA.AX: BUY signal, 78% confidence, Technical Score: 28.1
ANZ.AX: HOLD signal, 65% confidence, Technical Score: 26.2
Simple Summary:
The evening routine feeds the ML system yesterday's market data + news + social sentiment, and the system learns "what combination of signals led to profitable trades". Then it uses this knowledge to predict "what should I do tomorrow" for each bank stock.

It's essentially teaching the computer: "Here's what happened in the market, here's what traders did, here's whether they made money - now learn the patterns so you can make better predictions next time."