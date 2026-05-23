"""Utilities for interacting with Hedera Localnet in tests."""
import os
from hiero_sdk_python import AccountId, PrivateKey, Client

# Standard Hedera Localnet operator details
LOCALNET_OPERATOR_ID = "0.0.2"
LOCALNET_OPERATOR_KEY = "302e020100300506032b65700422042091132178e721ef634027d091010023a1a361bc41a32948c2b74070a75d1d6438"
LOCALNET_HNODE_URL = "127.0.0.1:50211"
LOCALNET_MIRROR_URL = "http://127.0.0.1:5551"

def get_localnet_client():
    """Create a Hedera client configured for Localnet."""
    network = {LOCALNET_HNODE_URL: AccountId.from_string("0.0.3")}
    client = Client(network)
    client.set_mirror_network(["127.0.0.1:5551"])
    client.set_operator(
        AccountId.from_string(LOCALNET_OPERATOR_ID),
        PrivateKey.from_string(LOCALNET_OPERATOR_KEY)
    )
    return client

async def create_localnet_account(client, initial_balance_hbar=1000):
    """Create a new account on localnet for testing."""
    from hiero_sdk_python import AccountCreateTransaction, Hbar
    
    new_key = PrivateKey.generate_ed25519()
    resp = await AccountCreateTransaction() \
        .set_key(new_key.public_key) \
        .set_initial_balance(Hbar.from_tinybars(int(initial_balance_hbar * 100_000_000))) \
        .execute(client)
    
    receipt = await resp.get_receipt(client)
    return receipt.account_id.to_string(), new_key.to_string()
