"""Performance metrics collection and reporting."""
import time
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from enum import Enum


class MetricType(Enum):
    """Types of metrics to track."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    LATENCY_P95 = "latency_p95"
    LATENCY_P99 = "latency_p99"


@dataclass
class PerformanceMetric:
    """Single performance metric."""
    name: str
    value: float
    unit: str
    timestamp: float
    context: Optional[Dict] = None


@dataclass
class PerformanceReport:
    """Complete performance test report."""
    test_name: str
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    metrics: List[PerformanceMetric]


class MetricsCollector:
    """Collects and analyzes performance metrics."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = None
        self.end_time = None
        self.metrics: List[Dict] = []
        self.response_times: List[float] = []
        self.errors: List[str] = []

    def start(self):
        """Start timing."""
        self.start_time = time.time()

    def stop(self):
        """Stop timing."""
        self.end_time = time.time()

    def record_response(self, response_time_ms: float, success: bool, error: Optional[str] = None):
        """Record a response."""
        self.response_times.append(response_time_ms)
        if not success and error:
            self.errors.append(error)

    def record_metric(self, name: str, value: float, unit: str = "", context: Optional[Dict] = None):
        """Record a custom metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=time.time(),
            context=context or {}
        )
        self.metrics.append(asdict(metric))

    def get_duration(self) -> float:
        """Get test duration in seconds."""
        if not self.start_time or not self.end_time:
            return 0
        return self.end_time - self.start_time

    def get_throughput(self) -> float:
        """Get requests per second."""
        duration = self.get_duration()
        if duration == 0:
            return 0
        return len(self.response_times) / duration

    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        if not self.response_times:
            return 0
        successful = len(self.response_times) - len(self.errors)
        return (successful / len(self.response_times)) * 100

    def get_error_rate(self) -> float:
        """Get error rate percentage."""
        return 100 - self.get_success_rate()

    def get_avg_response_time(self) -> float:
        """Get average response time in ms."""
        if not self.response_times:
            return 0
        return sum(self.response_times) / len(self.response_times)

    def get_min_response_time(self) -> float:
        """Get minimum response time."""
        return min(self.response_times) if self.response_times else 0

    def get_max_response_time(self) -> float:
        """Get maximum response time."""
        return max(self.response_times) if self.response_times else 0

    def get_percentile(self, p: int) -> float:
        """Get response time percentile."""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int((p / 100) * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]

    def get_report(self) -> PerformanceReport:
        """Generate performance report."""
        total = len(self.response_times)
        successful = total - len(self.errors)
        failed = len(self.errors)

        metrics = [
            PerformanceMetric(
                name="Average Response Time",
                value=self.get_avg_response_time(),
                unit="ms",
                timestamp=time.time(),
            ),
            PerformanceMetric(
                name="Min Response Time",
                value=self.get_min_response_time(),
                unit="ms",
                timestamp=time.time(),
            ),
            PerformanceMetric(
                name="Max Response Time",
                value=self.get_max_response_time(),
                unit="ms",
                timestamp=time.time(),
            ),
            PerformanceMetric(
                name="P95 Latency",
                value=self.get_percentile(95),
                unit="ms",
                timestamp=time.time(),
            ),
            PerformanceMetric(
                name="P99 Latency",
                value=self.get_percentile(99),
                unit="ms",
                timestamp=time.time(),
            ),
            PerformanceMetric(
                name="Throughput",
                value=self.get_throughput(),
                unit="requests/sec",
                timestamp=time.time(),
            ),
            PerformanceMetric(
                name="Success Rate",
                value=self.get_success_rate(),
                unit="%",
                timestamp=time.time(),
            ),
            PerformanceMetric(
                name="Error Rate",
                value=self.get_error_rate(),
                unit="%",
                timestamp=time.time(),
            ),
        ]

        return PerformanceReport(
            test_name=self.test_name,
            duration_seconds=self.get_duration(),
            total_requests=total,
            successful_requests=successful,
            failed_requests=failed,
            metrics=metrics,
        )

    def print_report(self):
        """Print formatted performance report."""
        report = self.get_report()

        print("\n" + "="*70)
        print(f"Performance Report: {report.test_name}")
        print("="*70)
        print(f"Duration:           {report.duration_seconds:.1f}s")
        print(f"Total Requests:     {report.total_requests}")
        print(f"Successful:         {report.successful_requests} ({report.successful_requests/max(report.total_requests,1)*100:.1f}%)")
        print(f"Failed:             {report.failed_requests} ({report.failed_requests/max(report.total_requests,1)*100:.1f}%)")
        print("-"*70)
        for metric in report.metrics:
            print(f"{metric.name:.<45} {metric.value:>10.2f} {metric.unit}")
        print("="*70 + "\n")

    def export_json(self, filepath: str):
        """Export report to JSON file."""
        report = self.get_report()
        data = {
            "test_name": report.test_name,
            "duration_seconds": report.duration_seconds,
            "total_requests": report.total_requests,
            "successful_requests": report.successful_requests,
            "failed_requests": report.failed_requests,
            "metrics": [asdict(m) for m in report.metrics],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✓ Report exported to {filepath}")


class PerformanceBenchmark:
    """Benchmark specification."""

    def __init__(self, name: str):
        self.name = name
        self.thresholds: Dict[str, tuple] = {}

    def add_threshold(self, metric: str, min_value: float = None, max_value: float = None):
        """Add performance threshold.
        
        Args:
            metric: Metric name
            min_value: Minimum acceptable value (lower is better)
            max_value: Maximum acceptable value (upper limit)
        """
        self.thresholds[metric] = (min_value, max_value)

    def check(self, report: PerformanceReport) -> tuple[bool, List[str]]:
        """Check if report meets benchmarks.
        
        Returns:
            (passed, failures) - Boolean and list of failure messages
        """
        failures = []

        for metric in report.metrics:
            if metric.name in self.thresholds:
                min_val, max_val = self.thresholds[metric.name]
                value = metric.value

                if min_val is not None and value < min_val:
                    failures.append(
                        f"{metric.name}: {value:.2f} {metric.unit} "
                        f"(expected >= {min_val})"
                    )

                if max_val is not None and value > max_val:
                    failures.append(
                        f"{metric.name}: {value:.2f} {metric.unit} "
                        f"(expected <= {max_val})"
                    )

        return len(failures) == 0, failures

    def print_check_results(self, report: PerformanceReport):
        """Print benchmark check results."""
        passed, failures = self.check(report)

        print("\n" + "="*70)
        print(f"Benchmark Check: {self.name}")
        print("="*70)

        if passed:
            print("✓ All benchmarks passed!")
        else:
            print("✗ Benchmark failures:")
            for failure in failures:
                print(f"  - {failure}")

        print("="*70 + "\n")


# Common benchmark presets
BENCHMARK_API = PerformanceBenchmark("API Endpoints")
BENCHMARK_API.add_threshold("Average Response Time", max_value=500)  # < 500ms
BENCHMARK_API.add_threshold("P99 Latency", max_value=2000)  # < 2s
BENCHMARK_API.add_threshold("Success Rate", min_value=95)  # > 95%

BENCHMARK_PAYMENTS = PerformanceBenchmark("Payment Processing")
BENCHMARK_PAYMENTS.add_threshold("Average Response Time", max_value=2000)  # < 2s
BENCHMARK_PAYMENTS.add_threshold("P95 Latency", max_value=3000)  # < 3s
BENCHMARK_PAYMENTS.add_threshold("Success Rate", min_value=90)  # > 90%

BENCHMARK_THROUGHPUT = PerformanceBenchmark("Throughput")
BENCHMARK_THROUGHPUT.add_threshold("Throughput", min_value=10)  # > 10 req/s
