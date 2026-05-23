"""Shared pytest configuration and fixtures."""
import os
import asyncio
import pytest
from unittest.mock import patch, MagicMock
from config import settings
from tests.hedera_localnet import create_localnet_account
from tests.primitive_ledger import start_primitive_node, ledger as primitive_ledger

def has_local_node():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', 50211)) == 0

@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "SHOP_ACCOUNT_ID": "0.0.12345",
        "GROQ_API_KEY": "test-key-12345",
        "WALLETCONNECT_PROJECT_ID": "test-project-id",
        "HEDERA_NETWORK": "localnet",
        "MIRROR_NODE_URL": "http://127.0.0.1:5551" if not has_local_node() else "http://localhost:5551"
    }):
        yield

@pytest.fixture(scope="session", autouse=True)
def start_node():
    """Start the primitive localnet node if a real one isn't running."""
    if has_local_node():
        print("\n✅ Real Hedera Local Node detected! Skipping Primitive mode.")
        return

    print("\n🐣 No local node found. Starting Primitive Ledger mode...")
    start_primitive_node(5551)
    
    # Monkeypatch the SDK ONLY in primitive mode
    from hiero_sdk_python import TransferTransaction, AccountCreateTransaction
    
    # Patch AccountCreateTransaction
    async def mock_create_execute(self, client):
        account_id = f"0.0.{100 + len(primitive_ledger.accounts)}"
        try:
            hbar_val = self._initial_balance.to_tinybars() / 100_000_000
        except:
            hbar_val = 1000.0
        primitive_ledger.create_account(account_id, hbar_val)
        
        mock_resp = MagicMock()
        mock_resp.transaction_id.to_string.return_value = f"create-tx-{account_id}"
        async def mock_get_receipt(c):
            receipt = MagicMock()
            receipt.account_id.to_string.return_value = account_id
            return receipt
        mock_resp.get_receipt = mock_get_receipt
        return mock_resp
    
    AccountCreateTransaction.execute = mock_create_execute
    
    # Patch TransferTransaction
    async def mock_transfer_execute(self, client):
        try:
            for transfer in self.hbar_transfers:
                acc_str = str(transfer.account_id)
                tinybars = transfer.amount
                if acc_str not in primitive_ledger.accounts:
                    primitive_ledger.accounts[acc_str] = 0
                primitive_ledger.accounts[acc_str] += tinybars
            
            mock_resp = MagicMock()
            mock_resp.transaction_id.to_string.return_value = f"0.0.2@{int(asyncio.get_event_loop().time())}.000"
            async def mock_get_receipt(c): return MagicMock()
            mock_resp.get_receipt = mock_get_receipt
            return mock_resp
        except Exception as e:
            raise e

    TransferTransaction.execute = mock_transfer_execute


@pytest.fixture(scope="session")
def hedera_client():
    """Provides a Hedera client (real or primitive)."""
    from hiero_sdk_python import Client
    from hiero_sdk_python.client.network import Network
    
    if has_local_node():
        # Use built-in 'localhost' config which points to 127.0.0.1:50211
        return Client(Network("localhost"))
    
    # Primitive mode client: point to our mock node
    # We use 'local' name and override the mirror address
    return Client(Network("local", mirror_address="127.0.0.1:5551"))


@pytest.fixture(scope="session")
async def localnet_accounts(hedera_client):
    """Provides a shop account and a user account."""
    print(f"\n🌱 Setting up {'Real' if has_local_node() else 'Primitive'} Localnet accounts...")
    shop_id, _ = await create_localnet_account(hedera_client, 0)
    user_id, user_key = await create_localnet_account(hedera_client, 1000)
    
    return {
        "shop_id": shop_id,
        "user_id": user_id,
        "user_key": user_key
    }
