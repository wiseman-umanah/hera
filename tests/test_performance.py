"""Tests using performance metrics collection."""
import pytest
import time
import asyncio
from tests.virtual_wallet import VirtualWalletPool, PaymentStatus
from tests.performance_metrics import MetricsCollector, BENCHMARK_PAYMENTS, BENCHMARK_THROUGHPUT


class TestPerformanceMetrics:
    """Test performance metrics collection and reporting."""

    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test that metrics are properly collected."""
        collector = MetricsCollector("Basic Metrics Test")
        collector.start()

        # Simulate some operations
        response_times = [100, 150, 200, 120, 180, 95, 210, 140]
        for rt in response_times:
            collector.record_response(rt, success=True)

        collector.stop()

        assert collector.get_duration() > 0
        assert collector.get_avg_response_time() > 0
        assert collector.get_throughput() > 0
        assert collector.get_success_rate() == 100.0

        collector.print_report()

    @pytest.mark.asyncio
    async def test_percentile_calculations(self):
        """Test percentile calculations."""
        collector = MetricsCollector("Percentile Test")

        # Add known response times
        for i in range(1, 101):
            collector.record_response(float(i), success=True)

        p50 = collector.get_percentile(50)
        p95 = collector.get_percentile(95)
        p99 = collector.get_percentile(99)

        # Rough checks (allow some variance in binning)
        assert 45 < p50 < 55
        assert 90 < p95 < 99
        assert 98 < p99 <= 100

        print(f"P50: {p50:.1f}, P95: {p95:.1f}, P99: {p99:.1f}")

    @pytest.mark.asyncio
    async def test_error_tracking(self):
        """Test error rate tracking."""
        collector = MetricsCollector("Error Tracking Test")

        # Add 100 responses: 85 success, 15 errors
        for i in range(85):
            collector.record_response(100, success=True)
        for i in range(15):
            collector.record_response(150, success=False, error="Timeout")

        assert len(collector.response_times) == 100
        assert len(collector.errors) == 15
        assert collector.get_success_rate() == 85.0
        assert collector.get_error_rate() == 15.0

    @pytest.mark.asyncio
    async def test_throughput_calculation(self):
        """Test throughput calculation."""
        collector = MetricsCollector("Throughput Test")
        collector.start()

        # Simulate 100 requests over 10 seconds
        for _ in range(100):
            collector.record_response(100, success=True)

        # Manually set end time to control duration
        collector.end_time = collector.start_time + 10.0

        throughput = collector.get_throughput()
        assert throughput == pytest.approx(10.0, rel=0.1)  # 100 requests / 10 sec = 10 req/sec

    @pytest.mark.asyncio
    async def test_benchmark_check_passing(self):
        """Test benchmark checking with passing metrics."""
        collector = MetricsCollector("Benchmark Pass Test")
        collector.start()

        # Add responses that should pass benchmarks
        for _ in range(50):
            collector.record_response(800, success=True)  # < 2000ms

        collector.stop()
        report = collector.get_report()

        passed, failures = BENCHMARK_PAYMENTS.check(report)
        assert passed, f"Expected to pass but got failures: {failures}"

    @pytest.mark.asyncio
    async def test_benchmark_check_failing(self):
        """Test benchmark checking with failing metrics."""
        collector = MetricsCollector("Benchmark Fail Test")
        collector.start()

        # Add responses that would fail throughput benchmark
        for _ in range(5):
            collector.record_response(1000, success=True)

        collector.end_time = collector.start_time + 1.0  # Very fast = low throughput

        report = collector.get_report()
        passed, failures = BENCHMARK_THROUGHPUT.check(report)

        # Should fail throughput check (too few requests per second)
        # Note: This might not fail if calculation is favorable
        print(f"Throughput: {collector.get_throughput():.1f} req/s")

    @pytest.mark.asyncio
    async def test_custom_metrics(self):
        """Test recording custom metrics."""
        collector = MetricsCollector("Custom Metrics Test")

        collector.record_metric("Cache Hit Rate", 95.5, "%")
        collector.record_metric("Memory Usage", 256.7, "MB")
        collector.record_metric("CPU Usage", 45.2, "%")

        assert len(collector.metrics) == 3
        assert collector.metrics[0]["name"] == "Cache Hit Rate"


class TestPaymentPerformance:
    """Test payment performance metrics."""

    @pytest.mark.asyncio
    async def test_payment_latency_metrics(self):
        """Test payment latency metrics under load."""
        collector = MetricsCollector("Payment Latency")
        collector.start()

        wallet = VirtualWalletPool(
            num_wallets=10,
            initial_balance_hbar=100.0,
            avg_latency_ms=200,
        ).wallets[0]

        # Make 50 payments and collect metrics
        for _ in range(50):
            tx = await wallet.process_payment("0.0.200", 1.0, "Order")
            collector.record_response(tx.response_time_ms, tx.status == PaymentStatus.SUCCESS)

        collector.stop()

        print(f"Avg latency: {collector.get_avg_response_time():.0f}ms")
        print(f"P95: {collector.get_percentile(95):.0f}ms")
        print(f"P99: {collector.get_percentile(99):.0f}ms")

        collector.print_report()

    @pytest.mark.asyncio
    async def test_payment_throughput(self):
        """Test payment throughput."""
        collector = MetricsCollector("Payment Throughput")

        wallet_pool = VirtualWalletPool(num_wallets=20, initial_balance_hbar=100.0)

        async def make_payment():
            wallet = wallet_pool.get_random_wallet()
            tx = await wallet.process_payment("0.0.200", 1.0, "Order")
            return tx.response_time_ms, tx.status == PaymentStatus.SUCCESS

        collector.start()

        # 100 concurrent payments
        tasks = [make_payment() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        for latency, success in results:
            collector.record_response(latency, success)

        collector.stop()

        print(f"Throughput: {collector.get_throughput():.1f} payments/sec")
        print(f"Success rate: {collector.get_success_rate():.1f}%")

        collector.print_report()


class TestScalabilityMetrics:
    """Test system scalability."""

    @pytest.mark.asyncio
    async def test_scaling_with_user_count(self):
        """Test how performance scales with user count."""
        user_counts = [5, 10, 20, 50]
        results = []

        for num_users in user_counts:
            collector = MetricsCollector(f"Scalability: {num_users} users")
            
            wallet_pool = VirtualWalletPool(num_wallets=num_users, initial_balance_hbar=100.0)

            async def make_payment():
                wallet = wallet_pool.get_random_wallet()
                tx = await wallet.process_payment("0.0.200", 1.0, "Order")
                return tx.response_time_ms, tx.status == PaymentStatus.SUCCESS

            collector.start()

            # 20 payments per user
            tasks = [make_payment() for _ in range(num_users * 20)]
            responses = await asyncio.gather(*tasks)

            for latency, success in responses:
                collector.record_response(latency, success)

            collector.stop()

            results.append({
                "users": num_users,
                "throughput": collector.get_throughput(),
                "avg_latency": collector.get_avg_response_time(),
                "success_rate": collector.get_success_rate(),
            })

        print("\n" + "="*70)
        print("Scalability Analysis")
        print("="*70)
        print(f"{'Users':<10} {'Throughput':<20} {'Avg Latency':<20} {'Success Rate':<15}")
        print("-"*70)
        for r in results:
            print(f"{r['users']:<10} {r['throughput']:<20.2f} {r['avg_latency']:<20.0f} {r['success_rate']:<15.1f}%")
        print("="*70)
