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
- Output: `reports/crypto/{SYMBOL}/{timeframe}.json` + `REPORTS.md`
- Auto-commits results back to this repo

Reports track:
- Expected vs actual candle count per symbol/timeframe
- Coverage percentage
- Consolidated gap ranges (continuous missing periods merged)

See [REPORTS.md](REPORTS.md) for the latest audit results.

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
