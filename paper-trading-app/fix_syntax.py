#!/usr/bin/env python3

# Fix syntax error in stop-loss string

def fix_syntax_error(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    # Fix the problematic line
    content = content.replace(
        'f"Stop loss triggered (${current_profit:.2f} <= -${self.config[\\"stop_loss\\"]:.2f})"',
        'f"Stop loss triggered (${current_profit:.2f} <= -${self.config[\'stop_loss\']:.2f})"'
    )
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print("✅ Syntax error fixed")

if __name__ == "__main__":
    fix_syntax_error("enhanced_paper_trading_service.py")
