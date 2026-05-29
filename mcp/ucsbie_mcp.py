#!/usr/bin/env python3
"""
ucsbie MCP server — exposes UCSB I&E public data as agent tools.

Works with any MCP client: Claude Desktop / Claude Code, the Gemini CLI,
ChatGPT developer mode, and the OpenAI Agents SDK.

Run:    python ucsbie_mcp.py         (stdio transport)
Deps:   pip install "mcp>=1.2" requests
        plus the ucsbie package on the path (pip install ucsbie) OR run from
        the repo so ../src is importable.

Tools (all read-only, live from the public sources):
  - tech_list(campus="SB", keyword=None)     fast list: id/title/url
  - tech_get(tech_id)                         full record for one technology
  - tech_search(terms, campus="SB")          keyword search across the catalog
  - tech_categories(campus="SB")             category facets with counts
  - startups_list(filter="all", status=None, industry=None)
"""
import os
import sys

# Make the ucsbie package importable whether installed or run from the repo.
try:
    from ucsbie import cli as ucsbie
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
    from ucsbie import cli as ucsbie  # type: ignore

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.stderr.write('This server needs the MCP SDK:  pip install "mcp>=1.2"\n')
    raise

mcp = FastMCP("ucsbie")
_session = ucsbie.make_session()


@mcp.tool()
def tech_list(campus: str = "SB", keyword: str | None = None) -> list:
    """List UCSB technologies available for licensing (id, title, url).

    Fast — does not fetch each technology's full detail. Use tech_get for that.
    campus: UC campus code (SB default; B, LA, SD, SF, D, I, R, SC, M; ALL = system).
    keyword: optional case-insensitive title filter.
    """
    rows, _ = ucsbie.fetch_tech_list(_session, "" if campus.upper() == "ALL" else campus,
                                     keyword=keyword, fetch_all=True)
    return rows


@mcp.tool()
def tech_get(tech_id: str) -> dict:
    """Full record for one technology: title, UC case, disclosure year, inventors,
    description, advantages, categories, and the patent table."""
    return ucsbie.fetch_tech_detail(_session, str(tech_id))


@mcp.tool()
def tech_search(terms: str, campus: str = "SB") -> list:
    """Keyword search of available technologies by title/Tech ID. Returns id/title/url."""
    rows, _ = ucsbie.fetch_tech_list(_session, "" if campus.upper() == "ALL" else campus,
                                     keyword=terms, fetch_all=True)
    return rows


@mcp.tool()
def tech_categories(campus: str = "SB") -> list:
    """Technology category facets with counts. `top_level` flags the 18 rollup
    categories; counts overlap, so they sum to more than the unique technology count."""
    return ucsbie.fetch_categories(_session, "" if campus.upper() == "ALL" else campus)


@mcp.tool()
def startups_list(filter: str = "all", status: str | None = None,
                  industry: str | None = None) -> list:
    """List UCSB ventures. filter: all | licensed (licenses UCSB IP) | affiliated.
    status: Active/Acquired/Inactive. industry: substring match (e.g. Healthcare)."""
    return ucsbie.fetch_startups(_session, which=filter, status=status, industry=industry)


if __name__ == "__main__":
    mcp.run()
