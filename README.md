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
| MCP (streamable-http) | `https://haris-api.vercel.app/mcp` — tool `check_solana_token` |
| REST (free, 3/day) | `GET https://haris-api.vercel.app/v1/check/{mint}` |
| REST (paid, x402) | `POST https://haris-api.vercel.app/v1/paid/check` · `GET /v1/paid/check/{mint}` |
| OpenAPI | https://haris-api.vercel.app/openapi.json |
| Docs | https://haris-api.vercel.app/docs |
| A2A agent card | https://haris-api.vercel.app/.well-known/agent.json |

## Pricing
- 3 free checks per day per IP.
- After that: **$0.01 USDC per check on Solana via x402** (HTTP 402 → pay → retry). Payments go to `7ZpBTGZ7mBm81esAq77FFm293zAuGM3Hi249fKPnVDfJ`.

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
