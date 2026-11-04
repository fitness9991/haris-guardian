"""Haris Guardian quickstart (Python): pay per call with USDC on Base or Solana via x402.

pip install "x402[httpx,evm,svm]"
export EVM_PRIVATE_KEY=0x...        # a Base wallet holding a little USDC (no ETH needed)
export SOLANA_PRIVATE_KEY=...       # and/or a base58 Solana key holding USDC (no SOL needed)
python quickstart.py DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
"""
import asyncio
import os
import sys

from x402 import x402Client
from x402.http.clients import x402HttpxClient

API = "https://haris-api.vercel.app"


def build_client() -> x402Client:
    client = x402Client()
    if os.getenv("EVM_PRIVATE_KEY"):
        from eth_account import Account
        from x402.mechanisms.evm.exact import register_exact_evm_client
        from x402.mechanisms.evm.signers import EthAccountSigner
        register_exact_evm_client(client, EthAccountSigner(Account.from_key(os.environ["EVM_PRIVATE_KEY"])))
    if os.getenv("SOLANA_PRIVATE_KEY"):
        from solders.keypair import Keypair
        from x402.mechanisms.svm.exact import register_exact_svm_client
        from x402.mechanisms.svm.signers import KeypairSigner
        register_exact_svm_client(client, KeypairSigner(Keypair.from_base58_string(os.environ["SOLANA_PRIVATE_KEY"])))
    return client


async def main(mint: str) -> None:
    async with x402HttpxClient(build_client(), timeout=60) as http:
        # Free tier (3/day per IP, no wallet needed):
        free = await http.get(f"{API}/v1/check/{mint}")
        print("free:", free.status_code, free.json() if free.status_code == 200 else free.text[:200])
        # Paid: $0.01 per check. The client answers the 402 with a signed USDC payment and retries.
        if os.getenv("EVM_PRIVATE_KEY") or os.getenv("SOLANA_PRIVATE_KEY"):
            r = await http.post(f"{API}/v1/paid/check", json={"mint": mint})
            print("paid:", r.status_code, r.json())


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"))
