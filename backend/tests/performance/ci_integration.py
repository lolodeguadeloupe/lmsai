#!/usr/bin/env python3
"""
CI/CD Integration for Performance Testing

Provides integration points for continuous integration and deployment pipelines.
Supports various CI systems including GitHub Actions, GitLab CI, Jenkins, etc.
"""

import os
import sys
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .run_performance_suite import PerformanceTestSuite
from .monitoring import global_performance_monitor


class CIPerformanceIntegration:
    """CI/CD integration for performance testing"""
    
    def __init__(self, ci_system: str = "generic"):
        self.ci_system = ci_system.lower()
        self.suite = PerformanceTestSuite(verbose=True)
        self.results_dir = Path("performance_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def detect_ci_environment(self) -> str:
        """Auto-detect CI environment"""
        if os.getenv("GITHUB_ACTIONS"):
            return "github"
        elif os.getenv("GITLAB_CI"):
            return "gitlab"
        elif os.getenv("JENKINS_URL"):
            return "jenkins"
        elif os.getenv("TRAVIS"):
            return "travis"
        elif os.getenv("CIRCLECI"):
            return "circleci"
        else:
            return "generic"
    
    def should_run_performance_tests(self) -> bool:
        """Determine if performance tests should run in current CI context"""
        # Run performance tests on main branch or performance-related changes
        branch = os.getenv("GITHUB_REF_NAME") or os.getenv("CI_COMMIT_REF_NAME") or "unknown"
        
        # Always run on main/master
        if branch in ["main", "master"]:
            return True
        
        # Run if performance-related files changed
        if self._has_performance_related_changes():
            return True
        
        # Run if explicitly requested
        if os.getenv("RUN_PERFORMANCE_TESTS", "").lower() in ["true", "1", "yes"]:
            return True
        
        return False
    
    def _has_performance_related_changes(self) -> bool:
        """Check if performance-related files have changed"""
        # This would need to be implemented based on the specific CI system
        # For now, return False as a safe default
        return False
    
    def run_performance_tests_for_ci(self) -> Dict[str, Any]:
        """Run performance tests optimized for CI environment"""
        print(f"🔧 Running performance tests in {self.ci_system} CI environment")
        
        start_time = time.time()
        
        # Determine test type based on CI context
        is_quick_run = os.getenv("PERFORMANCE_QUICK_RUN", "false").lower() == "true"
        
        try:
            if is_quick_run:
                success = self.suite.run_quick_suite()
                test_type = "quick"
            else:
                success = self.suite.run_full_suite()
                test_type = "full"
            
            duration = time.time() - start_time
            
            # Generate CI-specific outputs
            ci_result = {
                "success": success,
                "test_type": test_type,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "ci_system": self.ci_system,
                "results": self.suite.results
            }
            
            # Save results for CI artifacts
            self._save_ci_results(ci_result)
            
            # Generate CI-specific outputs
            self._generate_ci_outputs(ci_result)
            
            return ci_result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "test_type": "failed",
                "duration": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "ci_system": self.ci_system
            }
            
            self._save_ci_results(error_result)
            return error_result
    
    def _save_ci_results(self, results: Dict[str, Any]):
        """Save results in CI-friendly format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON results for programmatic use
        json_file = self.results_dir / f"performance_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📊 Performance results saved to: {json_file}")
    
    def _generate_ci_outputs(self, results: Dict[str, Any]):
        """Generate CI system specific outputs"""
        if self.ci_system == "github":
            self._generate_github_outputs(results)
        elif self.ci_system == "gitlab":
            self._generate_gitlab_outputs(results)
        elif self.ci_system == "jenkins":
            self._generate_jenkins_outputs(results)
    
    def _generate_github_outputs(self, results: Dict[str, Any]):
        """Generate GitHub Actions specific outputs"""
        # Set GitHub Actions outputs
        if os.getenv("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"performance_success={str(results['success']).lower()}\n")
                f.write(f"performance_duration={results['duration']:.2f}\n")
                f.write(f"performance_test_type={results['test_type']}\n")
        
        # Generate GitHub Actions summary
        if os.getenv("GITHUB_STEP_SUMMARY"):
            self._generate_github_summary(results)
    
    def _generate_github_summary(self, results: Dict[str, Any]):
        """Generate GitHub Actions job summary"""
        summary_lines = [
            "# 📊 Performance Test Results",
            "",
            f"**Status:** {'✅ PASSED' if results['success'] else '❌ FAILED'}",
            f"**Test Type:** {results['test_type']}",
            f"**Duration:** {results['duration']:.2f} seconds",
            f"**Timestamp:** {results['timestamp']}",
            ""
        ]
        
        if "results" in results:
            summary_lines.extend([
                "## Test Suite Results",
                "| Test Suite | Status | Duration |",
                "|------------|--------|----------|"
            ])
            
            for test_result in results["results"]:
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                duration = f"{test_result['duration']:.2f}s"
                summary_lines.append(f"| {test_result['test_suite']} | {status} | {duration} |")
        
        summary_lines.extend([
            "",
            "## Performance Thresholds",
            "- API Response Time (95p): <200ms",
            "- Load Test Success Rate: >95%",
            "- Concurrent Operations: 100 simultaneous",
            ""
        ])
        
        with open(os.environ["GITHUB_STEP_SUMMARY"], "w") as f:
            f.write("\n".join(summary_lines))
    
    def _generate_gitlab_outputs(self, results: Dict[str, Any]):
        """Generate GitLab CI specific outputs"""
        # Create GitLab metrics report
        metrics = {
            "performance_success": 1 if results["success"] else 0,
            "performance_duration_seconds": results["duration"],
            "performance_test_count": len(results.get("results", []))
        }
        
        with open("performance_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
    
    def _generate_jenkins_outputs(self, results: Dict[str, Any]):
        """Generate Jenkins specific outputs"""
        # Create Jenkins properties file
        properties = [
            f"PERFORMANCE_SUCCESS={str(results['success']).lower()}",
            f"PERFORMANCE_DURATION={results['duration']:.2f}",
            f"PERFORMANCE_TEST_TYPE={results['test_type']}"
        ]
        
        with open("performance.properties", "w") as f:
            f.write("\n".join(properties))
    
    def check_performance_regression(self, baseline_file: Optional[str] = None) -> Dict[str, Any]:
        """Check for performance regression against baseline"""
        if not baseline_file or not Path(baseline_file).exists():
            return {"regression_detected": False, "message": "No baseline available for comparison"}
        
        try:
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)
            
            # Get current monitoring data
            current_summary = global_performance_monitor.get_performance_summary(hours=1)
            
            # Simple regression check (can be enhanced)
            regression_detected = False
            issues = []
            
            if "performance_metrics" in current_summary and "performance_metrics" in baseline:
                current_p95 = current_summary["performance_metrics"].get("p95_response_time", 0)
                baseline_p95 = baseline["performance_metrics"].get("p95_response_time", 0)
                
                if baseline_p95 > 0 and current_p95 > baseline_p95 * 1.2:  # 20% degradation
                    regression_detected = True
                    issues.append(f"Response time degraded: {current_p95:.2f}ms vs {baseline_p95:.2f}ms baseline")
            
            return {
                "regression_detected": regression_detected,
                "issues": issues,
                "current_summary": current_summary
            }
            
        except Exception as e:
            return {"regression_detected": False, "error": f"Failed to check regression: {e}"}


def main():
    """Main CLI entry point for CI integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CI/CD Performance Testing Integration")
    parser.add_argument("--ci-system", default="auto", help="CI system (auto, github, gitlab, jenkins)")
    parser.add_argument("--quick", action="store_true", help="Run quick performance tests")
    parser.add_argument("--check-regression", help="Check for regression against baseline file")
    parser.add_argument("--force", action="store_true", help="Force run even if conditions don't match")
    
    args = parser.parse_args()
    
    # Initialize CI integration
    ci_system = args.ci_system if args.ci_system != "auto" else None
    ci = CIPerformanceIntegration(ci_system)
    
    if ci_system is None:
        ci.ci_system = ci.detect_ci_environment()
        print(f"🔍 Detected CI environment: {ci.ci_system}")
    
    # Set quick run environment variable if specified
    if args.quick:
        os.environ["PERFORMANCE_QUICK_RUN"] = "true"
    
    # Check if we should run performance tests
    should_run = args.force or ci.should_run_performance_tests()
    
    if not should_run:
        print("⏭️  Skipping performance tests (conditions not met)")
        print("   Use --force to run anyway or set RUN_PERFORMANCE_TESTS=true")
        return
    
    # Run performance tests
    results = ci.run_performance_tests_for_ci()
    
    # Check for regression if baseline provided
    if args.check_regression:
        regression_result = ci.check_performance_regression(args.check_regression)
        if regression_result.get("regression_detected"):
            print("⚠️  Performance regression detected!")
            for issue in regression_result.get("issues", []):
                print(f"   {issue}")
            # Don't fail the build for regression, just warn
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()