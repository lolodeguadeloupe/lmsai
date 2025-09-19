#!/usr/bin/env python3
"""
Performance test runner script with comprehensive reporting.
"""
import os
import sys
import argparse
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def run_command(command, description=""):
    """Run a shell command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description or command}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"Command failed with return code: {result.returncode}")
            return False
        
        print("Command completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print("Command timed out after 30 minutes")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def create_performance_report(test_results_dir):
    """Create an HTML performance report."""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Performance Test Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
            .section { margin: 20px 0; }
            .metric { display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .pass { background-color: #d4edda; }
            .fail { background-color: #f8d7da; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Performance Test Report</h1>
            <p>Generated: {timestamp}</p>
            <p>Test Environment: {environment}</p>
        </div>
        
        <div class="section">
            <h2>Test Summary</h2>
            <div class="metric pass">
                <strong>Tests Passed:</strong> {tests_passed}
            </div>
            <div class="metric {'pass' if tests_failed == 0 else 'fail'}">
                <strong>Tests Failed:</strong> {tests_failed}
            </div>
            <div class="metric">
                <strong>Total Duration:</strong> {total_duration}
            </div>
        </div>
        
        <div class="section">
            <h2>Performance Metrics</h2>
            <table>
                <tr>
                    <th>Test</th>
                    <th>P95 Response Time (ms)</th>
                    <th>Throughput (req/s)</th>
                    <th>Success Rate</th>
                    <th>Status</th>
                </tr>
                {metrics_rows}
            </table>
        </div>
        
        <div class="section">
            <h2>Detailed Results</h2>
            <pre>{detailed_results}</pre>
        </div>
    </body>
    </html>
    """
    
    # This is a placeholder - in a real implementation, you'd parse the actual test results
    return html_template.format(
        timestamp=datetime.now().isoformat(),
        environment="Test Environment",
        tests_passed="N/A",
        tests_failed="N/A", 
        total_duration="N/A",
        metrics_rows="<tr><td colspan='5'>Results will be populated after test execution</td></tr>",
        detailed_results="Detailed results will be available after test execution"
    )

def main():
    """Main performance test runner."""
    parser = argparse.ArgumentParser(description="Run performance tests for the course generation platform")
    parser.add_argument("--suite", choices=["api", "load", "all"], default="all", 
                       help="Test suite to run")
    parser.add_argument("--duration", type=int, default=60,
                       help="Test duration in seconds for load tests")
    parser.add_argument("--concurrent-users", type=int, default=100,
                       help="Number of concurrent users for load tests")
    parser.add_argument("--report-dir", default="performance_reports",
                       help="Directory to save performance reports")
    parser.add_argument("--skip-setup", action="store_true",
                       help="Skip database setup")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Create report directory
    report_dir = Path(args.report_dir)
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("="*80)
    print("COURSE GENERATION PLATFORM - PERFORMANCE TESTING")
    print("="*80)
    print(f"Test Suite: {args.suite}")
    print(f"Duration: {args.duration} seconds")
    print(f"Concurrent Users: {args.concurrent_users}")
    print(f"Report Directory: {report_dir}")
    print("="*80)
    
    # Set environment variables for test configuration
    os.environ["PERFORMANCE_TEST_DURATION"] = str(args.duration)
    os.environ["PERFORMANCE_CONCURRENT_USERS"] = str(args.concurrent_users)
    
    success = True
    
    # Database setup (if not skipped)
    if not args.skip_setup:
        print("\n🔧 Setting up test database...")
        if not run_command("python -m alembic upgrade head", "Database migration"):
            print("❌ Database setup failed!")
            return 1
    
    # Run performance tests based on suite selection
    if args.suite in ["api", "all"]:
        print("\n🚀 Running API performance tests...")
        cmd = f"pytest tests/performance/test_api_performance.py -v --tb=short"
        if args.verbose:
            cmd += " -s"
        if not run_command(cmd, "API Performance Tests"):
            print("❌ API performance tests failed!")
            success = False
    
    if args.suite in ["load", "all"]:
        print("\n📈 Running load tests...")
        cmd = f"pytest tests/performance/test_load.py -v --tb=short"
        if args.verbose:
            cmd += " -s"
        if not run_command(cmd, "Load Tests"):
            print("❌ Load tests failed!")
            success = False
    
    # Generate benchmark report if pytest-benchmark was used
    print("\n📊 Generating performance reports...")
    
    # Create HTML report
    html_report = create_performance_report(report_dir)
    html_report_path = report_dir / f"performance_report_{timestamp}.html"
    
    with open(html_report_path, 'w') as f:
        f.write(html_report)
    
    print(f"📄 HTML report saved to: {html_report_path}")
    
    # Summary
    print("\n" + "="*80)
    if success:
        print("✅ All performance tests completed successfully!")
        print(f"📊 View detailed report: {html_report_path}")
        return 0
    else:
        print("❌ Some performance tests failed!")
        print(f"📊 Check detailed report: {html_report_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main())