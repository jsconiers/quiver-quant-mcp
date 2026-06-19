"""Offline tests for the Quiver Quantitative MCP (no network required)."""
import asyncio
import quiver_quant_mcp as q


def test_result_trim():
    data = [{"i": i} for i in range(10)]
    r = q._result("ds", data, 3)
    assert r["count"] == 3 and r["total"] == 10 and len(r["data"]) == 3, r
    # non-list passthrough
    r2 = q._result("ds", {"k": "v"}, 5)
    assert r2["data"] == {"k": "v"} and "count" not in r2, r2
    print("  test_result_trim: OK")


def test_auth_headers():
    orig = q.API_TOKEN
    try:
        q.API_TOKEN = ""
        assert q._auth_headers() == {}, "no token -> no header"
        q.API_TOKEN = "abc123"
        assert q._auth_headers() == {"Authorization": "Token abc123"}, q._auth_headers()
    finally:
        q.API_TOKEN = orig
    print("  test_auth_headers: OK")


def test_token_hint():
    orig = q.API_TOKEN
    try:
        q.API_TOKEN = ""
        assert "requires a Quiver API token" in q._token_hint("Auth failed")
        q.API_TOKEN = "abc"
        assert "may be invalid" in q._token_hint("Auth failed")
    finally:
        q.API_TOKEN = orig
    print("  test_token_hint: OK")


def test_status():
    s = asyncio.run(q.quiver_status())
    assert s["authScheme"] == "Token"
    assert "congress_trading_recent" in s["openWithoutToken"]
    assert "lobbying_recent" in s["requiresToken"]
    print("  test_status: OK")


def test_parse_range():
    p = q._parse_range("$1,001 - $15,000")
    assert p == {"amountMin": 1001.0, "amountMax": 15000.0, "amountMid": 8000.5}, p
    assert q._parse_range("n/a") is None
    print("  test_parse_range: OK")


def test_tools_registered():
    names = {t.name for t in asyncio.run(q.mcp.list_tools())}
    expected = {
        "quiver_status", "congress_trading_recent", "congress_trading_by_ticker",
        "insider_trading_recent", "insider_trading_by_ticker",
        "gov_contracts_recent", "gov_contracts_by_ticker",
        "lobbying_recent", "lobbying_by_ticker",
        "wallstreetbets_recent", "wallstreetbets_by_ticker",
        "offexchange_recent", "offexchange_by_ticker",
        "sec13f_changes_recent", "house_trading_recent", "senate_trading_recent",
        "twitter_followers_recent", "twitter_followers_by_ticker",
        "corporate_flights_recent", "patents_by_ticker", "etf_holdings_recent",
        "political_beta_recent", "app_ratings_recent", "sec13f_holdings_recent",
        "gov_contracts_all_recent", "congress_trading_bulk",
        "quiver_datasets", "ticker_signal_scan",
    }
    missing = expected - names
    assert not missing, f"missing tools: {missing}"
    print(f"  test_tools_registered: OK ({len(names)} tools)")


if __name__ == "__main__":
    print("Running Quiver MCP offline tests...")
    test_result_trim()
    test_auth_headers()
    test_token_hint()
    test_status()
    test_parse_range()
    test_tools_registered()
    print("ALL TESTS PASSED")
