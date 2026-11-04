// Haris Guardian quickstart (TypeScript): pay per call with USDC on Base or Solana via x402.
//   npm i @x402/fetch @x402/evm @x402/svm viem @solana/kit @scure/base
//   EVM_PRIVATE_KEY=0x... and/or SOLANA_PRIVATE_KEY=<base58> npx tsx quickstart.ts <mint>
// Wallets need USDC only: the facilitator pays gas/fees on both chains.
import { wrapFetchWithPayment, x402Client } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { ExactSvmScheme } from "@x402/svm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { base58 } from "@scure/base";

const API = "https://haris-api.vercel.app";
const mint = process.argv[2] ?? "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263";

const client = new x402Client();
if (process.env.EVM_PRIVATE_KEY) {
  client.register("eip155:8453", new ExactEvmScheme(privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`)));
}
if (process.env.SOLANA_PRIVATE_KEY) {
  const signer = await createKeyPairSignerFromBytes(base58.decode(process.env.SOLANA_PRIVATE_KEY));
  client.register("solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp", new ExactSvmScheme(signer));
}
const fetchWithPayment = wrapFetchWithPayment(fetch, client);

// Free tier: 3 checks per UTC day per IP, no wallet needed.
const free = await fetch(`${API}/v1/check/${mint}`);
console.log("free:", free.status, free.status === 200 ? await free.json() : await free.text());

// Paid: $0.01 per check. The wrapper answers the 402 with a signed USDC payment and retries.
if (process.env.EVM_PRIVATE_KEY || process.env.SOLANA_PRIVATE_KEY) {
  const r = await fetchWithPayment(`${API}/v1/paid/check`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ mint }),
  });
  console.log("paid:", r.status, await r.json());
}
