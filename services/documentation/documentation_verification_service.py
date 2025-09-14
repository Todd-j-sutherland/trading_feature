#!/usr/bin/env python3
"""
Documentation Verification Service
Complete documentation review and validation of all implementation details
"""
import asyncio
import os
import sys
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.base_service import BaseService

@dataclass
class DocumentationCheck:
    check_type: str
    file_path: str
    status: str  # "passed", "failed", "warning", "incomplete"
    details: Optional[Dict] = None
    issues: List[str] = None
    suggestions: List[str] = None
    timestamp: str = ""

@dataclass
class CodeDocumentation:
    file_path: str
    functions_documented: int
    functions_total: int
    classes_documented: int
    classes_total: int
    has_module_docstring: bool
    docstring_quality_score: float
    missing_documentation: List[str]

class DocumentationVerificationService(BaseService):
    """Documentation verification service for comprehensive implementation validation"""

    def __init__(self):
        super().__init__("documentation-verifier")
        self.documentation_checks = {}
        self.code_documentation_cache = {}
        
        # Register documentation verification methods
        self.register_handler("verify_all_documentation", self.verify_all_documentation)
        self.register_handler("check_code_documentation", self.check_code_documentation)
        self.register_handler("validate_configuration_docs", self.validate_configuration_docs)
        self.register_handler("check_deployment_documentation", self.check_deployment_documentation)
        self.register_handler("verify_api_documentation", self.verify_api_documentation)
        self.register_handler("generate_documentation_report", self.generate_documentation_report)
        self.register_handler("create_missing_documentation", self.create_missing_documentation)
        self.register_handler("update_readme", self.update_readme)

    async def verify_all_documentation(self):
        """Comprehensive documentation verification"""
        verification_session = {
            "session_id": f"doc_verification_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {}
        }

        self.logger.info(f'"action": "documentation_verification_started", "session_id": "{verification_session["session_id"]}"')

        # Run all documentation checks
        verification_session["checks"]["code_documentation"] = await self._check_all_code_documentation()
        verification_session["checks"]["configuration_docs"] = await self._validate_configuration_documentation()
        verification_session["checks"]["deployment_docs"] = await self._check_deployment_documentation()
        verification_session["checks"]["api_documentation"] = await self._verify_api_documentation()
        verification_session["checks"]["readme_files"] = await self._check_readme_files()
        verification_session["checks"]["project_documentation"] = await self._check_project_documentation()
        verification_session["checks"]["user_guides"] = await self._check_user_guides()

        # Generate documentation summary
        verification_session["summary"] = self._generate_documentation_summary(verification_session["checks"])
        
        # Store results
        self.documentation_checks[verification_session["session_id"]] = verification_session

        self.logger.info(f'"action": "documentation_verification_completed", "session_id": "{verification_session["session_id"]}", "overall_score": {verification_session["summary"]["overall_documentation_score"]:.1f}"')

        return verification_session

    async def _check_all_code_documentation(self) -> DocumentationCheck:
        """Check documentation coverage for all Python files"""
        try:
            python_files = []
            
            # Find all Python files in services directory
            for root, dirs, files in os.walk("services"):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        python_files.append(os.path.join(root, file))

            documentation_results = {}
            total_functions = 0
            documented_functions = 0
            total_classes = 0
            documented_classes = 0
            files_with_module_docs = 0

            for file_path in python_files:
                try:
                    doc_analysis = await self._analyze_file_documentation(file_path)
                    documentation_results[file_path] = doc_analysis
                    
                    total_functions += doc_analysis.functions_total
                    documented_functions += doc_analysis.functions_documented
                    total_classes += doc_analysis.classes_total
                    documented_classes += doc_analysis.classes_documented
                    
                    if doc_analysis.has_module_docstring:
                        files_with_module_docs += 1
                        
                except Exception as e:
                    documentation_results[file_path] = f"Error analyzing file: {e}"

            # Calculate overall statistics
            function_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 100
            class_coverage = (documented_classes / total_classes * 100) if total_classes > 0 else 100
            module_coverage = (files_with_module_docs / len(python_files) * 100) if python_files else 100
            
            overall_score = (function_coverage + class_coverage + module_coverage) / 3

            issues = []
            if function_coverage < 80:
                issues.append(f"Low function documentation coverage: {function_coverage:.1f}%")
            if class_coverage < 80:
                issues.append(f"Low class documentation coverage: {class_coverage:.1f}%")
            if module_coverage < 90:
                issues.append(f"Low module documentation coverage: {module_coverage:.1f}%")

            return DocumentationCheck(
                check_type="code_documentation",
                file_path="services/",
                status="passed" if overall_score >= 80 else "warning" if overall_score >= 60 else "failed",
                details={
                    "files_analyzed": len(python_files),
                    "function_coverage": function_coverage,
                    "class_coverage": class_coverage,
                    "module_coverage": module_coverage,
                    "overall_score": overall_score,
                    "file_results": documentation_results
                },
                issues=issues,
                suggestions=[
                    "Add docstrings to undocumented functions and classes",
                    "Include module-level docstrings for all Python files",
                    "Use consistent docstring format (Google or NumPy style)"
                ],
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DocumentationCheck(
                check_type="code_documentation",
                file_path="services/",
                status="failed",
                issues=[f"Error checking code documentation: {e}"],
                timestamp=datetime.now().isoformat()
            )

    async def _analyze_file_documentation(self, file_path: str) -> CodeDocumentation:
        """Analyze documentation coverage for a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse file content
            lines = content.split('\n')
            
            # Check for module docstring
            has_module_docstring = False
            if content.strip().startswith('"""') or content.strip().startswith("'''"):
                has_module_docstring = True
            elif any(line.strip().startswith('"""') or line.strip().startswith("'''") 
                    for line in lines[:10] if line.strip() and not line.strip().startswith('#')):
                has_module_docstring = True

            # Find functions and their documentation
            function_pattern = re.compile(r'^\s*def\s+(\w+)\s*\(')
            class_pattern = re.compile(r'^\s*class\s+(\w+)')
            docstring_pattern = re.compile(r'^\s*""".*?"""', re.DOTALL | re.MULTILINE)

            functions = []
            classes = []
            
            for i, line in enumerate(lines):
                func_match = function_pattern.match(line)
                if func_match:
                    function_name = func_match.group(1)
                    if not function_name.startswith('_'):  # Skip private functions for now
                        # Check if next non-empty line is a docstring
                        has_docstring = False
                        for j in range(i + 1, min(i + 5, len(lines))):
                            next_line = lines[j].strip()
                            if next_line:
                                if next_line.startswith('"""') or next_line.startswith("'''"):
                                    has_docstring = True
                                break
                        functions.append((function_name, has_docstring))
                
                class_match = class_pattern.match(line)
                if class_match:
                    class_name = class_match.group(1)
                    # Check if next non-empty line is a docstring
                    has_docstring = False
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if next_line:
                            if next_line.startswith('"""') or next_line.startswith("'''"):
                                has_docstring = True
                            break
                    classes.append((class_name, has_docstring))

            # Calculate statistics
            functions_total = len(functions)
            functions_documented = sum(1 for _, has_doc in functions if has_doc)
            classes_total = len(classes)
            classes_documented = sum(1 for _, has_doc in classes if has_doc)

            # Calculate quality score
            coverage_score = 0
            if functions_total > 0:
                coverage_score += (functions_documented / functions_total) * 0.5
            if classes_total > 0:
                coverage_score += (classes_documented / classes_total) * 0.3
            if has_module_docstring:
                coverage_score += 0.2

            # Find missing documentation
            missing_documentation = []
            for func_name, has_doc in functions:
                if not has_doc:
                    missing_documentation.append(f"Function: {func_name}")
            for class_name, has_doc in classes:
                if not has_doc:
                    missing_documentation.append(f"Class: {class_name}")

            return CodeDocumentation(
                file_path=file_path,
                functions_documented=functions_documented,
                functions_total=functions_total,
                classes_documented=classes_documented,
                classes_total=classes_total,
                has_module_docstring=has_module_docstring,
                docstring_quality_score=coverage_score,
                missing_documentation=missing_documentation
            )

        except Exception as e:
            return CodeDocumentation(
                file_path=file_path,
                functions_documented=0,
                functions_total=0,
                classes_documented=0,
                classes_total=0,
                has_module_docstring=False,
                docstring_quality_score=0.0,
                missing_documentation=[f"Error analyzing file: {e}"]
            )

    async def _validate_configuration_documentation(self) -> DocumentationCheck:
        """Validate configuration documentation"""
        try:
            config_docs = {}
            issues = []
            suggestions = []

            # Check if settings.py has proper documentation
            settings_files = ["settings.py", "app/config/settings.py", "config/settings.py"]
            settings_documented = False
            
            for settings_file in settings_files:
                if os.path.exists(settings_file):
                    with open(settings_file, 'r') as f:
                        content = f.read()
                    
                    # Check for configuration comments/documentation
                    has_comments = '#' in content
                    has_docstrings = '"""' in content or "'''" in content
                    
                    config_docs[settings_file] = {
                        "exists": True,
                        "has_comments": has_comments,
                        "has_docstrings": has_docstrings,
                        "documented": has_comments or has_docstrings
                    }
                    
                    if has_comments or has_docstrings:
                        settings_documented = True
                    
                    if not (has_comments or has_docstrings):
                        issues.append(f"Settings file {settings_file} lacks documentation")

            if not settings_documented:
                issues.append("No documented settings files found")
                suggestions.append("Add inline comments explaining configuration options")

            # Check for configuration README or guide
            config_guides = [
                "CONFIG.md", "CONFIGURATION.md", "docs/configuration.md",
                "app/config/README.md", "config/README.md"
            ]
            
            config_guide_exists = any(os.path.exists(guide) for guide in config_guides)
            config_docs["configuration_guide"] = {
                "exists": config_guide_exists,
                "checked_paths": config_guides
            }
            
            if not config_guide_exists:
                issues.append("No configuration guide documentation found")
                suggestions.append("Create a comprehensive configuration guide")

            # Check microservices configuration documentation
            microservices_docs = {}
            service_dirs = ["services/core", "services/market_data", "services/ml", "services/prediction"]
            
            for service_dir in service_dirs:
                if os.path.exists(service_dir):
                    readme_path = os.path.join(service_dir, "README.md")
                    config_path = os.path.join(service_dir, "config.py")
                    
                    microservices_docs[service_dir] = {
                        "has_readme": os.path.exists(readme_path),
                        "has_config": os.path.exists(config_path),
                        "documented": os.path.exists(readme_path) or os.path.exists(config_path)
                    }
                    
                    if not os.path.exists(readme_path):
                        issues.append(f"Service {service_dir} missing README.md")

            overall_config_score = 0
            if settings_documented:
                overall_config_score += 40
            if config_guide_exists:
                overall_config_score += 30
            
            documented_services = sum(1 for docs in microservices_docs.values() if docs["documented"])
            if microservices_docs:
                overall_config_score += (documented_services / len(microservices_docs)) * 30

            return DocumentationCheck(
                check_type="configuration_documentation",
                file_path="configuration files",
                status="passed" if overall_config_score >= 70 else "warning" if overall_config_score >= 50 else "failed",
                details={
                    "settings_files": config_docs,
                    "configuration_guide": config_guide_exists,
                    "microservices_docs": microservices_docs,
                    "overall_score": overall_config_score
                },
                issues=issues,
                suggestions=suggestions,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DocumentationCheck(
                check_type="configuration_documentation", 
                file_path="configuration files",
                status="failed",
                issues=[f"Error checking configuration documentation: {e}"],
                timestamp=datetime.now().isoformat()
            )

    async def _check_deployment_documentation(self) -> DocumentationCheck:
        """Check deployment documentation"""
        try:
            deployment_docs = {}
            issues = []
            suggestions = []

            # Check for deployment guides
            deployment_guides = [
                "DEPLOYMENT.md", "docs/deployment.md", "INSTALL.md", 
                "docs/installation.md", "setup/README.md"
            ]
            
            deployment_guide_exists = False
            for guide in deployment_guides:
                if os.path.exists(guide):
                    deployment_guide_exists = True
                    with open(guide, 'r') as f:
                        content = f.read()
                    
                    deployment_docs[guide] = {
                        "exists": True,
                        "size": len(content),
                        "has_systemd_info": "systemd" in content.lower(),
                        "has_requirements": "requirements" in content.lower() or "dependencies" in content.lower(),
                        "has_installation_steps": "install" in content.lower() or "setup" in content.lower()
                    }

            if not deployment_guide_exists:
                issues.append("No deployment documentation found")
                suggestions.append("Create comprehensive deployment guide")

            # Check for systemd service files documentation
            systemd_services = [
                "trading-news-scraper.service", "trading-market-data.service",
                "trading-prediction.service", "trading-scheduler.service"
            ]
            
            systemd_docs = {}
            for service in systemd_services:
                service_file = f"systemd/{service}"
                if os.path.exists(service_file):
                    with open(service_file, 'r') as f:
                        content = f.read()
                    
                    systemd_docs[service] = {
                        "exists": True,
                        "has_description": "Description=" in content,
                        "has_dependencies": "After=" in content or "Requires=" in content,
                        "documented": "Description=" in content
                    }
                else:
                    systemd_docs[service] = {"exists": False}

            # Check for Docker documentation
            docker_docs = {}
            docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.dev.yml"]
            
            for docker_file in docker_files:
                if os.path.exists(docker_file):
                    with open(docker_file, 'r') as f:
                        content = f.read()
                    
                    docker_docs[docker_file] = {
                        "exists": True,
                        "has_comments": "#" in content,
                        "documented": "#" in content and len([line for line in content.split('\n') if line.strip().startswith('#')]) >= 3
                    }

            # Check for requirements documentation
            requirements_files = ["requirements.txt", "requirements-prod.txt", "setup.py"]
            requirements_docs = {}
            
            for req_file in requirements_files:
                if os.path.exists(req_file):
                    requirements_docs[req_file] = {"exists": True}

            # Calculate deployment documentation score
            deployment_score = 0
            if deployment_guide_exists:
                deployment_score += 50
            
            documented_systemd = sum(1 for docs in systemd_docs.values() if docs.get("documented", False))
            if systemd_docs:
                deployment_score += (documented_systemd / len(systemd_docs)) * 25
            
            if requirements_docs:
                deployment_score += 25

            return DocumentationCheck(
                check_type="deployment_documentation",
                file_path="deployment files",
                status="passed" if deployment_score >= 70 else "warning" if deployment_score >= 50 else "failed",
                details={
                    "deployment_guides": deployment_docs,
                    "systemd_services": systemd_docs,
                    "docker_files": docker_docs,
                    "requirements_files": requirements_docs,
                    "deployment_score": deployment_score
                },
                issues=issues,
                suggestions=suggestions + [
                    "Document systemd service configurations",
                    "Add Docker deployment instructions if using containers",
                    "Include troubleshooting section in deployment guide"
                ],
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DocumentationCheck(
                check_type="deployment_documentation",
                file_path="deployment files",
                status="failed",
                issues=[f"Error checking deployment documentation: {e}"],
                timestamp=datetime.now().isoformat()
            )

    async def _verify_api_documentation(self) -> DocumentationCheck:
        """Verify API documentation"""
        try:
            api_docs = {}
            issues = []
            suggestions = []

            # Check for API documentation files
            api_doc_files = [
                "API.md", "docs/api.md", "api/README.md",
                "docs/api_reference.md", "API_REFERENCE.md"
            ]
            
            api_doc_exists = any(os.path.exists(doc) for doc in api_doc_files)
            
            if api_doc_exists:
                for doc_file in api_doc_files:
                    if os.path.exists(doc_file):
                        with open(doc_file, 'r') as f:
                            content = f.read()
                        
                        api_docs[doc_file] = {
                            "exists": True,
                            "size": len(content),
                            "has_endpoints": "endpoint" in content.lower() or "api" in content.lower(),
                            "has_examples": "example" in content.lower() or "curl" in content.lower(),
                            "has_response_formats": "response" in content.lower() or "json" in content.lower()
                        }

            # Check service API documentation by examining docstrings
            service_apis = {}
            service_files = [
                "services/base_service.py",
                "services/core/news_scraper.py",
                "services/market_data/market_data_service.py",
                "services/prediction/prediction_service.py"
            ]
            
            for service_file in service_files:
                if os.path.exists(service_file):
                    with open(service_file, 'r') as f:
                        content = f.read()
                    
                    # Count documented handler methods
                    handler_methods = re.findall(r'register_handler\(["\'](\w+)["\']', content)
                    documented_handlers = 0
                    
                    for handler in handler_methods:
                        # Check if handler method has docstring
                        handler_pattern = f"async def {handler}"
                        if handler_pattern in content:
                            handler_index = content.find(handler_pattern)
                            if handler_index != -1:
                                # Look for docstring after method definition
                                method_section = content[handler_index:handler_index + 500]
                                if '"""' in method_section or "'''" in method_section:
                                    documented_handlers += 1
                    
                    service_apis[service_file] = {
                        "total_handlers": len(handler_methods),
                        "documented_handlers": documented_handlers,
                        "documentation_coverage": (documented_handlers / len(handler_methods) * 100) if handler_methods else 100
                    }

            # Calculate API documentation score
            api_score = 0
            if api_doc_exists:
                api_score += 40
            
            if service_apis:
                avg_coverage = sum(api["documentation_coverage"] for api in service_apis.values()) / len(service_apis)
                api_score += (avg_coverage / 100) * 60

            if api_score < 60:
                issues.append("Insufficient API documentation")
                suggestions.extend([
                    "Create comprehensive API documentation",
                    "Document all service endpoints and methods",
                    "Include request/response examples"
                ])

            return DocumentationCheck(
                check_type="api_documentation",
                file_path="API documentation",
                status="passed" if api_score >= 70 else "warning" if api_score >= 50 else "failed",
                details={
                    "api_doc_files": api_docs,
                    "service_apis": service_apis,
                    "api_score": api_score,
                    "average_handler_coverage": sum(api["documentation_coverage"] for api in service_apis.values()) / len(service_apis) if service_apis else 0
                },
                issues=issues,
                suggestions=suggestions,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DocumentationCheck(
                check_type="api_documentation",
                file_path="API documentation",
                status="failed",
                issues=[f"Error checking API documentation: {e}"],
                timestamp=datetime.now().isoformat()
            )

    async def _check_readme_files(self) -> DocumentationCheck:
        """Check README files throughout the project"""
        try:
            readme_files = {}
            issues = []
            suggestions = []

            # Check main README
            main_readme_files = ["README.md", "Readme.md", "readme.md"]
            main_readme_exists = False
            
            for readme in main_readme_files:
                if os.path.exists(readme):
                    main_readme_exists = True
                    with open(readme, 'r') as f:
                        content = f.read()
                    
                    readme_files[readme] = {
                        "exists": True,
                        "size": len(content),
                        "has_description": len(content) > 100,
                        "has_installation": "install" in content.lower() or "setup" in content.lower(),
                        "has_usage": "usage" in content.lower() or "how to" in content.lower(),
                        "has_structure": "structure" in content.lower() or "directory" in content.lower(),
                        "quality_score": self._calculate_readme_quality(content)
                    }
                    break

            if not main_readme_exists:
                issues.append("No main README.md file found")
                suggestions.append("Create comprehensive main README.md")

            # Check subdirectory READMEs
            subdirs_to_check = [
                "services", "app", "docs", "scripts", "data",
                "models", "paper-trading-app", "ig_markets_paper_trading"
            ]
            
            subdir_readmes = {}
            for subdir in subdirs_to_check:
                if os.path.exists(subdir):
                    readme_path = os.path.join(subdir, "README.md")
                    if os.path.exists(readme_path):
                        with open(readme_path, 'r') as f:
                            content = f.read()
                        
                        subdir_readmes[subdir] = {
                            "has_readme": True,
                            "size": len(content),
                            "quality_score": self._calculate_readme_quality(content)
                        }
                    else:
                        subdir_readmes[subdir] = {"has_readme": False}
                        if subdir in ["services", "app", "docs"]:  # Important directories
                            issues.append(f"Missing README.md in {subdir} directory")

            # Calculate overall README score
            readme_score = 0
            if main_readme_exists and readme_files:
                main_readme_quality = list(readme_files.values())[0]["quality_score"]
                readme_score += main_readme_quality * 0.6
            
            documented_subdirs = sum(1 for readme in subdir_readmes.values() if readme["has_readme"])
            if subdir_readmes:
                readme_score += (documented_subdirs / len(subdir_readmes)) * 40

            return DocumentationCheck(
                check_type="readme_files",
                file_path="README files",
                status="passed" if readme_score >= 70 else "warning" if readme_score >= 50 else "failed",
                details={
                    "main_readme": readme_files,
                    "subdirectory_readmes": subdir_readmes,
                    "readme_score": readme_score,
                    "documented_directories": documented_subdirs,
                    "total_directories": len(subdir_readmes)
                },
                issues=issues,
                suggestions=suggestions + [
                    "Add README files to important subdirectories",
                    "Include project structure in main README",
                    "Add usage examples and getting started guide"
                ],
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DocumentationCheck(
                check_type="readme_files",
                file_path="README files",
                status="failed",
                issues=[f"Error checking README files: {e}"],
                timestamp=datetime.now().isoformat()
            )

    def _calculate_readme_quality(self, content: str) -> float:
        """Calculate README quality score based on content"""
        score = 0
        
        # Basic content checks
        if len(content) > 500:
            score += 20
        elif len(content) > 200:
            score += 10
        
        # Structure checks
        if "# " in content:  # Has headers
            score += 15
        if "## " in content:  # Has subheaders
            score += 10
        
        # Content quality checks
        content_lower = content.lower()
        if "installation" in content_lower or "install" in content_lower:
            score += 15
        if "usage" in content_lower or "how to" in content_lower:
            score += 15
        if "example" in content_lower:
            score += 10
        if "configuration" in content_lower or "config" in content_lower:
            score += 10
        if "api" in content_lower or "endpoint" in content_lower:
            score += 5
        
        return min(score, 100)

    async def _check_project_documentation(self) -> DocumentationCheck:
        """Check overall project documentation"""
        try:
            project_docs = {}
            issues = []
            suggestions = []

            # Check for project documentation files
            project_doc_files = [
                "ARCHITECTURE.md", "DESIGN.md", "OVERVIEW.md",
                "docs/architecture.md", "docs/design.md", "docs/overview.md"
            ]
            
            for doc_file in project_doc_files:
                if os.path.exists(doc_file):
                    with open(doc_file, 'r') as f:
                        content = f.read()
                    
                    project_docs[doc_file] = {
                        "exists": True,
                        "size": len(content),
                        "has_diagrams": "![" in content or "diagram" in content.lower(),
                        "has_architecture": "architecture" in content.lower() or "microservice" in content.lower(),
                        "comprehensive": len(content) > 1000
                    }

            # Check for changelog
            changelog_files = ["CHANGELOG.md", "CHANGES.md", "HISTORY.md"]
            has_changelog = any(os.path.exists(f) for f in changelog_files)
            
            # Check for contributing guidelines
            contributing_files = ["CONTRIBUTING.md", "docs/contributing.md"]
            has_contributing = any(os.path.exists(f) for f in contributing_files)

            # Check for license
            license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt"]
            has_license = any(os.path.exists(f) for f in license_files)

            project_score = 0
            if project_docs:
                project_score += 40
            if has_changelog:
                project_score += 20
            if has_contributing:
                project_score += 20
            if has_license:
                project_score += 20

            if not project_docs:
                issues.append("No architecture/design documentation found")
                suggestions.append("Create project architecture documentation")
            
            if not has_changelog:
                suggestions.append("Add CHANGELOG.md to track project changes")

            return DocumentationCheck(
                check_type="project_documentation",
                file_path="project documentation",
                status="passed" if project_score >= 60 else "warning" if project_score >= 40 else "failed",
                details={
                    "project_docs": project_docs,
                    "has_changelog": has_changelog,
                    "has_contributing": has_contributing,
                    "has_license": has_license,
                    "project_score": project_score
                },
                issues=issues,
                suggestions=suggestions,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DocumentationCheck(
                check_type="project_documentation",
                file_path="project documentation", 
                status="failed",
                issues=[f"Error checking project documentation: {e}"],
                timestamp=datetime.now().isoformat()
            )

    async def _check_user_guides(self) -> DocumentationCheck:
        """Check user guides and tutorials"""
        try:
            user_guides = {}
            issues = []
            suggestions = []

            # Check for user guide files
            user_guide_files = [
                "USER_GUIDE.md", "GETTING_STARTED.md", "TUTORIAL.md",
                "docs/user_guide.md", "docs/getting_started.md", "docs/tutorial.md",
                "QUICK_START.md", "docs/quick_start.md"
            ]
            
            guide_exists = False
            for guide_file in user_guide_files:
                if os.path.exists(guide_file):
                    guide_exists = True
                    with open(guide_file, 'r') as f:
                        content = f.read()
                    
                    user_guides[guide_file] = {
                        "exists": True,
                        "size": len(content),
                        "has_examples": "example" in content.lower(),
                        "has_screenshots": "![" in content or "image" in content.lower(),
                        "step_by_step": "step" in content.lower() or "1." in content,
                        "comprehensive": len(content) > 800
                    }

            # Check for troubleshooting documentation
            troubleshooting_files = [
                "TROUBLESHOOTING.md", "FAQ.md", "docs/troubleshooting.md", "docs/faq.md"
            ]
            
            has_troubleshooting = any(os.path.exists(f) for f in troubleshooting_files)

            user_guide_score = 0
            if guide_exists:
                user_guide_score += 60
                # Bonus for quality
                for guide in user_guides.values():
                    if guide.get("has_examples"):
                        user_guide_score += 10
                    if guide.get("step_by_step"):
                        user_guide_score += 10
                    break  # Only check first guide for bonuses
            
            if has_troubleshooting:
                user_guide_score += 20

            if not guide_exists:
                issues.append("No user guides or getting started documentation found")
                suggestions.extend([
                    "Create a getting started guide for new users",
                    "Add step-by-step tutorials with examples",
                    "Include troubleshooting documentation"
                ])

            return DocumentationCheck(
                check_type="user_guides",
                file_path="user guides",
                status="passed" if user_guide_score >= 60 else "warning" if user_guide_score >= 40 else "failed",
                details={
                    "user_guides": user_guides,
                    "has_troubleshooting": has_troubleshooting,
                    "user_guide_score": user_guide_score
                },
                issues=issues,
                suggestions=suggestions,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DocumentationCheck(
                check_type="user_guides",
                file_path="user guides",
                status="failed",
                issues=[f"Error checking user guides: {e}"],
                timestamp=datetime.now().isoformat()
            )

    def _generate_documentation_summary(self, checks: Dict[str, DocumentationCheck]) -> Dict:
        """Generate documentation verification summary"""
        total_checks = len(checks)
        passed_checks = sum(1 for check in checks.values() if check.status == "passed")
        warning_checks = sum(1 for check in checks.values() if check.status == "warning")
        failed_checks = sum(1 for check in checks.values() if check.status == "failed")

        # Calculate overall documentation score
        check_scores = []
        for check in checks.values():
            if check.status == "passed":
                check_scores.append(100)
            elif check.status == "warning":
                check_scores.append(70)
            elif check.status == "failed":
                check_scores.append(30)
            else:
                check_scores.append(0)

        overall_documentation_score = sum(check_scores) / len(check_scores) if check_scores else 0

        # Collect all issues and suggestions
        all_issues = []
        all_suggestions = []
        
        for check in checks.values():
            if check.issues:
                all_issues.extend(check.issues)
            if check.suggestions:
                all_suggestions.extend(check.suggestions)

        # Remove duplicates while preserving order
        unique_issues = list(dict.fromkeys(all_issues))
        unique_suggestions = list(dict.fromkeys(all_suggestions))

        return {
            "overall_documentation_score": overall_documentation_score,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "warning_checks": warning_checks,
            "failed_checks": failed_checks,
            "documentation_status": self._get_documentation_status(overall_documentation_score),
            "critical_issues": unique_issues[:5],  # Top 5 issues
            "priority_suggestions": unique_suggestions[:5],  # Top 5 suggestions
            "documentation_recommendation": self._get_documentation_recommendation(overall_documentation_score)
        }

    def _get_documentation_status(self, score: float) -> str:
        """Get documentation status based on score"""
        if score >= 85:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "adequate"
        elif score >= 40:
            return "needs_improvement"
        else:
            return "poor"

    def _get_documentation_recommendation(self, score: float) -> str:
        """Get documentation recommendation based on score"""
        if score >= 85:
            return "✅ Documentation is comprehensive and well-maintained"
        elif score >= 75:
            return "👍 Documentation is good with minor improvements needed"
        elif score >= 60:
            return "📝 Documentation is adequate but could be enhanced"
        elif score >= 40:
            return "⚠️ Documentation needs significant improvement"
        else:
            return "❌ Documentation is insufficient and requires immediate attention"

    async def check_code_documentation(self, file_path: str = None):
        """Public endpoint to check code documentation"""
        if file_path:
            if os.path.exists(file_path):
                return await self._analyze_file_documentation(file_path)
            else:
                return {"error": f"File {file_path} not found"}
        else:
            return await self._check_all_code_documentation()

    async def validate_configuration_docs(self):
        """Public endpoint to validate configuration documentation"""
        return await self._validate_configuration_documentation()

    async def check_deployment_documentation(self):
        """Public endpoint to check deployment documentation"""
        return await self._check_deployment_documentation()

    async def verify_api_documentation(self):
        """Public endpoint to verify API documentation"""
        return await self._verify_api_documentation()

    async def generate_documentation_report(self):
        """Generate comprehensive documentation report"""
        verification_result = await self.verify_all_documentation()
        
        report = {
            "report_id": f"documentation_report_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "verification_results": verification_result,
            "action_plan": [],
            "quick_wins": [],
            "long_term_improvements": []
        }

        summary = verification_result["summary"]
        
        # Generate action plan based on results
        if summary["overall_documentation_score"] < 60:
            report["action_plan"].extend([
                "1. Prioritize creating missing critical documentation",
                "2. Add docstrings to all public functions and classes",
                "3. Create comprehensive README files",
                "4. Document API endpoints and configuration options"
            ])
        elif summary["overall_documentation_score"] < 75:
            report["action_plan"].extend([
                "1. Enhance existing documentation with more details",
                "2. Add examples and usage scenarios",
                "3. Create user guides and tutorials",
                "4. Improve code documentation coverage"
            ])

        # Quick wins (easy improvements)
        report["quick_wins"].extend([
            "Add module docstrings to Python files without them",
            "Create missing README files in subdirectories",
            "Add inline comments to configuration files",
            "Update main README with current project structure"
        ])

        # Long-term improvements
        report["long_term_improvements"].extend([
            "Create comprehensive architecture documentation",
            "Develop interactive API documentation",
            "Add automated documentation generation",
            "Create video tutorials for complex workflows"
        ])

        # Save report
        report_file = f"documentation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            report["report_saved"] = report_file
        except Exception as e:
            report["report_save_error"] = str(e)

        return report

    async def create_missing_documentation(self, doc_type: str = "all"):
        """Create missing documentation files"""
        created_files = []
        
        try:
            if doc_type in ["all", "readme"]:
                # Create main README if missing
                if not any(os.path.exists(f) for f in ["README.md", "Readme.md", "readme.md"]):
                    readme_content = self._generate_main_readme()
                    with open("README.md", 'w') as f:
                        f.write(readme_content)
                    created_files.append("README.md")

            if doc_type in ["all", "api"]:
                # Create API documentation if missing
                api_files = ["API.md", "docs/api.md", "api/README.md"]
                if not any(os.path.exists(f) for f in api_files):
                    api_content = self._generate_api_documentation()
                    os.makedirs("docs", exist_ok=True)
                    with open("docs/api.md", 'w') as f:
                        f.write(api_content)
                    created_files.append("docs/api.md")

            if doc_type in ["all", "deployment"]:
                # Create deployment guide if missing
                deployment_files = ["DEPLOYMENT.md", "docs/deployment.md"]
                if not any(os.path.exists(f) for f in deployment_files):
                    deployment_content = self._generate_deployment_guide()
                    with open("DEPLOYMENT.md", 'w') as f:
                        f.write(deployment_content)
                    created_files.append("DEPLOYMENT.md")

            return {
                "created_files": created_files,
                "total_created": len(created_files),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "error": f"Error creating documentation: {e}",
                "created_files": created_files
            }

    def _generate_main_readme(self) -> str:
        """Generate main README.md content"""
        return '''# Trading Microservices System

A comprehensive microservices-based trading system for Australian stock market analysis and automated paper trading.

## Overview

This system provides real-time stock market analysis, prediction generation, and automated paper trading capabilities using a microservices architecture.

## Architecture

- **News Scraper Service**: RSS news collection and sentiment analysis
- **Market Data Service**: Real-time market data and technical indicators
- **ML Model Service**: Machine learning model management and predictions
- **Prediction Service**: Comprehensive stock prediction generation
- **Scheduler Service**: Market-aware task scheduling
- **Paper Trading Service**: Automated paper trading execution
- **Configuration Manager**: Centralized configuration management
- **Performance Monitor**: System performance monitoring

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure settings:
   ```bash
   cp settings.example.py settings.py
   # Edit settings.py with your configuration
   ```

3. Deploy services:
   ```bash
   python scripts/service_manager.py deploy
   python scripts/service_manager.py start
   ```

## Usage

### Generate Predictions
```bash
python scripts/service_manager.py call prediction generate_predictions
```

### Monitor System
```bash
python scripts/service_manager.py dashboard
```

## Configuration

See `settings.py` for configuration options including:
- Stock symbols to track
- News sources and sentiment analysis
- Machine learning parameters
- Trading thresholds and limits

## Documentation

- [API Documentation](docs/api.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Configuration Guide](docs/configuration.md)

## License

This project is licensed under the MIT License.
'''

    def _generate_api_documentation(self) -> str:
        """Generate API documentation content"""
        return '''# API Documentation

## Microservices API Reference

### Base Service Endpoints

All services inherit these base endpoints:

#### Health Check
- **Endpoint**: `health`
- **Method**: Call service method
- **Response**: Service health status and metrics

#### Metrics
- **Endpoint**: `metrics`
- **Method**: Call service method
- **Response**: Performance and resource usage metrics

### Prediction Service

#### Generate Single Prediction
- **Endpoint**: `generate_single_prediction`
- **Parameters**: 
  - `symbol` (string): Stock symbol (e.g., "CBA.AX")
  - `force_refresh` (boolean, optional): Force fresh prediction
- **Response**: Prediction object with confidence, action, and details

#### Generate Multiple Predictions
- **Endpoint**: `generate_predictions`
- **Parameters**:
  - `symbols` (array, optional): Array of stock symbols
  - `force_refresh` (boolean, optional): Force fresh predictions
- **Response**: Dictionary of predictions keyed by symbol

### Market Data Service

#### Get Market Data
- **Endpoint**: `get_market_data`
- **Parameters**:
  - `symbol` (string): Stock symbol
- **Response**: Market data including technical indicators

#### Get Technical Indicators
- **Endpoint**: `get_technical_indicators`
- **Parameters**:
  - `symbol` (string): Stock symbol
- **Response**: Technical analysis indicators (RSI, MACD, Bollinger Bands)

### News Scraper Service

#### Get Latest News
- **Endpoint**: `get_latest_news`
- **Parameters**:
  - `symbol` (string, optional): Filter by stock symbol
  - `limit` (integer, optional): Number of articles to return
- **Response**: Array of news articles with sentiment analysis

### Paper Trading Service

#### Execute Paper Trade
- **Endpoint**: `execute_paper_trade`
- **Parameters**:
  - `symbol` (string): Stock symbol
  - `action` (string): "BUY" or "SELL"
  - `quantity` (integer): Number of shares
- **Response**: Trade execution result

#### Get Positions
- **Endpoint**: `get_positions`
- **Response**: Current paper trading positions

## Error Handling

All endpoints return standardized error responses:

```json
{
  "status": "error",
  "error": "Error description",
  "request_id": "unique_request_id"
}
```

## Rate Limiting

Services implement rate limiting to prevent abuse. Limits vary by service and endpoint.
'''

    def _generate_deployment_guide(self) -> str:
        """Generate deployment guide content"""
        return '''# Deployment Guide

## Prerequisites

- Ubuntu 20.04+ or compatible Linux distribution
- Python 3.8+
- Redis server
- SystemD (for service management)
- Minimum 2GB RAM, 5GB disk space

## Installation Steps

### 1. System Dependencies

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 2. Python Environment

```bash
python3 -m venv /opt/trading_venv
source /opt/trading_venv/bin/activate
pip install -r requirements.txt
```

### 3. Directory Setup

```bash
sudo mkdir -p /var/log/trading /tmp/trading_sockets /opt/trading_services
sudo chown $USER:$USER /var/log/trading /tmp/trading_sockets /opt/trading_services
```

### 4. Configuration

1. Copy settings template:
   ```bash
   cp settings.example.py settings.py
   ```

2. Edit configuration:
   ```bash
   nano settings.py
   ```

3. Configure API keys and database paths

### 5. Service Deployment

```bash
# Deploy systemd service files
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable trading-*.service
sudo systemctl start trading-*.service
```

### 6. Verification

```bash
# Check service status
python scripts/service_manager.py status

# Run health checks
python scripts/service_manager.py health

# Monitor services
python scripts/service_manager.py dashboard
```

## Service Management

### Start All Services
```bash
python scripts/service_manager.py start
```

### Stop All Services
```bash
python scripts/service_manager.py stop
```

### Restart Services
```bash
python scripts/service_manager.py restart
```

### View Logs
```bash
python scripts/service_manager.py logs --service trading-prediction --follow
```

## Troubleshooting

### Services Won't Start
1. Check dependencies are installed
2. Verify Redis is running
3. Check file permissions
4. Review service logs

### High Memory Usage
1. Monitor with `python scripts/service_manager.py dashboard`
2. Adjust service resource limits in systemd files
3. Consider scaling to multiple servers

### Database Issues
1. Verify database files exist and are writable
2. Check disk space
3. Validate database schema

## Security Considerations

- Run services as non-root user
- Restrict file permissions (644 for configs, 755 for executables)
- Use firewall to limit network access
- Regularly update dependencies
- Monitor logs for suspicious activity

## Backup and Recovery

### Automated Backups
```bash
# Daily backup cron job
0 2 * * * /opt/trading_venv/bin/python /opt/trading_services/scripts/backup.py
```

### Manual Backup
```bash
python scripts/backup_manager.py create_backup
```

### Recovery
```bash
python scripts/backup_manager.py restore_backup <backup_id>
```

## Monitoring

### System Monitoring
- Service health dashboard
- Performance metrics
- Resource usage alerts
- Error rate monitoring

### Log Aggregation
- Centralized logging in `/var/log/trading/`
- JSON structured logs
- Log rotation and archival

## Scaling

### Horizontal Scaling
- Deploy services on multiple servers
- Use Redis cluster for shared state
- Load balance service calls

### Vertical Scaling
- Increase server resources
- Adjust service resource limits
- Optimize database performance
'''

    async def update_readme(self, sections: List[str] = None):
        """Update README.md with current information"""
        if not sections:
            sections = ["overview", "installation", "usage", "services"]

        readme_path = "README.md"
        updated_sections = []

        try:
            # Read existing README or create new one
            if os.path.exists(readme_path):
                with open(readme_path, 'r') as f:
                    existing_content = f.read()
            else:
                existing_content = ""

            # Update specified sections
            new_content = existing_content
            
            for section in sections:
                if section == "services":
                    # Update services section with current service list
                    services_section = self._generate_services_section()
                    new_content = self._update_readme_section(new_content, "Services", services_section)
                    updated_sections.append("Services")

            # Write updated README
            with open(readme_path, 'w') as f:
                f.write(new_content)

            return {
                "updated_sections": updated_sections,
                "file_path": readme_path,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Error updating README: {e}"}

    def _generate_services_section(self) -> str:
        """Generate services section for README"""
        return '''
## Services

### Core Services
- **news-scraper**: RSS news collection and sentiment analysis for Australian financial sources
- **market-data**: Real-time market data collection with technical indicators (RSI, MACD, Bollinger Bands)
- **ml-model**: Machine learning model management with bank-specific model loading
- **prediction**: Comprehensive stock prediction generation using ML and technical analysis

### Supporting Services
- **scheduler**: Market-aware task scheduling and cron job management
- **paper-trading**: Automated paper trading execution with IG Markets integration
- **config-manager**: Centralized configuration management and validation
- **performance**: System performance monitoring and optimization
- **integration-test**: Comprehensive service testing and validation
- **deployment-validator**: Production readiness and deployment validation

### Service Communication
- Unix socket-based inter-service communication
- Redis pub/sub for event messaging
- Structured JSON logging
- Health checks and metrics endpoints
'''

    def _update_readme_section(self, content: str, section_name: str, new_section_content: str) -> str:
        """Update a specific section in README content"""
        # Simple implementation - could be enhanced with proper markdown parsing
        section_pattern = f"## {section_name}"
        
        if section_pattern in content:
            # Find the section and replace it
            lines = content.split('\n')
            start_index = -1
            end_index = len(lines)
            
            for i, line in enumerate(lines):
                if line.strip() == section_pattern:
                    start_index = i
                elif start_index != -1 and line.startswith('## ') and i > start_index:
                    end_index = i
                    break
            
            if start_index != -1:
                new_lines = lines[:start_index] + [section_pattern] + new_section_content.strip().split('\n') + lines[end_index:]
                return '\n'.join(new_lines)
        
        # If section doesn't exist, append it
        return content + f"\n{section_pattern}\n{new_section_content}\n"

    async def health_check(self):
        """Enhanced health check with documentation status"""
        base_health = await super().health_check()
        
        documentation_health = {
            **base_health,
            "documentation_checks": len(self.documentation_checks),
            "code_documentation_cache": len(self.code_documentation_cache),
            "last_verification": "available" if self.documentation_checks else "none"
        }

        return documentation_health

async def main():
    service = DocumentationVerificationService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
