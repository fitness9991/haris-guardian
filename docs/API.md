# Haris Guardian public API (v1, read-only)

**Score: 0-100, HIGHER = RISKIER.** Levels: low <20, medium 20-49, high 50-74, critical 75+.
The score is the capped sum of the published flag weights (`haris/scoring.py` WEIGHTS).
Every flag includes a plain-English `reason`. Signals, not guarantees. Not financial advice.

## Endpoints
| Method | Path | Notes |
|---|---|---|
| GET | `/v1/check/{mint}` | Risk check. Free tier: 3 per UTC day per IP. Then HTTP 402 x402: **$0.01 USDC on Solana per check**. Optional `X-API-Key` (or `Authorization: Bearer`) gives 1000/day. 60 s cache. |
| POST | `/v1/paid/check` | **Canonical x402 resource.** JSON body `{"mint": "<base58>"}`. Always paid via x402 ($0.01 USDC, Solana). Also `GET /v1/paid/check?mint=...`. |
| GET, POST | `/v1/paid/check/{mint}` | Same, mint in the path (served, not listed in OpenAPI: discovery tools only read body/query input schemas). |
| GET | `/favicon.ico` | Logo icon. |
| GET | `/health` | Liveness. |
| GET | `/.well-known/agent.json` (alias `agent-card.json`) | A2A-style agent card. |
| GET | `/openapi.json`, `/docs` | OpenAPI 3.1 spec and Swagger UI. Static copy: `docs/openapi.json`. |
| POST | `/mcp` | MCP streamable HTTP (stateless JSON) with tool `check_solana_token(mint)`. |

Stdio MCP: `python -m haris_api.mcp_server` (no quota).

Response fields: `mint, name, score, score_scale, level, verdict, flags[{id,weight,reason}], positives[], not_checked[],
liquidity{usd,pools,price_usd,oldest_pool_age_hours,top_pool}, lp_locked_pct, lp_status, lp_detail, authorities{...},
holders{...}, streamflow_locked_pct, sell_simulation{...}, partial_failures[], checked_at (UTC ISO), disclaimer`.

Errors: 400 invalid_mint / invalid_payload, 401 invalid_api_key, 402 payment required/rejected, 404 not_a_token_mint,
429 quota_exceeded (only when x402 is off) / rate_limited (burst 20/min per IP), 502 upstream_unavailable,
503 facilitator_unavailable / facilitator_refused. Failed and invalid calls do not use up the free quota.
Headers: `X-RateLimit-Limit/Remaining/Reset`, `X-Cache: HIT|MISS`.

## Config (env)
`HARIS_API_BASE_URL`, `HARIS_API_FREE_PER_DAY` (3), `HARIS_API_KEY_PER_DAY` (1000), `HARIS_API_BURST_PER_MIN` (20),
`HARIS_API_CACHE_TTL` (60), `HARIS_API_TRUST_PROXY` (0; set 1 behind a hosting proxy),
`HARIS_API_KEY_HASHES` (comma-separated SHA-256 hex of keys; raw keys are never stored), `HARIS_RPC_URL` (optional keyed RPC).

## x402 pay-per-call (LIVE on Solana mainnet)
Price **$0.01 per check = `10000` USDC atomic units** (6 decimals), asset USDC mint
`EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`, scheme `exact`, paid to the owner-approved receive-only wallet
`7ZpBTGZ7mBm81esAq77FFm293zAuGM3Hi249fKPnVDfJ`. Facilitator: PayAI (`https://facilitator.payai.network`, no API key,
it is the Solana fee payer, so payers need USDC only, no SOL). The server never holds a key, signs, or moves funds.

Flow (both protocol versions are accepted):
1. `POST /v1/paid/check` `{"mint":..}` (or `GET /v1/paid/check?mint=`, `GET /v1/paid/check/{mint}`, or `/v1/check/{mint}` after
   the free tier) -> **402**. On paid routes the paywall runs **before** any input validation: any method (GET/POST/HEAD) and any
   mint, even missing or a placeholder like `{mint}`, gets the 402 challenge, so x402scan/Bazaar probes succeed. `OPTIONS` -> 204.
   * Body = x402 **v1** `{"x402Version":1,"error":..,"accepts":[{"scheme":"exact","network":"solana","maxAmountRequired":"10000",
     "resource":"<url>","payTo":"7ZpB…VDfJ","asset":"EPjF…Dt1v","maxTimeoutSeconds":60,"extra":{"feePayer":"<PayAI fee payer>"},...}]}`.
   * Header `PAYMENT-REQUIRED` = base64 x402 **v2** PaymentRequired (`network":"solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"`, `"amount":"10000"`),
     with `extensions.bazaar` (input example + JSON schema for the body / query / path mint, output example + schema).
   * The mint is validated only when a payment header is present; an invalid mint then returns 400 before verify/settle (not charged).
2. Client builds a USDC `TransferChecked` to `payTo` with `feePayer` as fee payer, partially signs it, and retries the same URL with
   `X-PAYMENT` (v1) or `PAYMENT-SIGNATURE` (v2): base64 JSON with `payload.transaction` (base64 tx). Any x402 client library works.
3. Server -> facilitator `/verify`; runs the check; -> `/settle` (facilitator co-signs and broadcasts). The result is returned
   **only if settle succeeds**, with `X-PAYMENT-RESPONSE` (v1) or `PAYMENT-RESPONSE` (v2): base64 `{"success":true,"transaction":"<sig>","network":..,"payer":..}`.
   If the check fails (404/502) the payment is never settled, so the caller is not charged.

Paid calls do not use the free quota. The MCP tool, once the free tier is used, returns `quota_exceeded` with the exact REST
paid endpoint, price, pay_to and network. Config: `HARIS_X402_ENABLED`, `HARIS_X402_PAY_TO` (required, refuses to start without a
valid address), `HARIS_X402_PRICE_USD` (0.01), `HARIS_X402_NETWORK` (`solana`), `HARIS_X402_ASSET`, `HARIS_X402_FACILITATOR`
(PayAI default), optional `HARIS_X402_FEE_PAYER` (else read from facilitator `/supported`, cached 10 min).
PayAI gives 1,000 free credits per receiving wallet (about 800 Solana settlements); after that it needs credits plus an API key.

### Discovery (x402scan / AgentCash / Bazaar)
`/openapi.json` follows the x402scan discovery spec: `info.x-guidance`, `info.contact.email`; paid operations carry
`x-payment-info` (`{"price":{"mode":"fixed","currency":"USD","amount":"0.01"},"protocols":[{"x402":{}}]}`), a `402` response,
input schema (requestBody / parameters) and a 200 output schema; free endpoints (`/health`, `/v1/check/{mint}`, `/.well-known/*`)
have `"security": []` so scanners skip them. Register the **origin** `https://haris-api.vercel.app` at
https://www.x402scan.com/resources/register (or just `https://haris-api.vercel.app/v1/paid/check`). Check locally with
`npx @agentcash/discovery https://haris-api.vercel.app`.

## Run / test locally
```
./run_api.sh start          # http://127.0.0.1:8787 (localhost only), log: api.log
.venv-api/bin/python -m pytest tests_api -q -c /dev/null --rootdir tests_api   # HARIS_LIVE=1 adds a live BONK test
```
Limits are in memory (reset on restart). On Vercel each serverless instance has its own counters, so the free tier is
best-effort (a caller hitting several instances, or changing IP, gets more free checks). Use Redis or KV for a strict quota.
