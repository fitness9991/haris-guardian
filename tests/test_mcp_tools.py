"""Offline-safe tests for the four declared Haris Guardian MCP tools.

Run:
  python3 -m unittest tests/test_mcp_tools.py

Optional live smoke test against the hosted MCP (skipped if the network is down):
  HARIS_LIVE=1 python3 -m unittest tests/test_mcp_tools.py
"""
from __future__ import annotations

import json
import os
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = Path(__file__).resolve().parent / "mcp-tools.json"
VALID_MINT = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
DOC_FILES = ("README.md", "llms-install.md", "docs/API.md")


def load_declared_tools() -> dict:
    return json.loads(TOOLS_PATH.read_text(encoding="utf-8"))


def schema_errors(tool: dict, arguments: dict) -> list[str]:
    """Minimal JSON-schema check for the declared tool input schemas."""
    errors: list[str] = []
    if not isinstance(arguments, dict):
        return ["arguments must be an object"]
    for key in tool["required"]:
        if key not in arguments:
            errors.append(f"missing required {key}")
    for key, value in arguments.items():
        spec = tool["properties"].get(key)
        if spec is None:
            continue
        expected = spec["type"]
        if expected == "string" and not isinstance(value, str):
            errors.append(f"{key} must be a string")
        elif expected == "object" and not isinstance(value, dict):
            errors.append(f"{key} must be an object")
        elif expected == "array":
            if not isinstance(value, list):
                errors.append(f"{key} must be an array")
            else:
                item_type = (spec.get("items") or {}).get("type")
                if item_type == "string" and any(not isinstance(item, str) for item in value):
                    errors.append(f"{key} items must be strings")
    return errors


class DeclaredToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_declared_tools()
        cls.tools = {tool["name"]: tool for tool in cls.catalog["tools"]}

    def test_four_declared_tools(self) -> None:
        expected = {
            "check_solana_token",
            "diff_solana_token",
            "deep_check_solana_token",
            "batch_check_solana_tokens",
        }
        self.assertEqual(set(self.tools), expected)
        self.assertEqual(self.catalog["endpoint"], "https://haris-api.vercel.app/mcp")

    def test_docs_name_each_tool(self) -> None:
        for rel in DOC_FILES:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for name in self.tools:
                self.assertIn(name, text, f"{rel} should mention {name}")

    def test_examples_point_at_hosted_api(self) -> None:
        for rel in ("examples/quickstart.py", "examples/quickstart.ts"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("https://haris-api.vercel.app", text)

    def test_valid_and_invalid_inputs_for_each_tool(self) -> None:
        valid_payloads = {
            "check_solana_token": {"mint": VALID_MINT},
            "deep_check_solana_token": {"mint": VALID_MINT},
            "batch_check_solana_tokens": {"mints": [VALID_MINT]},
            "diff_solana_token": {"mint": VALID_MINT, "previous": {"mint": VALID_MINT, "score": 5}},
        }
        invalid_payloads = {
            "check_solana_token": {},
            "deep_check_solana_token": {"mint": 123},
            "batch_check_solana_tokens": {"mints": VALID_MINT},
            "diff_solana_token": {"mint": VALID_MINT},
        }
        for name, tool in self.tools.items():
            with self.subTest(tool=name, case="valid"):
                self.assertEqual(schema_errors(tool, valid_payloads[name]), [])
            with self.subTest(tool=name, case="invalid"):
                self.assertTrue(schema_errors(tool, invalid_payloads[name]))


@unittest.skipUnless(os.getenv("HARIS_LIVE") == "1", "set HARIS_LIVE=1 to hit the hosted MCP")
class LiveMcpSmokeTests(unittest.TestCase):
    def test_hosted_mcp_lists_declared_tools(self) -> None:
        catalog = load_declared_tools()
        declared = {tool["name"]: tool for tool in catalog["tools"]}
        payload = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        ).encode("utf-8")
        request = urllib.request.Request(
            catalog["endpoint"],
            data=payload,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.skipTest(f"hosted MCP unavailable: {exc}")

        tools = ((body.get("result") or {}).get("tools")) or []
        by_name = {tool["name"]: tool for tool in tools if "name" in tool}
        for name, declared_tool in declared.items():
            self.assertIn(name, by_name, f"hosted MCP missing declared tool {name}")
            schema = by_name[name].get("inputSchema") or {}
            self.assertEqual(schema.get("type"), "object")
            self.assertEqual(set(schema.get("required") or []), set(declared_tool["required"]))
            for prop, spec in declared_tool["properties"].items():
                self.assertEqual((schema.get("properties") or {}).get(prop, {}).get("type"), spec["type"])


if __name__ == "__main__":
    unittest.main()
