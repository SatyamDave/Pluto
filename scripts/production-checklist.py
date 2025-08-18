#!/usr/bin/env python3
"""
Production Checklist Script
Verifies that the AI Market Terminal is ready for beta deployment
"""

import subprocess
import sys
import os
import requests
import json
from datetime import datetime

class ProductionChecklist:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.issues = []
        
    def log_success(self, message):
        print(f"✅ {message}")
        self.checks_passed += 1
        
    def log_failure(self, message, details=""):
        print(f"❌ {message}")
        if details:
            print(f"   Details: {details}")
        self.checks_failed += 1
        self.issues.append(message)
        
    def log_warning(self, message):
        print(f"⚠️  {message}")
        
    def run_command(self, command, capture_output=True):
        """Run a shell command and return result"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def check_python_tests(self):
        """Check Python tests pass"""
        print("\n🔍 Checking Python tests...")
        
        # Check API tests
        success, stdout, stderr = self.run_command("cd apps/api && python -m pytest tests/ -v")
        if success:
            self.log_success("API tests passed")
        else:
            self.log_failure("API tests failed", stderr)
        
        # Check CLI tests
        success, stdout, stderr = self.run_command("cd apps/cli && python -m pytest tests/ -v")
        if success:
            self.log_success("CLI tests passed")
        else:
            self.log_failure("CLI tests failed", stderr)
    
    def check_web_tests(self):
        """Check web application tests"""
        print("\n🔍 Checking web application tests...")
        
        success, stdout, stderr = self.run_command("cd apps/web && npm test -- --watchAll=false")
        if success:
            self.log_success("Web tests passed")
        else:
            self.log_failure("Web tests failed", stderr)
    
    def check_code_quality(self):
        """Check code quality tools"""
        print("\n🔍 Checking code quality...")
        
        # Check Python linting
        success, stdout, stderr = self.run_command("cd apps/api && black --check .")
        if success:
            self.log_success("Python code formatting (Black) passed")
        else:
            self.log_failure("Python code formatting (Black) failed", stderr)
        
        success, stdout, stderr = self.run_command("cd apps/api && flake8 .")
        if success:
            self.log_success("Python linting (Flake8) passed")
        else:
            self.log_failure("Python linting (Flake8) failed", stderr)
        
        # Check JavaScript linting
        success, stdout, stderr = self.run_command("cd apps/web && npm run lint")
        if success:
            self.log_success("JavaScript linting passed")
        else:
            self.log_failure("JavaScript linting failed", stderr)
    
    def check_docker_builds(self):
        """Check Docker images build successfully"""
        print("\n🔍 Checking Docker builds...")
        
        # Build API image
        success, stdout, stderr = self.run_command("docker build -t ai-market-api:test apps/api/")
        if success:
            self.log_success("API Docker image builds successfully")
        else:
            self.log_failure("API Docker image build failed", stderr)
        
        # Build web image
        success, stdout, stderr = self.run_command("docker build -t ai-market-web:test apps/web/")
        if success:
            self.log_success("Web Docker image builds successfully")
        else:
            self.log_failure("Web Docker image build failed", stderr)
    
    def check_docker_compose(self):
        """Check Docker Compose starts successfully"""
        print("\n🔍 Checking Docker Compose...")
        
        # Start services
        success, stdout, stderr = self.run_command("docker-compose -f docker-compose.prod.yml up -d")
        if success:
            self.log_success("Docker Compose started successfully")
            
            # Wait for services to be ready
            import time
            time.sleep(30)
            
            # Check API health
            try:
                response = requests.get("http://localhost:8000/health", timeout=10)
                if response.status_code == 200:
                    self.log_success("API health check passed")
                else:
                    self.log_failure("API health check failed", f"Status: {response.status_code}")
            except Exception as e:
                self.log_failure("API health check failed", str(e))
            
            # Check web application
            try:
                response = requests.get("http://localhost", timeout=10)
                if response.status_code == 200:
                    self.log_success("Web application accessible")
                else:
                    self.log_failure("Web application not accessible", f"Status: {response.status_code}")
            except Exception as e:
                self.log_failure("Web application not accessible", str(e))
            
            # Stop services
            self.run_command("docker-compose -f docker-compose.prod.yml down")
        else:
            self.log_failure("Docker Compose failed to start", stderr)
    
    def check_kubernetes_manifests(self):
        """Check Kubernetes manifests are valid"""
        print("\n🔍 Checking Kubernetes manifests...")
        
        manifests = [
            "infra/k8s/namespace.yaml",
            "infra/k8s/postgres.yaml",
            "infra/k8s/api.yaml",
            "infra/k8s/ingress.yaml"
        ]
        
        for manifest in manifests:
            if os.path.exists(manifest):
                success, stdout, stderr = self.run_command(f"kubectl apply --dry-run=client -f {manifest}")
                if success:
                    self.log_success(f"Kubernetes manifest {manifest} is valid")
                else:
                    self.log_failure(f"Kubernetes manifest {manifest} is invalid", stderr)
            else:
                self.log_failure(f"Kubernetes manifest {manifest} not found")
    
    def check_security(self):
        """Check security configurations"""
        print("\n🔍 Checking security configurations...")
        
        # Check for hardcoded secrets
        secrets_patterns = [
            "password.*=.*['\"]",
            "secret.*=.*['\"]",
            "key.*=.*['\"]",
        ]
        
        for pattern in secrets_patterns:
            success, stdout, stderr = self.run_command(f"grep -r '{pattern}' . --exclude-dir=.git --exclude-dir=node_modules")
            if not success and not stdout.strip():
                self.log_success(f"No hardcoded secrets found with pattern: {pattern}")
            else:
                self.log_warning(f"Potential hardcoded secrets found with pattern: {pattern}")
        
        # Check JWT secret
        if os.path.exists("env.example"):
            with open("env.example", "r") as f:
                content = f.read()
                if "your-secret-key-change-in-production" in content:
                    self.log_warning("JWT secret is still using default value")
                else:
                    self.log_success("JWT secret is configured")
    
    def check_documentation(self):
        """Check documentation completeness"""
        print("\n🔍 Checking documentation...")
        
        required_docs = [
            "README.md",
            "docs/BETA_GUIDE.md",
            "docs/API_DOCS.md"
        ]
        
        for doc in required_docs:
            if os.path.exists(doc):
                self.log_success(f"Documentation {doc} exists")
            else:
                self.log_failure(f"Documentation {doc} missing")
    
    def check_environment_variables(self):
        """Check environment variable configuration"""
        print("\n🔍 Checking environment variables...")
        
        if os.path.exists("env.example"):
            self.log_success("Environment variables template exists")
        else:
            self.log_failure("Environment variables template missing")
    
    def check_demo_workflows(self):
        """Check demo workflows are functional"""
        print("\n🔍 Checking demo workflows...")
        
        demos = [
            "demos/learner_demo.py",
            "demos/pro_demo.py"
        ]
        
        for demo in demos:
            if os.path.exists(demo):
                self.log_success(f"Demo workflow {demo} exists")
            else:
                self.log_failure(f"Demo workflow {demo} missing")
    
    def generate_report(self):
        """Generate production readiness report"""
        print("\n" + "="*60)
        print("📊 PRODUCTION READINESS REPORT")
        print("="*60)
        
        print(f"✅ Checks Passed: {self.checks_passed}")
        print(f"❌ Checks Failed: {self.checks_failed}")
        print(f"📊 Success Rate: {self.checks_passed/(self.checks_passed+self.checks_failed)*100:.1f}%")
        
        if self.issues:
            print("\n🚨 Issues Found:")
            for issue in self.issues:
                print(f"  - {issue}")
        
        if self.checks_failed == 0:
            print("\n🎉 PRODUCTION READY!")
            print("All checks passed. The system is ready for beta deployment.")
        else:
            print(f"\n⚠️  NOT PRODUCTION READY")
            print(f"Please fix {self.checks_failed} issues before deployment.")
        
        # Save report to file
        report = {
            "timestamp": datetime.now().isoformat(),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "success_rate": self.checks_passed/(self.checks_passed+self.checks_failed)*100,
            "issues": self.issues,
            "production_ready": self.checks_failed == 0
        }
        
        with open("production-readiness-report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: production-readiness-report.json")
        
        return self.checks_failed == 0
    
    def run_all_checks(self):
        """Run all production readiness checks"""
        print("🚀 Starting Production Readiness Checklist")
        print("="*60)
        
        self.check_python_tests()
        self.check_web_tests()
        self.check_code_quality()
        self.check_docker_builds()
        self.check_docker_compose()
        self.check_kubernetes_manifests()
        self.check_security()
        self.check_documentation()
        self.check_environment_variables()
        self.check_demo_workflows()
        
        return self.generate_report()

if __name__ == "__main__":
    checklist = ProductionChecklist()
    success = checklist.run_all_checks()
    
    if not success:
        sys.exit(1)
