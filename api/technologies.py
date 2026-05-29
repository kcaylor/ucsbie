"""GET /api/technologies — UCSB technologies available for licensing.

Query params (all optional):
  q              keyword in title/summary/description
  field          top-level category (e.g. Semiconductors)
  disclosed_after  minimum UC-case disclosure year (e.g. 2022)
  patent         issued | pending
  limit          max results (default 200)
Returns JSON: { meta, count, technologies: [...] }.
"""
import json, os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

def _data(name):
    here = os.path.dirname(__file__)
    for c in (os.path.join(here, "..", "public", "data", name),
              os.path.join(here, "public", "data", name),
              os.path.join(os.getcwd(), "public", "data", name),
              os.path.join("/var/task", "public", "data", name)):
        if os.path.exists(c):
            return c
    return os.path.join(here, "..", "public", "data", name)


DATA = _data("technologies.json")


def _maturity(t):
    blob = " ".join(p.get("type", "") for p in (t.get("patents") or [])).lower() + " " + (t.get("patent_status") or "").lower()
    if "issued" in blob or "granted" in blob:
        return "issued"
    if any(k in blob for k in ("application", "pending", "filed", "provisional")):
        return "pending"
    return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        bundle = json.load(open(DATA))
        techs = bundle["technologies"]
        qs = parse_qs(urlparse(self.path).query)
        q = (qs.get("q", [""])[0]).lower().strip()
        field = (qs.get("field", [""])[0]).strip()
        after = qs.get("disclosed_after", [None])[0]
        patent = (qs.get("patent", [""])[0]).strip().lower()
        try:
            limit = int(qs.get("limit", ["200"])[0])
        except ValueError:
            limit = 200

        out = []
        for t in techs:
            if q and q not in (t.get("title", "") + " " + t.get("summary", "") + " " +
                               t.get("description", "")).lower():
                continue
            if field and field not in (t.get("fields") or []):
                continue
            if after:
                try:
                    if not t.get("disclosed_year") or int(t["disclosed_year"]) < int(after):
                        continue
                except ValueError:
                    pass
            if patent and _maturity(t) != patent:
                continue
            out.append(t)
        out = out[:limit]

        body = json.dumps({"meta": bundle.get("meta", {}), "count": len(out),
                           "technologies": out}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(body)
