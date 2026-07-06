import asyncio
import logging
import os
import random
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

# Config
RPC_URL = "https://rpc.testnet.arc.network"
WALLET   = os.getenv("WALLET_ADDRESS")
PK       = os.getenv("PRIVATE_KEY")
CONTRACT = "0x31B5ca34AD2E898b40DdE64CaFF2B569c8A65f81"

ABI = [
    {
        "inputs": [],
        "name": "recordActivity",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getMyStats",
        "outputs": [
            {"internalType": "uint256", "name": "count",    "type": "uint256"},
            {"internalType": "uint256", "name": "lastTime", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalActivities",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arc_onchain.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

def get_web3():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise ConnectionError("Gagal connect ke Arc Testnet")
    return w3

def send_record_activity(w3, contract, attempt=1):
    try:
        wallet = Web3.to_checksum_address(WALLET)
        nonce  = w3.eth.get_transaction_count(wallet)
        gas_price = w3.eth.gas_price

        txn = contract.functions.recordActivity().build_transaction({
            'from':     wallet,
            'nonce':    nonce,
            'gas':      100000,
            'gasPrice': gas_price,
            'chainId':  5042002,
        })

        signed = w3.eth.account.sign_transaction(txn, private_key=PK)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        if receipt.status == 1:
            log.info(f"✅ recordActivity SUCCESS | tx: {tx_hash.hex()}")
            log.info(f"   Arcscan: https://testnet.arcscan.app/tx/{tx_hash.hex()}")
            return tx_hash.hex()
        else:
            log.error(f"❌ Transaction reverted | tx: {tx_hash.hex()}")
            return None

    except Exception as e:
        log.error(f"❌ Error attempt {attempt}: {str(e)}")
        if attempt < 3:
            log.info("Retry in 10s...")
            import time; time.sleep(10)
            return send_record_activity(w3, contract, attempt + 1)
        return None

def check_stats(w3, contract):
    try:
        wallet = Web3.to_checksum_address(WALLET)
        count, last_time = contract.functions.getMyStats().call({'from': wallet})
        total = contract.functions.totalActivities().call()
        
        last_dt = datetime.fromtimestamp(last_time) if last_time > 0 else "Never"
        log.info(f"📊 Stats — My count: {count} | Last: {last_dt} | Contract total: {total}")
        return count
    except Exception as e:
        log.error(f"Stats error: {e}")
        return 0

async def run_daily(w3, contract, day, total_days):
    log.info("=" * 55)
    log.info(f"DAY {day}/{total_days} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info("=" * 55)

    # Cek stats dulu
    check_stats(w3, contract)

    # Jumlah call per hari (2-4x, random)
    calls = random.randint(2, 4)
    log.info(f"Plan: {calls} on-chain recordActivity calls hari ini")

    for i in range(1, calls + 1):
        delay = random.uniform(300, 900)  # 5-15 menit antar call
        log.info(f"Call {i}/{calls} — tunggu {delay/60:.1f} menit...")
        await asyncio.sleep(delay)
        
        tx = send_record_activity(w3, contract)
        if tx:
            log.info(f"   ✅ Call {i} done")
        else:
            log.warning(f"   ⚠️ Call {i} gagal, lanjut...")

    # Summary akhir hari
    log.info("\n--- End of Day Summary ---")
    check_stats(w3, contract)

async def main():
    log.info("🤖 Arc On-Chain Bot Starting...")
    log.info(f"Wallet  : {WALLET}")
    log.info(f"Contract: {CONTRACT}")

    w3 = get_web3()
    balance = w3.eth.get_balance(Web3.to_checksum_address(WALLET))
    log.info(f"Balance : {w3.from_wei(balance, 'ether'):.4f} ETH")

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT),
        abi=ABI
    )

    # Test 1 call dulu sebelum loop
    log.info("\n🧪 Test call pertama...")
    tx = send_record_activity(w3, contract)
    if not tx:
        log.error("Test gagal. Cek private key dan balance.")
        return

    log.info("✅ Test berhasil! Mulai continuous mode...")
    DAYS = 7

    for day in range(1, DAYS + 1):
        await run_daily(w3, contract, day, DAYS)
        
        if day < DAYS:
            sleep_sec = 86400 + random.uniform(-3600, 3600)
            log.info(f"\n💤 Sleep {sleep_sec/3600:.1f} jam sampai hari berikutnya...")
            await asyncio.sleep(sleep_sec)

    log.info("\n🎉 Selesai! Semua aktivitas sudah on-chain.")
    check_stats(w3, contract)

if __name__ == "__main__":
    asyncio.run(main())
