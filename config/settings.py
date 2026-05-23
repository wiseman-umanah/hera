import os
from dotenv import load_dotenv

load_dotenv()

SHOP_ACCOUNT_ID = os.getenv("SHOP_ACCOUNT_ID", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
WALLETCONNECT_PROJECT_ID = os.getenv("WALLETCONNECT_PROJECT_ID", "")


def validate():
    missing = [k for k, v in {
        "SHOP_ACCOUNT_ID": SHOP_ACCOUNT_ID,
        "GROQ_API_KEY": GROQ_API_KEY,
    }.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")
