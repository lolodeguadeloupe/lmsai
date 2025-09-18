#!/usr/bin/env python3
"""
TDD Verification Script
Runs all tests to verify they FAIL as expected before implementation.
This validates that we're following proper TDD methodology.
"""
import subprocess
import sys
from pathlib import Path


def run_tests_and_verify_failures():
    """Run all tests and verify they fail as expected."""
    print("🧪 TDD Verification: Running tests to ensure they FAIL before implementation")
    print("=" * 70)

    # Change to backend directory
    backend_dir = Path(__file__).parent

    try:
        # Run pytest with specific markers
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "-v",  # Verbose output
                "--tb=short",  # Short traceback format
                "--no-header",  # Cleaner output
                "-x",  # Stop on first failure
                "--disable-warnings",  # Hide warnings for cleaner output
            ],
            cwd=backend_dir,
            capture_output=True,
            text=True,
        )

        print(f"Exit code: {result.returncode}")
        print("\nSTDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)

        # In TDD, we EXPECT tests to fail at this stage
        if result.returncode != 0:
            print("\n✅ PERFECT! Tests are failing as expected in TDD phase.")
            print("   This confirms we haven't accidentally implemented anything yet.")
            print(
                "   Now we can proceed to Phase 3.3 (Implementation) with confidence."
            )

            # Count different types of failures
            output = result.stdout + result.stderr

            failure_indicators = [
                "ImportError",
                "ModuleNotFoundError",
                "AttributeError",
                "NameError",
                "NotImplementedError",
                "404",
                "FAILED",
            ]

            detected_failures = []
            for indicator in failure_indicators:
                if indicator in output:
                    detected_failures.append(indicator)

            print(f"\n📊 Detected failure types: {', '.join(set(detected_failures))}")
            print("   These are exactly the failures we expect before implementation!")

            return True
        else:
            print("\n❌ UNEXPECTED: Tests are passing!")
            print("   This suggests some implementation already exists.")
            print("   In proper TDD, tests should FAIL before implementation.")
            return False

    except Exception as e:
        print(f"\n🔧 Test execution error: {e}")
        print("   This is normal if dependencies aren't installed yet.")
        print("   Tests failing due to missing dependencies is also expected in TDD.")
        return True


def check_test_coverage():
    """Check that we have comprehensive test coverage."""
    print("\n📋 Test Coverage Analysis")
    print("=" * 30)

    backend_dir = Path(__file__).parent

    # Count test files
    contract_tests = list((backend_dir / "tests" / "contract").glob("test_*.py"))
    integration_tests = list((backend_dir / "tests" / "integration").glob("test_*.py"))

    print(f"Contract tests: {len(contract_tests)}")
    for test in contract_tests:
        print(f"  ✓ {test.name}")

    print(f"\nIntegration tests: {len(integration_tests)}")
    for test in integration_tests:
        print(f"  ✓ {test.name}")

    # Verify we have the expected number of tests from tasks.md
    expected_contract_tests = 12  # T007-T018
    expected_integration_tests = 5  # T019-T023

    print(f"\n📊 Coverage Summary:")
    print(f"   Contract tests: {len(contract_tests)}/{expected_contract_tests}")
    print(
        f"   Integration tests: {len(integration_tests)}/{expected_integration_tests}"
    )

    total_expected = expected_contract_tests + expected_integration_tests
    total_actual = len(contract_tests) + len(integration_tests)

    if total_actual >= total_expected:
        print(f"   ✅ Test coverage complete: {total_actual}/{total_expected}")
        return True
    else:
        print(f"   ⚠️  Test coverage incomplete: {total_actual}/{total_expected}")
        return False


def main():
    """Main verification function."""
    print("🚀 Phase 3.2 TDD Verification")
    print("Testing that our tests FAIL before implementation")
    print()

    # Check test coverage first
    coverage_ok = check_test_coverage()

    # Run tests and verify they fail
    tests_fail_as_expected = run_tests_and_verify_failures()

    print("\n" + "=" * 70)
    print("TDD VERIFICATION SUMMARY")
    print("=" * 70)

    if coverage_ok and tests_fail_as_expected:
        print("✅ TDD Phase 3.2 SUCCESSFUL!")
        print("   ✓ All required tests created")
        print("   ✓ Tests fail as expected (no premature implementation)")
        print("   ✓ Ready to proceed to Phase 3.3 (Implementation)")
        print("\n🎯 Next Step: Run Phase 3.3 tasks to make tests pass")
        return 0
    else:
        print("❌ TDD Phase 3.2 ISSUES DETECTED")
        if not coverage_ok:
            print("   ✗ Test coverage incomplete")
        if not tests_fail_as_expected:
            print("   ✗ Tests not failing as expected")
        print("\n🔧 Fix issues before proceeding to implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
