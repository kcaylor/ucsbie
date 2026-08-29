#!/usr/bin/env python3
"""
refresh.py — rebuild the UC Santa Barbara Innovation Marketplace from live sources.

Pipeline:
  1. Harvest all available technologies (with full detail) + all ventures
     via the ucsbie harvester (src/ucsbie/cli.py).
  2. Write canonical JSON into ./data/.
  3. Report any technologies that lack a card summary (new disclosures).
  4. Rebuild public/index.html (build_marketplace.py) and the AI data
     bundle under public/data/ (make_bundle.py).

New-technology summaries: this script falls back to a truncated description for
any tech missing from data/tech_summaries.json, so it always produces a valid
page on its own. The monthly scheduled Claude task generates proper one-line
summaries for the IDs printed under "SUMMARIES_MISSING", appends them to
data/tech_summaries.json, and re-runs build_marketplace.py.

Time-limited environments
-------------------------
Some runners (the Cowork workspace shell, CI steps) cap a single command at a
few tens of seconds and kill anything still running when the call returns. Two
features make the refresh survive that:

  * --workers N   fetch detail pages concurrently (default 6). This alone takes
                  a full refresh from roughly 70s to under 30s, which fits in a
                  single call.
  * --max-seconds S
                  stop cleanly after S seconds, checkpoint progress to
                  data/.refresh_state.json, and exit 75. Re-run the same command
                  to pick up exactly where it stopped. Repeat until exit 0.

Nothing under data/ is replaced and the HTML is never rebuilt until the harvest
is complete, so an interrupted run cannot publish a partial page.

Exit codes:  0 = complete   75 = incomplete, run again to resume   1 = error

Requires: requests  (pip install requests)

Usage:
    python3 refresh.py                          # one-shot, concurrent
    python3 refresh.py --max-seconds 30         # resumable; repeat until exit 0
    python3 refresh.py --fresh                  # ignore any existing checkpoint
"""
import os, sys, json, time, subprocess, argparse

BASE = os.path.dirname(os.path.abspath(__file__))   # scripts/
ROOT = os.path.dirname(BASE)                        # repo root
DATA = os.path.join(ROOT, "data")
STATE = os.path.join(DATA, ".refresh_state.json")
sys.path.insert(0, os.path.join(ROOT, "src"))

EX_RESUME = 75  # EX_TEMPFAIL: partial progress checkpointed, run again


def log(msg):
    sys.stderr.write(f"[refresh] {msg}\n")
    sys.stderr.flush()


def write_json(path, obj):
    """Write to a temp file in the same directory, then rename over the target.

    The previous good copy stays intact if the process is killed mid-write.
    """
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, ensure_ascii=False)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def load_state():
    try:
        with open(STATE) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_state(state):
    state["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    write_json(STATE, state)


def clear_state():
    """Drop the checkpoint. Some sandboxed mounts allow rename-over but not
    unlink, so fall back to emptying the file — load_state() reads {} as
    'no checkpoint' either way."""
    try:
        os.remove(STATE)
    except FileNotFoundError:
        pass
    except OSError:
        write_json(STATE, {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campus", default="SB")
    ap.add_argument("--delay", type=float, default=0.05,
                    help="pause before each detail fetch, per worker")
    ap.add_argument("--workers", type=int, default=6,
                    help="concurrent detail fetches (1 = sequential)")
    ap.add_argument("--max-seconds", type=float, default=0,
                    help="stop and checkpoint after this long; 0 = no limit")
    ap.add_argument("--fresh", action="store_true",
                    help="discard any existing checkpoint and start over")
    ap.add_argument("--no-build", action="store_true",
                    help="harvest and write JSON, but skip the HTML rebuild")
    args = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)

    deadline = time.monotonic() + args.max_seconds if args.max_seconds else None

    def expired():
        return deadline is not None and time.monotonic() > deadline

    def pause(state, what):
        save_state(state)
        left = sum(1 for r in state.get("techs", []) if not r.get("_enriched"))
        log(f"time budget reached during {what}; checkpointed "
            f"({left} technologies still to enrich). Re-run to resume.")
        print("RESUME_NEEDED")
        return EX_RESUME

    from ucsbie import cli as ucsbie
    s = ucsbie.make_session()

    if args.fresh and os.path.exists(STATE):
        clear_state()
        log("discarded existing checkpoint (--fresh)")
    state = load_state()
    if state.get("techs"):
        n_done = sum(1 for r in state["techs"] if r.get("_enriched"))
        log(f"resuming checkpoint from {state.get('updated', '?')}: "
            f"{n_done}/{len(state['techs'])} technologies enriched")

    # ---- phase 1: technology list ----------------------------------------
    if not state.get("techs"):
        log("harvesting technology list…")
        techs, _total = ucsbie.fetch_tech_list(s, args.campus, fetch_all=True,
                                               verbose=True)
        state["techs"] = techs
        save_state(state)
    techs = state["techs"]

    # ---- phase 2: detail pages (resumable) -------------------------------
    remaining = [r for r in techs if not r.get("_enriched")]
    if remaining:
        log(f"enriching {len(remaining)} technologies "
            f"({args.workers} worker(s))…")
        ucsbie.enrich_with_details(s, techs, delay=args.delay, verbose=True,
                                   workers=args.workers, deadline=deadline,
                                   skip_enriched=True, track_progress=True)
        save_state(state)
        if any(not r.get("_enriched") for r in techs):
            return pause(state, "technology details")

    # ---- phase 3: ventures ------------------------------------------------
    if state.get("ventures") is None:
        if expired():
            return pause(state, "ventures")
        log("harvesting ventures…")
        state["ventures"] = ucsbie.fetch_startups(s, "all", verbose=True)
        save_state(state)
    vents = state["ventures"]

    # ---- phase 4: publish JSON -------------------------------------------
    errs = [r["id"] for r in techs if r.get("error")]
    clean = [{k: v for k, v in r.items() if k != "_enriched"} for r in techs]
    write_json(os.path.join(DATA, "tech_full.json"), clean)
    write_json(os.path.join(DATA, "startups.json"), vents)
    log(f"{len(clean)} technologies, {len(vents)} ventures written"
        + (f" ({len(errs)} with fetch errors: {errs})" if errs else ""))

    # which technologies still need a human/AI card summary?
    spath = os.path.join(DATA, "tech_summaries.json")
    summ = json.load(open(spath)) if os.path.exists(spath) else {}
    missing = [t["id"] for t in clean if t["id"] not in summ]
    print("SUMMARIES_MISSING:", json.dumps(missing))

    # ---- phase 5: rebuild HTML + AI bundle --------------------------------
    if not args.no_build:
        log("rebuilding Marketplace…")
        subprocess.run([sys.executable,
                        os.path.join(BASE, "build_marketplace.py")], check=True)
        subprocess.run([sys.executable,
                        os.path.join(BASE, "make_bundle.py")], check=True)

    clear_state()
    log("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
