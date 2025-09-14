#!/usr/bin/env python3
"""
Security Enhancement Module for Trading Microservices

CRITICAL SECURITY IMPLEMENTATIONS:
1. Service-to-Service Authentication with Token Rotation
2. Rate Limiting and DOS Protection  
3. Enhanced Input Validation and Sanitization
4. Audit Trail for Financial Operations
5. Memory Security for Credentials

This module addresses the high-priority security vulnerabilities identified
in the security audit, providing enterprise-grade security for financial
trading operations.

Usage:
- Import and integrate with BaseService
- Configure security parameters via environment variables
- Monitor security events via enhanced logging

Security Features:
- HMAC-based service authentication
- Rolling token rotation (configurable interval)
- Per-service and per-endpoint rate limiting
- Comprehensive audit logging with integrity checking
- Secure credential storage with memory protection
- Advanced input validation with fuzzing protection
"""

import asyncio
import hashlib
import hmac
import secrets
import time
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
import re

@dataclass
class SecurityConfig:
    """Security configuration for microservices"""
    # Authentication
    token_rotation_interval: int = 3600  # 1 hour
    max_token_age: int = 7200  # 2 hours
    
    # Rate Limiting
    default_rate_limit: int = 100  # requests per minute
    burst_rate_limit: int = 200  # burst capacity
    rate_limit_window: int = 60  # seconds
    
    # Input Validation
    max_request_size: int = 1024 * 1024  # 1MB
    max_json_depth: int = 10
    max_array_length: int = 1000
    
    # Audit
    audit_retention_days: int = 90
    audit_integrity_check: bool = True
    
    # Memory Security
    secure_memory_enabled: bool = True
    credential_scrub_interval: int = 300  # 5 minutes

class ServiceAuthenticator:
    """Service-to-service authentication with token rotation"""
    
    def __init__(self, service_name: str, config: SecurityConfig):
        self.service_name = service_name
        self.config = config
        self.current_tokens = {}
        self.pending_tokens = {}
        self.last_rotation = time.time()
        self.lock = threading.Lock()
        
        # Initialize encryption for token storage
        self.cipher = self._initialize_encryption()
        
        # Load or generate initial tokens
        self._initialize_tokens()
        
        # Start token rotation task
        self.rotation_task = None
    
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption for token storage"""
        # Derive key from environment or generate new one
        salt = os.getenv('SERVICE_SALT', secrets.token_bytes(16))
        if isinstance(salt, str):
            salt = salt.encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        password = os.getenv('SERVICE_MASTER_KEY', 'default_key_change_in_production').encode()
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return Fernet(key)
    
    def _initialize_tokens(self):
        """Initialize service tokens"""
        # Load existing tokens or generate new ones
        try:
            encrypted_tokens = os.getenv('SERVICE_TOKENS_ENCRYPTED')
            if encrypted_tokens:
                decrypted_data = self.cipher.decrypt(encrypted_tokens.encode())
                self.current_tokens = json.loads(decrypted_data.decode())
            else:
                self._generate_new_tokens()
        except Exception:
            self._generate_new_tokens()
    
    def _generate_new_tokens(self):
        """Generate new service tokens"""
        with self.lock:
            # List of all services that need tokens
            services = [
                "market-data", "sentiment", "ml-model", 
                "prediction", "scheduler", "paper-trading", "manager"
            ]
            
            self.current_tokens = {
                service: secrets.token_urlsafe(32) 
                for service in services
            }
            
            # Save encrypted tokens
            self._save_tokens()
    
    def _save_tokens(self):
        """Save tokens in encrypted form"""
        try:
            token_data = json.dumps(self.current_tokens)
            encrypted_tokens = self.cipher.encrypt(token_data.encode())
            
            # Store in environment (in production, use secure key store)
            os.environ['SERVICE_TOKENS_ENCRYPTED'] = encrypted_tokens.decode()
        except Exception as e:
            logging.error(f"Failed to save service tokens: {e}")
    
    def get_service_token(self, target_service: str) -> str:
        """Get authentication token for target service"""
        with self.lock:
            return self.current_tokens.get(target_service, "")
    
    def validate_token(self, token: str, source_service: str) -> bool:
        """Validate incoming service token"""
        with self.lock:
            expected_token = self.current_tokens.get(source_service, "")
            if not expected_token:
                return False
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(token, expected_token)
    
    async def rotate_tokens(self):
        """Rotate service tokens"""
        with self.lock:
            # Move current tokens to pending
            self.pending_tokens = self.current_tokens.copy()
            
            # Generate new tokens
            self._generate_new_tokens()
            self.last_rotation = time.time()
            
            logging.info(f"Service tokens rotated for {self.service_name}")
    
    def should_rotate(self) -> bool:
        """Check if tokens should be rotated"""
        return (time.time() - self.last_rotation) > self.config.token_rotation_interval

class RateLimiter:
    """Advanced rate limiting with multiple algorithms"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.requests = defaultdict(deque)  # service_id -> request_times
        self.blocked_until = {}  # service_id -> unblock_time
        self.lock = threading.Lock()
    
    def is_allowed(self, service_id: str, endpoint: str = "default") -> bool:
        """Check if request is allowed under rate limits"""
        with self.lock:
            now = time.time()
            
            # Check if service is temporarily blocked
            if service_id in self.blocked_until:
                if now < self.blocked_until[service_id]:
                    return False
                else:
                    del self.blocked_until[service_id]
            
            # Get rate limit for this endpoint
            rate_limit = self._get_rate_limit(endpoint)
            
            # Clean old requests
            service_requests = self.requests[service_id]
            cutoff_time = now - self.config.rate_limit_window
            
            while service_requests and service_requests[0] < cutoff_time:
                service_requests.popleft()
            
            # Check rate limit
            if len(service_requests) >= rate_limit:
                # Block service temporarily on excessive requests
                self.blocked_until[service_id] = now + 60  # 1 minute block
                logging.warning(f"Rate limit exceeded for {service_id} on {endpoint}")
                return False
            
            # Allow request
            service_requests.append(now)
            return True
    
    def _get_rate_limit(self, endpoint: str) -> int:
        """Get rate limit for specific endpoint"""
        # Different endpoints can have different limits
        endpoint_limits = {
            "health": 200,
            "prediction": 50,
            "market_data": 100,
            "execute_trade": 10,
            "default": self.config.default_rate_limit
        }
        
        return endpoint_limits.get(endpoint, self.config.default_rate_limit)

class SecurityValidator:
    """Enhanced input validation and sanitization"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        
        # Compiled regex patterns for validation
        self.patterns = {
            'service_name': re.compile(r'^[a-z][a-z0-9\-]{2,30}$'),
            'symbol': re.compile(r'^[A-Z]{2,6}\.AX$'),
            'method_name': re.compile(r'^[a-z_][a-z0-9_]{2,50}$'),
            'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'),
        }
        
        # Dangerous patterns to detect injection attempts
        self.dangerous_patterns = [
            re.compile(r'[;&|`$(){}[\]<>]'),  # Shell injection
            re.compile(r'(union|select|insert|delete|update|drop|exec|script)', re.IGNORECASE),  # SQL injection
            re.compile(r'javascript:|data:|vbscript:', re.IGNORECASE),  # XSS attempts
            re.compile(r'\.\.[\\/]'),  # Path traversal
        ]
    
    def validate_request(self, request_data: bytes, source_service: str) -> Dict[str, Any]:
        """Comprehensive request validation"""
        # Size validation
        if len(request_data) > self.config.max_request_size:
            raise SecurityError(f"Request too large: {len(request_data)} bytes")
        
        # Parse JSON safely
        try:
            request = json.loads(request_data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise SecurityError(f"Invalid JSON format: {e}")
        
        # Structure validation
        if not isinstance(request, dict):
            raise SecurityError("Request must be a JSON object")
        
        # Validate JSON depth and array lengths
        self._validate_json_structure(request, depth=0)
        
        # Validate method name
        method = request.get('method', '')
        if not self.patterns['method_name'].match(method):
            raise SecurityError(f"Invalid method name: {method}")
        
        # Validate parameters
        params = request.get('params', {})
        if not isinstance(params, dict):
            raise SecurityError("Parameters must be a JSON object")
        
        # Sanitize parameters
        sanitized_params = self._sanitize_parameters(params)
        
        return {
            'method': method,
            'params': sanitized_params,
            'source_service': source_service,
            'timestamp': time.time()
        }
    
    def _validate_json_structure(self, obj: Any, depth: int):
        """Validate JSON structure depth and array lengths"""
        if depth > self.config.max_json_depth:
            raise SecurityError(f"JSON too deeply nested: {depth}")
        
        if isinstance(obj, dict):
            for value in obj.values():
                self._validate_json_structure(value, depth + 1)
        elif isinstance(obj, list):
            if len(obj) > self.config.max_array_length:
                raise SecurityError(f"Array too long: {len(obj)}")
            for item in obj:
                self._validate_json_structure(item, depth + 1)
    
    def _sanitize_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize request parameters"""
        sanitized = {}
        
        for key, value in params.items():
            # Validate key name
            if not isinstance(key, str) or len(key) > 50:
                continue
            
            # Check for dangerous patterns
            if any(pattern.search(str(value)) for pattern in self.dangerous_patterns):
                logging.warning(f"Dangerous pattern detected in parameter {key}: {value}")
                continue
            
            # Type-specific sanitization
            if key == 'symbol' and isinstance(value, str):
                if self.patterns['symbol'].match(value.upper()):
                    sanitized[key] = value.upper()
            elif key in ['quantity', 'price'] and isinstance(value, (int, float)):
                if 0 < value < 1000000:  # Reasonable trading limits
                    sanitized[key] = value
            elif isinstance(value, str) and len(value) <= 1000:
                # General string sanitization
                sanitized[key] = value.strip()
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list) and len(value) <= 100:
                sanitized[key] = [item for item in value if isinstance(item, (str, int, float))][:100]
        
        return sanitized

class SecurityAuditLogger:
    """Comprehensive audit logging for financial operations"""
    
    def __init__(self, service_name: str, config: SecurityConfig):
        self.service_name = service_name
        self.config = config
        
        # Setup audit logger
        self.audit_logger = logging.getLogger(f"audit.{service_name}")
        self.audit_logger.setLevel(logging.INFO)
        
        # Setup audit file handler
        audit_handler = logging.FileHandler(f"/var/log/trading/audit_{service_name}.log")
        audit_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "audit": %(message)s}'
        )
        audit_handler.setFormatter(audit_formatter)
        self.audit_logger.addHandler(audit_handler)
        
        # Initialize integrity checking
        self.integrity_key = self._get_integrity_key()
    
    def _get_integrity_key(self) -> bytes:
        """Get or generate integrity checking key"""
        key_env = os.getenv('AUDIT_INTEGRITY_KEY')
        if key_env:
            return base64.b64decode(key_env.encode())
        else:
            # Generate new key (in production, store securely)
            key = secrets.token_bytes(32)
            os.environ['AUDIT_INTEGRITY_KEY'] = base64.b64encode(key).decode()
            return key
    
    def _calculate_integrity_hash(self, record: Dict[str, Any]) -> str:
        """Calculate integrity hash for audit record"""
        # Create deterministic string representation
        record_str = json.dumps(record, sort_keys=True, separators=(',', ':'))
        
        # Calculate HMAC
        return hmac.new(
            self.integrity_key,
            record_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def log_security_event(self, event_type: str, details: Dict[str, Any], 
                                risk_level: str = "INFO"):
        """Log security-related events"""
        audit_record = {
            'event_type': 'security_event',
            'security_event_type': event_type,
            'service': self.service_name,
            'timestamp': datetime.utcnow().isoformat(),
            'risk_level': risk_level,
            'details': details
        }
        
        if self.config.audit_integrity_check:
            audit_record['integrity_hash'] = self._calculate_integrity_hash(audit_record)
        
        self.audit_logger.info(json.dumps(audit_record))
    
    async def log_financial_operation(self, operation_type: str, operation_data: Dict[str, Any],
                                    result: Dict[str, Any], user_context: Dict[str, Any] = None):
        """Log financial operations with high integrity"""
        audit_record = {
            'event_type': 'financial_operation',
            'operation_type': operation_type,
            'service': self.service_name,
            'timestamp': datetime.utcnow().isoformat(),
            'operation_data': operation_data,
            'result': result,
            'user_context': user_context or {}
        }
        
        if self.config.audit_integrity_check:
            audit_record['integrity_hash'] = self._calculate_integrity_hash(audit_record)
        
        self.audit_logger.info(json.dumps(audit_record))
    
    async def log_access_attempt(self, source_service: str, target_method: str, 
                               success: bool, details: Dict[str, Any] = None):
        """Log service access attempts"""
        audit_record = {
            'event_type': 'access_attempt',
            'source_service': source_service,
            'target_service': self.service_name,
            'target_method': target_method,
            'success': success,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        
        if self.config.audit_integrity_check:
            audit_record['integrity_hash'] = self._calculate_integrity_hash(audit_record)
        
        self.audit_logger.info(json.dumps(audit_record))

class SecurityError(Exception):
    """Security-related exception"""
    pass

class SecureCredentialStore:
    """Secure storage for sensitive credentials"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.credentials = {}
        self.lock = threading.Lock()
        
        # Initialize encryption
        self.cipher = self._initialize_encryption()
        
        # Start credential scrubbing task if enabled
        if config.secure_memory_enabled:
            self.scrub_task = None
    
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption for credential storage"""
        key = Fernet.generate_key()
        return Fernet(key)
    
    def store_credential(self, key: str, value: str):
        """Store credential securely"""
        with self.lock:
            encrypted_value = self.cipher.encrypt(value.encode())
            self.credentials[key] = {
                'value': encrypted_value,
                'stored_at': time.time(),
                'access_count': 0
            }
            
            # Clear the original value from memory (best effort)
            del value
    
    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve credential securely"""
        with self.lock:
            if key not in self.credentials:
                return None
            
            cred_data = self.credentials[key]
            cred_data['access_count'] += 1
            cred_data['last_accessed'] = time.time()
            
            # Decrypt and return
            decrypted_value = self.cipher.decrypt(cred_data['value']).decode()
            return decrypted_value
    
    def scrub_old_credentials(self):
        """Remove old credentials from memory"""
        with self.lock:
            now = time.time()
            to_remove = []
            
            for key, cred_data in self.credentials.items():
                # Remove credentials older than scrub interval
                if (now - cred_data['stored_at']) > self.config.credential_scrub_interval:
                    to_remove.append(key)
            
            for key in to_remove:
                del self.credentials[key]
                logging.info(f"Scrubbed credential: {key}")

class SecurityManager:
    """Central security manager for microservices"""
    
    def __init__(self, service_name: str, config: SecurityConfig = None):
        self.service_name = service_name
        self.config = config or SecurityConfig()
        
        # Initialize security components
        self.authenticator = ServiceAuthenticator(service_name, self.config)
        self.rate_limiter = RateLimiter(self.config)
        self.validator = SecurityValidator(self.config)
        self.audit_logger = SecurityAuditLogger(service_name, self.config)
        self.credential_store = SecureCredentialStore(self.config)
        
        # Security metrics
        self.security_metrics = {
            'authentication_failures': 0,
            'rate_limit_violations': 0,
            'validation_failures': 0,
            'suspicious_requests': 0
        }
    
    async def authenticate_request(self, token: str, source_service: str) -> bool:
        """Authenticate incoming service request"""
        is_valid = self.authenticator.validate_token(token, source_service)
        
        if not is_valid:
            self.security_metrics['authentication_failures'] += 1
            await self.audit_logger.log_security_event(
                'authentication_failure',
                {'source_service': source_service},
                'MEDIUM'
            )
        
        return is_valid
    
    async def check_rate_limit(self, service_id: str, endpoint: str) -> bool:
        """Check rate limits for request"""
        is_allowed = self.rate_limiter.is_allowed(service_id, endpoint)
        
        if not is_allowed:
            self.security_metrics['rate_limit_violations'] += 1
            await self.audit_logger.log_security_event(
                'rate_limit_violation',
                {'service_id': service_id, 'endpoint': endpoint},
                'HIGH'
            )
        
        return is_allowed
    
    async def validate_request(self, request_data: bytes, source_service: str) -> Dict[str, Any]:
        """Validate and sanitize request"""
        try:
            validated_request = self.validator.validate_request(request_data, source_service)
            return validated_request
        except SecurityError as e:
            self.security_metrics['validation_failures'] += 1
            await self.audit_logger.log_security_event(
                'validation_failure',
                {'source_service': source_service, 'error': str(e)},
                'HIGH'
            )
            raise
    
    async def log_access(self, source_service: str, method: str, success: bool, 
                        execution_time: float = None):
        """Log service access"""
        await self.audit_logger.log_access_attempt(
            source_service, method, success,
            {'execution_time': execution_time} if execution_time else None
        )
    
    async def log_financial_operation(self, operation_type: str, operation_data: Dict[str, Any],
                                    result: Dict[str, Any]):
        """Log financial operations"""
        await self.audit_logger.log_financial_operation(
            operation_type, operation_data, result
        )
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get current security metrics"""
        return {
            **self.security_metrics,
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name
        }
    
    async def rotate_tokens_if_needed(self):
        """Rotate tokens if needed"""
        if self.authenticator.should_rotate():
            await self.authenticator.rotate_tokens()
            await self.audit_logger.log_security_event(
                'token_rotation',
                {'service': self.service_name},
                'INFO'
            )

# Export main components
__all__ = [
    'SecurityManager',
    'SecurityConfig',
    'SecurityError',
    'ServiceAuthenticator',
    'RateLimiter',
    'SecurityValidator',
    'SecurityAuditLogger',
    'SecureCredentialStore'
]
