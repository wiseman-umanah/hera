import os
from dotenv import load_dotenv

if "PYTEST_CURRENT_TEST" not in os.environ:
    load_dotenv()

SHOP_ACCOUNT_ID = os.getenv("SHOP_ACCOUNT_ID", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
WALLETCONNECT_PROJECT_ID = os.getenv("WALLETCONNECT_PROJECT_ID", "")

# Hedera Network Settings
HEDERA_NETWORK = os.getenv("HEDERA_NETWORK", "testnet")  # testnet, previewnet, mainnet, or localnet
MIRROR_NODE_URL = os.getenv("MIRROR_NODE_URL", "https://testnet.mirrornode.hedera.com")
HNODE_URL = os.getenv("HNODE_URL", "")  # Only needed for localnet

def validate():
    missing = [k for k, v in {
        "SHOP_ACCOUNT_ID": SHOP_ACCOUNT_ID,
        "GROQ_API_KEY": GROQ_API_KEY,
    }.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")
