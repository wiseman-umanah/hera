"""Locust load testing suite for HBAR Coffee Shop.

Run with:
  locust -f tests/locustfile.py --host=http://localhost:8000
"""
import os
import asyncio
import json
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
from tests.virtual_wallet import VirtualWalletPool, PaymentStatus


# Global wallet pool
WALLET_POOL = None


class CoffeeShopUser(FastHttpUser):
    """Simulates a coffee shop customer."""

    wait_time = between(0.5, 2.0)  # Wait 0.5-2s between actions

    def on_start(self):
        """Initialize user with a virtual wallet."""
        global WALLET_POOL
        if WALLET_POOL is None:
            WALLET_POOL = VirtualWalletPool(
                num_wallets=50,
                initial_balance_hbar=100.0,
                rejection_rate=0.05,
                timeout_rate=0.02,
                network_error_rate=0.01,
                avg_latency_ms=150,
            )
        self.wallet = WALLET_POOL.get_random_wallet()
        self.cart = []

    @task(5)
    def browse_menu(self):
        """Fetch menu configuration."""
        with self.client.get("/api/config", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(3)
    def check_balance(self):
        """Check account balance."""
        with self.client.get(
            f"/api/balance/{self.wallet.account_id}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "hbar" in data:
                    response.success()
                else:
                    response.failure("Missing 'hbar' in response")
            else:
                response.failure(f"Got status {response.status_code}")

    @task(10)
    def add_to_cart(self):
        """Add item to cart (simulated)."""
        items = [
            ("espresso", 1.0),
            ("flat white", 2.0),
            ("cappuccino", 2.0),
            ("cold brew", 3.0),
            ("matcha latte", 3.0),
            ("chai latte", 2.0),
            ("blueberry muffin", 1.0),
            ("croissant", 1.0),
            ("avocado toast", 3.0),
        ]
        item, price = items[hash(self.wallet.account_id) % len(items)]
        self.cart.append({"item": item, "price": price})

    @task(1)
    async def checkout_and_pay(self):
        """Checkout and process payment."""
        if not self.cart:
            return

        total = sum(item["price"] for item in self.cart)
        items = [item["item"] for item in self.cart]

        # Simulate payment with virtual wallet
        tx = await asyncio.to_thread(
            self._process_payment,
            total,
            f"Order: {', '.join(items)}"
        )

        # Log result
        if tx.status == PaymentStatus.SUCCESS:
            self.environment.events.request.fire(
                request_type="payment",
                name="checkout_success",
                response_time=tx.response_time_ms,
                response_length=len(tx.tx_id),
                response=None,
                context={}
            )
        else:
            self.environment.events.request.fire(
                request_type="payment",
                name=f"checkout_failed_{tx.status.value}",
                response_time=tx.response_time_ms,
                response_length=0,
                response=None,
                context={}
            )

        self.cart.clear()

    def _process_payment(self, amount, description):
        """Blocking wrapper for async payment."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.wallet.process_payment(
                    "0.0.200",
                    amount,
                    description
                )
            )
            return result
        finally:
            loop.close()


class CoffeeShopPowerUser(FastHttpUser):
    """Power user making frequent rapid orders."""

    wait_time = between(0.1, 0.5)  # Very short wait times

    def on_start(self):
        """Initialize power user."""
        global WALLET_POOL
        if WALLET_POOL is None:
            WALLET_POOL = VirtualWalletPool(num_wallets=30, initial_balance_hbar=500.0)
        self.wallet = WALLET_POOL.get_random_wallet()

    @task(2)
    def rapid_payment(self):
        """Make a rapid small payment."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tx = loop.run_until_complete(
                self.wallet.process_payment("0.0.200", 1.0, "Quick espresso")
            )
            
            if tx.status == PaymentStatus.SUCCESS:
                self.environment.events.request.fire(
                    request_type="rapid_payment",
                    name="success",
                    response_time=tx.response_time_ms,
                    response_length=1,
                    response=None,
                    context={}
                )
            else:
                self.environment.events.request.fire(
                    request_type="rapid_payment",
                    name="failed",
                    response_time=tx.response_time_ms,
                    response_length=0,
                    response=None,
                    context={}
                )
        finally:
            loop.close()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize wallet pool at test start."""
    global WALLET_POOL
    WALLET_POOL = VirtualWalletPool(
        num_wallets=100,
        initial_balance_hbar=150.0,
        rejection_rate=0.05,
        timeout_rate=0.02,
        network_error_rate=0.01,
        avg_latency_ms=100,
    )
    print("\n" + "="*60)
    print("Load Test Starting")
    print("="*60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print final statistics."""
    global WALLET_POOL
    if WALLET_POOL:
        stats = WALLET_POOL.get_pool_stats()
        print("\n" + "="*60)
        print("Load Test Results - Virtual Wallet Pool")
        print("="*60)
        print(f"Total Payments:       {stats['total_payments']}")
        print(f"Successful:           {stats['total_successful']}")
        print(f"Failed:               {stats['total_failed']}")
        print(f"Success Rate:         {stats['pool_success_rate_pct']:.1f}%")
        print(f"Remaining Balance:    {stats['total_balance_remaining']:.1f} HBAR")
        print("="*60 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Log individual requests."""
    if exception:
        print(f"✗ {request_type}/{name}: {exception}")
    else:
        print(f"✓ {request_type}/{name}: {response_time:.0f}ms")
