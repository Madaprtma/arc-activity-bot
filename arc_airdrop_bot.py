import json
import random
import time
import logging
import os
import asyncio
from datetime import datetime
from typing import List, Optional
from web3 import Web3
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Config
ARC_RPC = "https://rpc.testnet.arc.network"

class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class ActivityType(Enum):
    DAILY_GM = "daily_gm"
    STABLECOIN_SWAP = "swap"
    TOKEN_TRANSFER = "transfer"
    NFT_MINT = "nft_mint"

@dataclass
class Activity:
    timestamp: datetime
    activity_type: ActivityType
    protocol: str
    amount_usdc: float = 0.0
    gas_used: float = 0.0
    status: str = "pending"
    notes: str = ""

class ArcAirdropBot:
    def __init__(self, wallet_address: str, private_key: str, risk_level: RiskLevel = RiskLevel.MODERATE):
        self.wallet_address = Web3.to_checksum_address(wallet_address)
        self.private_key = private_key
        self.risk_level = risk_level
        self.w3 = Web3(Web3.HTTPProvider(ARC_RPC))
        
        if not self.w3.is_connected():
            raise ConnectionError("Gagal connect ke Arc Testnet")
        
        print(f"Connected to Arc Testnet (Chain ID: {self.w3.eth.chain_id})")
        print(f"Wallet: {self.wallet_address}")
        
        balance = self.w3.eth.get_balance(self.wallet_address)
        print(f"Balance: {self.w3.from_wei(balance, 'ether')} ETH")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('arc_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.activities: List[Activity] = []
    
    def _daily_count(self):
        counts = {RiskLevel.LOW: (2,3), RiskLevel.MODERATE: (4,6), RiskLevel.AGGRESSIVE: (7,10)}
        lo, hi = counts[self.risk_level]
        return random.randint(lo, hi)
    
    async def perform_daily_gm(self):
        self.logger.info("Performing daily GM...")
        await asyncio.sleep(random.uniform(1, 2))
        
        activity = Activity(
            timestamp=datetime.now(),
            activity_type=ActivityType.DAILY_GM,
            protocol="Arc_Core",
            status="success",
            notes="Daily GM recorded"
        )
        self.activities.append(activity)
        self.logger.info("GM done!")
        return True
    
    async def perform_swap(self):
        amounts = {RiskLevel.LOW: [5,10,15], RiskLevel.MODERATE: [10,25,50], RiskLevel.AGGRESSIVE: [25,50,100]}
        amount = random.choice(amounts[self.risk_level])
        direction = random.choice(["USDC->EURC", "EURC->USDC"])
        
        self.logger.info(f"Simulating swap: {amount} {direction}...")
        await asyncio.sleep(random.uniform(2, 4))
        
        activity = Activity(
            timestamp=datetime.now(),
            activity_type=ActivityType.STABLECOIN_SWAP,
            protocol="DEX_Arc",
            amount_usdc=float(amount),
            gas_used=round(random.uniform(0.5, 2.0), 4),
            status="success",
            notes=f"Swap {direction} amount {amount}"
        )
        self.activities.append(activity)
        self.logger.info(f"Swap done: {direction}")
        return True
    
    async def perform_transfer(self):
        amount = round(random.uniform(5, 20), 2)
        self.logger.info(f"Simulating transfer: {amount} USDC...")
        await asyncio.sleep(random.uniform(1, 3))
        
        activity = Activity(
            timestamp=datetime.now(),
            activity_type=ActivityType.TOKEN_TRANSFER,
            protocol="Core_Arc",
            amount_usdc=amount,
            gas_used=round(random.uniform(0.1, 0.5), 4),
            status="success",
            notes=f"Transfer {amount} USDC"
        )
        self.activities.append(activity)
        self.logger.info(f"Transfer done: {amount} USDC")
        return True
    
    async def run_daily_cycle(self):
        self.logger.info("=" * 50)
        self.logger.info(f"Starting daily cycle | Risk: {self.risk_level.value}")
        self.logger.info("=" * 50)
        
        task_pool = [self.perform_daily_gm, self.perform_swap, self.perform_transfer]
        count = self._daily_count()
        
        for i in range(count):
            fn = random.choice(task_pool)
            delay = random.uniform(10, 30)  # 10-30 detik untuk test
            self.logger.info(f"Activity {i+1}/{count} — delay {delay:.0f}s...")
            await asyncio.sleep(delay)
            await fn()
        
        self._print_summary()
    
    async def run_continuous(self, days: int = 7):
        self.logger.info(f"Running for {days} days...")
        for day in range(1, days + 1):
            self.logger.info(f"\n=== DAY {day}/{days} ===")
            await self.run_daily_cycle()
            if day < days:
                sleep_hrs = 24 + random.uniform(-1, 1)
                self.logger.info(f"Sleeping {sleep_hrs:.1f} hours...")
                await asyncio.sleep(sleep_hrs * 3600)
    
    def _print_summary(self):
        total = len(self.activities)
        protocols = len(set(a.protocol for a in self.activities))
        volume = sum(a.amount_usdc for a in self.activities)
        
        print("\n" + "=" * 50)
        print("DAILY SUMMARY")
        print("=" * 50)
        print(f"Total Activities : {total}")
        print(f"Protocols Used   : {protocols}")
        print(f"Total Volume     : {volume:.2f} USDC")
        print("=" * 50)
    
    def export_json(self, filename="arc_activities.json"):
        data = {
            "wallet": self.wallet_address,
            "risk_level": self.risk_level.value,
            "total": len(self.activities),
            "activities": [
                {
                    "time": a.timestamp.isoformat(),
                    "type": a.activity_type.value,
                    "protocol": a.protocol,
                    "amount": a.amount_usdc,
                    "status": a.status,
                    "notes": a.notes
                } for a in self.activities
            ]
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Exported to {filename}")


async def main():
    load_dotenv()
    
    wallet = os.getenv("WALLET_ADDRESS")
    pk = os.getenv("PRIVATE_KEY")
    
    if not wallet or not pk or pk == "your_actual_private_key_here":
        print("ERROR: Isi WALLET_ADDRESS dan PRIVATE_KEY di file .env dulu!")
        return
    
    bot = ArcAirdropBot(
        wallet_address=wallet,
        private_key=pk,
        risk_level=RiskLevel.MODERATE
    )
    
    print("\nMode: Single daily cycle test")
    await bot.run_daily_cycle()
    bot.export_json()

if __name__ == "__main__":
    asyncio.run(main())
