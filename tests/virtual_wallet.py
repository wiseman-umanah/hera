"""Virtual wallet simulator for stress testing.

Simulates realistic wallet behavior including:
- Random delays (network latency)
- Occasional payment rejections
- Balance fluctuations
- Transaction timeouts
- Connection drops
"""
import asyncio
import random
import uuid
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    """Payment outcomes."""
    SUCCESS = "success"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    INSUFFICIENT_BALANCE = "insufficient_balance"


@dataclass
class Transaction:
    """Represents a simulated transaction."""
    tx_id: str
    from_account: str
    to_account: str
    amount_hbar: float
    status: PaymentStatus
    response_time_ms: float
    timestamp: float


class VirtualWallet:
    """Simulates a user wallet with realistic behavior."""

    def __init__(
        self,
        account_id: str,
        initial_balance_hbar: float = 100.0,
        rejection_rate: float = 0.05,
        timeout_rate: float = 0.02,
        network_error_rate: float = 0.01,
        avg_latency_ms: float = 200,
        latency_variance_ms: float = 100,
        client=None,
        private_key: str = "",
    ):
        """Initialize virtual wallet.
        
        Args:
            account_id: Hedera account ID
            initial_balance_hbar: Starting balance in HBAR
            rejection_rate: Probability wallet rejects payment (0.0-1.0)
            timeout_rate: Probability payment times out (0.0-1.0)
            network_error_rate: Probability of network error (0.0-1.0)
            avg_latency_ms: Average response time in milliseconds
            latency_variance_ms: Standard deviation of latency
            client: Optional hiero_sdk_python Client for real transactions
            private_key: Private key for the account (required if client is provided)
        """
        self.account_id = account_id
        self.balance = initial_balance_hbar
        self.rejection_rate = rejection_rate
        self.timeout_rate = timeout_rate
        self.network_error_rate = network_error_rate
        self.avg_latency_ms = avg_latency_ms
        self.latency_variance_ms = latency_variance_ms
        self.client = client
        self.private_key = private_key
        
        self.transactions: list[Transaction] = []
        self.payment_count = 0
        self.rejection_count = 0
        self.timeout_count = 0
        self.error_count = 0

    def _get_latency(self) -> float:
        """Get realistic latency in milliseconds."""
        return max(50, random.gauss(self.avg_latency_ms, self.latency_variance_ms))

    async def process_payment(
        self,
        to_account: str,
        amount_hbar: float,
        description: str = "",
    ) -> Optional[Transaction]:
        """Process a payment with realistic wallet behavior.
        
        Returns Transaction with success/failure details, or None if unrecoverable error.
        """
        start_time = asyncio.get_event_loop().time()
        latency_ms = self._get_latency()
        
        # Simulate network delay
        await asyncio.sleep(latency_ms / 1000.0)
        
        self.payment_count += 1
        
        # Determine outcome based on configured rates
        rand = random.random()
        
        # Network error (highest priority - most unrecoverable)
        if rand < self.network_error_rate:
            self.error_count += 1
            tx = Transaction(
                tx_id="",
                from_account=self.account_id,
                to_account=to_account,
                amount_hbar=amount_hbar,
                status=PaymentStatus.NETWORK_ERROR,
                response_time_ms=latency_ms,
                timestamp=start_time,
            )
            self.transactions.append(tx)
            return tx
        
        # Timeout
        if rand < (self.network_error_rate + self.timeout_rate):
            self.timeout_count += 1
            tx = Transaction(
                tx_id="",
                from_account=self.account_id,
                to_account=to_account,
                amount_hbar=amount_hbar,
                status=PaymentStatus.TIMEOUT,
                response_time_ms=latency_ms,
                timestamp=start_time,
            )
            self.transactions.append(tx)
            return tx
        
        # Check insufficient balance
        if self.balance < amount_hbar:
            tx = Transaction(
                tx_id="",
                from_account=self.account_id,
                to_account=to_account,
                amount_hbar=amount_hbar,
                status=PaymentStatus.INSUFFICIENT_BALANCE,
                response_time_ms=latency_ms,
                timestamp=start_time,
            )
            self.transactions.append(tx)
            return tx
        
        # User rejection
        if rand < (self.network_error_rate + self.timeout_rate + self.rejection_rate):
            self.rejection_count += 1
            tx = Transaction(
                tx_id="",
                from_account=self.account_id,
                to_account=to_account,
                amount_hbar=amount_hbar,
                status=PaymentStatus.REJECTED,
                response_time_ms=latency_ms,
                timestamp=start_time,
            )
            self.transactions.append(tx)
            return tx
        
        # Success!
        if self.client and self.private_key:
            from hiero_sdk_python import TransferTransaction, Hbar, AccountId, PrivateKey
            
            # Debug prints
            print(f"\nDEBUG: Wallet {self.account_id} sending {amount_hbar} to {to_account}")
            
            self.client.set_operator(
                AccountId.from_string(self.account_id),
                PrivateKey.from_string(self.private_key)
            )
            
            tx = TransferTransaction() \
                .add_hbar_transfer(AccountId.from_string(self.account_id), Hbar.from_tinybars(int(-amount_hbar * 100_000_000))) \
                .add_hbar_transfer(AccountId.from_string(to_account), Hbar.from_tinybars(int(amount_hbar * 100_000_000)))
            
            resp = await tx.execute(self.client)
            receipt = await resp.get_receipt(self.client)
            tx_id = resp.transaction_id.to_string()
            
            # Fetch real balance after transaction
            from httpx import get
            from config import settings
            try:
                url = f"{settings.MIRROR_NODE_URL}/api/v1/accounts/{self.account_id}"
                balance_resp = get(url, timeout=5)
                if balance_resp.status_code == 200:
                    self.balance = balance_resp.json()["balance"]["balance"] / 100_000_000
            except:
                self.balance -= amount_hbar
        else:
            # Simulated success
            tx_id = f"0.0.1-{random.randint(1000, 9999)}-{random.randint(1, 100)}"
            self.balance -= amount_hbar
        
        tx = Transaction(
            tx_id=tx_id,
            from_account=self.account_id,
            to_account=to_account,
            amount_hbar=amount_hbar,
            status=PaymentStatus.SUCCESS,
            response_time_ms=latency_ms,
            timestamp=start_time,
        )
        self.transactions.append(tx)
        return tx

    def get_stats(self) -> dict:
        """Get wallet statistics."""
        successful = sum(1 for tx in self.transactions if tx.status == PaymentStatus.SUCCESS)
        failed = self.payment_count - successful
        success_rate = (successful / self.payment_count * 100) if self.payment_count > 0 else 0
        avg_latency = (
            sum(tx.response_time_ms for tx in self.transactions) / len(self.transactions)
            if self.transactions else 0
        )
        
        return {
            "account_id": self.account_id,
            "balance": self.balance,
            "total_payments": self.payment_count,
            "successful": successful,
            "failed": failed,
            "success_rate_pct": success_rate,
            "rejections": self.rejection_count,
            "timeouts": self.timeout_count,
            "errors": self.error_count,
            "avg_latency_ms": avg_latency,
        }

    def reset(self):
        """Reset wallet state for new test."""
        self.transactions.clear()
        self.payment_count = 0
        self.rejection_count = 0
        self.timeout_count = 0
        self.error_count = 0


class VirtualWalletPool:
    """Manages pool of virtual wallets for multi-user scenarios."""

    def __init__(self,        num_wallets: int = 10,
        network: str = "testnet",
        **wallet_kwargs
    ):
        """Initialize wallet pool.
        
        Args:
            num_wallets: Number of virtual wallets to create
            network: Hedera network (e.g. "localnet")
            **wallet_kwargs: Arguments passed to VirtualWallet constructor
        """
        self.network = network
        self.wallet_kwargs = wallet_kwargs
        self.num_wallets = num_wallets
        self.wallets: list[VirtualWallet] = []
        
        if network != "localnet":
            self.wallets = [
                VirtualWallet(
                    account_id=f"0.0.{1000 + i}",
                    **wallet_kwargs
                )
                for i in range(num_wallets)
            ]

    async def initialize_localnet(self, client):
        """Provision real accounts on localnet for the pool."""
        from tests.hedera_localnet import create_localnet_account
        self.wallets = []
        for i in range(self.num_wallets):
            print(f"  Creating localnet wallet {i+1}/{self.num_wallets}...")
            account_id, private_key = await create_localnet_account(client, self.wallet_kwargs.get("initial_balance_hbar", 1000.0))
            self.wallets.append(
                VirtualWallet(
                    account_id=account_id,
                    client=client,
                    private_key=private_key,
                    **self.wallet_kwargs
                )
            )

    def get_random_wallet(self) -> VirtualWallet:
        """Get a random wallet from pool."""
        return random.choice(self.wallets)

    def get_all_stats(self) -> list[dict]:
        """Get stats for all wallets."""
        return [w.get_stats() for w in self.wallets]

    def get_pool_stats(self) -> dict:
        """Get aggregated pool statistics."""
        all_stats = self.get_all_stats()
        total_payments = sum(s["total_payments"] for s in all_stats)
        total_successful = sum(s["successful"] for s in all_stats)
        total_failed = sum(s["failed"] for s in all_stats)
        
        return {
            "num_wallets": len(self.wallets),
            "total_payments": total_payments,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "pool_success_rate_pct": (total_successful / total_payments * 100) if total_payments > 0 else 0,
            "total_balance_remaining": sum(s["balance"] for s in all_stats),
        }

    def reset_all(self):
        """Reset all wallets."""
        for wallet in self.wallets:
            wallet.reset()
