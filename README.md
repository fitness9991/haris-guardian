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
```bash
curl https://haris-api.vercel.app/v1/check/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```
MCP client config:
```json
{ "mcpServers": { "haris-guardian": { "type": "http", "url": "https://haris-api.vercel.app/mcp" } } }
```

## Limits / honesty
A score is a heuristic signal, not financial advice or a guarantee. A low score does not mean a token is safe or will go up.

## Links
Website https://harisguardian.netlify.app · X [@HarisGuard_SOL](https://x.com/HarisGuard_SOL) · Telegram bot: Haris Guardian · Contact mansor791@gmail.com
