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
| POST | `/v1/paid/deep-check` | **Deep check, $0.10 USDC (x402).** Body `{"mint"}`. Holder concentration (top1/top5/top10 % of supply, holder count), top wallets linked by a shared first funder (bundle/insider clusters), creator-funded and fresh top wallets, LP lock/burn status, authorities, score + reasons. 120 s cache. |
| POST | `/v1/paid/batch-check` | **Batch check, $0.10 USDC flat per batch (x402).** Body `{"mints": [...]}` with 1-20 unique mints. Per-mint results (same shape as `/v1/check`) + summary. Charged only if at least one mint was checked. |
| POST | `/v1/paid/diff` | **Watch/diff, $0.02 USDC (x402).** Body `{"mint", "previous"}` where `previous` is an earlier Haris result for that mint (check, deep-check, or a previous diff response). Returns `changed`, `severity`, `alerts[]` and the fresh `current` result. Stateless: nothing is stored server-side. |
| GET | `/favicon.ico` | Logo icon. |
| GET | `/health` | Liveness, plus `limiter` (`memory`/`kv`) and, when x402 is on, `facilitators[{url, fee_payer, healthy, down_reason?}]`. |
| GET | `/.well-known/agent.json` (alias `agent-card.json`) | A2A-style agent card. |
| GET | `/openapi.json`, `/docs` | OpenAPI 3.1 spec and Swagger UI. Static copy: `docs/openapi.json`. |
| POST | `/mcp` | MCP streamable HTTP (stateless JSON). Tools: `check_solana_token(mint)` and `diff_solana_token(mint, previous)` (free tier, then `quota_exceeded` with x402 instructions); `deep_check_solana_token(mint)`, `batch_check_solana_tokens(mints)` (paid only: return `payment_required` with the exact REST endpoint, body, price, amount, pay_to, network, facilitator). |

Stdio MCP: `python -m haris_api.mcp_server` (no quota).

Response fields: `mint, name, score, score_scale, level, verdict, flags[{id,weight,reason}], positives[], not_checked[],
liquidity{usd,pools,price_usd,oldest_pool_age_hours,top_pool}, lp_locked_pct, lp_status, lp_detail, authorities{...},
holders{...}, streamflow_locked_pct, sell_simulation{...}, partial_failures[], checked_at (UTC ISO), disclaimer`.

### Paid products

| Product | Endpoint | Price (USD) | Atomic USDC | Body |
|---|---|---|---|---|
| check | `POST /v1/paid/check` | 0.01 | `10000` | `{"mint": "<base58>"}` |
| deep-check | `POST /v1/paid/deep-check` | 0.10 | `100000` | `{"mint": "<base58>"}` |
| batch-check | `POST /v1/paid/batch-check` | 0.10 per batch (1-20 mints) | `100000` | `{"mints": ["<base58>", ...]}` |
| diff | `POST /v1/paid/diff` | 0.02 | `20000` | `{"mint": "<base58>", "previous": {<earlier Haris result>}}` |

The new endpoints follow the same flow as `/v1/paid/check` (below): 402 before any validation for POST/GET/HEAD, `OPTIONS` 204,
input validated only once a payment header is present (400 `invalid_mint` / `invalid_mints` / `too_many_mints` /
`invalid_previous` / `previous_mismatch` / `invalid_body`, 413 `payload_too_large` over 64 KB, all before verify: not charged),
then verify -> run -> settle. Failed runs (404/502/504) are never settled. Paid work has a hard budget (30 s by default):
deep-check trims holder tracing to fit it (missing parts listed in `partial_failures`), batch-check gives each mint up to 25 s
(timed-out mints come back as per-mint errors), and anything still over budget returns 504 `work_timeout`, unsettled, so a
signed payment is always settled well inside its blockhash lifetime.

**deep-check** adds to the base result: `base_score`, `base_level`, `reasons[]`, `flags[]` tagged `source: base|deep`,
`holders{top1_wallet_pct, top5_wallet_pct, top10_wallet_pct, excluded_pct, holder_count, wallets[{owner, pct, funder,
funded_via, first_tx_at, age_days, fresh, creator_linked}]}`, `clusters[{funder, wallets, size, combined_pct,
funder_is_top_holder, funder_is_creator, funder_busy, confidence}]`, `lp{status, locked_pct, detail, lp_mint, streamflow_*}`.
Deep flags (added to the base score, capped at 100): `linked_holders_high` +20 (a shared-funder cluster holds >=20%),
`linked_holders` +10 (>=5%), `creator_funded_holders` +15 (top wallets that are or were funded by an authority/dev hold >=5%),
`fresh_top_wallets` +10 (3+ top wallets first active <3 days ago holding >=10%). Funders with 1000+ transactions (exchanges,
bots) are marked `funder_busy` and not scored. Method: the oldest transaction of each of the top 8 wallets (public RPC).

**diff** alert severities: `critical` (mint/freeze authority or permanent delegate set, LP burned -> not burned, locked LP
share down 10+ points, liquidity down 50%+, selling now fails), `warning` (risk level up, score up 5+, new flags, liquidity
down 20%+, top-holder % up 5+ points, round-trip loss up 10+ points), `info` (improvements). Store `current` and send it as
`previous` next time.

Errors: 400 invalid_mint / invalid_payload, 401 invalid_api_key, 402 payment required/rejected, 404 not_a_token_mint,
429 quota_exceeded (only when x402 is off) / rate_limited (burst 20/min per IP), 502 upstream_unavailable,
503 facilitator_unavailable / facilitator_refused (retry: the next 402 challenge points at a healthy facilitator), 504 work_timeout. Failed and invalid calls do not use up the free quota.
Headers: `X-RateLimit-Limit/Remaining/Reset`, `X-Cache: HIT|MISS`.

## Config (env)
`HARIS_API_BASE_URL`, `HARIS_API_FREE_PER_DAY` (3), `HARIS_API_KEY_PER_DAY` (1000), `HARIS_API_BURST_PER_MIN` (20),
`HARIS_API_CACHE_TTL` (60), `HARIS_API_TRUST_PROXY` (0; set 1 behind a hosting proxy),
`HARIS_API_KEY_HASHES` (comma-separated SHA-256 hex of keys; raw keys are never stored), `HARIS_RPC_URL` (optional keyed RPC),
`HARIS_API_PAID_WORK_BUDGET` (30 s), `HARIS_API_BATCH_TIMEOUT` (25 s).
Durable free-tier counter (shared by all serverless instances): set `KV_REST_API_URL` + `KV_REST_API_TOKEN` (Vercel KV /
Upstash Redis REST; `UPSTASH_REDIS_REST_URL`/`_TOKEN` also accepted). Identities are stored hashed, keys expire after 2 days;
if the store is unreachable the counter falls back to per-instance memory.

## x402 pay-per-call (LIVE on Solana mainnet)
Price **$0.01 per check = `10000` USDC atomic units** (6 decimals), asset USDC mint
`EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`, scheme `exact`, paid to the owner-approved receive-only wallet
`7ZpBTGZ7mBm81esAq77FFm293zAuGM3Hi249fKPnVDfJ`. Facilitator: PayAI (`https://facilitator.payai.network`), with keyless fallbacks
(`https://x402.dexter.cash`, `https://facilitator.ultravioletadao.xyz`). The facilitator is the Solana fee payer, so payers
need USDC only, no SOL. The server never holds a key, signs, or moves funds.

Flow (both protocol versions are accepted):
1. `POST /v1/paid/check` `{"mint":..}` (or `GET /v1/paid/check?mint=`, `GET /v1/paid/check/{mint}`, or `/v1/check/{mint}` after
   the free tier) -> **402**. On paid routes the paywall runs **before** any input validation: any method (GET/POST/HEAD) and any
   mint, even missing or a placeholder like `{mint}`, gets the 402 challenge, so x402scan/Bazaar probes succeed. `OPTIONS` -> 204.
   * Body = x402 **v1** `{"x402Version":1,"error":..,"accepts":[{"scheme":"exact","network":"solana","maxAmountRequired":"10000",
     "resource":"<url>","payTo":"7ZpB…VDfJ","asset":"EPjF…Dt1v","maxTimeoutSeconds":60,"extra":{"feePayer":"<active facilitator fee payer>"},...}]}`.
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
(PayAI default), `HARIS_X402_PRICE_DEEP_USD` (0.10), `HARIS_X402_PRICE_BATCH_USD` (0.10), `HARIS_X402_PRICE_DIFF_USD` (0.02),
optional `HARIS_X402_FEE_PAYER` (else read from facilitator `/supported`, cached 10 min),
`HARIS_X402_FALLBACK_FACILITATORS` (comma-separated https URLs; empty disables), optional `PAYAI_API_KEY_ID` +
`PAYAI_API_KEY_SECRET` (PayAI merchant key, sent as a short-lived EdDSA JWT on /verify and /settle only).
PayAI gives 1,000 free credits per receiving wallet (about 800 Solana settlements at ~1.25 credits each); after that it needs
paid credits ($1 = 1,000 credits). Free-credit status is checked via `/free-credits`; when exhausted (or a facilitator errors or
refuses), new 402 challenges advertise the next healthy facilitator's fee payer. A signed payment names one facilitator's fee
payer, so it is always verified and settled by that same facilitator (unknown fee payer -> fresh 402).

### Discovery (x402scan / AgentCash / Bazaar)
`/openapi.json` follows the x402scan discovery spec: `info.x-guidance`, `info.contact.email`; paid operations carry
`x-payment-info` (`{"price":{"mode":"fixed","currency":"USD","amount":"0.01"},"protocols":[{"x402":{}}]}`; 0.10 for deep-check
and batch-check, 0.02 for diff), a `402` response,
input schema (requestBody / parameters) and a 200 output schema; free endpoints (`/health`, `/v1/check/{mint}`, `/.well-known/*`)
have `"security": []` so scanners skip them. Register the **origin** `https://haris-api.vercel.app` at
https://www.x402scan.com/resources/register (or the resources `https://haris-api.vercel.app/v1/paid/check`,
`/v1/paid/deep-check`, `/v1/paid/batch-check`, `/v1/paid/diff`). Check locally with
`npx @agentcash/discovery https://haris-api.vercel.app`.

## Run / test locally
```
./run_api.sh start          # http://127.0.0.1:8787 (localhost only), log: api.log
.venv-api/bin/python -m pytest tests_api -q -c /dev/null --rootdir tests_api   # HARIS_LIVE=1 adds a live BONK test
```
Limits are in memory (reset on restart). On Vercel each serverless instance has its own counters, so the free tier is
best-effort (a caller hitting several instances, or changing IP, gets more free checks). Use Redis or KV for a strict quota.
