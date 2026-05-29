# ucsbie — UCSB Innovation & Entrepreneurship data + Marketplace

Tools and a public website for exploring **UCSB technologies available for licensing**
(UCOP technology-transfer portal) and **UCSB ventures** (TIA Startup Database). One harvester
feeds a CLI, an MCP server, a small HTTP API, an AI-ready data bundle, and the
**UCSB Innovation Marketplace** web page. Public data; contact **info@innovation.ucsb.edu**.

> Status: **draft / research preview** for feedback. Not an official UCSB page.

## What's here
```
src/ucsbie/cli.py        the harvester + CLI  (pip install ucsbie → `ucsbie`)
mcp/ucsbie_mcp.py        MCP server (Claude, Gemini CLI, ChatGPT dev mode, OpenAI Agents SDK)
api/*.py                 Vercel serverless API over the bundled data (for GPT/Gemini Actions)
public/                  the website: index.html (Marketplace), data/ (JSON+CSV), openapi.yaml
scripts/                 refresh.py + build_marketplace.py + vendored Chart.js
data/                    last harvested raw JSON + the summary cache
docs/                    USING-WITH-AI.md, DISTRIBUTION.md, gem-instructions.md, ACCESSIBILITY.md
```

## Use it with your AI tool
See **docs/USING-WITH-AI.md** — three levels from "upload two CSVs into a Gemini Gem"
(no code) to "register the MCP server" (developer). Gemini-first, but covers ChatGPT and Claude.

## CLI quick start
```bash
pip install ucsbie        # or: pipx install ucsbie   (only dep: requests)
ucsbie tech list --campus SB --all
ucsbie tech get 34770
ucsbie startups list --filter licensed
ucsbie tech categories --format table
```
JSON by default; `--format csv|table`, `--out FILE`. Reference at the top of `src/ucsbie/cli.py`.

## Refresh the data + rebuild the page
```bash
pip install requests
python scripts/refresh.py        # harvest → data/ → public/data/* → public/index.html
```
`refresh.py` prints `SUMMARIES_MISSING` (new technologies needing a one-line card summary);
add them to `data/tech_summaries.json` and re-run `scripts/build_marketplace.py`. The build is
self-contained (Chart.js vendored), so only the harvest needs network. After a refresh,
regenerate the AI bundle (`scripts/make_bundle.py`) and redeploy.

## Deploy (Vercel)
`vercel.json` serves `public/` statically and `api/*.py` as Python functions. See
**docs/DISTRIBUTION.md** for the one-time deploy + GitHub steps. After the first deploy,
update the `servers:` URL in `public/openapi.yaml`.

## Accessibility
The Marketplace targets **WCAG 2.1 AA**; see `docs/ACCESSIBILITY.md` (0 axe-core violations,
contrast verified). Do a manual keyboard + screen-reader pass before any official launch.

## License
MIT (code). Data is UCSB's, published publicly by TIA/UCOP. See `LICENSE`.
