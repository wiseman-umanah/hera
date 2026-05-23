from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from hedera_agent_kit.langchain.toolkit import HederaLangchainToolkit
from hedera_agent_kit.plugins import core_account_query_plugin
from hedera_agent_kit.shared.configuration import Configuration, Context, AgentMode

from agent.tools import get_menu, calculate_order, check_balance, make_transfer_tool
from agent.prompts import SYSTEM_PROMPT
from config import settings


def build_agent(user_account_id: str, pay_session):
    """Build a per-session barista agent.

    pay_session: PaySession — routes payment requests to the user's wallet.
    No private key needed; the wallet signs everything.
    """
    # Use a lightweight client for the agent kit's query tools (no operator needed)
    from hiero_sdk_python import Client, Network
    client = Client(Network(network="testnet"))

    hedera_toolkit = HederaLangchainToolkit(
        client=client,
        configuration=Configuration(
            tools=[],
            plugins=[core_account_query_plugin],
            context=Context(
                mode=AgentMode.AUTONOMOUS,
                account_id=user_account_id,
            ),
        ),
    )

    pay_tool = make_transfer_tool(
        user_account_id=user_account_id,
        shop_account_id=settings.SHOP_ACCOUNT_ID,
        pay_session=pay_session,
    )

    all_tools = hedera_toolkit.get_tools() + [
        get_menu,
        calculate_order,
        check_balance,
        pay_tool,
    ]

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=settings.GROQ_API_KEY,
        temperature=0,
    )

    system_prompt = (
        SYSTEM_PROMPT
        + f"\n\nShop wallet (recipient for all payments): {settings.SHOP_ACCOUNT_ID}"
        + f"\nCustomer wallet: {user_account_id}"
    )

    return create_agent(
        model=llm,
        tools=all_tools,
        checkpointer=MemorySaver(),
        system_prompt=system_prompt,
    )
