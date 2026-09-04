#!/usr/bin/env python3
"""Generate Job Summary and write tv.json for TV symbol check results.

Reads symbol_check.json produced by `node src/main.js --mode symbol-check`
and writes:
  1. reports/{category}/symbols/tv.json  (copy of symbol_check.json)
  2. $GITHUB_STEP_SUMMARY               (Markdown table)

Environment variables:
  SYMBOL_CHECK_JSON   Path to symbol_check.json  (default: ./output/symbol_check.json)
  TV_JSON_OUTPUT      Path to write tv.json       (default: ./reports/forex/symbols/tv.json)
  GITHUB_STEP_SUMMARY Path to GitHub step summary (provided by GitHub Actions)

Exit code: always 0 (report generation only; pass/fail decision is in the workflow).
"""

import json
import os
import sys

SYMBOL_CHECK_JSON = os.environ.get("SYMBOL_CHECK_JSON", "./output/symbol_check.json")
TV_JSON_OUTPUT    = os.environ.get("TV_JSON_OUTPUT",    "./reports/forex/symbols/tv.json")
SUMMARY_PATH      = os.environ.get("GITHUB_STEP_SUMMARY", "/dev/null")

# ---------------------------------------------------------------------------
# Read symbol_check.json
# ---------------------------------------------------------------------------

if not os.path.exists(SYMBOL_CHECK_JSON):
    print(f"[generate_symbol_summary] WARNING: {SYMBOL_CHECK_JSON} not found", file=sys.stderr)
    with open(SUMMARY_PATH, "a") as f:
        f.write("## TV Symbol Validation\n\n")
        f.write("❌ `symbol_check.json` not found — collection may have failed before producing output.\n")
    sys.exit(0)

with open(SYMBOL_CHECK_JSON, encoding="utf-8") as f:
    data = json.load(f)

# ---------------------------------------------------------------------------
# Write tv.json
# ---------------------------------------------------------------------------

os.makedirs(os.path.dirname(TV_JSON_OUTPUT), exist_ok=True)
with open(TV_JSON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"[generate_symbol_summary] tv.json written to {TV_JSON_OUTPUT}", file=sys.stderr)

# ---------------------------------------------------------------------------
# Generate Job Summary
# ---------------------------------------------------------------------------

summary  = data.get("summary", {})
symbols  = data.get("symbols", [])
gen_at   = data.get("generated_at", "?")
cfg_file = data.get("config_file", "?")

found    = [s for s in symbols if s.get("status") == "found"]
missing  = [s for s in symbols if s.get("status") == "not_found"]
timeouts = [s for s in symbols if s.get("status") == "timeout"]

lines = []
lines.append("## TV Symbol Validation")
lines.append("")
lines.append("| Field | Value |")
lines.append("|-------|-------|")
lines.append("| Config | `" + cfg_file + "` |")
lines.append("| Run at | " + gen_at + " |")
lines.append("| Total | " + str(summary.get("total", "?")) + " |")
lines.append("")
lines.append("| Status | Count |")
lines.append("|--------|-------|")
lines.append("| \u2705 Found | " + str(len(found)) + " |")
lines.append("| \u274c Not found | " + str(len(missing)) + " |")
lines.append("| \u26a0\ufe0f Timeout | " + str(len(timeouts)) + " |")
lines.append("")

if missing:
    lines.append("### \u274c Not Found (" + str(len(missing)) + ")")
    lines.append("")
    lines.append("| Symbol | Error |")
    lines.append("|--------|-------|")
    for s in missing:
        err = s.get("error", "?").replace("|", "\\|")
        lines.append("| `" + s["tv_symbol"] + "` | " + err + " |")
    lines.append("")

if timeouts:
    lines.append("### \u26a0\ufe0f Timeout (" + str(len(timeouts)) + ")")
    lines.append("")
    lines.append("| Symbol | Error |")
    lines.append("|--------|-------|")
    for s in timeouts:
        err = s.get("error", "?").replace("|", "\\|")
        lines.append("| `" + s["tv_symbol"] + "` | " + err + " |")
    lines.append("")

if found:
    lines.append("### \u2705 Found (" + str(len(found)) + ")")
    lines.append("")
    lines.append("| Symbol | Description | Type | Exchange | Currency | Session |")
    lines.append("|--------|-------------|------|----------|----------|---------|")
    for s in found:
        info = s.get("info", {})
        desc     = str(info.get("description", "?")).replace("|", "\\|")
        sym_type = str(info.get("type", "?"))
        exchange = str(info.get("exchange", "?"))
        currency = str(info.get("currency_code", "?"))
        session  = str(info.get("session", "?"))
        lines.append(
            "| `" + s["tv_symbol"] + "` | " + desc + " | " +
            sym_type + " | " + exchange + " | " + currency + " | " + session + " |"
        )
    lines.append("")

with open(SUMMARY_PATH, "a", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(
    "[generate_symbol_summary] Job Summary written"
    " (" + str(len(lines)) + " lines,"
    " found=" + str(len(found)) +
    " not_found=" + str(len(missing)) +
    " timeout=" + str(len(timeouts)) + ")",
    file=sys.stderr,
)

sys.exit(0)
