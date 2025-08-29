#!/usr/bin/env python3
"""
Pluto AI Phone Assistant - Test Runner
Comprehensive testing suite for all Pluto features

Usage:
    python run_tests.py                    # Run all tests with coverage
    python run_tests.py --unit            # Run only unit tests
    python run_tests.py --integration     # Run only integration tests
    python run_tests.py --coverage        # Generate coverage report
    python run_tests.py --clean           # Clean up test artifacts
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n🔄 {description}...")
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def install_dependencies() -> bool:
    """Install testing dependencies"""
    print("📦 Installing testing dependencies...")
    
    # Check if requirements-test.txt exists
    if not Path("requirements-test.txt").exists():
        print("❌ requirements-test.txt not found")
        return False
    
    return run_command(
        "pip install -r requirements-test.txt",
        "Installing testing dependencies"
    )

def run_unit_tests() -> bool:
    """Run unit tests"""
    return run_command(
        "pytest tests/ -v --tb=short --strict-markers",
        "Running unit tests"
    )

def run_integration_tests() -> bool:
    """Run integration tests"""
    return run_command(
        "pytest tests/ -m integration -v --tb=short",
        "Running integration tests"
    )

def run_all_tests() -> bool:
    """Run all tests with coverage"""
    return run_command(
        "pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing --tb=short",
        "Running all tests with coverage"
    )

def generate_coverage_report() -> bool:
    """Generate detailed coverage report"""
    return run_command(
        "coverage html --title='Pluto AI Phone Assistant Coverage Report'",
        "Generating coverage report"
    )

def clean_test_artifacts() -> bool:
    """Clean up test artifacts"""
    print("🧹 Cleaning up test artifacts...")
    
    artifacts = [
        ".coverage",
        "htmlcov/",
        ".pytest_cache/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd"
    ]
    
    for artifact in artifacts:
        if Path(artifact).exists():
            try:
                if Path(artifact).is_dir():
                    import shutil
                    shutil.rmtree(artifact)
                else:
                    Path(artifact).unlink()
                print(f"✅ Removed {artifact}")
            except Exception as e:
                print(f"⚠️  Could not remove {artifact}: {e}")
    
    return True

def check_environment() -> bool:
    """Check if testing environment is properly set up"""
    print("🔍 Checking testing environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} available")
    except ImportError:
        print("❌ pytest not available")
        return False
    
    # Check if pytest-asyncio is available
    try:
        import pytest_asyncio
        print(f"✅ pytest-asyncio {pytest_asyncio.__version__} available")
    except ImportError:
        print("❌ pytest-asyncio not available")
        return False
    
    # Check if coverage is available
    try:
        import coverage
        print(f"✅ coverage {coverage.__version__} available")
    except ImportError:
        print("❌ coverage not available")
        return False
    
    print("✅ Testing environment ready")
    return True

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Pluto AI Phone Assistant Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--clean", action="store_true", help="Clean up test artifacts")
    parser.add_argument("--install", action="store_true", help="Install testing dependencies")
    parser.add_argument("--check", action="store_true", help="Check testing environment")
    
    args = parser.parse_args()
    
    print("🚀 Pluto AI Phone Assistant - Test Runner")
    print("=" * 50)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Testing environment not ready. Run with --install to install dependencies.")
        return 1
    
    # Handle specific commands
    if args.install:
        if not install_dependencies():
            return 1
        return 0
    
    if args.check:
        return 0
    
    if args.clean:
        clean_test_artifacts()
        return 0
    
    if args.coverage:
        if not generate_coverage_report():
            return 1
        return 0
    
    # Run tests based on arguments
    success = True
    
    if args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    else:
        # Default: run all tests with coverage
        success = run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("\n📊 Coverage report generated in htmlcov/")
        print("📋 View detailed results: open htmlcov/index.html")
        return 0
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
