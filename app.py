import asyncio
import re
import uuid
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from config import settings

app = FastAPI(title="HBAR Coffee Shop")
app.mount("/static", StaticFiles(directory="static"), name="static")

TINYBARS_PER_HBAR = 100_000_000
MIRROR_NODE = "https://testnet.mirrornode.hedera.com/api/v1"

TX_ID_RE = re.compile(r"\b(\d+\.\d+\.\d+)[@-](\d+)[.\-](\d+)\b")


@app.on_event("startup")
async def startup():
    settings.validate()


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/api/balance/{account_id}")
async def get_balance(account_id: str):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{MIRROR_NODE}/accounts/{account_id}", timeout=8)
            r.raise_for_status()
            tinybars = r.json()["balance"]["balance"]
            return {"hbar": round(tinybars / TINYBARS_PER_HBAR, 4)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)


@app.get("/api/config")
async def get_config():
    """Public config the frontend needs at startup."""
    return {
        "shop_account_id": settings.SHOP_ACCOUNT_ID,
        "wc_project_id": settings.WALLETCONNECT_PROJECT_ID,
    }


def extract_tx_id(text: str) -> str | None:
    m = TX_ID_RE.search(text)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def hashscan_url(tx_id: str) -> str:
    return f"https://hashscan.io/testnet/transaction/{tx_id}"


async def fetch_balance(account_id: str) -> float | None:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{MIRROR_NODE}/accounts/{account_id}", timeout=8)
            r.raise_for_status()
            return round(r.json()["balance"]["balance"] / TINYBARS_PER_HBAR, 4)
    except Exception:
        return None


class PaySession:
    """Routes pay requests from the agent tool to the connected wallet via WebSocket."""

    def __init__(self, ws: WebSocket):
        self._ws = ws
        self._pending: dict[str, asyncio.Event] = {}
        self._results: dict[str, str | None] = {}

    async def request_payment(
        self,
        from_account: str,
        to_account: str,
        amount_hbar: float,
        description: str,
    ) -> str:
        """Ask the frontend wallet to execute a transfer. Returns the TX ID."""
        request_id = str(uuid.uuid4())
        event = asyncio.Event()
        self._pending[request_id] = event

        await self._ws.send_json({
            "type": "pay",
            "request_id": request_id,
            "from_account": from_account,
            "to_account": to_account,
            "amount_hbar": amount_hbar,
            "description": description,
        })

        try:
            await asyncio.wait_for(event.wait(), timeout=120)
            result = self._results.pop(request_id, None)
            if result is None:
                raise RuntimeError("Payment was rejected or timed out.")
            return result
        except asyncio.TimeoutError:
            raise RuntimeError("Wallet did not respond within 120 seconds.")
        finally:
            self._pending.pop(request_id, None)

    def resolve(self, request_id: str, tx_id: str | None):
        self._results[request_id] = tx_id
        if request_id in self._pending:
            self._pending[request_id].set()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    pay_session = PaySession(websocket)
    user_msg_queue: asyncio.Queue[dict] = asyncio.Queue()

    async def ws_reader():
        """Continuously read incoming WS messages and route them."""
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                if msg_type == "payment_done":
                    pay_session.resolve(data["request_id"], data.get("tx_id"))
                elif msg_type == "payment_rejected":
                    pay_session.resolve(data["request_id"], None)
                else:
                    await user_msg_queue.put(data)
        except Exception:
            pass

    reader_task = asyncio.create_task(ws_reader())

    try:
        # First message: wallet sends its account_id after connecting
        init = await user_msg_queue.get()
        account_id = init.get("account_id", "").strip()

        if not account_id:
            await websocket.send_json({"type": "error", "text": "No account ID received."})
            return

        await websocket.send_json({"type": "status", "text": "Brewing your session…"})

        from agent.coffee_agent import build_agent
        try:
            agent = build_agent(account_id, pay_session)
        except Exception as e:
            await websocket.send_json({"type": "error", "text": f"Agent error: {e}"})
            return

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        balance = await fetch_balance(account_id)
        if balance is not None:
            await websocket.send_json({"type": "balance", "hbar": balance})

        # Greeting
        response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "hello"}]},
            config=config,
        )
        reply = response["messages"][-1].content
        await websocket.send_json({"type": "message", "text": reply})

        # Chat loop
        while True:
            data = await user_msg_queue.get()
            user_text = data.get("text", "").strip()
            if not user_text:
                continue

            await websocket.send_json({"type": "typing"})

            response = await agent.ainvoke(
                {"messages": [{"role": "user", "content": user_text}]},
                config=config,
            )
            reply = response["messages"][-1].content
            tx_id = extract_tx_id(reply)

            await websocket.send_json({"type": "message", "text": reply})

            if tx_id:
                await websocket.send_json({
                    "type": "receipt",
                    "tx_id": tx_id,
                    "url": hashscan_url(tx_id),
                })
                # Wait for the mirror node to index the transaction before polling balance
                await asyncio.sleep(5)
                balance = await fetch_balance(account_id)
                if balance is not None:
                    await websocket.send_json({"type": "balance", "hbar": balance})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "text": str(e)})
        except Exception:
            pass
    finally:
        reader_task.cancel()
