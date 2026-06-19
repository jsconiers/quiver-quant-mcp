# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-19

### Added
- 10 additional dataset tools: `twitter_followers_recent` / `_by_ticker`,
  `corporate_flights_recent`, `patents_by_ticker`, `etf_holdings_recent`,
  `political_beta_recent`, `app_ratings_recent`, `sec13f_holdings_recent`,
  `gov_contracts_all_recent`, and `congress_trading_bulk`.
- `quiver_datasets` — lists every dataset this server exposes, its endpoint, and
  whether it needs an API token.
- `ticker_signal_scan` — one call that fans out across many per-ticker datasets
  concurrently (congress, insiders, lobbying, contracts, WSB, off-exchange,
  patents, Twitter) and returns a per-signal count summary plus raw rows.
- Automatic dollar-`Range` normalization: rows like `$1,001 - $15,000` gain numeric
  `amountMin` / `amountMax` / `amountMid` fields.
- 60-second in-memory response cache so repeated/fanned-out calls share fetches.

### Changed
- 28 tools total (up from 16). `quiver_status` now lists the new gated datasets.

## [0.1.0] - 2026-06-19

### Added
- Initial release of the Quiver Quantitative MCP server (Python / FastMCP).
- 16 tools: congressional trading (live + by ticker), SEC Form 4 insider
  transactions (live + by ticker), government contracts, lobbying,
  r/WallStreetBets activity, off-exchange / dark-pool short volume, 13F
  institutional changes, House and Senate feeds, and a `quiver_status` diagnostic.
- Token authentication via a local `.env` (`QUIVER_API_TOKEN`); open feeds work
  with no token, while token-gated datasets return a clear setup message instead
  of a raw error.
- `limit` (1-1000) result trimming with `total` reporting on every dataset.
- Offline test suite (`test_quiver.py`) covering result trimming, auth-header
  construction, token messaging, `quiver_status`, and tool registration.

### Notes
- Only Quiver endpoints with verified API paths are wired up. A few datasets
  exposed elsewhere (per-ticker 13F, Wikipedia views, "off the radar" spikes) are
  intentionally omitted until their paths are confirmed.
