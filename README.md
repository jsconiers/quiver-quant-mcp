# Quiver Quantitative MCP

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for the
[Quiver Quantitative](https://www.quiverquant.com/) alternative-data API, built on
[FastMCP](https://github.com/jlowin/fastmcp).

It exposes 16 tools covering congressional trading, SEC Form 4 insider transactions,
government contracts, lobbying, r/WallStreetBets activity, off-exchange (dark-pool)
short volume, and 13F institutional changes.

> ⚠️ **Not investment advice.** Datasets are provided for research and transparency only.

## Authentication

Quiver uses a token header: `Authorization: Token <YOUR_TOKEN>`.

Some live feeds are currently **open** (work with no token); most datasets **require a key**:

| Tool | Dataset | Token |
|------|---------|:----:|
| `congress_trading_recent` | Live congressional trades (all members) | — |
| `congress_trading_by_ticker` | Congressional trades for one ticker | — |
| `insider_trading_recent` | Live SEC Form 4 firehose (all tickers) | — |
| `insider_trading_by_ticker` | Form 4 for one ticker | ✅ |
| `gov_contracts_recent` / `_by_ticker` | US government contract awards | ✅ |
| `lobbying_recent` / `_by_ticker` | Corporate lobbying disclosures | ✅ |
| `wallstreetbets_recent` / `_by_ticker` | r/WallStreetBets mention activity | ✅ |
| `offexchange_recent` / `_by_ticker` | Off-exchange / dark-pool short volume | ✅ |
| `sec13f_changes_recent` | Changes in 13F institutional holdings | ✅ |
| `house_trading_recent` | US House trades | ✅ |
| `senate_trading_recent` | US Senate trades | ✅ |
| `quiver_status` | Reports token status + which datasets are open | — |

Token-gated tools return a clear "set QUIVER_API_TOKEN" message when no key is configured,
so the open datasets remain usable immediately. Get a key at <https://www.quiverquant.com/>.

## Setup

```bash
cd quiver-quant-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env and paste your token
```

> 🍏 **Apple Silicon note:** install with the virtual-env's own `pip` (as above),
> **not** a Rosetta/x86_64 `uv`, or native wheels (e.g. `pydantic-core`) can fail to
> load with an "incompatible architecture" error.

Set your token in `.env`:

```
QUIVER_API_TOKEN=your_token_here
```

It also runs dependency-free via [`uv`](https://github.com/astral-sh/uv) thanks to inline
[PEP 723](https://peps.python.org/pep-0723/) metadata:

```bash
uv run quiver_quant_mcp.py
```

## Claude Desktop configuration

Add to `claude_desktop_config.json`, using **absolute** paths. The server reads the token
from its own `.env`, so the `env` block can stay empty:

```json
{
  "mcpServers": {
    "quiver-quant": {
      "command": "/absolute/path/to/quiver-quant-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/quiver-quant-mcp/quiver_quant_mcp.py"],
      "env": {}
    }
  }
}
```

Restart Claude Desktop.

## Usage examples

- "What congressional trades came in today?" → `congress_trading_recent`
- "Show me every congressional trade in NVDA." → `congress_trading_by_ticker`
- "Any recent insider buying at TSLA?" → `insider_trading_by_ticker` (needs token)
- "Which companies just won government contracts?" → `gov_contracts_recent` (needs token)
- "What's trending on WallStreetBets?" → `wallstreetbets_recent` (needs token)
- "Is my token set up?" → `quiver_status`

## Testing

```bash
python test_quiver.py
```

Offline tests cover the result-trimming helper, auth-header construction (with/without a
token), the token-hint messaging, `quiver_status`, and tool registration. No network needed.

The open endpoints (`congress_trading_recent`, `congress_trading_by_ticker`,
`insider_trading_recent`) can be smoke-tested live with no token.

## Notes

- **`limit`** (1–1000, default 100) trims results client-side; each tool also reports `total`.
- **`insider_trading_recent`** is a large firehose — prefer `insider_trading_by_ticker`
  (token) or a small `limit` for targeted work.
- A few Quiver datasets exposed elsewhere (per-ticker 13F, Wikipedia views, "off the radar"
  spikes) are intentionally omitted because their API paths could not be confirmed; only
  verified endpoints are wired up.
- Please respect Quiver Quantitative's API terms and rate limits.

## Credits

Data: [Quiver Quantitative](https://www.quiverquant.com/). This is an independent
Python/FastMCP client and is not affiliated with or endorsed by Quiver Quantitative.

## License

MIT — see `LICENSE` if included. Quiver data remains subject to Quiver's terms of use.
