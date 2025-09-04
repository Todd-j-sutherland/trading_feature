#!/usr/bin/env python3
"""
Trading Predictions Historical Analysis & Visualization
Correlates price movements with news sentiment, technical analysis, and ML predictions
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def examine_database_structure():
    """Examine the database structure and available data"""
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        
        # Get table names
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("🔍 DATABASE STRUCTURE ANALYSIS")
        print("=" * 50)
        print(f"📊 Available tables: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print(f"   Columns ({len(columns)}):")
            for col in columns:
                print(f"     - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   📈 Rows: {count:,}")
            
            # Show sample data
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample = cursor.fetchall()
                print(f"   📄 Sample data:")
                for i, row in enumerate(sample, 1):
                    print(f"     Row {i}: {str(row)[:100]}{'...' if len(str(row)) > 100 else ''}")
        
        conn.close()
        return [table[0] for table in tables]
        
    except Exception as e:
        print(f"❌ Database examination error: {e}")
        return []

def load_prediction_data():
    """Load and prepare prediction data for analysis"""
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        
        # Try to load predictions data
        query = """
        SELECT 
            symbol,
            prediction_timestamp,
            prediction_direction,
            confidence_score,
            current_price,
            predicted_price,
            news_sentiment,
            technical_score,
            ml_confidence,
            volume_ratio,
            features
        FROM predictions 
        WHERE prediction_timestamp IS NOT NULL
        ORDER BY symbol, prediction_timestamp
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"\n📊 LOADED DATA SUMMARY")
        print("=" * 30)
        print(f"Total predictions: {len(df):,}")
        print(f"Unique symbols: {df['symbol'].nunique()}")
        print(f"Date range: {df['prediction_timestamp'].min()} to {df['prediction_timestamp'].max()}")
        print(f"Symbols: {', '.join(df['symbol'].unique())}")
        
        return df
        
    except Exception as e:
        print(f"❌ Data loading error: {e}")
        return pd.DataFrame()

def calculate_price_changes(df):
    """Calculate actual price changes and prediction accuracy"""
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['prediction_timestamp'])
    df = df.sort_values(['symbol', 'timestamp'])
    
    # Calculate price changes
    df['price_change'] = df.groupby('symbol')['current_price'].pct_change() * 100
    df['predicted_change'] = ((df['predicted_price'] - df['current_price']) / df['current_price']) * 100
    
    # Forward-fill to get next actual price for accuracy calculation
    df['next_price'] = df.groupby('symbol')['current_price'].shift(-1)
    df['actual_change'] = ((df['next_price'] - df['current_price']) / df['current_price']) * 100
    
    # Calculate prediction accuracy
    df['prediction_correct'] = (
        ((df['prediction_direction'] == 'BUY') & (df['actual_change'] > 0)) |
        ((df['prediction_direction'] == 'SELL') & (df['actual_change'] < 0))
    )
    
    return df

def create_correlation_analysis(df):
    """Create comprehensive correlation analysis"""
    print(f"\n🔍 CORRELATION ANALYSIS")
    print("=" * 40)
    
    # Prepare correlation data
    corr_data = df[['price_change', 'actual_change', 'news_sentiment', 'technical_score', 
                   'ml_confidence', 'confidence_score', 'volume_ratio']].copy()
    
    # Remove NaN values
    corr_data = corr_data.dropna()
    
    if len(corr_data) == 0:
        print("❌ No complete data available for correlation analysis")
        return
    
    print(f"📊 Analyzing {len(corr_data)} complete data points")
    
    # Calculate correlations
    correlation_matrix = corr_data.corr()
    
    # Create visualization
    plt.figure(figsize=(15, 12))
    
    # Correlation heatmap
    plt.subplot(2, 3, 1)
    sns.heatmap(correlation_matrix, annot=True, cmap='RdBu_r', center=0, 
                square=True, fmt='.3f', cbar_kws={'label': 'Correlation'})
    plt.title('📊 Correlation Matrix\nPrediction Components vs Price Changes')
    plt.tight_layout()
    
    # Price vs News Sentiment
    plt.subplot(2, 3, 2)
    plt.scatter(corr_data['news_sentiment'], corr_data['actual_change'], 
               alpha=0.6, c='blue', s=20)
    plt.xlabel('News Sentiment')
    plt.ylabel('Actual Price Change (%)')
    plt.title('📰 News Sentiment vs Price Change')
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    plt.axvline(x=0, color='red', linestyle='--', alpha=0.5)
    
    # Price vs Technical Score
    plt.subplot(2, 3, 3)
    plt.scatter(corr_data['technical_score'], corr_data['actual_change'], 
               alpha=0.6, c='green', s=20)
    plt.xlabel('Technical Score')
    plt.ylabel('Actual Price Change (%)')
    plt.title('📈 Technical Score vs Price Change')
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    # Price vs ML Confidence
    plt.subplot(2, 3, 4)
    plt.scatter(corr_data['ml_confidence'], corr_data['actual_change'], 
               alpha=0.6, c='purple', s=20)
    plt.xlabel('ML Confidence')
    plt.ylabel('Actual Price Change (%)')
    plt.title('🤖 ML Confidence vs Price Change')
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    # Combined confidence vs actual change
    plt.subplot(2, 3, 5)
    plt.scatter(corr_data['confidence_score'], corr_data['actual_change'], 
               alpha=0.6, c='orange', s=20)
    plt.xlabel('Combined Confidence Score')
    plt.ylabel('Actual Price Change (%)')
    plt.title('🎯 Combined Confidence vs Price Change')
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    # Volume ratio vs price change
    plt.subplot(2, 3, 6)
    plt.scatter(corr_data['volume_ratio'], corr_data['actual_change'], 
               alpha=0.6, c='red', s=20)
    plt.xlabel('Volume Ratio')
    plt.ylabel('Actual Price Change (%)')
    plt.title('📊 Volume Ratio vs Price Change')
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('data/correlation_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print correlation insights
    print(f"\n🎯 KEY CORRELATIONS WITH ACTUAL PRICE CHANGES:")
    price_correlations = correlation_matrix['actual_change'].sort_values(key=abs, ascending=False)
    for metric, corr in price_correlations.items():
        if metric != 'actual_change':
            strength = "Strong" if abs(corr) > 0.3 else "Moderate" if abs(corr) > 0.1 else "Weak"
            direction = "Positive" if corr > 0 else "Negative"
            print(f"   {metric:20}: {corr:6.3f} ({strength} {direction})")

def create_time_series_analysis(df):
    """Create time series analysis of predictions vs price movements"""
    print(f"\n📈 TIME SERIES ANALYSIS")
    print("=" * 30)
    
    # Focus on symbols with most data
    symbol_counts = df['symbol'].value_counts()
    top_symbols = symbol_counts.head(3).index.tolist()
    
    plt.figure(figsize=(15, 10))
    
    for i, symbol in enumerate(top_symbols, 1):
        symbol_data = df[df['symbol'] == symbol].copy()
        symbol_data = symbol_data.sort_values('timestamp')
        
        # Remove NaN values
        symbol_data = symbol_data.dropna(subset=['actual_change', 'news_sentiment', 
                                                'technical_score', 'ml_confidence'])
        
        if len(symbol_data) == 0:
            continue
            
        plt.subplot(len(top_symbols), 1, i)
        
        # Create dual y-axis plot
        ax1 = plt.gca()
        ax2 = ax1.twinx()
        
        # Plot price changes
        ax1.plot(symbol_data['timestamp'], symbol_data['actual_change'], 
                color='black', linewidth=2, label='Actual Price Change (%)', alpha=0.8)
        ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax1.set_ylabel('Price Change (%)', color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        
        # Plot prediction components
        ax2.plot(symbol_data['timestamp'], symbol_data['news_sentiment'], 
                color='blue', alpha=0.7, label='News Sentiment')
        ax2.plot(symbol_data['timestamp'], symbol_data['technical_score'] / 100, 
                color='green', alpha=0.7, label='Technical Score (scaled)')
        ax2.plot(symbol_data['timestamp'], symbol_data['ml_confidence'], 
                color='purple', alpha=0.7, label='ML Confidence')
        
        ax2.set_ylabel('Prediction Components', color='blue')
        ax2.tick_params(axis='y', labelcolor='blue')
        
        plt.title(f'📊 {symbol} - Price Changes vs Prediction Components')
        
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('data/time_series_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_prediction_accuracy_analysis(df):
    """Analyze prediction accuracy by different components"""
    print(f"\n🎯 PREDICTION ACCURACY ANALYSIS")
    print("=" * 40)
    
    # Remove NaN values
    clean_df = df.dropna(subset=['prediction_correct', 'news_sentiment', 
                                'technical_score', 'ml_confidence'])
    
    if len(clean_df) == 0:
        print("❌ No complete data for accuracy analysis")
        return
    
    plt.figure(figsize=(15, 8))
    
    # Accuracy by confidence score ranges
    plt.subplot(2, 3, 1)
    confidence_bins = pd.cut(clean_df['confidence_score'], bins=5)
    accuracy_by_confidence = clean_df.groupby(confidence_bins)['prediction_correct'].mean()
    accuracy_by_confidence.plot(kind='bar', rot=45)
    plt.title('🎯 Accuracy by Confidence Score')
    plt.ylabel('Accuracy Rate')
    
    # Accuracy by news sentiment ranges
    plt.subplot(2, 3, 2)
    sentiment_bins = pd.cut(clean_df['news_sentiment'], bins=5)
    accuracy_by_sentiment = clean_df.groupby(sentiment_bins)['prediction_correct'].mean()
    accuracy_by_sentiment.plot(kind='bar', rot=45, color='blue')
    plt.title('📰 Accuracy by News Sentiment')
    plt.ylabel('Accuracy Rate')
    
    # Accuracy by technical score ranges
    plt.subplot(2, 3, 3)
    technical_bins = pd.cut(clean_df['technical_score'], bins=5)
    accuracy_by_technical = clean_df.groupby(technical_bins)['prediction_correct'].mean()
    accuracy_by_technical.plot(kind='bar', rot=45, color='green')
    plt.title('📈 Accuracy by Technical Score')
    plt.ylabel('Accuracy Rate')
    
    # Overall accuracy by symbol
    plt.subplot(2, 3, 4)
    accuracy_by_symbol = clean_df.groupby('symbol')['prediction_correct'].mean()
    accuracy_by_symbol.plot(kind='bar', rot=45, color='orange')
    plt.title('📊 Accuracy by Symbol')
    plt.ylabel('Accuracy Rate')
    
    # Accuracy by prediction direction
    plt.subplot(2, 3, 5)
    accuracy_by_direction = clean_df.groupby('prediction_direction')['prediction_correct'].mean()
    accuracy_by_direction.plot(kind='bar', rot=45, color='purple')
    plt.title('🔄 Accuracy by Direction')
    plt.ylabel('Accuracy Rate')
    
    # Combined components effectiveness
    plt.subplot(2, 3, 6)
    # Create composite score
    clean_df['composite_score'] = (
        clean_df['news_sentiment'] * 0.3 +
        clean_df['technical_score'] / 100 * 0.4 +
        clean_df['ml_confidence'] * 0.3
    )
    composite_bins = pd.cut(clean_df['composite_score'], bins=5)
    accuracy_by_composite = clean_df.groupby(composite_bins)['prediction_correct'].mean()
    accuracy_by_composite.plot(kind='bar', rot=45, color='red')
    plt.title('🎭 Accuracy by Composite Score')
    plt.ylabel('Accuracy Rate')
    
    plt.tight_layout()
    plt.savefig('data/accuracy_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print accuracy statistics
    overall_accuracy = clean_df['prediction_correct'].mean()
    print(f"📊 Overall Prediction Accuracy: {overall_accuracy:.1%}")
    
    print(f"\n📈 Accuracy by Symbol:")
    for symbol, accuracy in accuracy_by_symbol.items():
        print(f"   {symbol}: {accuracy:.1%}")

def main():
    """Main analysis function"""
    print("🔍 TRADING PREDICTIONS HISTORICAL ANALYSIS")
    print("=" * 60)
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Examine database
    tables = examine_database_structure()
    
    if not tables:
        print("❌ No tables found in database")
        return
    
    # Load data
    df = load_prediction_data()
    
    if df.empty:
        print("❌ No prediction data found")
        return
    
    # Calculate price changes and accuracy
    df = calculate_price_changes(df)
    
    # Create visualizations
    create_correlation_analysis(df)
    create_time_series_analysis(df)
    create_prediction_accuracy_analysis(df)
    
    print(f"\n🎯 ANALYSIS COMPLETE!")
    print("=" * 30)
    print("📊 Generated visualizations:")
    print("   - data/correlation_analysis.png")
    print("   - data/time_series_analysis.png") 
    print("   - data/accuracy_analysis.png")
    print("\n💡 Key insights:")
    print("   1. Check correlation matrix for strongest predictive signals")
    print("   2. Review time series to see how components align with price moves")
    print("   3. Analyze accuracy patterns to optimize prediction thresholds")

if __name__ == "__main__":
    main()
