import httpx
from langchain_core.tools import tool, StructuredTool
from config.menu import MENU
from config import settings

TINYBARS_PER_HBAR = 100_000_000
PORTAL_URL = "https://portal.hedera.com/dashboard"


def make_transfer_tool(user_account_id: str, shop_account_id: str, pay_session):
    """Return an async LangChain tool that requests payment via the user's connected wallet."""

    async def _pay(amount_hbar: float, order_description: str = "") -> str:
        """Transfer HBAR from the customer's wallet to the shop to pay for an order.

        Args:
            amount_hbar: Amount of HBAR to transfer.
            order_description: Short description shown in the wallet approval popup.
        """
        try:
            tx_id = await pay_session.request_payment(
                from_account=user_account_id,
                to_account=shop_account_id,
                amount_hbar=amount_hbar,
                description=order_description or "HBAR Coffee Shop",
            )
            return (
                f"Payment of {amount_hbar}ℏ confirmed on-chain. "
                f"TRANSACTION_ID: {tx_id}"
            )
        except Exception as e:
            return f"Payment failed: {e}"

    return StructuredTool.from_function(
        coroutine=_pay,
        name="transfer_hbar_tool",
        description=(
            "Transfer HBAR from the customer's connected wallet to the coffee shop. "
            "Only call this AFTER the customer explicitly confirms their order. "
            "Args: amount_hbar (float), order_description (str)."
        ),
    )


@tool
def check_balance(account_id: str, required_hbar: float) -> str:
    """Check if an account has enough HBAR for a purchase before attempting payment.

    Args:
        account_id: The Hedera account ID (e.g. 0.0.12345)
        required_hbar: The amount of HBAR needed
    """
    try:
        url = f"{settings.MIRROR_NODE_URL}/api/v1/accounts/{account_id}"
        resp = httpx.get(url, timeout=8)
        resp.raise_for_status()
        tinybars = resp.json()["balance"]["balance"]
        balance = tinybars / TINYBARS_PER_HBAR
    except Exception as e:
        return f"Could not fetch balance: {e}. Proceeding with payment attempt."

    if balance < required_hbar:
        short = required_hbar - balance
        return (
            f"Insufficient balance. You have {balance:.2f}ℏ but need {required_hbar}ℏ "
            f"(short by {short:.2f}ℏ). "
            f"Top up at {PORTAL_URL} and come back!"
        )
    return f"Balance OK — you have {balance:.2f}ℏ, order costs {required_hbar}ℏ. Proceeding with payment."


@tool
def get_menu() -> str:
    """Return the full HBAR Coffee Shop menu with prices in HBAR."""
    lines = ["☕ HBAR Coffee Shop Menu\n"]
    by_category: dict[str, list] = {}
    for item, info in MENU.items():
        by_category.setdefault(info["category"], []).append(
            f"  {item.title()} — {info['price_hbar']}ℏ"
        )
    for category, items in by_category.items():
        lines.append(f"{category}:")
        lines.extend(items)
        lines.append("")
    return "\n".join(lines)


@tool
def calculate_order(items: list[str]) -> str:
    """Calculate the total HBAR cost for a list of menu items.

    Args:
        items: List of item names (e.g. ["flat white", "croissant"])
    """
    found = []
    not_found = []
    total = 0

    for raw in items:
        key = raw.strip().lower()
        if key in MENU:
            found.append((raw.title(), MENU[key]["price_hbar"]))
            total += MENU[key]["price_hbar"]
        else:
            not_found.append(raw)

    if not_found:
        return f"Sorry, I don't have: {', '.join(not_found)}. Try get_menu to see what's available."

    lines = ["Your order:"]
    for name, price in found:
        lines.append(f"  {name} — {price}ℏ")
    lines.append(f"\nTotal: {total}ℏ")
    lines.append("\nReply 'confirm' or 'yes' to pay, or let me know if you'd like to change anything.")
    return "\n".join(lines)
