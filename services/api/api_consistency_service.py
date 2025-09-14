#!/usr/bin/env python3
"""
API Consistency Service
Validates all microservice APIs match existing system interfaces
Ensures backward compatibility with current prediction system, paper trading, and ML components

Key Features:
- Validates API endpoint compatibility across all services
- Checks return format consistency with enhanced_efficient_system_market_aware.py
- Ensures prediction output matches existing database schemas
- Validates paper trading API compatibility with ig_markets_paper_trading
- Comprehensive interface validation for seamless migration

Dependencies:
- All trading microservices
- Original system interfaces for comparison
- Database schemas for format validation

Related Files:
- enhanced_efficient_system_market_aware.py (main prediction interface)
- paper-trading-app/enhanced_efficient_system_market_aware.py
- app/main_enhanced.py
- services/prediction/prediction_service.py
"""

import asyncio
import sys
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

# Settings.py integration for configuration management
SETTINGS_AVAILABLE = False
try:
    sys.path.append("app/config")
    import settings as Settings
    SETTINGS_AVAILABLE = True
except ImportError:
    try:
        sys.path.append("paper-trading-app/app/config")
        import settings as Settings
        SETTINGS_AVAILABLE = True
    except ImportError:
        Settings = None
        print("Warning: settings.py not found - using fallback configuration")

class APIConsistencyService(BaseService):
    """
    Comprehensive API consistency validation service
    Ensures all microservice APIs maintain exact compatibility with existing interfaces
    """
    
    def __init__(self):
        super().__init__("api-consistency")
        
        # Expected API interfaces from original system
        self.expected_interfaces = self._load_expected_interfaces()
        
        # Service endpoints to validate
        self.services_to_validate = [
            "market-data",
            "sentiment", 
            "prediction",
            "paper-trading",
            "ml-model",
            "scheduler",
            "database"
        ]
        
        # Validation results
        self.validation_results = {}
        self.compatibility_issues = []
        
        # Register API consistency methods
        self.register_handler("validate_all_apis", self.validate_all_apis)
        self.register_handler("validate_service_api", self.validate_service_api)
        self.register_handler("validate_prediction_compatibility", self.validate_prediction_compatibility)
        self.register_handler("validate_paper_trading_compatibility", self.validate_paper_trading_compatibility)
        self.register_handler("get_compatibility_report", self.get_compatibility_report)
        self.register_handler("fix_compatibility_issues", self.fix_compatibility_issues)
        
    def _load_expected_interfaces(self) -> Dict[str, Any]:
        """Load expected API interfaces from original system analysis"""
        return {
            "prediction_service": {
                "endpoints": {
                    "generate_predictions": {
                        "params": ["symbols", "force_refresh"],
                        "returns": {
                            "predictions": "dict",
                            "summary": {
                                "total_symbols": "int",
                                "successful": "int", 
                                "failed": "int",
                                "buy_rate": "float"
                            }
                        }
                    },
                    "generate_single_prediction": {
                        "params": ["symbol", "force_refresh"],
                        "returns": {
                            "action": "str",  # BUY/SELL/HOLD
                            "confidence": "float",
                            "technical_score": "float",
                            "sentiment_score": "float",
                            "market_context": "str",
                            "components": "dict"
                        }
                    }
                },
                "compatibility_requirements": {
                    "enhanced_efficient_system_market_aware": {
                        "make_enhanced_prediction": {
                            "returns": {
                                "predicted_action": "str",
                                "action_confidence": "float", 
                                "entry_price": "float",
                                "market_context": "str",
                                "prediction_details": "dict",
                                "components": "dict",
                                "feature_vector": "str"
                            }
                        }
                    }
                }
            },
            "market_data_service": {
                "endpoints": {
                    "get_market_data": {
                        "params": ["symbol"],
                        "returns": {
                            "technical": "dict",
                            "volume": "dict", 
                            "market_context": "dict"
                        }
                    },
                    "get_technical_indicators": {
                        "params": ["symbol"],
                        "returns": {
                            "rsi": "float",
                            "macd": "dict",
                            "bollinger_bands": "dict",
                            "moving_averages": "dict"
                        }
                    }
                }
            },
            "sentiment_service": {
                "endpoints": {
                    "analyze_sentiment": {
                        "params": ["symbol"],
                        "returns": {
                            "sentiment_score": "float",
                            "news_confidence": "float",
                            "news_quality_score": "float"
                        }
                    }
                }
            },
            "paper_trading_service": {
                "endpoints": {
                    "execute_trade": {
                        "params": ["symbol", "action", "quantity"],
                        "returns": {
                            "trade_id": "str",
                            "status": "str",
                            "ig_order_id": "str",
                            "timestamp": "str"
                        }
                    },
                    "get_positions": {
                        "params": [],
                        "returns": {
                            "positions": "dict"
                        }
                    }
                },
                "compatibility_requirements": {
                    "ig_markets_paper_trading": {
                        "database_schema": {
                            "paper_trades": ["id", "symbol", "action", "quantity", "price", "timestamp"],
                            "positions": ["symbol", "quantity", "avg_price", "current_value"]
                        }
                    }
                }
            }
        }
    
    async def validate_all_apis(self) -> Dict[str, Any]:
        """Validate all service APIs for consistency and compatibility"""
        self.logger.info('"action": "api_validation_started"')
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "services_validated": 0,
            "total_endpoints": 0,
            "compatibility_issues": [],
            "critical_issues": [],
            "warnings": [],
            "service_results": {}
        }
        
        for service_name in self.services_to_validate:
            try:
                service_result = await self.validate_service_api(service_name)
                validation_results["service_results"][service_name] = service_result
                validation_results["services_validated"] += 1
                validation_results["total_endpoints"] += service_result.get("endpoints_validated", 0)
                
                # Collect issues
                if service_result.get("compatibility_issues"):
                    validation_results["compatibility_issues"].extend(service_result["compatibility_issues"])
                    
                if service_result.get("critical_issues"):
                    validation_results["critical_issues"].extend(service_result["critical_issues"])
                    
                if service_result.get("warnings"):
                    validation_results["warnings"].extend(service_result["warnings"])
                    
            except Exception as e:
                self.logger.error(f'"service": "{service_name}", "error": "{e}", "action": "service_validation_failed"')
                validation_results["critical_issues"].append({
                    "service": service_name,
                    "type": "service_unreachable",
                    "error": str(e)
                })
        
        # Validate cross-service compatibility
        cross_service_issues = await self._validate_cross_service_compatibility()
        validation_results["cross_service_issues"] = cross_service_issues
        
        # Calculate overall compatibility score
        total_issues = len(validation_results["compatibility_issues"]) + len(validation_results["critical_issues"])
        total_checks = validation_results["total_endpoints"] + len(self.services_to_validate)
        compatibility_score = max(0, 100 - (total_issues / total_checks * 100)) if total_checks > 0 else 0
        validation_results["compatibility_score"] = round(compatibility_score, 1)
        
        # Store results
        self.validation_results = validation_results
        
        self.logger.info(f'"services_validated": {validation_results["services_validated"]}, "compatibility_score": {compatibility_score}, "action": "api_validation_completed"')
        
        return validation_results
    
    async def validate_service_api(self, service_name: str) -> Dict[str, Any]:
        """Validate specific service API compatibility"""
        service_result = {
            "service": service_name,
            "available": False,
            "endpoints_validated": 0,
            "compatibility_issues": [],
            "critical_issues": [],
            "warnings": [],
            "endpoint_results": {}
        }
        
        try:
            # Check if service is available
            health_result = await self.call_service(service_name, "health", timeout=10.0)
            service_result["available"] = True
            service_result["health"] = health_result
            
            # Get expected endpoints for this service
            expected_endpoints = self._get_expected_endpoints(service_name)
            
            for endpoint_name, endpoint_spec in expected_endpoints.items():
                try:
                    endpoint_result = await self._validate_endpoint(service_name, endpoint_name, endpoint_spec)
                    service_result["endpoint_results"][endpoint_name] = endpoint_result
                    service_result["endpoints_validated"] += 1
                    
                    if endpoint_result.get("issues"):
                        service_result["compatibility_issues"].extend(endpoint_result["issues"])
                        
                except Exception as e:
                    service_result["critical_issues"].append({
                        "endpoint": endpoint_name,
                        "error": str(e),
                        "type": "endpoint_validation_failed"
                    })
                    
        except Exception as e:
            service_result["critical_issues"].append({
                "error": str(e),
                "type": "service_connection_failed"
            })
            
        return service_result
    
    def _get_expected_endpoints(self, service_name: str) -> Dict[str, Any]:
        """Get expected endpoints for a service"""
        service_key = f"{service_name.replace('-', '_')}_service"
        return self.expected_interfaces.get(service_key, {}).get("endpoints", {})
    
    async def _validate_endpoint(self, service_name: str, endpoint_name: str, endpoint_spec: Dict) -> Dict[str, Any]:
        """Validate specific endpoint compatibility"""
        endpoint_result = {
            "endpoint": endpoint_name,
            "accessible": False,
            "return_format_valid": False,
            "issues": [],
            "response_time": 0
        }
        
        try:
            start_time = datetime.now()
            
            # Test endpoint with sample parameters
            test_params = self._generate_test_params(endpoint_spec.get("params", []))
            response = await self.call_service(service_name, endpoint_name, timeout=30.0, **test_params)
            
            endpoint_result["accessible"] = True
            endpoint_result["response_time"] = (datetime.now() - start_time).total_seconds()
            
            # Validate return format
            expected_returns = endpoint_spec.get("returns", {})
            format_issues = self._validate_return_format(response, expected_returns)
            
            if not format_issues:
                endpoint_result["return_format_valid"] = True
            else:
                endpoint_result["issues"].extend(format_issues)
                
        except Exception as e:
            endpoint_result["issues"].append({
                "type": "endpoint_call_failed",
                "error": str(e)
            })
            
        return endpoint_result
    
    def _generate_test_params(self, param_names: List[str]) -> Dict[str, Any]:
        """Generate test parameters for endpoint validation"""
        test_params = {}
        
        # Use settings symbols if available, otherwise fallback
        if SETTINGS_AVAILABLE and hasattr(Settings, 'BANK_SYMBOLS'):
            test_symbol = Settings.BANK_SYMBOLS[0]
        else:
            test_symbol = "CBA.AX"
        
        for param in param_names:
            if param == "symbol":
                test_params[param] = test_symbol
            elif param == "symbols":
                if SETTINGS_AVAILABLE and hasattr(Settings, 'BANK_SYMBOLS'):
                    test_params[param] = Settings.BANK_SYMBOLS[:3]  # Test with 3 symbols
                else:
                    test_params[param] = ["CBA.AX", "ANZ.AX", "WBC.AX"]
            elif param == "force_refresh":
                test_params[param] = False
            elif param == "action":
                test_params[param] = "BUY"
            elif param == "quantity":
                test_params[param] = 100
            # Add more parameter mappings as needed
                
        return test_params
    
    def _validate_return_format(self, response: Any, expected_format: Dict) -> List[Dict]:
        """Validate response format matches expected structure"""
        issues = []
        
        if not isinstance(response, dict):
            issues.append({
                "type": "invalid_return_type",
                "expected": "dict",
                "actual": type(response).__name__
            })
            return issues
        
        # Check required fields
        for field_name, field_type in expected_format.items():
            if field_name not in response:
                issues.append({
                    "type": "missing_field",
                    "field": field_name,
                    "expected_type": field_type
                })
                continue
                
            # Validate field type (simplified validation)
            actual_value = response[field_name]
            if field_type == "str" and not isinstance(actual_value, str):
                issues.append({
                    "type": "invalid_field_type",
                    "field": field_name,
                    "expected_type": field_type,
                    "actual_type": type(actual_value).__name__
                })
            elif field_type == "float" and not isinstance(actual_value, (int, float)):
                issues.append({
                    "type": "invalid_field_type",
                    "field": field_name,
                    "expected_type": field_type,
                    "actual_type": type(actual_value).__name__
                })
            elif field_type == "dict" and not isinstance(actual_value, dict):
                issues.append({
                    "type": "invalid_field_type",
                    "field": field_name,
                    "expected_type": field_type,
                    "actual_type": type(actual_value).__name__
                })
                
        return issues
    
    async def validate_prediction_compatibility(self) -> Dict[str, Any]:
        """Validate prediction service compatibility with enhanced_efficient_system_market_aware.py"""
        compatibility_result = {
            "compatible": False,
            "issues": [],
            "warnings": [],
            "tested_endpoints": 0,
            "successful_tests": 0
        }
        
        try:
            # Test symbols
            if SETTINGS_AVAILABLE and hasattr(Settings, 'BANK_SYMBOLS'):
                test_symbols = Settings.BANK_SYMBOLS[:2]  # Test with 2 symbols
            else:
                test_symbols = ["CBA.AX", "ANZ.AX"]
            
            # Test generate_single_prediction endpoint
            for symbol in test_symbols:
                try:
                    prediction = await self.call_service("prediction", "generate_single_prediction", symbol=symbol)
                    compatibility_result["tested_endpoints"] += 1
                    
                    # Validate prediction structure matches original system
                    required_fields = ["action", "confidence", "technical_score", "sentiment_score", "market_context"]
                    for field in required_fields:
                        if field not in prediction:
                            compatibility_result["issues"].append({
                                "type": "missing_prediction_field",
                                "field": field,
                                "symbol": symbol
                            })
                    
                    # Validate action values
                    if prediction.get("action") not in ["BUY", "SELL", "HOLD", "STRONG_BUY"]:
                        compatibility_result["issues"].append({
                            "type": "invalid_action_value",
                            "value": prediction.get("action"),
                            "symbol": symbol
                        })
                    
                    # Validate confidence range
                    confidence = prediction.get("confidence", 0)
                    if not (0 <= confidence <= 1):
                        compatibility_result["issues"].append({
                            "type": "invalid_confidence_range",
                            "value": confidence,
                            "symbol": symbol
                        })
                    
                    compatibility_result["successful_tests"] += 1
                    
                except Exception as e:
                    compatibility_result["issues"].append({
                        "type": "prediction_call_failed",
                        "symbol": symbol,
                        "error": str(e)
                    })
            
            # Test batch prediction
            try:
                batch_result = await self.call_service("prediction", "generate_predictions", symbols=test_symbols)
                compatibility_result["tested_endpoints"] += 1
                
                if "predictions" not in batch_result:
                    compatibility_result["issues"].append({
                        "type": "missing_batch_predictions_field",
                        "response_keys": list(batch_result.keys())
                    })
                
                if "summary" not in batch_result:
                    compatibility_result["issues"].append({
                        "type": "missing_batch_summary_field"
                    })
                
                compatibility_result["successful_tests"] += 1
                
            except Exception as e:
                compatibility_result["issues"].append({
                    "type": "batch_prediction_failed",
                    "error": str(e)
                })
            
            # Calculate compatibility
            compatibility_result["compatible"] = len(compatibility_result["issues"]) == 0
            
        except Exception as e:
            compatibility_result["issues"].append({
                "type": "prediction_compatibility_test_failed",
                "error": str(e)
            })
        
        return compatibility_result
    
    async def validate_paper_trading_compatibility(self) -> Dict[str, Any]:
        """Validate paper trading service compatibility with existing IG Markets integration"""
        compatibility_result = {
            "compatible": False,
            "issues": [],
            "warnings": [],
            "database_compatible": False,
            "ig_markets_integration": False
        }
        
        try:
            # Test paper trading service availability
            health = await self.call_service("paper-trading", "health")
            
            # Test position retrieval
            try:
                positions = await self.call_service("paper-trading", "get_positions")
                if "positions" not in positions:
                    compatibility_result["issues"].append({
                        "type": "invalid_positions_response",
                        "response_keys": list(positions.keys())
                    })
                    
            except Exception as e:
                compatibility_result["issues"].append({
                    "type": "positions_call_failed",
                    "error": str(e)
                })
            
            # Test trade execution interface
            try:
                # This is a test call - should not execute actual trade
                test_trade_result = await self.call_service("paper-trading", "validate_trade_interface", 
                                                          symbol="CBA.AX", action="BUY", quantity=1)
                
            except Exception as e:
                # Expected if validate_trade_interface doesn't exist
                compatibility_result["warnings"].append({
                    "type": "trade_interface_validation_unavailable",
                    "note": "Cannot test trade execution without actual execution"
                })
            
            # Validate database compatibility
            try:
                # Check if paper trading database exists and has correct schema
                db_validation = await self.call_service("database", "validate_database_schema", 
                                                      database="paper_trading")
                compatibility_result["database_compatible"] = db_validation.get("valid", False)
                
                if not compatibility_result["database_compatible"]:
                    compatibility_result["issues"].extend(db_validation.get("schema_issues", []))
                    
            except Exception as e:
                compatibility_result["warnings"].append({
                    "type": "database_validation_unavailable",
                    "error": str(e)
                })
            
            # Check IG Markets integration
            try:
                ig_status = await self.call_service("paper-trading", "get_ig_markets_status")
                compatibility_result["ig_markets_integration"] = ig_status.get("connected", False)
                
                if not compatibility_result["ig_markets_integration"]:
                    compatibility_result["warnings"].append({
                        "type": "ig_markets_not_connected",
                        "note": "IG Markets integration not active"
                    })
                    
            except Exception as e:
                compatibility_result["warnings"].append({
                    "type": "ig_markets_status_unavailable",
                    "error": str(e)
                })
            
            # Calculate overall compatibility
            critical_issues = [issue for issue in compatibility_result["issues"] 
                             if issue["type"] in ["invalid_positions_response", "positions_call_failed"]]
            compatibility_result["compatible"] = len(critical_issues) == 0
            
        except Exception as e:
            compatibility_result["issues"].append({
                "type": "paper_trading_compatibility_test_failed",
                "error": str(e)
            })
        
        return compatibility_result
    
    async def _validate_cross_service_compatibility(self) -> List[Dict]:
        """Validate compatibility between services"""
        cross_service_issues = []
        
        try:
            # Test prediction service dependency on market data service
            try:
                prediction_result = await self.call_service("prediction", "generate_single_prediction", symbol="CBA.AX")
                
                # Check if prediction service can get market data
                if "error" in str(prediction_result).lower() and "market" in str(prediction_result).lower():
                    cross_service_issues.append({
                        "type": "prediction_market_data_dependency_issue",
                        "details": "Prediction service may have issues accessing market data service"
                    })
                    
            except Exception as e:
                cross_service_issues.append({
                    "type": "prediction_service_integration_failed",
                    "error": str(e)
                })
            
            # Test paper trading dependency on prediction service
            try:
                # This would test if paper trading can get predictions for trade decisions
                pass  # Implement if paper trading service has prediction integration
                
            except Exception as e:
                pass
            
        except Exception as e:
            cross_service_issues.append({
                "type": "cross_service_validation_failed",
                "error": str(e)
            })
        
        return cross_service_issues
    
    async def get_compatibility_report(self) -> Dict[str, Any]:
        """Get comprehensive compatibility report"""
        if not self.validation_results:
            await self.validate_all_apis()
        
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "overall_compatibility": self.validation_results.get("compatibility_score", 0),
            "critical_issues_count": len(self.validation_results.get("critical_issues", [])),
            "compatibility_issues_count": len(self.validation_results.get("compatibility_issues", [])),
            "warnings_count": len(self.validation_results.get("warnings", [])),
            "services_status": {},
            "recommendations": []
        }
        
        # Service-specific status
        for service_name, service_result in self.validation_results.get("service_results", {}).items():
            report["services_status"][service_name] = {
                "available": service_result.get("available", False),
                "endpoints_validated": service_result.get("endpoints_validated", 0),
                "issues_count": len(service_result.get("compatibility_issues", [])) + len(service_result.get("critical_issues", []))
            }
        
        # Generate recommendations
        if report["critical_issues_count"] > 0:
            report["recommendations"].append("Address critical issues before production deployment")
        
        if report["compatibility_issues_count"] > 5:
            report["recommendations"].append("Review API compatibility issues for seamless migration")
        
        if report["overall_compatibility"] < 80:
            report["recommendations"].append("Improve API compatibility before switching from monolithic system")
        
        return report
    
    async def fix_compatibility_issues(self, issue_types: List[str] = None) -> Dict[str, Any]:
        """Attempt to fix common compatibility issues"""
        fix_result = {
            "fixes_attempted": 0,
            "fixes_successful": 0,
            "fixes_failed": 0,
            "fix_details": []
        }
        
        if not self.validation_results:
            await self.validate_all_apis()
        
        # Get all issues to fix
        all_issues = []
        all_issues.extend(self.validation_results.get("critical_issues", []))
        all_issues.extend(self.validation_results.get("compatibility_issues", []))
        
        # Filter by issue types if specified
        if issue_types:
            all_issues = [issue for issue in all_issues if issue.get("type") in issue_types]
        
        for issue in all_issues:
            fix_result["fixes_attempted"] += 1
            
            try:
                if issue["type"] == "missing_field":
                    # Attempt to add missing field to service response
                    fix_details = await self._fix_missing_field(issue)
                    fix_result["fix_details"].append(fix_details)
                    
                elif issue["type"] == "invalid_return_type":
                    # Attempt to fix return type mismatch
                    fix_details = await self._fix_return_type(issue)
                    fix_result["fix_details"].append(fix_details)
                    
                elif issue["type"] == "service_unreachable":
                    # Attempt to restart service
                    fix_details = await self._fix_service_unreachable(issue)
                    fix_result["fix_details"].append(fix_details)
                    
                else:
                    fix_result["fix_details"].append({
                        "issue_type": issue["type"],
                        "status": "not_fixable_automatically",
                        "note": "Manual intervention required"
                    })
                    continue
                
                if fix_details.get("success"):
                    fix_result["fixes_successful"] += 1
                else:
                    fix_result["fixes_failed"] += 1
                    
            except Exception as e:
                fix_result["fixes_failed"] += 1
                fix_result["fix_details"].append({
                    "issue_type": issue.get("type", "unknown"),
                    "status": "fix_failed",
                    "error": str(e)
                })
        
        return fix_result
    
    async def _fix_missing_field(self, issue: Dict) -> Dict:
        """Attempt to fix missing field issues"""
        return {
            "issue_type": "missing_field",
            "status": "requires_manual_fix",
            "note": f"Service needs to be updated to include field: {issue.get('field')}"
        }
    
    async def _fix_return_type(self, issue: Dict) -> Dict:
        """Attempt to fix return type issues"""
        return {
            "issue_type": "invalid_return_type", 
            "status": "requires_manual_fix",
            "note": f"Service return type needs to be changed from {issue.get('actual')} to {issue.get('expected')}"
        }
    
    async def _fix_service_unreachable(self, issue: Dict) -> Dict:
        """Attempt to fix service unreachable issues"""
        service_name = issue.get("service")
        if service_name:
            try:
                # Try to restart service (this would require system privileges)
                # For now, just report the issue
                return {
                    "issue_type": "service_unreachable",
                    "status": "restart_required",
                    "note": f"Service {service_name} needs to be restarted"
                }
            except Exception as e:
                return {
                    "issue_type": "service_unreachable",
                    "status": "restart_failed",
                    "error": str(e)
                }
        
        return {
            "issue_type": "service_unreachable",
            "status": "cannot_identify_service"
        }

async def main():
    service = APIConsistencyService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
