import re

# Read current evaluator file
with open('corrected_outcome_evaluator_updated.py', 'r') as f:
    content = f.read()

# Update the database path to correct location
content = content.replace('db_path: str = "predictions.db"', 'db_path: str = "data/trading_predictions.db"')

# Fix get_pending_predictions query to get confidence data
old_query = '''cursor.execute("""
                SELECT p.prediction_id, p.symbol, p.prediction_timestamp, 
                       p.predicted_action, p.action_confidence, p.entry_price
                FROM predictions p'''

new_query = '''cursor.execute("""
                SELECT p.prediction_id, p.symbol, p.prediction_timestamp, 
                       p.predicted_action, p.action_confidence, p.entry_price
                FROM predictions p'''

# Add entry price validation method
validation_method = '''
    def validate_entry_price(self, symbol: str, stored_price: float, prediction_time: datetime) -> float:
        """Validate entry price is reasonable for the symbol"""
        if stored_price is None or stored_price <= 0:
            return self.get_precise_entry_price(symbol, prediction_time)
        
        # Basic validation - entry price should be reasonable for Australian stocks
        if symbol.endswith('.AX'):
            if stored_price < 1.0:  # Most ASX stocks are > 
                logger.warning(f"Suspicious low entry price for {symbol}:  - fetching fresh price")
                return self.get_precise_entry_price(symbol, prediction_time)
            if stored_price > 1000.0:  # Most ASX stocks are < 000
                logger.warning(f"Suspicious high entry price for {symbol}:  - fetching fresh price")
                return self.get_precise_entry_price(symbol, prediction_time)
        
        return stored_price'''

# Add performance metrics calculation
performance_calc = '''
        # Calculate performance metrics
        confidence = prediction.get('action_confidence', 0.0) or 0.0
        performance_metrics = {
            "confidence": round(float(confidence), 3),
            "success": success,
            "return": round(actual_return / 100, 6),  # Convert percentage to decimal
            "entry_validation": "validated" if stored_entry_price > 0 else "fetched",
            "evaluation_method": "timezone_corrected"
        }'''

# Update outcome creation to include performance_metrics
old_outcome = '''outcome = {
                'outcome_id': str(uuid.uuid4()),
                'prediction_id': prediction['prediction_id'],
                'actual_return': round(actual_return, 4),
                'actual_direction': actual_direction,
                'entry_price': round(entry_price, 4),
                'exit_price': round(exit_price, 4),
                'evaluation_timestamp': evaluation_time.isoformat(),
                'outcome_details': json.dumps({
                    'predicted_action': predicted_action,
                    'success': success,
                    'price_change': round(exit_price - entry_price, 4),
                    'price_change_pct': round(actual_return, 2),
                    'evaluation_method': 'corrected_timestamp_pricing',
                    'entry_method': 'stored_price' if stored_entry_price > 0 else 'precise_timestamp',
                    'exit_method': 'evaluation_time_price'
                })
            }'''

new_outcome = '''# Calculate performance metrics
            confidence = prediction.get('action_confidence', 0.0) or 0.0
            performance_metrics = {
                "confidence": round(float(confidence), 3),
                "success": success,
                "return": round(actual_return / 100, 6),  # Convert percentage to decimal
                "entry_validation": "validated" if stored_entry_price > 0 else "fetched",
                "evaluation_method": "timezone_corrected"
            }
            
            outcome = {
                'outcome_id': str(uuid.uuid4()),
                'prediction_id': prediction['prediction_id'],
                'actual_return': round(actual_return, 4),
                'actual_direction': actual_direction,
                'entry_price': round(entry_price, 4),
                'exit_price': round(exit_price, 4),
                'evaluation_timestamp': evaluation_time.isoformat(),
                'outcome_details': json.dumps({
                    'predicted_action': predicted_action,
                    'success': success,
                    'price_change': round(exit_price - entry_price, 4),
                    'price_change_pct': round(actual_return, 2),
                    'evaluation_method': 'corrected_timestamp_pricing',
                    'entry_method': 'stored_price' if stored_entry_price > 0 else 'precise_timestamp',
                    'exit_method': 'evaluation_time_price'
                }),
                'performance_metrics': json.dumps(performance_metrics)
            }'''

# Apply changes
content = content.replace(old_outcome, new_outcome)

# Add entry price validation to evaluation logic
old_entry_logic = '''# Get PRECISE entry price at prediction timestamp (1-minute interval)
            stored_entry_price = prediction.get('entry_price', 0.0) or 0.0
            
            if stored_entry_price > 0:
                # Use the stored entry price if available
                entry_price = stored_entry_price
                logger.info(f"Using stored entry price for {symbol}: ")
            else:'''

new_entry_logic = '''# Get PRECISE entry price at prediction timestamp (1-minute interval)
            stored_entry_price = prediction.get('entry_price', 0.0) or 0.0
            
            # Validate entry price
            entry_price = self.validate_entry_price(symbol, stored_entry_price, prediction_time)
            if entry_price != stored_entry_price:
                logger.info(f"Entry price corrected for {symbol}:  -> ")
            else:
                logger.info(f"Using validated entry price for {symbol}: ")
                
            if entry_price <= 0:'''

old_entry_logic2 = '''else:
                # Get precise entry price at prediction time
                entry_price = self.get_precise_entry_price(symbol, prediction_time)
                if entry_price == 0.0:'''

new_entry_logic2 = '''# Get precise entry price if validation failed
                entry_price = self.get_precise_entry_price(symbol, prediction_time)
                if entry_price == 0.0:'''

content = content.replace(old_entry_logic, new_entry_logic)
content = content.replace(old_entry_logic2, new_entry_logic2)

# Add validation method after ensure_timezone_aware
insert_point = '''return dt
        
    def get_db_connection(self):'''

new_insert = '''return dt
        
    def validate_entry_price(self, symbol: str, stored_price: float, prediction_time: datetime) -> float:
        """Validate entry price is reasonable for the symbol"""
        if stored_price is None or stored_price <= 0:
            return self.get_precise_entry_price(symbol, prediction_time)
        
        # Basic validation - entry price should be reasonable for Australian stocks
        if symbol.endswith('.AX'):
            if stored_price < 1.0:  # Most ASX stocks are > 
                logger.warning(f"Suspicious low entry price for {symbol}:  - fetching fresh price")
                return self.get_precise_entry_price(symbol, prediction_time)
            if stored_price > 1000.0:  # Most ASX stocks are < 000
                logger.warning(f"Suspicious high entry price for {symbol}:  - fetching fresh price")
                return self.get_precise_entry_price(symbol, prediction_time)
        
        return stored_price
        
    def get_db_connection(self):'''

content = content.replace(insert_point, new_insert)

# Write updated file
with open('corrected_outcome_evaluator_updated.py', 'w') as f:
    f.write(content)

print("✅ Enhanced evaluator with performance_metrics and entry price validation")
