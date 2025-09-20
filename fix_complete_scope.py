#!/usr/bin/env python3
"""
Complete fix for volume calculation scope issue
"""

def fix_complete_scope():
    """Completely fix the volume scope issue"""
    
    file_path = "/root/test/enhanced_efficient_system_market_aware.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix the details section - get volume_change_pct from volume_data
        old_details = '''            "details": {
                "tech_score": tech_score,
                "news_sentiment": news_sentiment,
                "news_confidence": news_confidence,
                "volume_trend": volume_trend,
        "volume_change_pct": volume_change_pct,  # Store original percentage
                "volume_correlation": volume_correlation,'''
        
        new_details = '''            "details": {
                "tech_score": tech_score,
                "news_sentiment": news_sentiment,
                "news_confidence": news_confidence,
                "volume_trend": volume_trend,
                "volume_change_pct": volume_data.get("volume_change_pct", 0.0),  # From volume_data
                "volume_correlation": volume_correlation,'''
        
        content = content.replace(old_details, new_details)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ Fixed complete scope issue")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing complete scope: {e}")
        return False

if __name__ == "__main__":
    fix_complete_scope()