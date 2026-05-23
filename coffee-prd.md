# ☕ HBAR Coffee Shop — Product Requirements Document

**Version:** 1.0.0
**Bounty:** Week 1 — Fun Basic Hedera Agent
**Payout:** $500 in HBAR
**Deadline:** Sunday 23:59 UTC
**Stack:** Python · Hedera Agent Kit · Groq (LLaMA 3)

---

## 1. Overview

HBAR Coffee Shop is a conversational AI agent that simulates a real commercial coffee shop experience on the Hedera testnet. Users browse a menu, place orders in plain English, and pay in HBAR — all through a single chat interface. Every purchase triggers a real on-chain transaction, making it an end-to-end demo of payment-gated commerce on Hedera.

This project targets the Week 1 bounty: **Fun Basic Hedera Agent**. The goal is to ship something delightful, immediately understandable, and technically correct — not overbuilt.

### Why This Idea Wins

- **Universal mental model** — everyone understands buying coffee. Zero explanation needed in the demo video.
- **Real transaction loop** — order → pay HBAR → receive confirmation. Judges see the full commercial interaction.
- **Personality-driven** — the agent has a barista persona, making it fun and memorable vs. generic wallet demos.
- **Extensible** — the same architecture scales directly to Weeks 2–5 (plugins, MCP, policy constraints).

---

## 2. Goals & Non-Goals

### Goals

- Ship a working agent before Sunday 23:59 UTC
- Execute at least one real HBAR transaction on testnet per order
- Build on Hedera Agent Kit (Python) with a plugin integration
- Produce a clean, public GitHub repo with clear README
- Record and post a demo video on X
- Submit one piece of feedback on a Hedera AI Studio tool
- Lay groundwork for Weeks 2–5 (modular, not throwaway code)

### Non-Goals

- No mainnet deployment — testnet only for Week 1
- No frontend UI — terminal / CLI interface is sufficient
- No real money — all transactions use testnet HBAR (free)
- No multi-user sessions — single user per agent instance
- No persistent order history — in-memory state is fine for Week 1

---

## 3. User Flow

| # | Step | Detail |
|---|------|--------|
| 1 | Agent greets user | Barista persona introduces the shop, mentions HBAR payment, lists menu categories |
| 2 | User browses menu | User asks what's available; agent returns formatted menu with item names and HBAR prices |
| 3 | User places order | User says e.g. "I'll have a flat white and a blueberry muffin" |
| 4 | Agent confirms order | Agent repeats the order, shows total in HBAR, asks user to confirm |
| 5 | User confirms | User says "yes" / "confirm" / "pay" |
| 6 | HBAR transaction fires | Agent calls Hedera Agent Kit to transfer HBAR from user wallet to shop wallet on testnet |
| 7 | On-chain confirmation | Agent returns transaction ID and confirms payment on Hedera testnet |
| 8 | Order receipt | Agent delivers a fun receipt with transaction ID and a barista message |
| 9 | Loop continues | User can order again or ask for anything else |

---

## 4. The Menu

All prices in HBAR on testnet. Small enough to be fun, visible enough to confirm on-chain.

| Item | Category | Price (HBAR) |
|------|----------|-------------|
| Espresso | Coffee | 1 |
| Flat White | Coffee | 2 |
| Cappuccino | Coffee | 2 |
| Cold Brew | Coffee | 3 |
| Matcha Latte | Specials | 3 |
| Chai Latte | Specials | 2 |
| Blueberry Muffin | Food | 1 |
| Avocado Toast | Food | 3 |
| Croissant | Food | 1 |

---

## 5. Technical Architecture

### 5.1 Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.10+ |
| Framework | LangChain v1 + LangGraph |
| Agent Kit | `hedera-agent-kit` (PyPI) |
| LLM | Groq — LLaMA 3 70B (free tier) |
| Network | Hedera Testnet |
| Interface | Terminal / CLI |
| Plugin | Hedera Transfer Plugin (built-in) |
| Config | `python-dotenv` |

### 5.2 Project Structure

```
coffee-shop-agent/
├── main.py                  # Agent entrypoint
├── agent/
│   ├── __init__.py
│   ├── coffee_agent.py      # LangGraph agent definition
│   ├── tools.py             # Custom tools (menu lookup, order builder)
│   └── prompts.py           # System prompt / barista persona
├── config/
│   ├── menu.py              # Menu items & HBAR prices
│   └── settings.py          # Env var loading
├── .env                     # Credentials (never commit)
├── .env.example             # Template for GitHub
├── requirements.txt
└── README.md
```

### 5.3 Key Components

#### `coffee_agent.py`
LangGraph ReAct agent with Hedera Agent Kit tools injected. Maintains conversation state across turns. Handles the order → confirm → pay loop.

#### `tools.py`
- `get_menu()` — returns current menu with HBAR prices
- `build_order(items)` — validates items against menu, calculates total
- `process_payment(total_hbar)` — calls Hedera Agent Kit to execute HBAR transfer
- `get_transaction_status(tx_id)` — confirms transaction on Hedera testnet

#### `prompts.py`
System prompt that gives the agent a barista persona: friendly, slightly cheeky, knows the menu cold, always confirms before charging. Never initiates a transaction without explicit user confirmation.

#### Plugin
Uses the built-in **Hedera Transfer Plugin** from the Agent Kit. No custom plugin required for Week 1 — the transfer tool is the commercial interaction.

### 5.4 Agent Initialization Pattern

```python
from hedera_agent_kit import HederaAgentKit
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

llm = ChatGroq(model="llama3-70b-8192", temperature=0)
kit = HederaAgentKit(account_id=ACCOUNT_ID, private_key=PRIVATE_KEY, network="testnet")
tools = kit.get_tools() + [get_menu, build_order]  # mix kit tools + custom tools
agent = create_react_agent(llm, tools, state_modifier=SYSTEM_PROMPT)
```

---

## 6. Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| R-01 | Agent executes real HBAR transfer on testnet per order | MUST | ⬜ Todo |
| R-02 | Built on `hedera-agent-kit` Python package | MUST | ⬜ Todo |
| R-03 | Uses at least one plugin (Hedera Transfer Plugin) | MUST | ⬜ Todo |
| R-04 | Public GitHub repository with README | MUST | ⬜ Todo |
| R-05 | Demo video posted on X, stays live 90 days | MUST | ⬜ Todo |
| R-06 | One piece of feedback submitted on a Hedera AI Studio tool | MUST | ⬜ Todo |
| R-07 | Agent confirms order and total before charging | MUST | ⬜ Todo |
| R-08 | Transaction ID returned to user after payment | MUST | ⬜ Todo |
| R-09 | Hedera wallet address ready for bounty form submission | MUST | ⬜ Todo |
| R-10 | Agent has distinct barista persona — not a generic chatbot | SHOULD | ⬜ Todo |
| R-11 | README includes setup steps, `.env.example`, and demo link | SHOULD | ⬜ Todo |
| R-12 | Code is modular enough to extend in Weeks 2–5 | SHOULD | ⬜ Todo |
| R-13 | Error handling for failed or timed-out transactions | SHOULD | ⬜ Todo |
| R-14 | Agent handles multi-item orders in a single message | SHOULD | ⬜ Todo |
| R-15 | User can modify order before confirming payment | COULD | ⬜ Todo |

---

## 7. Environment Setup

### Prerequisites

- Python 3.10+
- Hedera testnet account → [portal.hedera.com/dashboard](https://portal.hedera.com/dashboard) (free, 2 min)
- Groq API key → [console.groq.com](https://console.groq.com) (free tier, 2 min)
- Git + GitHub account

> **You need TWO Hedera testnet accounts:** one for the user (pays) and one for the shop (receives). Both are free.

### Install

```bash
mkdir coffee-shop-agent && cd coffee-shop-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install hedera-agent-kit langchain langgraph langchain-groq python-dotenv
```

### `.env` File

```env
# Hedera — user wallet (from portal.hedera.com)
ACCOUNT_ID=0.0.XXXXXX
PRIVATE_KEY=0x...
HEDERA_NETWORK=testnet

# Hedera — shop wallet (second testnet account, receives payments)
SHOP_ACCOUNT_ID=0.0.YYYYYY

# Groq (from console.groq.com)
GROQ_API_KEY=gsk_...
```

### `.env.example` (commit this, not `.env`)

```env
ACCOUNT_ID=0.0.XXXXXX
PRIVATE_KEY=0x...
HEDERA_NETWORK=testnet
SHOP_ACCOUNT_ID=0.0.YYYYYY
GROQ_API_KEY=gsk_...
```

---

## 8. Agent Persona & Sample Dialogue

### Persona: Hera the HBAR Barista

- **Name:** Hera
- **Tone:** Friendly, slightly witty, never robotic
- **Rules:**
  - Always mentions HBAR prices naturally
  - Always confirms order + total before charging
  - Never initiates a transaction without explicit "yes" / "confirm" / "pay"
  - Celebrates completed payments with a fun receipt

### System Prompt (starting point)

```
You are Hera, the barista at HBAR Coffee — a coffee shop that runs on the Hedera network.
You take orders, confirm totals, and process payments in HBAR.

Rules:
- Always greet new customers warmly
- Show the menu clearly when asked
- Always confirm the order and total BEFORE processing any payment
- Only call process_payment() after the user explicitly confirms
- After payment, always show the transaction ID
- Keep responses concise and friendly — you're a barista, not a bank
```

### Sample Dialogue

```
USER:  Hi, what do you have?

HERA:  Welcome to HBAR Coffee! ☕ Here's today's menu:

       Coffee:   Espresso (1 ℏ) · Flat White (2 ℏ) · Cappuccino (2 ℏ) · Cold Brew (3 ℏ)
       Specials: Matcha Latte (3 ℏ) · Chai Latte (2 ℏ)
       Food:     Croissant (1 ℏ) · Blueberry Muffin (1 ℏ) · Avocado Toast (3 ℏ)

       What can I get you?

USER:  I'll take a flat white and a croissant

HERA:  Here's your order:
         • Flat White — 2 ℏ
         • Croissant  — 1 ℏ
         Total: 3 HBAR

       Shall I go ahead and charge your wallet?

USER:  Yes, pay

HERA:  Payment sent! ✅
       Transaction ID: 0.0.XXXXXX@1234567890.000
       3 HBAR transferred on Hedera testnet

       Your flat white and croissant are on their way. Enjoy! ☕🥐
```

---

## 9. Submission Checklist

Everything required before hitting Submit on the bounty form.

- [ ] Hedera testnet account created (portal.hedera.com)
- [ ] Groq API key obtained (console.groq.com)
- [ ] Shop wallet (second testnet account) created
- [ ] Agent executes real HBAR transfer end-to-end
- [ ] Transaction ID displayed after every payment
- [ ] GitHub repo is public with README and `.env.example`
- [ ] README has setup instructions and demo link
- [ ] Demo video recorded — show full order → payment → receipt flow
- [ ] Demo video posted on X with `@hedera` and `@hedera_devs` tags
- [ ] Feedback issue opened on `github.com/hashgraph/hedera-agent-kit-js` or `-py`
- [ ] Bounty form filled: project name, description, GitHub URL, demo URL, wallet address, feedback link
- [ ] Terms & conditions accepted on submission form

---

## 10. Weeks 2–5 Roadmap

Every decision in Week 1 should make the next week easier.

| Week | Bounty | What Changes on Top of Week 1 |
|------|--------|-------------------------------|
| Week 2 — $750 | Enterprise Agent + Plugin | Add a real-world plugin — e.g. Google Sheets logs every order, or Slack notifies a channel on purchase. Same agent, new integration. |
| Week 3 — $1,000 | MCP or x402 Agent | Wrap the payment tool in x402 protocol. Coffee shop becomes pay-per-query: pay HBAR to unlock the agent's response. Direct use of finance knowledge. |
| Week 4 — $1,000 | Hedera Commerce Agent | Add payment-gated menu tiers — premium items unlocked after payment threshold. Loyalty token on HTS. |
| Week 5 — $1,500 | Hedera Policy Agent | Policy constraints: max spend per session, HBAR vs USDC toggle, human-in-the-loop approval for orders over X HBAR. |

---

## 11. Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Hedera Agent Kit API changes before deadline | Medium | Pin exact package version in `requirements.txt`. Check GitHub issues before starting. |
| Groq rate limits during demo recording | Low | Use a short, scripted demo. Free tier is generous for a 60-second video. |
| Testnet congestion or outage | Low | Record demo when testnet is stable. Have a backup screen recording ready. |
| Time runs out before demo video | High | Build agent first, record demo last. Working agent with no video = disqualified. |
| Transaction fails silently | Medium | Always surface transaction ID or explicit error. Never assume success. |
