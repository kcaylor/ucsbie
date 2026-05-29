#!/usr/bin/env python3
"""Generate the AI-ready data bundle (public/data/*) from data/*.json.

Reads:  data/tech_full.json, data/startups.json, data/tech_summaries.json
Writes: public/data/ucsb-ie.json, technologies.json, ventures.json,
        ucsb-technologies.csv, ucsb-ventures.csv
Run after scripts/refresh.py.
"""
import json, csv, datetime, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "public", "data")
os.makedirs(OUT, exist_ok=True)

TOP_LEVEL = {"Agriculture & Animal Science", "Biotechnology", "Communications", "Computer",
    "Energy", "Engineering", "Environment", "Imaging", "Materials & Chemicals", "Medical",
    "Nanotechnology", "Optics and Photonics", "Research Tools", "Security and Defense",
    "Semiconductors", "Sensors & Instrumentation", "Transportation", "Veterinary"}


def load(name):
    return json.load(open(os.path.join(DATA, name)))


def main():
    tech = load("tech_full.json")
    vent = load("startups.json")
    try:
        summ = load("tech_summaries.json")
    except Exception:
        summ = {}
    today = datetime.date.today().isoformat()

    techs = [{
        "tech_id": t["id"], "title": t["title"], "summary": summ.get(t["id"], ""),
        "disclosed_year": t.get("case_year"), "uc_case": t.get("uc_case"),
        "fields": [c for c in (t.get("categories") or []) if c in TOP_LEVEL],
        "categories": t.get("categories") or [], "inventors": t.get("inventors") or [],
        "patent_status": t.get("patent_status") or "", "patents": t.get("patents") or [],
        "description": t.get("description") or "", "advantages": t.get("advantages") or "",
        "url": t["url"],
    } for t in tech]

    vents = [{
        "company": v["company"], "status": v.get("status"), "founded": v.get("founding_year"),
        "industry": (v.get("industry") or "").replace("﻿", "").strip(),
        "licenses_ucsb_ip": bool(v.get("licenses_ucsb_ip")),
        "capital_raised": v.get("capital_raised"), "capital_raised_musd": v.get("capital_raised_musd"),
        "founders": v.get("founders") or [], "website": v.get("website"), "about": v.get("about") or "",
    } for v in vent]

    meta = {"generated": today,
            "source_technologies": "https://techtransfer.universityofcalifornia.edu/default?campus=SB",
            "source_ventures": "https://tia.ucsb.edu/startup-database/",
            "contact": "info@innovation.ucsb.edu",
            "note": "Public UCSB I&E data. Technologies available for licensing + UCSB ventures. Refreshed monthly."}

    json.dump({"meta": meta, "technologies": techs, "ventures": vents},
              open(os.path.join(OUT, "ucsb-ie.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"meta": meta, "technologies": techs},
              open(os.path.join(OUT, "technologies.json"), "w"), ensure_ascii=False)
    json.dump({"meta": meta, "ventures": vents},
              open(os.path.join(OUT, "ventures.json"), "w"), ensure_ascii=False)

    with open(os.path.join(OUT, "ucsb-technologies.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tech_id", "title", "summary", "disclosed_year", "uc_case",
                    "fields", "patent_status", "inventors", "url"])
        for t in techs:
            w.writerow([t["tech_id"], t["title"], t["summary"], t["disclosed_year"] or "",
                        t["uc_case"] or "", "; ".join(t["fields"]), t["patent_status"],
                        "; ".join(t["inventors"]), t["url"]])
    with open(os.path.join(OUT, "ucsb-ventures.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company", "status", "founded", "industry", "licenses_ucsb_ip",
                    "capital_raised", "capital_raised_musd", "founders", "website", "about"])
        for v in vents:
            w.writerow([v["company"], v["status"], v["founded"] or "", v["industry"],
                        v["licenses_ucsb_ip"], v["capital_raised"] or "",
                        v["capital_raised_musd"] if v["capital_raised_musd"] is not None else "",
                        "; ".join(v["founders"]), v["website"] or "", v["about"]])

    print(f"bundle: {len(techs)} technologies, {len(vents)} ventures, generated {today}")


if __name__ == "__main__":
    main()
