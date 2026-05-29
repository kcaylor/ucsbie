# Using UCSB I&E data in your AI tools

Three ways in, by how technical you want to get. Everyone can do Level 1.
Pick the row that matches your tool and comfort level.

| Level | You get | Works with | Effort |
|---|---|---|---|
| 1. Upload / paste the data | A chatbot that knows our tech + ventures | Gemini Gem, Custom GPT, Claude Project, any chat | 5 min, no code |
| 2. Connect the live API | Same, but always-current via the web | Custom GPT Actions, Gemini function-calling | ~15 min |
| 3. MCP server / CLI | Real-time tools inside an agent | Claude, Gemini CLI, ChatGPT dev mode, scripts | developer |

The data is **public** (UCOP techtransfer portal + TIA Startup Database). Contact for any
listing: **innovation@ucsb.edu**.

---

## Level 1 — no code (recommended for most people)

### Google Gemini Gem  ⭐ (UCSB's licensed AI)
1. Gemini → **Gems** → **New Gem**.
2. Name it "UCSB Innovation Assistant".
3. **Instructions:** paste the contents of `docs/gem-instructions.md`.
4. **Knowledge → Add files:** upload `ucsb-technologies.csv` and `ucsb-ventures.csv`
   (download from the site's `/data/` folder). A Gem accepts up to 10 files.
   - *Tip:* put the two CSVs in Google Drive and add them **from Drive** — the Gem then
     auto-uses the latest version whenever the monthly refresh updates them.
5. Save. Now ask it things like "What battery technologies can we license?" or
   "Which active healthcare startups raised the most?"

### ChatGPT — Custom GPT (knowledge upload)
Create a GPT, paste `docs/gem-instructions.md` as instructions, and upload the two CSVs
under **Knowledge**. (For live data instead, see Level 2.)

### Claude — Project
New Project → add `ucsb-technologies.csv` + `ucsb-ventures.csv` (or `ucsb-ie.json`) to
Project knowledge → paste the instructions. Or just drop the files into any chat.

### Absolute simplest
Paste this into any chatbot: *"Use the data at https://YOUR-SITE/data/ucsb-ie.json to
answer questions about UCSB technologies and ventures."* (Works in tools that can fetch URLs.)

---

## Level 2 — connect the live API (always current)

The site exposes a small read-only API (see `public/openapi.yaml`):
`/api/technologies`, `/api/ventures`, `/api/categories` (with filters like `?field=`,
`?status=`, `?licensed=true`, `?q=`).

### Custom GPT Action
GPT editor → **Actions** → **Import** → paste your site's `openapi.yaml` URL
(`https://YOUR-SITE/openapi.yaml`). No auth needed (public data). Update the `servers:` URL
in the schema to your deployment first.

### Gemini function-calling
Feed the same OpenAPI operations to the Gemini API as function declarations (the Gemini SDK
maps OpenAPI schemas to tools). Best for developers building on the Gemini API.

---

## Level 3 — MCP server or CLI (developers / power users)

### MCP server (works across Claude, Gemini CLI, ChatGPT dev mode, OpenAI Agents SDK)
```bash
pip install "mcp>=1.2" requests
pip install ucsbie            # or run from the repo
python mcp/ucsbie_mcp.py      # stdio
```
Tools: `tech_list`, `tech_get`, `tech_search`, `tech_categories`, `startups_list` (live).

Register it with your client:

- **Claude Desktop / Claude Code** — add to `claude_desktop_config.json` (or `.mcp.json`):
  ```json
  { "mcpServers": { "ucsbie": { "command": "python", "args": ["/abs/path/mcp/ucsbie_mcp.py"] } } }
  ```
- **Gemini CLI** — add to `~/.gemini/settings.json`:
  ```json
  { "mcpServers": { "ucsbie": { "command": "python", "args": ["/abs/path/mcp/ucsbie_mcp.py"] } } }
  ```
- **ChatGPT developer mode / OpenAI Agents SDK** — add it as an MCP server in the
  connectors/dev-mode settings (stdio command as above).

### CLI (any environment that runs Python)
```bash
pip install ucsbie         # or: pipx install ucsbie
ucsbie tech search "photonics" --details
ucsbie startups list --filter licensed --format csv --out ventures.csv
ucsbie tech categories
```
JSON by default; `--format csv|table`, `--out FILE`. Full reference: top of `src/ucsbie/cli.py`
and the project `README.md`.

### Claude slash commands (if you use Claude Code / Cowork in this vault)
`/ucsbie <args>` and `/ucsb-refresh` are available from `.claude/commands/`.

---

## Which should I tell a colleague to use?
- **"I just want my AI to know our portfolio"** → Level 1, Gemini Gem with the two CSVs.
- **"I want it to always be current without me re-uploading"** → Level 1 with the CSVs in
  Drive (auto-update), or Level 2 (API).
- **"I'm building an agent/automation"** → Level 3 (MCP or CLI).
