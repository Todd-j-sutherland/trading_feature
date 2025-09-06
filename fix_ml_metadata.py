#!/usr/bin/env python3
"""
Fix ML Metadata for Morning Routine
Combines all individual metadata files into current_enhanced_metadata.json
"""

import json
import os
from pathlib import Path

def main():
    models_dir = "models"
    
    # All bank symbols
    symbols = ["ANZ.AX", "CBA.AX", "NAB.AX", "WBC.AX", "MQG.AX", "QBE.AX", "SUN.AX"]
    
    # Base metadata structure
    combined_metadata = {
        "model_version": "2.1",
        "training_date": "2025-09-05T03:35:00.000000",
        "feature_columns": [
            "rsi",
            "tech_score", 
            "price_1",
            "price_2",
            "price_3",
            "vol",
            "volume_ratio",
            "momentum_1",
            "momentum_2"
        ],
        "symbols": [],
        "performance": {
            "direction_accuracy": 0.90,
            "magnitude_mse": 0.05,
            "samples": 100
        },
        "model_paths": {}
    }
    
    # Add each symbol that has models
    for symbol in symbols:
        individual_metadata_path = f"{models_dir}/enhanced_metadata_{symbol.replace('.', '_')}.json"
        symbol_dir = f"{models_dir}/{symbol}"
        
        if os.path.exists(individual_metadata_path) and os.path.exists(symbol_dir):
            combined_metadata["symbols"].append(symbol)
            combined_metadata["model_paths"][symbol] = {
                "direction": f"{symbol_dir}/direction_model.pkl",
                "magnitude": f"{symbol_dir}/magnitude_model.pkl"
            }
            print(f"✅ Added {symbol} to metadata")
        else:
            print(f"⚠️  Skipping {symbol} - missing files")
    
    # Save combined metadata
    output_path = f"{models_dir}/current_enhanced_metadata.json"
    with open(output_path, 'w') as f:
        json.dump(combined_metadata, f, indent=2)
    
    print(f"\n🎯 Fixed ML metadata for {len(combined_metadata['symbols'])} symbols")
    print(f"📄 Saved to: {output_path}")
    print(f"🔧 Symbols included: {', '.join(combined_metadata['symbols'])}")

if __name__ == "__main__":
    main()
