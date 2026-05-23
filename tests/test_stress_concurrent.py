"""Concurrent stress tests with virtual wallets.

Tests the system under load with multiple simultaneous users making orders.
"""
import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock
from tests.virtual_wallet import VirtualWalletPool, VirtualWallet, PaymentStatus
from config import settings


class TestConcurrentOrderProcessing:
    """Test system with concurrent user orders."""

    @pytest.mark.asyncio
    async def test_concurrent_payments_success(self, hedera_client, localnet_accounts):
        """Test multiple concurrent successful payments."""
        num_wallets = 3 if settings.HEDERA_NETWORK == "localnet" else 5
        wallet_pool = VirtualWalletPool(
            num_wallets=num_wallets,
            network=settings.HEDERA_NETWORK,
            initial_balance_hbar=100.0,
            rejection_rate=0.0,
            timeout_rate=0.0,
            network_error_rate=0.0,
            avg_latency_ms=100,
        )
        
        if hedera_client:
            await wallet_pool.initialize_localnet(hedera_client)

        async def make_payment(wallet):
            return await wallet.process_payment(localnet_accounts["shop_id"], 2.5, "Flat White")

        # Run 5 concurrent payments
        start_time = time.time()
        tasks = [make_payment(w) for w in wallet_pool.wallets]
        results = await asyncio.gather(*tasks)
        elapsed_ms = (time.time() - start_time) * 1000

        # All should succeed
        assert all(tx.status == PaymentStatus.SUCCESS for tx in results)
        assert all(tx.tx_id for tx in results)

        # Check stats
        stats = wallet_pool.get_pool_stats()
        assert stats["total_payments"] == num_wallets
        assert stats["total_successful"] == num_wallets
        assert stats["total_failed"] == 0
        
        print(f"✓ 5 concurrent payments completed in {elapsed_ms:.0f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_payments_with_failures(self):
        """Test concurrent payments with realistic failure rates."""
        wallet_pool = VirtualWalletPool(
            num_wallets=10,
            initial_balance_hbar=50.0,
            rejection_rate=0.1,       # 10% rejection
            timeout_rate=0.05,        # 5% timeout
            network_error_rate=0.02,  # 2% network error
            avg_latency_ms=150,
        )

        async def make_payment(wallet):
            return await wallet.process_payment("0.0.200", 2.0, "Cappuccino")

        # Run 20 concurrent payments
        tasks = [make_payment(wallet_pool.get_random_wallet()) for _ in range(20)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed_ms = (time.time() - start_time) * 1000

        # Track outcomes
        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)
        failed = len(results) - successful

        stats = wallet_pool.get_pool_stats()
        print(f"✓ 20 concurrent payments: {successful} success, {failed} failed in {elapsed_ms:.0f}ms")
        print(f"  Pool success rate: {stats['pool_success_rate_pct']:.1f}%")

        # At least some should succeed
        assert successful > 0
        assert stats["total_payments"] == 20

    @pytest.mark.asyncio
    async def test_concurrent_rapid_user_sequence(self):
        """Test realistic user scenario: browse menu -> add items -> pay."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=100.0,
            rejection_rate=0.0,
            timeout_rate=0.0,
            network_error_rate=0.0,
            avg_latency_ms=100,
        )

        async def user_order_sequence():
            """Simulate: espresso (1h) + croissant (1h) = 2h total."""
            # Payment request
            tx = await wallet.process_payment("0.0.200", 2.0, "Espresso + Croissant")
            return tx

        # Simulate 5 users making simultaneous orders
        tasks = [user_order_sequence() for _ in range(5)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed_ms = (time.time() - start_time) * 1000

        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)
        assert successful == 5
        print(f"✓ 5 user order sequences (2 items each) in {elapsed_ms:.0f}ms")

    @pytest.mark.asyncio
    async def test_high_volume_burst(self):
        """Test system under high-volume burst (50 concurrent payments)."""
        wallet_pool = VirtualWalletPool(
            num_wallets=20,
            initial_balance_hbar=150.0,
            rejection_rate=0.03,
            timeout_rate=0.01,
            avg_latency_ms=100,
        )

        async def make_random_order():
            wallet = wallet_pool.get_random_wallet()
            # Random order amount between 1-3 HBAR
            amount = round(1 + (2 * asyncio.get_event_loop().time() % 2), 1)
            return await wallet.process_payment("0.0.200", amount, "Order")

        # 50 concurrent payments
        tasks = [make_random_order() for _ in range(50)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed_ms = (time.time() - start_time) * 1000

        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)
        stats = wallet_pool.get_pool_stats()

        print(f"✓ 50 burst payments: {successful}/{len(results)} successful in {elapsed_ms:.0f}ms")
        print(f"  Success rate: {stats['pool_success_rate_pct']:.1f}%")
        print(f"  Avg latency: {sum(tx.response_time_ms for tx in results) / len(results):.0f}ms")

        # Most should succeed (allow some failures)
        assert successful >= 40

    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """Test system under sustained load over time."""
        wallet_pool = VirtualWalletPool(
            num_wallets=15,
            initial_balance_hbar=200.0,
            rejection_rate=0.05,
            timeout_rate=0.02,
            avg_latency_ms=120,
        )

        async def make_payment():
            wallet = wallet_pool.get_random_wallet()
            return await wallet.process_payment("0.0.200", 1.5, "Coffee")

        # Run 100 payments in batches of 10
        start_time = time.time()
        total_results = []

        for batch in range(10):
            batch_start = time.time()
            tasks = [make_payment() for _ in range(10)]
            results = await asyncio.gather(*tasks)
            total_results.extend(results)
            batch_time = time.time() - batch_start
            
            print(f"  Batch {batch+1}: 10 payments in {batch_time*1000:.0f}ms")
            # Brief pause between batches (realistic scenario)
            await asyncio.sleep(0.1)

        total_elapsed = time.time() - start_time
        stats = wallet_pool.get_pool_stats()

        print(f"✓ 100 sustained payments in {total_elapsed:.1f}s")
        print(f"  Success rate: {stats['pool_success_rate_pct']:.1f}%")
        print(f"  Throughput: {100/total_elapsed:.1f} payments/sec")

        assert len(total_results) == 100


class TestConcurrentPaymentConflicts:
    """Test handling of concurrent edge cases."""

    @pytest.mark.asyncio
    async def test_concurrent_insufficient_balance(self):
        """Test multiple users with insufficient balance."""
        wallet = VirtualWallet("0.0.100", initial_balance_hbar=5.0)

        async def attempt_payment(amount):
            return await wallet.process_payment("0.0.200", amount, "Order")

        # Try 5 concurrent 3 HBAR payments (wallet only has 5)
        tasks = [attempt_payment(3.0) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)
        insufficient = sum(1 for tx in results if tx.status == PaymentStatus.INSUFFICIENT_BALANCE)

        # First one succeeds (5-3=2), then next attempts fail
        assert successful <= 2
        assert insufficient > 0
        print(f"✓ Insufficient balance test: {successful} successful, {insufficient} insufficient")

    @pytest.mark.asyncio
    async def test_wallet_rejections_under_load(self):
        """Test wallet rejection rate under load."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=100.0,
            rejection_rate=0.2,  # 20% rejection rate
            timeout_rate=0.0,
            network_error_rate=0.0,
            avg_latency_ms=50,
        )

        async def make_payment():
            return await wallet.process_payment("0.0.200", 2.0, "Order")

        # 50 rapid payments
        tasks = [make_payment() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        rejected = sum(1 for tx in results if tx.status == PaymentStatus.REJECTED)
        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)

        rejection_rate = rejected / len(results)
        print(f"✓ Rejection rate test: {rejected} rejected, {successful} successful")
        print(f"  Actual rejection rate: {rejection_rate*100:.1f}% (configured: 20%)")

        # Should be close to configured 20% rejection rate
        assert 0.1 < rejection_rate < 0.3

    @pytest.mark.asyncio
    async def test_timeout_rate_under_load(self):
        """Test timeout behavior."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=100.0,
            rejection_rate=0.0,
            timeout_rate=0.1,  # 10% timeout
            network_error_rate=0.0,
            avg_latency_ms=200,
        )

        async def make_payment():
            return await wallet.process_payment("0.0.200", 1.0, "Order")

        tasks = [make_payment() for _ in range(40)]
        results = await asyncio.gather(*tasks)

        timeouts = sum(1 for tx in results if tx.status == PaymentStatus.TIMEOUT)
        successful = sum(1 for tx in results if tx.status == PaymentStatus.SUCCESS)

        timeout_rate = timeouts / len(results)
        print(f"✓ Timeout rate test: {timeouts} timeouts, {successful} successful")
        print(f"  Actual timeout rate: {timeout_rate*100:.1f}% (configured: 10%)")


class TestWalletStatsCollection:
    """Test wallet metrics and reporting."""

    @pytest.mark.asyncio
    async def test_wallet_stats_accuracy(self):
        """Test that wallet stats are accurately recorded."""
        wallet = VirtualWallet(
            "0.0.100",
            initial_balance_hbar=50.0,
            rejection_rate=0.0,
            timeout_rate=0.0,
            network_error_rate=0.0
        )

        # Make 10 payments
        for i in range(10):
            await wallet.process_payment("0.0.200", 1.0, f"Order {i+1}")

        stats = wallet.get_stats()
        assert stats["total_payments"] == 10
        assert stats["successful"] == 10
        assert stats["balance"] == 40.0  # 50 - (10 * 1.0)
        assert stats["success_rate_pct"] == 100.0
        print(f"✓ Wallet stats: {stats}")

    @pytest.mark.asyncio
    async def test_pool_stats_aggregation(self):
        """Test pool statistics aggregation."""
        wallet_pool = VirtualWalletPool(
            num_wallets=5,
            initial_balance_hbar=100.0,
            rejection_rate=0.0,
            timeout_rate=0.0,
            network_error_rate=0.0
        )

        async def make_payment(wallet):
            return await wallet.process_payment("0.0.200", 5.0, "Order")

        # Each wallet makes 2 payments
        for wallet in wallet_pool.wallets:
            tasks = [make_payment(wallet) for _ in range(2)]
            await asyncio.gather(*tasks)

        pool_stats = wallet_pool.get_pool_stats()
        assert pool_stats["total_payments"] == 10  # 5 wallets * 2 payments
        assert pool_stats["num_wallets"] == 5
        assert pool_stats["total_successful"] == 10
        print(f"✓ Pool stats: {pool_stats}")
