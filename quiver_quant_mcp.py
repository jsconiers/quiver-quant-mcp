# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastmcp>=2.0.0",
#     "httpx>=0.27.0",
#     "python-dotenv>=1.0.0",
# ]
# ///
"""
Quiver Quantitative MCP Server (Python / FastMCP).

Exposes alternative-data datasets from the Quiver Quantitative API
(https://api.quiverquant.com): congressional trading, SEC Form 4 insider
transactions, government contracts, lobbying, r/WallStreetBets activity,
off-exchange (dark-pool) short volume, and 13F institutional changes.

AUTH: Quiver uses ``Authorization: Token <API_TOKEN>``. Some live feeds
(congressional trading, the insider firehose) are currently open and work with
no token; most datasets require a key. Put your key in a .env file next to this
script as ``QUIVER_API_TOKEN=...`` (get one at https://www.quiverquant.com/).
Tools that need a token return a clear message when one isn't configured, so
the open datasets remain usable out of the box.

Run (stdio):   uv run quiver_quant_mcp.py
Verbose logs:  DEBUG=true uv run quiver_quant_mcp.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Annotated, Any, Optional

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import Field

# Load .env from THIS script's directory (robust regardless of launch cwd).
load_dotenv(Path(__file__).resolve().parent / ".env")

BASE_URL = "https://api.quiverquant.com"
API_TOKEN = os.getenv("QUIVER_API_TOKEN", "").strip()
AUTH_SCHEME = (os.getenv("QUIVER_AUTH_SCHEME", "Token").strip() or "Token")
REQUEST_TIMEOUT = 60.0
DEFAULT_LIMIT = 100

REQUEST_HEADERS = {"User-Agent": "quiver-quant-mcp/1.0", "Accept": "application/json"}

# stdio MCP servers must keep stdout for the protocol -> log to stderr only.
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG if os.environ.get("DEBUG") == "true" else logging.INFO,
    format="%(asctime)s [quiver-quant] %(levelname)s %(message)s",
)
log = logging.getLogger("quiver-quant")

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
    return _client


def _auth_headers() -> dict:
    return {"Authorization": f"{AUTH_SCHEME} {API_TOKEN}"} if API_TOKEN else {}


def _token_hint(prefix: str) -> str:
    if API_TOKEN:
        return (f"{prefix}. The configured QUIVER_API_TOKEN may be invalid or "
                "lack access to this dataset.")
    return (f"{prefix}. This dataset requires a Quiver API token. Set "
            "QUIVER_API_TOKEN in the server's .env file "
            "(get a key at https://www.quiverquant.com/).")


class QuiverError(Exception):
    pass


async def _get(path: str, params: Optional[dict] = None) -> Any:
    try:
        r = await _get_client().get(path, params=params, headers=_auth_headers())
    except Exception as exc:  # noqa: BLE001
        raise QuiverError(f"Request to Quiver failed: {exc}") from exc
    if r.status_code in (401, 403):
        raise QuiverError(_token_hint("Authentication failed"))
    if r.status_code == 500 and API_TOKEN:
        raise QuiverError(
            "Quiver returned HTTP 500 — this usually means the API token is "
            "invalid or not provisioned for this dataset. Verify QUIVER_API_TOKEN."
        )
    if r.status_code == 404:
        raise QuiverError(f"Not found (404): {path}. The ticker or dataset may not exist.")
    try:
        r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise QuiverError(f"HTTP {r.status_code} from Quiver: {r.text[:200]}") from exc
    try:
        return r.json()
    except Exception as exc:  # noqa: BLE001
        raise QuiverError(f"Invalid JSON from {path}") from exc


def _result(dataset: str, data: Any, limit: Optional[int], **extra) -> dict:
    if isinstance(data, list):
        trimmed = data[:limit] if limit else data
        return {"dataset": dataset, "count": len(trimmed), "total": len(data),
                **extra, "data": trimmed}
    return {"dataset": dataset, **extra, "data": data}


async def _fetch(dataset: str, path: str, params: Optional[dict], limit: Optional[int]) -> dict:
    """Fetch + wrap; convert QuiverError into a structured error dict (don't raise)."""
    try:
        data = await _get(path, params)
    except QuiverError as exc:
        return {"dataset": dataset, "error": str(exc)}
    return _result(dataset, data, limit)


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------

Limit = Annotated[int, Field(ge=1, le=1000)]

mcp = FastMCP("mcp-quiver-quant-server")


@mcp.tool()
async def quiver_status() -> dict:
    """Show whether a Quiver API token is configured and which datasets are open vs token-gated."""
    return {
        "tokenConfigured": bool(API_TOKEN),
        "authScheme": AUTH_SCHEME,
        "baseUrl": BASE_URL,
        "openWithoutToken": [
            "congress_trading_recent",
            "congress_trading_by_ticker",
            "insider_trading_recent",
        ],
        "requiresToken": [
            "insider_trading_by_ticker", "gov_contracts_recent",
            "gov_contracts_by_ticker", "lobbying_recent", "lobbying_by_ticker",
            "wallstreetbets_recent", "wallstreetbets_by_ticker",
            "offexchange_recent", "offexchange_by_ticker",
            "sec13f_changes_recent", "house_trading_recent",
            "senate_trading_recent",
        ],
        "getToken": "https://www.quiverquant.com/",
    }


# --- Congressional trading (open) ------------------------------------------


@mcp.tool()
async def congress_trading_recent(limit: Limit = DEFAULT_LIMIT) -> dict:
    """Most recent US congressional stock trades across all members (no token required)."""
    return await _fetch("congress_trading_recent", "/beta/live/congresstrading", None, limit)


@mcp.tool()
async def congress_trading_by_ticker(ticker: str, limit: Limit = DEFAULT_LIMIT) -> dict:
    """All disclosed congressional trades for one ticker, e.g. 'AAPL' (no token required)."""
    return await _fetch(
        "congress_trading_by_ticker",
        f"/beta/historical/congresstrading/{ticker.upper()}", None, limit,
    )


# --- Insider trading (SEC Form 4) ------------------------------------------


@mcp.tool()
async def insider_trading_recent(limit: Limit = DEFAULT_LIMIT) -> dict:
    """Recent SEC Form 4 insider transactions across all tickers (no token required; large feed)."""
    return await _fetch("insider_trading_recent", "/beta/live/insiders", None, limit)


@mcp.tool()
async def insider_trading_by_ticker(ticker: str, limit: Limit = DEFAULT_LIMIT) -> dict:
    """SEC Form 4 insider transactions for one ticker (requires a Quiver API token)."""
    return await _fetch(
        "insider_trading_by_ticker", "/beta/live/insiders", {"ticker": ticker.upper()}, limit,
    )


# --- Government contracts (token) ------------------------------------------


@mcp.tool()
async def gov_contracts_recent(limit: Limit = DEFAULT_LIMIT) -> dict:
    """Recent US government contract awards to public companies (requires a Quiver API token)."""
    return await _fetch("gov_contracts_recent", "/beta/live/govcontracts", None, limit)


@mcp.tool()
async def gov_contracts_by_ticker(ticker: str, limit: Limit = DEFAULT_LIMIT) -> dict:
    """Government contract awards for one ticker (requires a Quiver API token)."""
    return await _fetch(
        "gov_contracts_by_ticker",
        f"/beta/historical/govcontracts/{ticker.upper()}", None, limit,
    )


# --- Lobbying (token) ------------------------------------------------------


@mcp.tool()
async def lobbying_recent(limit: Limit = DEFAULT_LIMIT) -> dict:
    """Recent corporate lobbying disclosures (requires a Quiver API token)."""
    return await _fetch("lobbying_recent", "/beta/live/lobbying", None, limit)


@mcp.tool()
async def lobbying_by_ticker(ticker: str, limit: Limit = DEFAULT_LIMIT) -> dict:
    """Lobbying disclosures for one ticker (requires a Quiver API token)."""
    return await _fetch(
        "lobbying_by_ticker", f"/beta/historical/lobbying/{ticker.upper()}", None, limit,
    )


# --- r/WallStreetBets (token) ----------------------------------------------


@mcp.tool()
async def wallstreetbets_recent(limit: Limit = DEFAULT_LIMIT) -> dict:
    """Recent r/WallStreetBets ticker-mention activity (requires a Quiver API token)."""
    return await _fetch("wallstreetbets_recent", "/beta/live/wallstreetbets", None, limit)


@mcp.tool()
async def wallstreetbets_by_ticker(ticker: str, limit: Limit = DEFAULT_LIMIT) -> dict:
    """r/WallStreetBets mention history for one ticker (requires a Quiver API token)."""
    return await _fetch(
        "wallstreetbets_by_ticker",
        f"/beta/historical/wallstreetbets/{ticker.upper()}", None, limit,
    )


# --- Off-exchange / dark-pool short volume (token) -------------------------


@mcp.tool()
async def offexchange_recent(limit: Limit = DEFAULT_LIMIT) -> dict:
    """Recent off-exchange (dark-pool) short-volume activity across tickers (requires a Quiver API token)."""
    return await _fetch("offexchange_recent", "/beta/live/offexchange", None, limit)


@mcp.tool()
async def offexchange_by_ticker(ticker: str, limit: Limit = DEFAULT_LIMIT) -> dict:
    """Off-exchange (dark-pool) short-volume history for one ticker (requires a Quiver API token)."""
    return await _fetch(
        "offexchange_by_ticker",
        f"/beta/historical/offexchange/{ticker.upper()}", None, limit,
    )


# --- 13F institutional changes (token) -------------------------------------


@mcp.tool()
async def sec13f_changes_recent(limit: Limit = DEFAULT_LIMIT) -> dict:
    """Recent changes in SEC 13F institutional holdings (requires a Quiver API token)."""
    return await _fetch("sec13f_changes_recent", "/beta/live/sec13fchanges", None, limit)


# --- House / Senate convenience feeds (token) ------------------------------


@mcp.tool()
async def house_trading_recent(limit: Limit = DEFAULT_LIMIT) -> dict:
    """Recent US House representative stock trades (requires a Quiver API token)."""
    return await _fetch("house_trading_recent", "/beta/live/housetrading", None, limit)


@mcp.tool()
async def senate_trading_recent(limit: Limit = DEFAULT_LIMIT) -> dict:
    """Recent US Senate stock trades (requires a Quiver API token)."""
    return await _fetch("senate_trading_recent", "/beta/live/senatetrading", None, limit)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    log.info("MCP Quiver Quantitative Server starting on stdio (token configured: %s)", bool(API_TOKEN))
    mcp.run()


if __name__ == "__main__":
    main()
