# Installing Haris Guardian (for AI agents such as Cline)

Haris Guardian is a **remote** MCP server. Nothing to install, build or configure, and no API key.

Add this to the MCP settings file:

```json
{
  "mcpServers": {
    "haris-guardian": {
      "type": "streamableHttp",
      "url": "https://haris-api.vercel.app/mcp"
    }
  }
}
```

In Cline the `type` must be `"streamableHttp"` (camelCase). If it is omitted Cline falls back to legacy SSE and the connection fails. Other clients such as VS Code and Claude Code use `"type": "http"`.

Tools:
- `check_solana_token` `{ "mint": "<base58 mint>" }`: 0-100 risk score (higher = riskier), verdict, reasons. Free, 3/day per IP.
- `diff_solana_token` `{ "mint", "previous" }`: what changed since a previous result. Free tier.
- `deep_check_solana_token`, `batch_check_solana_tokens`: paid (x402, USDC on Solana or Base); they return payment instructions instead of charging anything.

Test it: ask "check the Solana token DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263" (Bonk); expect a low score.
The server is read-only: it never signs, trades or touches keys. Results are signals, not financial advice.
More: https://haris-api.vercel.app/llms.txt
