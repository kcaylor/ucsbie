# Distribution runbook

One-time setup to publish the repo (GitHub) and the site/API (Vercel), plus how to roll it
out to the team. Run these from the repo root on your machine (the `ucsbie/` folder).

## 1. Create the GitHub repo
You need the repo on GitHub before Vercel can auto-deploy it. Easiest with the GitHub CLI:
```bash
cd ucsbie
git init && git add -A && git commit -m "ucsbie: UCSB I&E tools + Marketplace (draft)"
gh repo create UCSB-TIA/ucsbie --public --source=. --remote=origin --push
```
(No `gh`? Create an empty repo at github.com, then:
`git remote add origin https://github.com/UCSB-TIA/ucsbie.git && git push -u origin main`.)

Confirm with TIA before making it public — it's TIA's brand/data even though everything in it
is already on public websites.

## 2. Deploy to Vercel
Either connect the GitHub repo in the Vercel dashboard (New Project → import `ucsbie` →
deploy; future pushes auto-deploy), or from the CLI:
```bash
npm i -g vercel
vercel            # first run: link/create the "ucsbie" project
vercel --prod     # production deploy
```
`vercel.json` already serves `public/` as the site and `api/*.py` as functions. After the
first deploy you'll get a URL like `https://ucsbie.vercel.app`.

## 3. Point things at the live URL
- Edit `public/openapi.yaml` → set `servers: url:` to your deployment URL, commit, redeploy.
- The Marketplace, the JSON/CSV bundle (`/data/...`), and the API (`/api/...`) are now public.

## 4. Wire the monthly refresh to auto-publish (optional but recommended)
The Cowork scheduled task `ucsb-marketplace-refresh` already regenerates the data + page
monthly. To auto-publish, add a final step to that task (or a cron on a machine with the repo):
```bash
cd ucsbie
python scripts/refresh.py
python scripts/make_bundle.py        # regenerate public/data bundle + CSVs
git commit -am "monthly data refresh $(date +%F)" && git push   # Vercel auto-deploys
```

## 5. Roll out to the team (by audience)
Send `docs/USING-WITH-AI.md` and point people to the level that fits:
- **Most staff (Gemini):** the Gemini Gem recipe — upload the two CSVs (or link from Drive
  for auto-update) + paste `docs/gem-instructions.md`. Share the CSVs' `/data/` links.
- **ChatGPT users:** Custom GPT with the CSVs, or an Action pointed at `/openapi.yaml`.
- **Claude users:** a Project with the CSVs, or the MCP server / slash commands.
- **Developers:** `pip install ucsbie`, or register the MCP server with their client.

Suggested announcement: link the **draft Marketplace** for feedback, and attach the one-page
"Using UCSB I&E data in your AI tools" guide. Collect feedback at innovation@ucsb.edu.

## Notes
- Keep the `noindex` tag on the draft Marketplace until TIA approves an official launch.
- The site has no backend state and no secrets; everything is public data, so hosting is low-risk.
