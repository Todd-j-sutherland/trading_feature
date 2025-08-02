#!/usr/bin/env python3
"""
Script to populate the database with current Reddit sentiment data
"""
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the news analyzer
from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer

# ASX Bank symbols
ASX_BANKS = [
    'CBA.AX',  # Commonwealth Bank
    'ANZ.AX',  # ANZ Banking Group
    'WBC.AX',  # Westpac Banking Corporation
    'NAB.AX',  # National Australia Bank
]

def create_sentiment_table():
    """Create the sentiment_scores table if it doesn't exist"""
    conn = sqlite3.connect('morning_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            sentiment_score REAL,
            confidence REAL,
            signal TEXT,
            news_count INTEGER,
            reddit_sentiment REAL,
            event_score REAL,
            technical_score REAL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Created sentiment_scores table")

def populate_reddit_sentiment():
    """Populate the database with current Reddit sentiment data"""
    print("🚀 Starting Reddit sentiment population...")
    
    # Create table first
    create_sentiment_table()
    
    # Initialize news analyzer
    analyzer = NewsSentimentAnalyzer()
    
    # Get current timestamp
    timestamp = datetime.now().isoformat()
    
    # Connect to database
    conn = sqlite3.connect('morning_analysis.db')
    cursor = conn.cursor()
    
    for symbol in ASX_BANKS:
        print(f"\n📊 Processing {symbol}...")
        
        # Get Reddit sentiment for this symbol
        reddit_data = analyzer._get_reddit_sentiment(symbol)
        reddit_sentiment = reddit_data.get('average_sentiment', 0.0) if isinstance(reddit_data, dict) else 0.0
        print(f"   Reddit sentiment: {reddit_sentiment}")
        print(f"   Posts analyzed: {reddit_data.get('posts_analyzed', 0) if isinstance(reddit_data, dict) else 0}")
        
        # Insert into database
        cursor.execute('''
            INSERT INTO sentiment_scores 
            (symbol, timestamp, sentiment_score, confidence, signal, news_count, reddit_sentiment, event_score, technical_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            timestamp,
            reddit_sentiment,  # Use reddit sentiment as main sentiment for now
            0.8,  # Default confidence
            'NEUTRAL',  # Default signal
            0,  # News count (we're focusing on Reddit)
            reddit_sentiment,
            0.0,  # Event score
            0.0   # Technical score
        ))
    
    conn.commit()
    conn.close()
    
    print("\n✅ Successfully populated database with Reddit sentiment data!")
    print("🔄 Please refresh your dashboard to see the updated values.")

if __name__ == "__main__":
    populate_reddit_sentiment()
