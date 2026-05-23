"""A lightweight in-memory Hedera ledger and Mirror Node mock.
Runs without Docker and allows real SDK-like behavior in tests.
"""
import asyncio
from fastapi import FastAPI, HTTPException
import uvicorn
from threading import Thread
from typing import Dict

class PrimitiveLedger:
    def __init__(self):
        # account_id -> tinybars
        self.accounts: Dict[str, int] = {
            "0.0.2": 100_000_000_000,  # Default operator starts with 1000 HBAR
        }
        self.transactions = []

    def create_account(self, account_id: str, initial_balance_hbar: float):
        self.accounts[account_id] = int(initial_balance_hbar * 100_000_000)
        return account_id

    def transfer(self, from_id: str, to_id: str, amount_tinybars: int):
        if from_id not in self.accounts:
            raise ValueError(f"Sender {from_id} not found")
        if self.accounts[from_id] < amount_tinybars:
            raise ValueError("Insufficient balance")
        
        self.accounts.setdefault(to_id, 0)
        self.accounts[from_id] -= amount_tinybars
        self.accounts[to_id] += amount_tinybars
        return f"primitive-tx-{len(self.transactions) + 1}"

# Global ledger instance
ledger = PrimitiveLedger()

app = FastAPI()

@app.get("/api/v1/accounts/{account_id}")
async def get_account(account_id: str):
    if account_id not in ledger.accounts:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "account": account_id,
        "balance": {"balance": ledger.accounts[account_id]},
        "deleted": False
    }

def start_primitive_node(port=5551):
    """Start the mock mirror node in a background thread."""
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, daemon=True)
    thread.start()
    return server
