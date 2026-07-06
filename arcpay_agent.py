import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from web3 import Web3

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WALLET = os.getenv("WALLET_ADDRESS")
PK = os.getenv("PRIVATE_KEY")
RPC_URL = "https://rpc.testnet.arc.network"
CHAIN_ID = 5042002

groq_client = Groq(api_key=GROQ_API_KEY)
w3 = Web3(Web3.HTTPProvider(RPC_URL))

def parse_payment_intent(user_input: str) -> dict:
    prompt = f"""
You are a payment AI agent for Arc blockchain. Extract payment details from the instruction.
Return ONLY valid JSON, no explanation, no markdown.

Instruction: "{user_input}"

Return format:
{{"action": "send_payment" or "check_balance" or "unknown", "amount": <number or null>, "recipient": "<address or null>", "description": "<purpose or null>"}}
"""
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=200
    )
    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1].replace("json", "").strip()
    return json.loads(raw)

def get_balance() -> float:
    wallet = Web3.to_checksum_address(WALLET)
    bal = w3.eth.get_balance(wallet)
    return float(w3.from_wei(bal, "ether"))

def send_payment(to_address: str, amount: float) -> dict:
    try:
        wallet = Web3.to_checksum_address(WALLET)
        to_addr = Web3.to_checksum_address(to_address)
        amount_wei = w3.to_wei(amount, "ether")
        nonce = w3.eth.get_transaction_count(wallet)
        gas_price = w3.eth.gas_price
        txn = {
            "from": wallet,
            "to": to_addr,
            "value": amount_wei,
            "nonce": nonce,
            "gas": 21000,
            "gasPrice": gas_price,
            "chainId": CHAIN_ID,
        }
        signed = w3.eth.account.sign_transaction(txn, private_key=PK)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt.status == 1:
            return {"success": True, "tx_hash": tx_hash.hex(), "arcscan": f"https://testnet.arcscan.app/tx/{tx_hash.hex()}"}
        else:
            return {"success": False, "error": "Transaction reverted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── UI ──────────────────────────────────────────────

st.set_page_config(page_title="ArcPay Agent", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .main { background: #0a0a0a; }
    .block-container { padding: 2rem 3rem; max-width: 1200px; }
    
    .hero-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3);
        color: #a5b4fc; padding: 4px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 500; margin-bottom: 16px;
    }
    .hero-title {
        font-size: 42px; font-weight: 700; margin: 0 0 12px;
        background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }
    .hero-sub {
        color: #6b7280; font-size: 16px; margin: 0 0 32px;
    }
    
    .stat-card {
        background: #111111; border: 1px solid #1f1f1f;
        border-radius: 12px; padding: 20px 24px;
    }
    .stat-label { color: #6b7280; font-size: 12px; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 8px; }
    .stat-value { color: #ffffff; font-size: 28px; font-weight: 700; font-family: monospace; }
    .stat-sub { color: #4b5563; font-size: 12px; margin-top: 4px; }
    
    .status-dot-green { display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; margin-right: 6px; box-shadow: 0 0 6px #10b981; }
    .status-dot-red { display: inline-block; width: 8px; height: 8px; background: #ef4444; border-radius: 50%; margin-right: 6px; }
    
    .tx-card {
        background: #0d1117; border: 1px solid #1f2937;
        border-radius: 10px; padding: 16px 20px; margin-bottom: 10px;
    }
    .tx-hash { font-family: monospace; color: #6366f1; font-size: 13px; }
    .tx-amount { color: #10b981; font-size: 18px; font-weight: 700; }
    .tx-meta { color: #6b7280; font-size: 12px; }
    
    .chat-container {
        background: #0f0f0f; border: 1px solid #1f1f1f;
        border-radius: 16px; padding: 0; overflow: hidden;
    }
    .chat-header {
        background: #111111; border-bottom: 1px solid #1f1f1f;
        padding: 16px 20px; display: flex; align-items: center; gap: 10px;
    }
    
    .stChatMessage { background: transparent !important; }
    .stChatInputContainer { background: #111111 !important; border: 1px solid #1f1f1f !important; border-radius: 12px !important; }
    
    [data-testid="stSidebar"] { background: #080808 !important; border-right: 1px solid #1a1a1a; }
    
    .tag {
        display: inline-block; background: rgba(99,102,241,0.1);
        border: 1px solid rgba(99,102,241,0.2); color: #a5b4fc;
        padding: 2px 10px; border-radius: 6px; font-size: 11px; margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ArcPay")
    st.markdown("---")
    
    connected = w3.is_connected()
    if connected:
        st.markdown('<span class="status-dot-green"></span> **Arc Testnet**', unsafe_allow_html=True)
        bal = get_balance()
        st.markdown(f"""
        <div class="stat-card" style="margin-top:12px">
            <div class="stat-label">Balance</div>
            <div class="stat-value">{bal:.4f}</div>
            <div class="stat-sub">USDC on Arc Testnet</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("**Wallet**")
        st.code(f"{WALLET[:6]}...{WALLET[-4:]}", language=None)
        st.caption(f"Chain ID: {CHAIN_ID}")
    else:
        st.markdown('<span class="status-dot-red"></span> **Disconnected**', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**Quick commands**")
    st.markdown("""
    ```
    Check my balance
    
    Send 0.01 USDC to 0x123...
    
    Pay 5 USDC to 0xabc...
    for freelance work
    ```
    """)
    
    st.markdown("---")
    st.caption("Built for Stablecoin Commerce Stack Challenge")
    st.caption("Track 4 · Agentic Economy · Arc (Circle)")

# Main content
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("""
    <div class="hero-badge">⚡ Powered by Llama 3.1 + Arc Testnet</div>
    <div class="hero-title">ArcPay Agent</div>
    <div class="hero-sub">Autonomous AI payment agent built on Circle's stablecoin infrastructure</div>
    """, unsafe_allow_html=True)

with col2:
    if connected:
        st.markdown(f"""
        <div class="stat-card" style="text-align:right">
            <div class="stat-label">Live balance</div>
            <div class="stat-value" style="font-size:22px">{get_balance():.4f} USDC</div>
            <div class="stat-sub">Arc Testnet · Chain {CHAIN_ID}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Tags
st.markdown("""
<span class="tag">Natural Language</span>
<span class="tag">On-chain Payments</span>
<span class="tag">USDC</span>
<span class="tag">Arc Testnet</span>
<span class="tag">Circle Infrastructure</span>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tx_history" not in st.session_state:
    st.session_state.tx_history = []

# Tabs
tab1, tab2 = st.tabs(["Chat", "Transaction history"])

with tab1:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Type a payment instruction...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    intent = parse_payment_intent(user_input)
                    action = intent.get("action")

                    if action == "check_balance":
                        bal = get_balance()
                        response = f"**Balance:** `{bal:.6f} USDC` on Arc Testnet\n\nChain ID: `{CHAIN_ID}` · Wallet: `{WALLET[:10]}...{WALLET[-4:]}`"

                    elif action == "send_payment":
                        amount = intent.get("amount")
                        recipient = intent.get("recipient")
                        desc = intent.get("description") or "payment"

                        if not amount or not recipient:
                            response = "Please specify amount and recipient.\n\nExample: `Send 0.01 USDC to 0x123...`"
                        elif not recipient.startswith("0x") or len(recipient) != 42:
                            response = f"Invalid address: `{recipient}`\n\nPlease provide a valid 42-character address."
                        else:
                            with st.spinner(f"Sending {amount} USDC to {recipient[:10]}..."):
                                result = send_payment(recipient, float(amount))

                            if result["success"]:
                                response = f"""**Payment sent**

| Field | Value |
|-------|-------|
| Amount | `{amount} USDC` |
| To | `{recipient}` |
| Purpose | {desc} |
| TX Hash | `{result['tx_hash'][:20]}...` |

[View on Arcscan]({result['arcscan']})"""

                                st.session_state.tx_history.append({
                                    "time": datetime.now().strftime("%H:%M:%S"),
                                    "amount": amount,
                                    "to": recipient,
                                    "purpose": desc,
                                    "tx_hash": result["tx_hash"],
                                    "arcscan": result["arcscan"],
                                    "status": "success"
                                })
                            else:
                                response = f"**Payment failed**\n\n`{result['error']}`"
                    else:
                        response = "I can help you:\n- **Check balance** — `Check my balance`\n- **Send payment** — `Send 0.01 USDC to 0x123...`"

                except json.JSONDecodeError:
                    response = "Could not parse instruction. Try: `Send 0.01 USDC to 0x123...`"
                except Exception as e:
                    response = f"Error: `{str(e)}`"

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

with tab2:
    if not st.session_state.tx_history:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color: #4b5563;">
            <div style="font-size:32px; margin-bottom:12px">📭</div>
            <div style="font-size:16px; font-weight:500; color:#6b7280">No transactions yet</div>
            <div style="font-size:14px; margin-top:8px">Send a payment to see it here</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        total = sum(float(t["amount"]) for t in st.session_state.tx_history)
        st.markdown(f"**{len(st.session_state.tx_history)} transactions** · Total: `{total:.6f} USDC`")
        st.markdown("---")
        
        for tx in reversed(st.session_state.tx_history):
            st.markdown(f"""
            <div class="tx-card">
                <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:8px">
                    <div class="tx-amount">+{tx['amount']} USDC</div>
                    <div style="background:#052e16; color:#10b981; padding:2px 10px; border-radius:20px; font-size:11px">Success</div>
                </div>
                <div class="tx-hash">{tx['tx_hash'][:20]}...</div>
                <div class="tx-meta" style="margin-top:6px">
                    To: {tx['to'][:16]}... · {tx['purpose']} · {tx['time']}
                </div>
                <div style="margin-top:8px">
                    <a href="{tx['arcscan']}" style="color:#6366f1; font-size:12px; text-decoration:none">
                        View on Arcscan →
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)
