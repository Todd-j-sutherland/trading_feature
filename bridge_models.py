#!/usr/bin/env python3
"""Bridge script to copy our models to the format expected by enhanced system"""

import pickle
import json
import shutil
from pathlib import Path

def bridge_models():
    """Copy symbol-specific models to global format expected by enhanced system"""
    
    models_dir = Path("models")
    
    # For now, use CBA.AX as the primary model (best performing with 21 samples)
    primary_symbol = "CBA.AX"
    primary_dir = models_dir / primary_symbol
    
    if not primary_dir.exists():
        print(f"❌ Primary symbol models not found: {primary_dir}")
        return False
    
    # Copy direction model
    src_direction = primary_dir / "direction_model.pkl"
    dst_direction = models_dir / "current_direction_model.pkl"
    
    if src_direction.exists():
        shutil.copy2(src_direction, dst_direction)
        print(f"✅ Direction model: {src_direction} -> {dst_direction}")
    
    # Copy magnitude model
    src_magnitude = primary_dir / "magnitude_model.pkl"
    dst_magnitude = models_dir / "current_magnitude_model.pkl"
    
    if src_magnitude.exists():
        shutil.copy2(src_magnitude, dst_magnitude)
        print(f"✅ Magnitude model: {src_magnitude} -> {dst_magnitude}")
    
    # Create enhanced metadata
    src_metadata = primary_dir / "metadata.json"
    if src_metadata.exists():
        with open(src_metadata, "r") as f:
            symbol_metadata = json.load(f)
        
        enhanced_metadata = {
            "version": "2.1",
            "training_date": "2025-08-25T09:52:00",
            "feature_columns": symbol_metadata["feature_names"],
            "model_type": "enhanced_multi_output",
            "direction_model_path": str(dst_direction),
            "magnitude_model_path": str(dst_magnitude),
            "base_symbol": primary_symbol,
            "performance": symbol_metadata["performance"]
        }
        
        dst_metadata = models_dir / "current_enhanced_metadata.json"
        with open(dst_metadata, "w") as f:
            json.dump(enhanced_metadata, f, indent=2)
        
        print(f"✅ Enhanced metadata: {dst_metadata}")
    
    # Verify files exist
    required_files = [
        models_dir / "current_direction_model.pkl",
        models_dir / "current_magnitude_model.pkl", 
        models_dir / "current_enhanced_metadata.json"
    ]
    
    all_exist = all(f.exists() for f in required_files)
    
    if all_exist:
        print(f"\n🎯 SUCCESS: All required files created")
        print(f"   Enhanced system should now find ML models")
        return True
    else:
        print(f"\n❌ FAILURE: Some files missing")
        return False

if __name__ == "__main__":
    print("🌉 BRIDGING MODELS TO ENHANCED SYSTEM FORMAT")
    print("=" * 50)
    bridge_models()
