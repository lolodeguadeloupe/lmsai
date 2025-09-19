"""
Performance Monitoring and Metrics Collection

Provides real-time monitoring, metrics collection, and analysis tools
for tracking performance across the course generation platform.
"""
import time
import threading
import statistics
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import psutil
import os
import json
from collections import defaultdict, deque
import asyncio
from contextlib import contextmanager


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    response_times: List[float]
    errors: List[Dict[str, Any]]
    endpoint: str
    method: str
    iterations: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def average(self) -> float:
        """Average response time in milliseconds"""
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def median(self) -> float:
        """Median response time in milliseconds"""
        return statistics.median(self.response_times) if self.response_times else 0
    
    @property
    def percentile_95(self) -> float:
        """95th percentile response time"""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    @property
    def percentile_99(self) -> float:
        """99th percentile response time"""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    @property
    def error_rate(self) -> float:
        """Error rate as percentage"""
        return len(self.errors) / self.iterations if self.iterations > 0 else 0
    
    @property
    def min_time(self) -> float:
        """Minimum response time"""
        return min(self.response_times) if self.response_times else 0
    
    @property
    def max_time(self) -> float:
        """Maximum response time"""
        return max(self.response_times) if self.response_times else 0
    
    @property
    def std_dev(self) -> float:
        """Standard deviation of response times"""
        return statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0


@dataclass
class LoadTestResults:
    """Container for load test results"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float  # milliseconds
    results: List[Dict[str, Any]]
    max_concurrent: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        return self.successful_requests / self.total_requests if self.total_requests > 0 else 0
    
    @property
    def requests_per_second(self) -> float:
        """Requests per second throughput"""
        return (self.total_requests / self.total_time * 1000) if self.total_time > 0 else 0
    
    @property
    def average_response_time(self) -> float:
        """Average response time across all requests"""
        response_times = [r['response_time'] for r in self.results if 'response_time' in r]
        return statistics.mean(response_times) if response_times else 0
    
    @property
    def percentile_95_response_time(self) -> float:
        """95th percentile response time"""
        response_times = [r['response_time'] for r in self.results if 'response_time' in r]
        if not response_times:
            return 0
        sorted_times = sorted(response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]


@dataclass
class SystemResourceMetrics:
    """System resource usage metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    open_files: int
    threads: int


class RealTimeMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self, collection_interval: float = 1.0, max_history: int = 1000):
        self.collection_interval = collection_interval
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.process = psutil.Process(os.getpid())
        self._stop_event = threading.Event()
        
    def start_monitoring(self):
        """Start real-time monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self._stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self._stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while not self._stop_event.is_set():
            try:
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
            except Exception as e:
                print(f"Error collecting metrics: {e}")
            
            self._stop_event.wait(self.collection_interval)
    
    def _collect_system_metrics(self) -> SystemResourceMetrics:
        """Collect current system metrics"""
        try:
            # CPU and memory
            cpu_percent = self.process.cpu_percent(interval=None)
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # IO counters
            io_counters = self.process.io_counters()
            
            # Network (system-wide)
            try:
                net_io = psutil.net_io_counters()
                network_sent = net_io.bytes_sent / 1024 / 1024  # MB
                network_recv = net_io.bytes_recv / 1024 / 1024  # MB
            except:
                network_sent = network_recv = 0
            
            # Connections and files
            try:
                connections = len(self.process.connections())
            except:
                connections = 0
            
            try:
                open_files = self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
            except:
                open_files = 0
            
            return SystemResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_mb=memory_info.rss / 1024 / 1024,
                memory_percent=memory_percent,
                disk_io_read_mb=io_counters.read_bytes / 1024 / 1024,
                disk_io_write_mb=io_counters.write_bytes / 1024 / 1024,
                network_sent_mb=network_sent,
                network_recv_mb=network_recv,
                active_connections=connections,
                open_files=open_files,
                threads=self.process.num_threads()
            )
        except Exception as e:
            # Return default metrics if collection fails
            return SystemResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0, memory_mb=0, memory_percent=0,
                disk_io_read_mb=0, disk_io_write_mb=0,
                network_sent_mb=0, network_recv_mb=0,
                active_connections=0, open_files=0, threads=0
            )
    
    def get_current_metrics(self) -> Optional[SystemResourceMetrics]:
        """Get the most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Get summarized metrics for the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(recent_metrics),
            'cpu_percent': {
                'avg': statistics.mean([m.cpu_percent for m in recent_metrics]),
                'max': max([m.cpu_percent for m in recent_metrics]),
                'min': min([m.cpu_percent for m in recent_metrics])
            },
            'memory_mb': {
                'avg': statistics.mean([m.memory_mb for m in recent_metrics]),
                'max': max([m.memory_mb for m in recent_metrics]),
                'min': min([m.memory_mb for m in recent_metrics])
            },
            'active_connections': {
                'avg': statistics.mean([m.active_connections for m in recent_metrics]),
                'max': max([m.active_connections for m in recent_metrics]),
                'min': min([m.active_connections for m in recent_metrics])
            },
            'threads': {
                'avg': statistics.mean([m.threads for m in recent_metrics]),
                'max': max([m.threads for m in recent_metrics]),
                'min': min([m.threads for m in recent_metrics])
            }
        }


class PerformanceMonitor:
    """Advanced performance monitoring with alerting"""
    
    def __init__(self):
        self.real_time_monitor = RealTimeMonitor()
        self.performance_history: List[PerformanceMetrics] = []
        self.load_test_history: List[LoadTestResults] = []
        self.alert_thresholds = {
            'response_time_95p': 200,  # ms
            'error_rate': 0.05,  # 5%
            'cpu_percent': 80,
            'memory_mb': 1000,
            'success_rate': 0.95
        }
        self.alert_callbacks: List[Callable] = []
    
    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add callback for performance alerts"""
        self.alert_callbacks.append(callback)
    
    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger performance alert"""
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, data)
            except Exception as e:
                print(f"Error in alert callback: {e}")
    
    def record_performance_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics and check for alerts"""
        self.performance_history.append(metrics)
        
        # Check for performance alerts
        if metrics.percentile_95 > self.alert_thresholds['response_time_95p']:
            self._trigger_alert('high_response_time', {
                'endpoint': metrics.endpoint,
                'method': metrics.method,
                'percentile_95': metrics.percentile_95,
                'threshold': self.alert_thresholds['response_time_95p']
            })
        
        if metrics.error_rate > self.alert_thresholds['error_rate']:
            self._trigger_alert('high_error_rate', {
                'endpoint': metrics.endpoint,
                'method': metrics.method,
                'error_rate': metrics.error_rate,
                'threshold': self.alert_thresholds['error_rate']
            })
    
    def record_load_test_results(self, results: LoadTestResults):
        """Record load test results and check for alerts"""
        self.load_test_history.append(results)
        
        # Check for load test alerts
        if results.success_rate < self.alert_thresholds['success_rate']:
            self._trigger_alert('low_success_rate', {
                'success_rate': results.success_rate,
                'threshold': self.alert_thresholds['success_rate'],
                'total_requests': results.total_requests,
                'failed_requests': results.failed_requests
            })
    
    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager for monitoring operations"""
        start_time = time.perf_counter()
        initial_metrics = self.real_time_monitor._collect_system_metrics()
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            final_metrics = self.real_time_monitor._collect_system_metrics()
            
            execution_time = (end_time - start_time) * 1000  # ms
            memory_delta = final_metrics.memory_mb - initial_metrics.memory_mb
            
            # Log operation performance
            print(f"Operation '{operation_name}' completed:")
            print(f"  Execution time: {execution_time:.2f}ms")
            print(f"  Memory delta: {memory_delta:.2f}MB")
            print(f"  CPU usage: {final_metrics.cpu_percent:.1f}%")
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        self.real_time_monitor.start_monitoring()
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.real_time_monitor.stop_monitoring()
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent performance metrics
        recent_performance = [m for m in self.performance_history if m.timestamp >= cutoff_time]
        recent_load_tests = [lt for lt in self.load_test_history if lt.timestamp >= cutoff_time]
        
        summary = {
            'time_period_hours': hours,
            'performance_tests': len(recent_performance),
            'load_tests': len(recent_load_tests)
        }
        
        if recent_performance:
            all_response_times = []
            all_error_rates = []
            
            for metrics in recent_performance:
                all_response_times.extend(metrics.response_times)
                all_error_rates.append(metrics.error_rate)
            
            summary['performance_metrics'] = {
                'avg_response_time': statistics.mean(all_response_times) if all_response_times else 0,
                'p95_response_time': (
                    statistics.quantiles(all_response_times, n=20)[18] 
                    if len(all_response_times) > 20 else 0
                ),
                'avg_error_rate': statistics.mean(all_error_rates) if all_error_rates else 0,
                'total_requests': sum(m.iterations for m in recent_performance)
            }
        
        if recent_load_tests:
            summary['load_test_metrics'] = {
                'avg_success_rate': statistics.mean([lt.success_rate for lt in recent_load_tests]),
                'avg_rps': statistics.mean([lt.requests_per_second for lt in recent_load_tests]),
                'total_load_requests': sum(lt.total_requests for lt in recent_load_tests)
            }
        
        # Add system resource summary
        system_summary = self.real_time_monitor.get_metrics_summary(duration_minutes=hours * 60)
        if system_summary:
            summary['system_resources'] = system_summary
        
        return summary
    
    def export_metrics(self, filename: str = None) -> str:
        """Export all metrics to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        # Prepare data for export
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'performance_tests': [],
            'load_tests': [],
            'system_metrics': []
        }
        
        # Export performance metrics
        for metrics in self.performance_history:
            export_data['performance_tests'].append({
                'endpoint': metrics.endpoint,
                'method': metrics.method,
                'timestamp': metrics.timestamp.isoformat(),
                'iterations': metrics.iterations,
                'average': metrics.average,
                'percentile_95': metrics.percentile_95,
                'error_rate': metrics.error_rate,
                'response_times': metrics.response_times[:100]  # Limit data size
            })
        
        # Export load test results
        for results in self.load_test_history:
            export_data['load_tests'].append({
                'timestamp': results.timestamp.isoformat(),
                'total_requests': results.total_requests,
                'success_rate': results.success_rate,
                'requests_per_second': results.requests_per_second,
                'average_response_time': results.average_response_time,
                'max_concurrent': results.max_concurrent
            })
        
        # Export system metrics (recent only)
        recent_system_metrics = list(self.real_time_monitor.metrics_history)[-100:]
        for metrics in recent_system_metrics:
            export_data['system_metrics'].append({
                'timestamp': metrics.timestamp.isoformat(),
                'cpu_percent': metrics.cpu_percent,
                'memory_mb': metrics.memory_mb,
                'active_connections': metrics.active_connections,
                'threads': metrics.threads
            })
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return filename


class LoadTestMonitor:
    """Specialized monitoring for load tests"""
    
    def __init__(self):
        self.active_requests = 0
        self.request_lock = threading.Lock()
        self.request_times: deque = deque(maxlen=1000)
        self.error_count = 0
        
    def request_started(self):
        """Mark a request as started"""
        with self.request_lock:
            self.active_requests += 1
    
    def request_completed(self, response_time: float, success: bool):
        """Mark a request as completed"""
        with self.request_lock:
            self.active_requests = max(0, self.active_requests - 1)
            self.request_times.append(response_time)
            if not success:
                self.error_count += 1
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current load test statistics"""
        with self.request_lock:
            recent_times = list(self.request_times)
            
            return {
                'active_requests': self.active_requests,
                'completed_requests': len(recent_times),
                'error_count': self.error_count,
                'avg_response_time': statistics.mean(recent_times) if recent_times else 0,
                'error_rate': self.error_count / len(recent_times) if recent_times else 0
            }


# Global performance monitor instance
global_performance_monitor = PerformanceMonitor()


def setup_performance_monitoring():
    """Set up performance monitoring with default configuration"""
    global_performance_monitor.start_monitoring()
    
    # Add default alert handler
    def default_alert_handler(alert_type: str, data: Dict[str, Any]):
        print(f"PERFORMANCE ALERT [{alert_type}]: {data}")
    
    global_performance_monitor.add_alert_callback(default_alert_handler)
    
    return global_performance_monitor


def cleanup_performance_monitoring():
    """Clean up performance monitoring"""
    global_performance_monitor.stop_monitoring()


# Context manager for easy performance monitoring
@contextmanager
def monitor_performance(operation_name: str):
    """Context manager for monitoring performance of operations"""
    monitor = global_performance_monitor
    with monitor.monitor_operation(operation_name):
        yield monitor