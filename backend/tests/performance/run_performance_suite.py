#!/usr/bin/env python3
"""
Performance Testing Suite Runner

Orchestrates comprehensive performance testing with monitoring and reporting.
Can be run standalone or integrated into CI/CD pipelines.

Usage:
    python -m tests.performance.run_performance_suite
    python -m tests.performance.run_performance_suite --quick
    python -m tests.performance.run_performance_suite --full --report
"""

import sys
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from .monitoring import setup_performance_monitoring, cleanup_performance_monitoring, global_performance_monitor
from .benchmarks import BenchmarkSuite, PERFORMANCE_THRESHOLDS


class PerformanceTestSuite:
    """Orchestrates comprehensive performance testing"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[Dict[str, Any]] = []
        self.monitor = None
        
    def setup(self):
        """Set up performance monitoring"""
        print("Setting up performance monitoring...")
        self.monitor = setup_performance_monitoring()
        time.sleep(2)  # Allow monitoring to stabilize
        
    def teardown(self):
        """Clean up performance monitoring"""
        print("Cleaning up performance monitoring...")
        cleanup_performance_monitoring()
        
    def run_api_performance_tests(self) -> Dict[str, Any]:
        """Run API performance tests"""
        print("\n" + "="*50)
        print("RUNNING API PERFORMANCE TESTS")
        print("="*50)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            "tests/performance/test_api_performance.py",
            "-m", "performance",
            "-v" if self.verbose else "-q",
            "--tb=short"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        success = result.returncode == 0
        
        test_result = {
            'test_suite': 'API Performance',
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
        self.results.append(test_result)
        
        if success:
            print("✅ API Performance tests PASSED")
        else:
            print("❌ API Performance tests FAILED")
            if self.verbose:
                print(f"STDOUT:\n{result.stdout}")
                print(f"STDERR:\n{result.stderr}")
        
        return test_result
    
    def run_load_tests(self) -> Dict[str, Any]:
        """Run load tests"""
        print("\n" + "="*50)
        print("RUNNING LOAD TESTS")
        print("="*50)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            "tests/performance/test_load.py",
            "-m", "load",
            "-v" if self.verbose else "-q",
            "--tb=short"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        success = result.returncode == 0
        
        test_result = {
            'test_suite': 'Load Tests',
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
        self.results.append(test_result)
        
        if success:
            print("✅ Load tests PASSED")
        else:
            print("❌ Load tests FAILED")
            if self.verbose:
                print(f"STDOUT:\n{result.stdout}")
                print(f"STDERR:\n{result.stderr}")
        
        return test_result
    
    def run_quick_tests(self) -> List[Dict[str, Any]]:
        """Run quick performance tests (subset)"""
        print("\n" + "="*50)
        print("RUNNING QUICK PERFORMANCE TESTS")
        print("="*50)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            "tests/performance/",
            "-m", "performance and not slow",
            "-v" if self.verbose else "-q",
            "--tb=short",
            "-x"  # Stop on first failure for quick tests
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        success = result.returncode == 0
        
        test_result = {
            'test_suite': 'Quick Performance Tests',
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
        self.results.append(test_result)
        
        if success:
            print("✅ Quick performance tests PASSED")
        else:
            print("❌ Quick performance tests FAILED")
        
        return [test_result]
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        print("\n" + "="*50)
        print("GENERATING PERFORMANCE REPORT")
        print("="*50)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_lines = [
            "Course Generation Platform - Performance Test Report",
            "=" * 60,
            f"Generated: {timestamp}",
            f"Test Suites Run: {len(self.results)}",
            ""
        ]
        
        # Summary
        total_duration = sum(r['duration'] for r in self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        
        report_lines.extend([
            "SUMMARY:",
            f"  Total Duration: {total_duration:.2f} seconds",
            f"  Tests Passed: {passed_tests}/{len(self.results)}",
            f"  Overall Success: {'✅ PASS' if passed_tests == len(self.results) else '❌ FAIL'}",
            ""
        ])
        
        # Detailed results
        report_lines.append("DETAILED RESULTS:")
        for result in self.results:
            status = "PASS" if result['success'] else "FAIL"
            report_lines.extend([
                f"  {result['test_suite']}: {status} ({result['duration']:.2f}s)",
                f"    Return Code: {result['return_code']}"
            ])
            
            if not result['success'] and result['stderr']:
                # Include first few lines of error
                error_lines = result['stderr'].split('\n')[:3]
                for line in error_lines:
                    if line.strip():
                        report_lines.append(f"    Error: {line.strip()}")
        
        report_lines.append("")
        
        # Performance monitoring summary
        if self.monitor:
            monitoring_summary = self.monitor.get_performance_summary(hours=1)
            if monitoring_summary:
                report_lines.extend([
                    "SYSTEM PERFORMANCE SUMMARY:",
                    f"  Performance Tests: {monitoring_summary.get('performance_tests', 0)}",
                    f"  Load Tests: {monitoring_summary.get('load_tests', 0)}"
                ])
                
                if 'performance_metrics' in monitoring_summary:
                    pm = monitoring_summary['performance_metrics']
                    report_lines.extend([
                        f"  Average Response Time: {pm.get('avg_response_time', 0):.2f}ms",
                        f"  95th Percentile: {pm.get('p95_response_time', 0):.2f}ms",
                        f"  Average Error Rate: {pm.get('avg_error_rate', 0):.2%}"
                    ])
                
                if 'system_resources' in monitoring_summary:
                    sr = monitoring_summary['system_resources']
                    if 'cpu_percent' in sr:
                        report_lines.extend([
                            f"  CPU Usage: {sr['cpu_percent'].get('avg', 0):.1f}% (max: {sr['cpu_percent'].get('max', 0):.1f}%)",
                            f"  Memory Usage: {sr['memory_mb'].get('avg', 0):.1f}MB (max: {sr['memory_mb'].get('max', 0):.1f}MB)"
                        ])
        
        # Performance thresholds
        report_lines.extend([
            "",
            "PERFORMANCE THRESHOLDS:",
            f"  API Response Time (95p): <{PERFORMANCE_THRESHOLDS['api_response_time_ms']['acceptable']}ms",
            f"  Database Query Time: <{PERFORMANCE_THRESHOLDS['database_query_time_ms']['acceptable']}ms",
            f"  Memory Usage: <{PERFORMANCE_THRESHOLDS['memory_usage_mb']['acceptable']}MB",
            f"  CPU Usage: <{PERFORMANCE_THRESHOLDS['cpu_usage_percent']['acceptable']}%",
            ""
        ])
        
        # Recommendations
        failed_tests = [r for r in self.results if not r['success']]
        if failed_tests:
            report_lines.extend([
                "RECOMMENDATIONS:",
                "  • Review failed test output for specific performance issues",
                "  • Check system resource usage during test execution",
                "  • Consider scaling database connections or optimizing queries",
                "  • Monitor API endpoint response times in production",
                ""
            ])
        else:
            report_lines.extend([
                "RECOMMENDATIONS:",
                "  • All performance tests passed - system is performing well",
                "  • Continue monitoring performance in production",
                "  • Consider running load tests periodically",
                ""
            ])
        
        report = "\n".join(report_lines)
        
        # Save report to file
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_report_{timestamp_file}.txt"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"📊 Performance report saved to: {report_file}")
        
        return report
    
    def run_full_suite(self) -> bool:
        """Run complete performance test suite"""
        try:
            self.setup()
            
            print("🚀 Starting comprehensive performance testing...")
            
            # Run API performance tests
            api_result = self.run_api_performance_tests()
            
            # Run load tests
            load_result = self.run_load_tests()
            
            # Generate report
            report = self.generate_performance_report()
            print("\n" + report)
            
            # Return overall success
            return all(r['success'] for r in self.results)
            
        finally:
            self.teardown()
    
    def run_quick_suite(self) -> bool:
        """Run quick performance test suite"""
        try:
            self.setup()
            
            print("⚡ Starting quick performance tests...")
            
            # Run quick tests
            quick_results = self.run_quick_tests()
            
            # Generate report
            report = self.generate_performance_report()
            print("\n" + report)
            
            # Return overall success
            return all(r['success'] for r in self.results)
            
        finally:
            self.teardown()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run performance test suite")
    parser.add_argument('--quick', action='store_true', 
                       help='Run quick performance tests only')
    parser.add_argument('--full', action='store_true', 
                       help='Run full performance test suite')
    parser.add_argument('--report', action='store_true', 
                       help='Generate detailed performance report')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    suite = PerformanceTestSuite(verbose=args.verbose)
    
    if args.quick:
        success = suite.run_quick_suite()
    else:
        success = suite.run_full_suite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()