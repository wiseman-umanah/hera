"""Chaos and failure scenario tests.

Tests system resilience under various failure conditions.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from tests.virtual_wallet import VirtualWalletPool, VirtualWallet, PaymentStatus


class TestPaymentTimeouts:
    """Test timeout handling."""

    @pytest.mark.asyncio
    async def test_payment_timeout_recovery(self):
        """Test system recovery from payment timeouts."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=100.0,
            timeout_rate=0.2,  # 20% timeout
            avg_latency_ms=300,
        )

        results = []
        for _ in range(10):
            tx = await wallet.process_payment("0.0.200", 1.0, "Order")
            results.append(tx)
            # Retry failed payments (realistic scenario)
            if tx.status == PaymentStatus.TIMEOUT:
                # Retry with fresh attempt
                retry_tx = await wallet.process_payment("0.0.200", 1.0, "Retry Order")
                results.append(retry_tx)

        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)
        timeouts = sum(1 for tx in results if tx.status == PaymentStatus.TIMEOUT)

        print(f"✓ Timeout recovery: {successful} successful, {timeouts} timeouts (with retries)")
        assert successful > timeouts  # Retries should succeed

    @pytest.mark.asyncio
    async def test_timeout_under_high_latency(self):
        """Test behavior under high latency conditions."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=100.0,
            avg_latency_ms=500,  # 500ms average latency
            latency_variance_ms=200,  # High variance
            timeout_rate=0.05,
        )

        results = []
        start_time = asyncio.get_event_loop().time()
        
        for _ in range(5):
            tx = await wallet.process_payment("0.0.200", 1.0, "Order")
            results.append(tx)

        elapsed = asyncio.get_event_loop().time() - start_time
        avg_latency = sum(tx.response_time_ms for tx in results) / len(results)

        print(f"✓ High latency test: {len(results)} payments in {elapsed:.1f}s")
        print(f"  Average latency: {avg_latency:.0f}ms")
        print(f"  Latency range: {min(tx.response_time_ms for tx in results):.0f}ms - {max(tx.response_time_ms for tx in results):.0f}ms")


class TestNetworkFailures:
    """Test network error handling."""

    @pytest.mark.asyncio
    async def test_network_errors_with_retries(self):
        """Test system handles network errors with retries."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=100.0,
            network_error_rate=0.2,  # 20% network errors
        )

        def attempt_with_retry(max_retries=3):
            """Attempt payment with exponential backoff retry."""
            async def _retry():
                for attempt in range(max_retries):
                    tx = await wallet.process_payment("0.0.200", 1.0, "Order")
                    if tx.status == PaymentStatus.SUCCESS:
                        return tx, attempt + 1
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                return tx, max_retries
            return _retry()

        results_with_attempts = []
        for _ in range(10):
            tx, attempts = await attempt_with_retry()
            results_with_attempts.append((tx, attempts))

        successful = sum(1 for tx, _ in results_with_attempts if tx.status == PaymentStatus.SUCCESS)
        avg_attempts = sum(attempts for _, attempts in results_with_attempts) / len(results_with_attempts)

        print(f"✓ Network error recovery: {successful}/10 successful")
        print(f"  Average attempts: {avg_attempts:.1f}")

    @pytest.mark.asyncio
    async def test_cascading_network_failures(self):
        """Test behavior when multiple wallets experience network issues."""
        wallet_pool = VirtualWalletPool(
            num_wallets=5,
            initial_balance_hbar=100.0,
            network_error_rate=0.25,  # 25% error rate
            avg_latency_ms=200,
        )

        async def make_payment(wallet):
            return await wallet.process_payment("0.0.200", 1.0, "Order")

        # 20 concurrent payments across pool
        tasks = [make_payment(wallet_pool.get_random_wallet()) for _ in range(20)]
        results = await asyncio.gather(*tasks)

        errors = sum(1 for tx in results if tx.status == PaymentStatus.NETWORK_ERROR)
        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)

        print(f"✓ Cascading failures: {errors} errors, {successful} successful out of {len(results)}")
        assert successful > 0  # Some should still succeed


class TestInsufficientFunds:
    """Test insufficient balance scenarios."""

    @pytest.mark.asyncio
    async def test_insufficient_balance_detection(self):
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=10.0,
            rejection_rate=0,
            timeout_rate=0,
            network_error_rate=0
        )

        # Orders increasing in cost
        orders = [
            (3.0, "Order 1"),
            (3.0, "Order 2"),
            (3.0, "Order 3"),
            (2.0, "Order 4"),  # This will fail (10 - 9 = 1 < 2)
        ]

        results = []
        for amount, desc in orders:
            tx = await wallet.process_payment("0.0.200", amount, desc)
            results.append(tx)

        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)
        insufficient = sum(1 for tx in results if tx.status == PaymentStatus.INSUFFICIENT_BALANCE)

        print(f"✓ Insufficient funds: {successful} successful, {insufficient} rejected due to balance")
        assert successful == 3
        assert insufficient == 1

    @pytest.mark.asyncio
    async def test_race_condition_on_balance(self):
        """Test concurrent payments racing for limited balance."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=5.0,
            rejection_rate=0,
            timeout_rate=0,
            network_error_rate=0
        )

        async def attempt_order():
            return await wallet.process_payment("0.0.200", 2.0, "Order")

        # 5 concurrent 2 HBAR payments (balance is 5 HBAR)
        tasks = [attempt_order() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)
        insufficient = sum(1 for tx in results if tx.status == PaymentStatus.INSUFFICIENT_BALANCE)

        print(f"✓ Balance race condition: {successful} successful, {insufficient} insufficient")
        print(f"  Remaining balance: {wallet.balance:.1f} HBAR")
        # At most 2 should succeed (5 / 2 = 2.5)
        assert successful <= 2


class TestRejectionScenarios:
    """Test payment rejection handling."""

    @pytest.mark.asyncio
    async def test_user_rejection_rate(self):
        """Test varying rejection rates and recovery."""
        for rejection_rate in [0.05, 0.1, 0.2]:
            wallet = VirtualWallet(
                "0.0.100",
                initial_balance_hbar=100.0,
                rejection_rate=rejection_rate,
                timeout_rate=0.0,
            )

            tasks = [
                wallet.process_payment("0.0.200", 1.0, "Order")
                for _ in range(40)
            ]
            results = await asyncio.gather(*tasks)

            rejected = sum(1 for tx in results if tx.status == PaymentStatus.REJECTED)
            successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)
            actual_rate = rejected / len(results)

            print(f"✓ Rejection rate {rejection_rate*100:.0f}%: {rejected} rejected, {successful} successful (actual: {actual_rate*100:.1f}%)")

    @pytest.mark.asyncio
    async def test_rejection_pattern_detection(self):
        """Test detecting patterns in rejections."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=100.0,
            rejection_rate=0.15,
        )

        results = []
        rejection_sequences = []
        consecutive_rejections = 0

        for _ in range(30):
            tx = await wallet.process_payment("0.0.200", 1.0, "Order")
            results.append(tx)

            if tx.status == PaymentStatus.REJECTED:
                consecutive_rejections += 1
            else:
                if consecutive_rejections > 0:
                    rejection_sequences.append(consecutive_rejections)
                consecutive_rejections = 0

        rejected = sum(1 for tx in results if tx.status == PaymentStatus.REJECTED)
        print(f"✓ Rejection patterns: {rejected}/30 rejected")
        if rejection_sequences:
            print(f"  Longest rejection sequence: {max(rejection_sequences)}")


class TestCombinedFailureModes:
    """Test multiple failure types simultaneously."""

    @pytest.mark.asyncio
    async def test_worst_case_scenario(self):
        """Test system under worst realistic conditions."""
        wallet_pool = VirtualWalletPool(
            num_wallets=10,
            initial_balance_hbar=50.0,
            rejection_rate=0.15,       # 15% rejection
            timeout_rate=0.1,         # 10% timeout
            network_error_rate=0.05,  # 5% network error
            avg_latency_ms=300,       # High latency
            latency_variance_ms=150,  # High variance
        )

        async def make_payment():
            wallet = wallet_pool.get_random_wallet()
            return await wallet.process_payment("0.0.200", 2.5, "Order")

        # 50 concurrent payments
        tasks = [make_payment() for _ in range(50)]
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks)
        elapsed = asyncio.get_event_loop().time() - start_time

        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)
        failed = len(results) - successful

        stats = wallet_pool.get_pool_stats()

        print(f"✓ Worst case scenario:")
        print(f"  50 payments in {elapsed:.1f}s")
        print(f"  Success rate: {stats['pool_success_rate_pct']:.1f}%")
        print(f"  Successful: {successful}, Failed: {failed}")

        # Even in worst case, significant portion should succeed
        assert successful >= 30  # At least 60% success

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test that system degrades gracefully."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=100.0,
            rejection_rate=0.2,
            timeout_rate=0.1,
            network_error_rate=0.05,
        )

        # Make payments and track success rate over time
        windows = []
        for window in range(5):
            window_results = []
            for _ in range(10):
                tx = await wallet.process_payment("0.0.200", 1.0, "Order")
                window_results.append(tx)

            success_rate = sum(1 for tx in window_results if tx.status == PaymentStatus.SUCCESS) / len(window_results)
            windows.append(success_rate)

        print(f"✓ Graceful degradation test:")
        for i, rate in enumerate(windows):
            print(f"  Window {i+1}: {rate*100:.0f}% success rate")

        # Should not crash or hang, maintain reasonable success
        assert all(w >= 0.4 for w in windows)  # At least 40% success in each window
