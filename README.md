# k-line-collector-workflow

Public workflow repository for scheduling K-line data collection using the private `k-line-collector` Docker image.

## Architecture

This repo is **public** to leverage GitHub Actions free runner minutes (2000 min/month). All collector source code lives inside the private Docker image on ghcr.io — this repo contains only workflow YAML files.

## Workflows

### Crypto Daily (`crypto-daily.yml`)

Runs automatically at **UTC 02:04** every day. Collects yesterday's data for all 30 symbols across 15 timeframes.

- Trigger: `schedule` (cron) + manual `workflow_dispatch`
- Duration: ~20-40 minutes
- Mode: `daily` (gap detection + yesterday's archive)

### Crypto Backfill (`crypto-backfill.yml`)

Manual trigger only. Downloads full historical data from 2017 to present.

- Trigger: `workflow_dispatch` only
- Duration: up to 5h 15min per batch (6 parallel batches)
- Mode: `backfill` with `--deadline-minutes 315`

#### Batches

| Batch | Symbols |
|-------|---------|
| 1 | BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT |
| 2 | TRXUSDT, DOGEUSDT, ZECUSDT, XLMUSDT, LINKUSDT |
| 3 | LINKUSDT, ADAUSDT, BCHUSDT, GRAMUSDT, LTCUSDT |
| 4 | SUIUSDT, HBARUSDT, AVAXUSDT, NEARUSDT, UNIUSDT |
| 5 | DOTUSDT, AAVEUSDT, POLUSDT, ATOMUSDT, ALGOUSDT |
| 6 | FILUSDT, INJUSDT, APTUSDT, SEIUSDT |

#### Re-running remaining symbols

If a batch times out or fails, check the workflow warning for remaining symbols, then re-trigger with:

- **batch**: the specific batch number (e.g., `3`)
- **symbols**: the remaining symbols from the warning (e.g., `GRAMUSDT,LTCUSDT`)

### Crypto Audit (`crypto-audit.yml`)

Weekly integrity check. Scans all parquet data on HuggingFace for missing K-line candles and generates gap reports.

- Trigger: `schedule` (every Sunday UTC 06:00) + manual `workflow_dispatch`
- Duration: ~30-90 minutes (reads all shards, checks timestamp continuity)
- Output: `reports/crypto/audit.json` + `reports/crypto/REPORTS.md`
- Auto-commits results back to this repo

Reports track:
- Expected vs actual candle count per symbol/timeframe
- Coverage percentage
- Consolidated gap ranges (continuous missing periods merged)

See [reports/REPORTS.md](reports/REPORTS.md) for the latest audit results.

## Report Structure

Audit reports follow a hierarchical structure designed to scale across multiple markets (crypto, forex, stock).

```
reports/
├── REPORTS.md              # Root summary table with links to each market
├── crypto/
│   ├── audit.json          # Machine-readable audit data
│   └── REPORTS.md          # Human-readable crypto details
├── forex/                   # (future)
│   ├── audit.json
│   └── REPORTS.md
└── stock/                   # (future)
    ├── _summary.json        # Per-region summary (stock has many regions)
    ├── {REGION}.json        # Per-region details (US.json, JP.json, etc.)
    └── REPORTS.md
```

### Design Principles

1. **Root `reports/REPORTS.md`**: One-line-per-market summary table with links
2. **Per-market `REPORTS.md`**: Full details for that market (coverage table, gap details, all-clear list)
3. **`audit.json`**: Machine-readable data for CI/automation
4. **Small markets (crypto, forex)**: Single `audit.json` per market
5. **Large markets (stock)**: Split by region to avoid huge files (40+ regions × 100+ symbols each)

### JSON Schema

Each `audit.json` follows this structure:

```json
{
  "market": "crypto",
  "source": "binance",
  "audited_at": "2026-07-31T12:00:00Z",
  "symbols_audited": 29,
  "timeframes_audited": 15,
  "total_storage": {
    "shard_count": 1234,
    "total_bytes": 12345678,
    "total_human": "11.8 MB"
  },
  "results": [
    {
      "symbol": "BTCUSDT",
      "timeframe": "1m",
      "coverage_pct": 99.95,
      "missing_count": 5,
      "shard_count": 90,
      "total_bytes": 400000
    }
  ]
}
```

### Adding a New Market Audit

When implementing forex or stock audit:

1. Create `{market}-audit.yml` workflow
2. Output to `reports/{market}/audit.json` and `reports/{market}/REPORTS.md`
3. Update `reports/REPORTS.md` to include the new market row (each audit regenerates this file)
4. For large markets (stock), split into `{REGION}.json` files with a `_summary.json`

## Secrets Required

| Secret | Description |
|--------|-------------|
| `GHCR_PAT` | Personal Access Token with `read:packages` scope to pull the private Docker image |
| `HF_TOKEN` | HuggingFace write token for uploading parquet files to `sheng9571/kline-crypto` |

## Setup

1. Create a PAT with `read:packages` scope on the k-line-collector repo owner account
2. Create a HuggingFace write token at https://huggingface.co/settings/tokens
3. Add both as repository secrets in this repo's Settings > Secrets > Actions

## Monthly Budget Estimate

| Workflow | Frequency | Est. per run | Monthly total |
|----------|-----------|-------------|---------------|
| crypto-daily | 30x/month | ~30 min | ~900 min |
| crypto-backfill | ad-hoc | ~5h per batch | as needed |
| crypto-audit | 4x/month | ~60 min | ~240 min |

Total steady-state: ~1140 min/month (well within 2000 min free tier).
