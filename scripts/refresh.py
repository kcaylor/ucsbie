#!/usr/bin/env python3
"""
refresh.py — rebuild the UCSB Innovation Marketplace from live sources.

Pipeline:
  1. Harvest all available technologies (with full detail) + all ventures via ucsbie.
  2. Write canonical JSON into ./data/.
  3. Report any technologies that lack a card summary (new disclosures).
  4. Rebuild the accessible Marketplace HTML (build_marketplace.py).

New-technology summaries: this script falls back to a truncated description for
any tech missing from data/tech_summaries.json, so it always produces a valid
page on its own. The monthly scheduled Claude task generates proper one-line
summaries for the IDs printed under "SUMMARIES_MISSING", appends them to
data/tech_summaries.json, and re-runs build_marketplace.py.

Requires: requests  (pip install requests)
Usage:    python3 refresh.py [--campus SB]
"""
import os, sys, json, subprocess, argparse

BASE = os.path.dirname(os.path.abspath(__file__))   # scripts/
ROOT = os.path.dirname(BASE)                          # repo root
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, os.path.join(ROOT, "src"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campus", default="SB")
    ap.add_argument("--delay", type=float, default=0.1)
    args = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)

    from ucsbie import cli as ucsbie
    s = ucsbie.make_session()

    sys.stderr.write("[refresh] harvesting technologies…\n")
    techs, total = ucsbie.fetch_tech_list(s, args.campus, fetch_all=True, verbose=True)
    ucsbie.enrich_with_details(s, techs, delay=args.delay, verbose=True)
    json.dump(techs, open(os.path.join(DATA, "tech_full.json"), "w"),
              ensure_ascii=False)
    sys.stderr.write(f"[refresh] {len(techs)} technologies written\n")

    sys.stderr.write("[refresh] harvesting ventures…\n")
    vents = ucsbie.fetch_startups(s, "all", verbose=True)
    json.dump(vents, open(os.path.join(DATA, "startups.json"), "w"),
              ensure_ascii=False)
    sys.stderr.write(f"[refresh] {len(vents)} ventures written\n")

    # which technologies still need a human/AI card summary?
    spath = os.path.join(DATA, "tech_summaries.json")
    summ = json.load(open(spath)) if os.path.exists(spath) else {}
    missing = [t["id"] for t in techs if t["id"] not in summ]
    print("SUMMARIES_MISSING:", json.dumps(missing))

    sys.stderr.write("[refresh] rebuilding Marketplace…\n")
    subprocess.run([sys.executable, os.path.join(BASE, "build_marketplace.py")], check=True)
    subprocess.run([sys.executable, os.path.join(BASE, "make_bundle.py")], check=True)
    sys.stderr.write("[refresh] done.\n")


if __name__ == "__main__":
    main()
