# Integration Testing

This folder contains integration tests for the enhanced ML system with existing app.main commands.

## Files

### `test_app_main_integration.py`
- **Purpose**: Tests integration between enhanced ML components and app.main commands
- **Features**:
  - Component detection testing
  - Feature extraction capability testing  
  - Morning/evening routine integration testing
  - Comprehensive integration validation

## Usage

### Run Integration Tests
```bash
cd enhanced_ml_system/integration
python test_app_main_integration.py
```

## Test Categories

### 1. Component Detection ✅
- Enhanced Morning Analyzer: Available
- Enhanced Evening Analyzer: Available
- Enhanced ML Pipeline: Available

### 2. Feature Extraction ✅
- Tests enhanced morning analysis
- Validates feature extraction capabilities
- Checks ML prediction generation

### 3. Morning Integration ✅
- Tests `app.main morning` integration
- Validates TradingSystemManager usage
- Ensures enhanced components are detected

### 4. Evening Integration ✅  
- Tests `app.main evening` integration
- Validates enhanced evening analysis
- Ensures proper system integration

## Integration Points
- **Daily Manager**: `app/services/daily_manager.py` (TradingSystemManager)
- **Morning Analysis**: Enhanced components automatically detected
- **Evening Analysis**: Enhanced components automatically detected
- **Fallback Mechanisms**: Graceful degradation when components unavailable

## Expected Results
- Component Detection: 3/3 enhanced components available
- Feature Extraction: Enhanced morning analysis working
- Integration: Both morning and evening routines functional
- Overall Assessment: System ready for production use
