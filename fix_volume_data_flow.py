#!/usr/bin/env python3
"""
Fix: Add Volume Data Storage to Morning Analyzer
Store volume data that evening analyzer can use
"""

def add_volume_storage_to_morning_analyzer():
    """Show how to add volume storage to the morning analyzer"""
    
    print("🔧 FIXING MORNING ANALYZER VOLUME STORAGE")
    print("=" * 60)
    
    print("📝 CHANGES NEEDED IN enhanced_morning_analyzer_with_ml.py:")
    print("-" * 60)
    
    print("1. 📊 CREATE VOLUME DATA TABLE:")
    print("""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_volume_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            latest_volume REAL,
            average_volume_20 REAL,
            volume_ratio REAL,
            market_hours BOOLEAN,
            data_timestamp DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, analysis_date)
        )
    ''')
    """)
    
    print("2. 🔄 MODIFY _save_analysis_results() METHOD:")
    print("""
    # Add volume data storage after existing database saves
    self._save_volume_data(analysis_results)
    """)
    
    print("3. ➕ ADD NEW _save_volume_data() METHOD:")
    print("""
    def _save_volume_data(self, analysis_results: Dict):
        \"\"\"Save volume data for evening analyzer to use\"\"\"
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create volume table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_volume_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    analysis_date DATE NOT NULL,
                    latest_volume REAL,
                    average_volume_20 REAL,
                    volume_ratio REAL,
                    market_hours BOOLEAN,
                    data_timestamp DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, analysis_date)
                )
            ''')
            
            analysis_date = self.get_australian_time().date()
            saved_count = 0
            
            for symbol in analysis_results['banks_analyzed']:
                try:
                    # Get volume data from market_data
                    market_data = get_market_data(symbol, period='3mo', interval='1h')
                    
                    if not market_data.empty and 'Volume' in market_data.columns:
                        latest_volume = float(market_data['Volume'].iloc[-1])
                        avg_volume_20 = float(market_data['Volume'].tail(20).mean())
                        volume_ratio = latest_volume / avg_volume_20 if avg_volume_20 > 0 else 0
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO daily_volume_data
                            (symbol, analysis_date, latest_volume, average_volume_20, 
                             volume_ratio, market_hours, data_timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            symbol,
                            analysis_date,
                            latest_volume,
                            avg_volume_20,
                            volume_ratio,
                            analysis_results['market_hours'],
                            analysis_results['timestamp']
                        ))
                        
                        saved_count += 1
                        self.logger.info(f"✅ Saved volume data: {symbol} = {latest_volume:,.0f} ({volume_ratio:.2f}x)")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to save volume for {symbol}: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Saved volume data for {saved_count} symbols")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving volume data: {e}")
    """)
    
    print("4. 🌙 EVENING ANALYZER ACCESS:")
    print("""
    def get_morning_volume_data(self, symbol: str) -> Dict:
        \"\"\"Get volume data collected by morning analyzer\"\"\"
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest volume data for symbol
            cursor.execute('''
                SELECT latest_volume, average_volume_20, volume_ratio, 
                       market_hours, data_timestamp
                FROM daily_volume_data 
                WHERE symbol = ? 
                ORDER BY analysis_date DESC 
                LIMIT 1
            ''', (symbol,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'has_volume_data': True,
                    'latest_volume': result[0],
                    'average_volume_20': result[1],
                    'volume_ratio': result[2],
                    'from_market_hours': result[3],
                    'data_timestamp': result[4]
                }
            else:
                return {'has_volume_data': False}
                
        except Exception as e:
            return {'has_volume_data': False, 'error': str(e)}
    """)
    
    print("5. 📈 VOLUME QUALITY ASSESSMENT UPDATE:")
    print("""
    # In evening analyzer volume assessment:
    volume_data = self.get_morning_volume_data(symbol)
    
    if volume_data['has_volume_data']:
        # Use actual volume data for quality assessment
        has_volume_data = True
        volume_ratio = volume_data['volume_ratio']
        
        # Adjust quality based on market hours
        if volume_data['from_market_hours']:
            data_availability = 1.0  # Live data
        else:
            data_availability = 0.8  # End-of-day data
            
        coverage_score = min(volume_ratio / 2.0, 1.0)  # Normalize ratio
        consistency_score = 0.6  # Baseline
        
        quality_score = (data_availability * 0.5) + (coverage_score * 0.3) + (consistency_score * 0.2)
        
    else:
        # No volume data available
        has_volume_data = False
        quality_score = 0.42  # Grade F
    """)
    
    print("🎯 EXPECTED RESULTS AFTER FIX:")
    print("-" * 60)
    print("✅ Morning run: Collects and stores volume data")
    print("✅ Evening run: Retrieves stored volume data")  
    print("✅ Volume assessment: Grade B/A instead of Grade F")
    print("✅ Data flow: Morning → Database → Evening")

if __name__ == "__main__":
    add_volume_storage_to_morning_analyzer()
