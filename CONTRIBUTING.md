# Contributing

Thanks for your interest in improving the Quiver Quantitative MCP! Bug reports,
fixes, new dataset tools, docs, and tests are all welcome.

## Getting started

```bash
git clone https://github.com/jsconiers/quiver-quant-mcp.git
cd quiver-quant-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your QUIVER_API_TOKEN for token-gated datasets
```

> On Apple Silicon, install with the virtual-env's own `pip` (not a Rosetta/x86_64
> `uv`), or native wheels such as `pydantic-core` may fail to load.

## Running the tests

```bash
python test_quiver.py
```

Offline tests (result trimming, auth-header construction, token messaging,
`quiver_status`, tool registration) require no network or token. The open feeds
(`congress_trading_recent`, `congress_trading_by_ticker`, `insider_trading_recent`)
can be smoke-tested live without a token.

## Coding guidelines

- Target Python 3.10+ and keep the module importable without side effects.
- stdio MCP servers must log to **stderr only** — never print to stdout.
- **Never commit secrets.** The real `.env` is git-ignored; only `.env.example`
  is tracked. Never paste a token into an issue or PR.
- Only wire up Quiver endpoints whose paths are verified; document any that are
  intentionally omitted.
- Token-gated tools should fail gracefully with a clear "set QUIVER_API_TOKEN"
  message rather than raising.
- Add or update a test in `test_quiver.py` for any new tool.

## Submitting changes

1. Fork the repo and create a feature branch (`git checkout -b feature/my-change`).
2. Keep commits focused; ensure `python test_quiver.py` passes.
3. Open a pull request describing the change and its motivation.

## Reporting issues

Please include what you ran, expected vs actual behavior (with any stderr output),
your OS / Python version, and whether a token was configured — but never paste the
token itself.

## Disclaimer

Data is provided by Quiver Quantitative and is subject to their terms of use. This
is an independent client and is not investment advice.
