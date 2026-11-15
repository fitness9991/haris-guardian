// Offline-safe tests for the four declared Haris Guardian MCP tools.
//   node --test tests/mcp_tools.test.mjs
// Optional live smoke test (skipped if the network is down):
//   HARIS_LIVE=1 node --test tests/mcp_tools.test.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const catalog = JSON.parse(readFileSync(join(root, "tests/mcp-tools.json"), "utf8"));
const tools = Object.fromEntries(catalog.tools.map((tool) => [tool.name, tool]));
const VALID_MINT = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263";
const DOC_FILES = ["README.md", "llms-install.md", "docs/API.md"];

function schemaErrors(tool, arguments_) {
  const errors = [];
  if (arguments_ === null || typeof arguments_ !== "object" || Array.isArray(arguments_)) {
    return ["arguments must be an object"];
  }
  for (const key of tool.required) {
    if (!(key in arguments_)) errors.push(`missing required ${key}`);
  }
  for (const [key, value] of Object.entries(arguments_)) {
    const spec = tool.properties[key];
    if (!spec) continue;
    if (spec.type === "string" && typeof value !== "string") errors.push(`${key} must be a string`);
    else if (spec.type === "object" && (typeof value !== "object" || value === null || Array.isArray(value))) {
      errors.push(`${key} must be an object`);
    } else if (spec.type === "array") {
      if (!Array.isArray(value)) errors.push(`${key} must be an array`);
      else if (spec.items?.type === "string" && value.some((item) => typeof item !== "string")) {
        errors.push(`${key} items must be strings`);
      }
    }
  }
  return errors;
}

test("declares the four MCP tools and hosted endpoint", () => {
  assert.deepEqual(new Set(Object.keys(tools)), new Set([
    "check_solana_token",
    "diff_solana_token",
    "deep_check_solana_token",
    "batch_check_solana_tokens",
  ]));
  assert.equal(catalog.endpoint, "https://haris-api.vercel.app/mcp");
});

test("docs name each declared tool", () => {
  for (const rel of DOC_FILES) {
    const text = readFileSync(join(root, rel), "utf8");
    for (const name of Object.keys(tools)) {
      assert.ok(text.includes(name), `${rel} should mention ${name}`);
    }
  }
});

test("examples point at the hosted API", () => {
  for (const rel of ["examples/quickstart.py", "examples/quickstart.ts"]) {
    const text = readFileSync(join(root, rel), "utf8");
    assert.ok(text.includes("https://haris-api.vercel.app"));
  }
});

test("valid and invalid inputs for each declared tool", () => {
  const valid = {
    check_solana_token: { mint: VALID_MINT },
    deep_check_solana_token: { mint: VALID_MINT },
    batch_check_solana_tokens: { mints: [VALID_MINT] },
    diff_solana_token: { mint: VALID_MINT, previous: { mint: VALID_MINT, score: 5 } },
  };
  const invalid = {
    check_solana_token: {},
    deep_check_solana_token: { mint: 123 },
    batch_check_solana_tokens: { mints: VALID_MINT },
    diff_solana_token: { mint: VALID_MINT },
  };
  for (const [name, tool] of Object.entries(tools)) {
    assert.deepEqual(schemaErrors(tool, valid[name]), [], `${name} valid payload`);
    assert.ok(schemaErrors(tool, invalid[name]).length, `${name} invalid payload`);
  }
});

test("hosted MCP lists declared tools when HARIS_LIVE=1", { skip: process.env.HARIS_LIVE !== "1" }, async (t) => {
  let body;
  try {
    const response = await fetch(catalog.endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json, text/event-stream",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list", params: {} }),
      signal: AbortSignal.timeout(30_000),
    });
    body = await response.json();
  } catch (err) {
    t.skip(`hosted MCP unavailable: ${err.message}`);
    return;
  }
  const byName = Object.fromEntries((body.result?.tools || []).map((tool) => [tool.name, tool]));
  for (const [name, declared] of Object.entries(tools)) {
    assert.ok(byName[name], `hosted MCP missing declared tool ${name}`);
    const schema = byName[name].inputSchema || {};
    assert.equal(schema.type, "object");
    assert.deepEqual(new Set(schema.required || []), new Set(declared.required));
    for (const [prop, spec] of Object.entries(declared.properties)) {
      assert.equal(schema.properties?.[prop]?.type, spec.type);
    }
  }
});
