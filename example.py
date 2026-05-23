# main.py
import asyncio
import os

from dotenv import load_dotenv
from hedera_agent_kit.langchain.toolkit import HederaLangchainToolkit
from hedera_agent_kit.plugins import (
    core_account_plugin,
    core_account_query_plugin,
    core_token_plugin,
    core_consensus_plugin,
)
from hedera_agent_kit.shared.configuration import Configuration, Context, AgentMode
from hiero_sdk_python import Client, Network, AccountId, PrivateKey
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


async def main():
    # Hedera client setup (Testnet by default)
    import asyncio
    account_id = AccountId.from_string(os.getenv("ACCOUNT_ID"))
    private_key = PrivateKey.from_string(os.getenv("PRIVATE_KEY"))
    client = Client(Network(network="testnet"))
    client.set_operator(account_id, private_key)

    # Prepare Hedera toolkit
    hedera_toolkit = HederaLangchainToolkit(
        client=client,
        configuration=Configuration(
            tools=[],  # Empty = load all tools from plugins
            plugins=[
                core_account_plugin,
                core_account_query_plugin,
                core_token_plugin,
                core_consensus_plugin,
            ],
            context=Context(
                mode=AgentMode.AUTONOMOUS,
                account_id=str(account_id),
            ),
        ),
    )

    tools = hedera_toolkit.get_tools()

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    agent = create_agent(
        model=llm,
        tools=tools,
        checkpointer=MemorySaver(),
        system_prompt="You are a helpful assistant with access to Hedera blockchain tools and plugin tools",
    )

    print("Sending a message to the agent...")

    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what's my balance?"}]},
        config={"configurable": {"thread_id": "1"}},
    )

    final_message_content = response["messages"][-1].content
    print("\n--- Agent Response ---")
    print(final_message_content)
    print("----------------------")


if __name__ == "__main__":
    asyncio.run(main())
