<img src="logo.png" width="120" alt="Haris Guardian logo">

# Haris Guardian — Solana token risk check (MCP + REST + x402)

Read-only scam/rug-risk checks for Solana SPL and Token-2022 tokens. Give it a mint address; get a **0–100 risk score (higher = riskier)**, a verdict, and plain-English reasons. It never signs, trades, or holds keys.

## What it checks
- Mint and freeze authority
- Token-2022 traps: permanent delegate, transfer hooks, transfer fees
- Holder concentration
- Liquidity, LP burn/lock %, Streamflow locks
- Simulated buy + sell (honeypot test)

## Endpoints
| Interface | URL |
|---|---|
| MCP (streamable-http) | `https://haris-api.vercel.app/mcp` — tools `check_solana_token`, `diff_solana_token`, `deep_check_solana_token`, `batch_check_solana_tokens` |
| REST (free, 3/day) | `GET https://haris-api.vercel.app/v1/check/{mint}` |
| REST (paid, x402) | `POST https://haris-api.vercel.app/v1/paid/check` · `GET /v1/paid/check/{mint}` |
| Deep check (x402) | `POST https://haris-api.vercel.app/v1/paid/deep-check` `{"mint"}` |
| Batch check (x402) | `POST https://haris-api.vercel.app/v1/paid/batch-check` `{"mints": [up to 20]}` |
| Watch/diff (x402) | `POST https://haris-api.vercel.app/v1/paid/diff` `{"mint", "previous"}` |
| OpenAPI | https://haris-api.vercel.app/openapi.json |
| Docs | https://haris-api.vercel.app/docs |
| llms.txt | https://haris-api.vercel.app/llms.txt |
| A2A agent card | https://haris-api.vercel.app/.well-known/agent.json |

## Pricing
- 3 free checks per day per IP.
- After that: **$0.01 USDC per check via x402, on Solana or Base** (HTTP 402 → pay → retry). Every 402 lists both options; pay with whichever chain you hold USDC on:
  - Base (`eip155:8453`, USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, exact / EIP-3009): pays `0xCf2187a039c9ac286Ee43ECc46cBc6DaEB4Fa633`
  - Solana (`solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp`, USDC `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`): pays `7ZpBTGZ7mBm81esAq77FFm293zAuGM3Hi249fKPnVDfJ`
  - The facilitator pays network fees on both chains, so you need USDC only.
- **Deep check $0.10**: holder concentration (top1/top5/top10 %), top wallets linked by a shared funder (bundles/insiders), creator-funded and fresh wallets, LP lock/burn, authorities, score + reasons.
- **Batch check $0.10 per batch** of up to 20 mints (charged only if at least one mint is checked).
- **Watch/diff $0.02**: send a previous result, get alerts on what changed (authority re-enabled, LP unlocked, liquidity pulled, sell blocked). Stateless.
- Failed calls are never charged. See [docs/API.md](docs/API.md).

## Quick start

**1. Free, no wallet** (3 checks per UTC day per IP):

```bash
curl https://haris-api.vercel.app/v1/check/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```

**2. Paid, $0.01 USDC per check via x402** on Solana or Base. Unpaid calls get HTTP 402 with one `accepts[]` entry per chain;
an x402 client signs a USDC payment and retries. Your wallet needs USDC only (the facilitator pays network fees), and a
check that fails is never charged.

```bash
curl -i -X POST https://haris-api.vercel.app/v1/paid/check -H 'content-type: application/json' -d '{"mint":"DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"}'
# -> 402, v1 challenge in the body, v2 challenge base64 in the PAYMENT-REQUIRED header
```

| Chain | Network (CAIP-2) | Asset | payTo |
|---|---|---|---|
| Base | `eip155:8453` | USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | `0xCf2187a039c9ac286Ee43ECc46cBc6DaEB4Fa633` |
| Solana | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | USDC `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` | `7ZpBTGZ7mBm81esAq77FFm293zAuGM3Hi249fKPnVDfJ` |

**Python** (`pip install "x402[httpx,evm,svm]"`):

```python
import asyncio, os
from x402 import x402Client
from x402.http.clients import x402HttpxClient

client = x402Client()
if os.getenv("EVM_PRIVATE_KEY"):      # Base
    from eth_account import Account
    from x402.mechanisms.evm.exact import register_exact_evm_client
    from x402.mechanisms.evm.signers import EthAccountSigner
    register_exact_evm_client(client, EthAccountSigner(Account.from_key(os.environ["EVM_PRIVATE_KEY"])))
if os.getenv("SOLANA_PRIVATE_KEY"):   # Solana (base58 secret key)
    from solders.keypair import Keypair
    from x402.mechanisms.svm.exact import register_exact_svm_client
    from x402.mechanisms.svm.signers import KeypairSigner
    register_exact_svm_client(client, KeypairSigner(Keypair.from_base58_string(os.environ["SOLANA_PRIVATE_KEY"])))

async def main():
    async with x402HttpxClient(client, timeout=60) as http:
        r = await http.post("https://haris-api.vercel.app/v1/paid/check", json={"mint": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"})
        print(r.status_code, r.json())

asyncio.run(main())
```

**TypeScript** (`npm i @x402/fetch @x402/evm @x402/svm viem @solana/kit @scure/base`):

```ts
import { wrapFetchWithPayment, x402Client } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { ExactSvmScheme } from "@x402/svm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { base58 } from "@scure/base";

const client = new x402Client();
if (process.env.EVM_PRIVATE_KEY)      // Base
  client.register("eip155:8453", new ExactEvmScheme(privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`)));
if (process.env.SOLANA_PRIVATE_KEY)   // Solana
  client.register("solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
    new ExactSvmScheme(await createKeyPairSignerFromBytes(base58.decode(process.env.SOLANA_PRIVATE_KEY))));

const fetchWithPayment = wrapFetchWithPayment(fetch, client);
const r = await fetchWithPayment("https://haris-api.vercel.app/v1/paid/check", {
  method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ mint: "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263" }),
});
console.log(r.status, await r.json());
```

Other paid endpoints work the same way (POST JSON): `/v1/paid/deep-check` `{"mint"}` $0.10,
`/v1/paid/batch-check` `{"mints": [...]}` (up to 20) $0.10, `/v1/paid/diff` `{"mint", "previous"}` $0.02.
**MCP**: `https://haris-api.vercel.app/mcp` (streamable HTTP), tools `check_solana_token`, `diff_solana_token` (free tier),
`deep_check_solana_token`, `batch_check_solana_tokens`.
Full runnable examples: https://github.com/fitness9991/haris-guardian/tree/main/examples

MCP client config:
```json
{ "mcpServers": { "haris-guardian": { "type": "http", "url": "https://haris-api.vercel.app/mcp" } } }
```

LLM-friendly summary: https://haris-api.vercel.app/llms.txt

## Limits / honesty
A score is a heuristic signal, not financial advice or a guarantee. A low score does not mean a token is safe or will go up.

## Links
Website https://harisguardian.netlify.app · X [@HarisGuard_SOL](https://x.com/HarisGuard_SOL) · Telegram bot: Haris Guardian · Contact mansor791@gmail.com
