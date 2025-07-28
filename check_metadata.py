#!/usr/bin/env python3
"""
ML Model Metadata Checker and Fixer
Verifies all metadata files have the required 'version' key
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

def check_and_fix_metadata_file(file_path):
    """Check and fix a single metadata file"""
    print(f"📄 Checking: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"   ❌ File does not exist")
        return False
    
    try:
        with open(file_path, 'r') as f:
            metadata = json.load(f)
        
        # Check if version key exists
        if 'version' in metadata:
            print(f"   ✅ Version found: {metadata['version']}")
            return True
        
        # Fix missing version
        print(f"   🔧 Version key missing, fixing...")
        
        # Generate version from available data
        if 'training_date' in metadata:
            version = f"v_{metadata['training_date']}"
        elif 'created_at' in metadata:
            try:
                created = datetime.fromisoformat(metadata['created_at'].replace('Z', '+00:00'))
                version = f"v_{created.strftime('%Y%m%d_%H%M%S')}"
            except:
                version = f"v_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            version = f"v_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add version to metadata
        metadata['version'] = version
        
        # Also ensure other required fields exist
        if 'training_date' not in metadata:
            metadata['training_date'] = version.replace('v_', '')
        
        if 'feature_columns' not in metadata and 'features' in metadata:
            metadata['feature_columns'] = metadata['features']
        
        # Write back the fixed metadata
        with open(file_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"   ✅ Fixed! Added version: {version}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main function to check all metadata files"""
    print("🔍 ML Model Metadata Checker")
    print("============================")
    
    # Find all current_metadata.json files
    metadata_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'current_metadata.json':
                metadata_files.append(os.path.join(root, file))
    
    if not metadata_files:
        print("❌ No current_metadata.json files found!")
        return False
    
    print(f"Found {len(metadata_files)} metadata files:")
    
    all_good = True
    for file_path in metadata_files:
        if not check_and_fix_metadata_file(file_path):
            all_good = False
    
    print("\n" + "="*40)
    if all_good:
        print("🎉 All metadata files are valid!")
    else:
        print("⚠️  Some metadata files had issues (attempted to fix)")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
