"""Real integration tests on Hedera Localnet."""
import pytest
from agent.tools import check_balance
from tests.virtual_wallet import VirtualWallet, PaymentStatus
from config import settings

@pytest.mark.asyncio
async def test_check_balance_real_localnet(localnet_accounts):
    """Test check_balance against the local mirror node."""
    if settings.HEDERA_NETWORK != "localnet":
        pytest.skip("Only for localnet")
        
    # User should have 1000 HBAR from fixture
    result = check_balance.func(localnet_accounts["user_id"], 5.0)
    assert "Balance OK" in result
    assert "1000" in result

@pytest.mark.asyncio
async def test_real_transfer_on_localnet(hedera_client, localnet_accounts):
    """Test a real TransferTransaction on localnet using VirtualWallet."""
    if not hedera_client:
        pytest.skip("Only for localnet")
        
    wallet = VirtualWallet(
        account_id=localnet_accounts["user_id"],
        client=hedera_client,
        private_key=localnet_accounts["user_key"],
        initial_balance_hbar=1000.0,
        rejection_rate=0,
        timeout_rate=0,
        network_error_rate=0
    )
    
    # Process a real payment of 10 HBAR
    try:
        tx = await wallet.process_payment(localnet_accounts["shop_id"], 10.0, "Test Integration")
        print(f"\nOUTCOME: {tx.status}")
    except Exception as e:
        print(f"\nEXCEPTION DURING PROCESS: {e}")
        raise e
    
    assert tx.status == PaymentStatus.SUCCESS
    assert tx.tx_id is not None
    assert "@" in tx.tx_id  # Real Hedera TX ID format
    
    print(f"\n✅ Real Transfer Success: {tx.tx_id}")
    
    # Verify balance updated in mirror node (might need a short delay for indexer)
    import asyncio
    await asyncio.sleep(2)
    
    result = check_balance.func(localnet_accounts["user_id"], 1.0)
    assert "990" in result # 1000 - 10 = 990
