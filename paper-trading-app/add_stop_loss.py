#!/usr/bin/env python3

# Script to add stop-loss functionality to enhanced_paper_trading_service.py

import sys

def add_stop_loss_logic(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Find the line with profit target check and add stop-loss after it
    for i, line in enumerate(lines):
        if 'exit_reason = f"Profit target reached' in line:
            # Insert stop-loss logic after this line
            indent = '            '  # Match existing indentation
            new_lines = [
                f'{indent}\n',
                f'{indent}# Stop loss triggered\n',
                f'{indent}elif current_profit <= -self.config["stop_loss"]:\n',
                f'{indent}    should_exit = True\n',
                f'{indent}    exit_reason = f"Stop loss triggered (${{current_profit:.2f}} <= -${{self.config[\\"stop_loss\\"]:.2f}})"\n'
            ]
            
            # Insert new lines after the current line
            lines[i+1:i+1] = new_lines
            break
    
    # Write back the modified content
    with open(filename, 'w') as f:
        f.writelines(lines)
    
    print("✅ Stop-loss logic added successfully")

if __name__ == "__main__":
    add_stop_loss_logic("enhanced_paper_trading_service.py")
