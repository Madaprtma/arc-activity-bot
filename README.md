# arc-activity-bot
On-chain activity bot for Arc Testnet. Automates smart contract interactions to explore Arc's payment infrastructure built on Circle's stablecoin stack.

# ArcPay Agent

AI-powered autonomous payment agent built on Arc Testnet (Circle).

## Track
Track 4 — Agentic Economy (Stablecoin Commerce Stack Challenge)

## Overview
ArcPay Agent allows users to send USDC payments on Arc Testnet using
natural language commands. Built with Llama 3.1 (Groq) + Web3.py +
Streamlit.

## How it works
1. User types natural language instruction
2. Llama 3.1 parses intent and extracts payment details
3. Web3.py builds and signs the transaction
4. Transaction submitted to Arc Testnet
5. TX hash and Arcscan link returned to user

## Circle products used
- USDC (primary payment rail on Arc Testnet)
- Arc smart contracts (ArcDailyActivity deployed at
  0x31B5ca34AD2E898b40DdE64CaFF2B569c8A65f81)

## Architecture
User Input → Groq/Llama 3.1 (NLP) → Web3.py → Arc Testnet → Arcscan

## Setup
1. Clone repo
2. Install dependencies: pip install streamlit groq web3 python-dotenv
3. Create .env file with WALLET_ADDRESS, PRIVATE_KEY, GROQ_API_KEY
4. Run: python -m streamlit run arcpay_agent.py

## Example commands
- Check my balance
- Send 0.01 USDC to 0x123... for freelance work
- Pay 5 USDC to 0xabc...

## Circle Product Feedback
**Why USDC on Arc:** Arc provides deterministic finality and
dollar-denominated fees, making it ideal for autonomous agent payments.

**What worked well:** USDC as native gas token simplifies agent
payment logic — single token for both fees and transfers.

**What could be improved:** More Arc Testnet faucet options and
better error messages when transactions revert.

**Recommendations:** Native USDC transfer ABI would simplify
integration vs using raw ETH-style transfers.

## Tech stack
- Python 3.14
- Streamlit (UI)
- Groq API / Llama 3.1 8B (NLP)
- Web3.py (blockchain)
- Arc Testnet Chain ID 5042002