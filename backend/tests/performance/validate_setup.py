#!/usr/bin/env python3
"""
Performance Testing Setup Validation

Validates that the performance testing suite is properly configured
and all dependencies are available.
"""

import sys
import importlib
from pathlib import Path


def validate_dependencies():
    """Validate required dependencies are installed"""
    required_packages = [
        'pytest',
        'pytest-asyncio',
        'httpx',
        'psutil',
        'fastapi',
        'sqlalchemy',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - MISSING")
    
    return len(missing_packages) == 0, missing_packages


def validate_test_structure():
    """Validate test file structure"""
    base_path = Path(__file__).parent
    
    required_files = [
        'test_api_performance.py',
        'test_load.py',
        'benchmarks.py',
        'monitoring.py',
        'run_performance_suite.py',
        'ci_integration.py',
        '__init__.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        file_path = base_path / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            missing_files.append(file)
            print(f"❌ {file} - MISSING")
    
    return len(missing_files) == 0, missing_files


def validate_imports():
    """Validate that all modules can be imported"""
    test_modules = [
        'tests.performance.benchmarks',
        'tests.performance.monitoring',
    ]
    
    import_errors = []
    
    for module in test_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            import_errors.append((module, str(e)))
            print(f"❌ {module} - IMPORT ERROR: {e}")
    
    return len(import_errors) == 0, import_errors


def validate_pytest_config():
    """Validate pytest configuration"""
    base_path = Path(__file__).parent.parent.parent
    pytest_ini = base_path / 'pytest.ini'
    
    if pytest_ini.exists():
        print("✅ pytest.ini exists")
        
        # Check for required markers
        content = pytest_ini.read_text()
        required_markers = ['performance', 'load', 'benchmark']
        
        missing_markers = []
        for marker in required_markers:
            if marker in content:
                print(f"✅ Marker '{marker}' configured")
            else:
                missing_markers.append(marker)
                print(f"❌ Marker '{marker}' not found in pytest.ini")
        
        return len(missing_markers) == 0, missing_markers
    else:
        print("❌ pytest.ini not found")
        return False, ['pytest.ini missing']


def run_sample_test():
    """Run a simple performance test to validate setup"""
    try:
        from .benchmarks import BenchmarkSuite
        
        suite = BenchmarkSuite()
        
        def sample_function():
            return sum(range(1000))
        
        result = suite.benchmark_function(
            sample_function,
            name="validation_test",
            iterations=10
        )
        
        if result.success and result.execution_time > 0:
            print(f"✅ Sample benchmark successful: {result.execution_time:.2f}ms")
            return True
        else:
            print(f"❌ Sample benchmark failed")
            return False
            
    except Exception as e:
        print(f"❌ Sample test failed: {e}")
        return False


def main():
    """Main validation function"""
    print("🔍 Validating Performance Testing Setup")
    print("=" * 50)
    
    all_valid = True
    
    # Validate dependencies
    print("\n📦 Checking Dependencies:")
    deps_valid, missing_deps = validate_dependencies()
    all_valid &= deps_valid
    
    # Validate file structure
    print("\n📁 Checking File Structure:")
    files_valid, missing_files = validate_test_structure()
    all_valid &= files_valid
    
    # Validate pytest configuration
    print("\n⚙️  Checking Pytest Configuration:")
    pytest_valid, pytest_issues = validate_pytest_config()
    all_valid &= pytest_valid
    
    # Validate imports (only if files exist)
    if files_valid:
        print("\n🔗 Checking Module Imports:")
        imports_valid, import_errors = validate_imports()
        all_valid &= imports_valid
        
        # Run sample test (only if imports work)
        if imports_valid:
            print("\n🧪 Running Sample Test:")
            sample_valid = run_sample_test()
            all_valid &= sample_valid
    
    # Summary
    print("\n" + "=" * 50)
    if all_valid:
        print("✅ Performance testing setup is VALID")
        print("\nYou can now run performance tests:")
        print("  pytest tests/performance/ -m performance")
        print("  python -m tests.performance.run_performance_suite --quick")
    else:
        print("❌ Performance testing setup has ISSUES")
        print("\nPlease fix the following issues:")
        
        if not deps_valid:
            print(f"\n📦 Install missing dependencies:")
            for dep in missing_deps:
                print(f"  pip install {dep}")
        
        if not files_valid:
            print(f"\n📁 Missing files:")
            for file in missing_files:
                print(f"  {file}")
        
        if not pytest_valid:
            print(f"\n⚙️  Pytest configuration issues:")
            for issue in pytest_issues:
                print(f"  {issue}")
    
    return all_valid


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)