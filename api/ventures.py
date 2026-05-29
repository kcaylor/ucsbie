"""GET /api/ventures — UCSB ventures (TIA Startup Database).

Query params (all optional):
  q          keyword in company/about/founders
  status     Active | Acquired | Inactive
  industry   substring match (e.g. Healthcare)
  licensed   true  -> only ventures that license UCSB IP
  founded_after  minimum founding year
  limit      max results (default 300)
Returns JSON: { meta, count, ventures: [...] }.
"""
import json, os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DATA = os.path.join(os.path.dirname(__file__), "..", "public", "data", "ventures.json")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        bundle = json.load(open(DATA))
        vents = bundle["ventures"]
        qs = parse_qs(urlparse(self.path).query)
        q = (qs.get("q", [""])[0]).lower().strip()
        status = (qs.get("status", [""])[0]).strip().lower()
        industry = (qs.get("industry", [""])[0]).strip().lower()
        licensed = (qs.get("licensed", [""])[0]).strip().lower() in ("1", "true", "yes")
        after = qs.get("founded_after", [None])[0]
        try:
            limit = int(qs.get("limit", ["300"])[0])
        except ValueError:
            limit = 300

        out = []
        for v in vents:
            if q and q not in (v.get("company", "") + " " + v.get("about", "") + " " +
                               " ".join(v.get("founders") or [])).lower():
                continue
            if status and (v.get("status") or "").lower() != status:
                continue
            if industry and industry not in (v.get("industry") or "").lower():
                continue
            if licensed and not v.get("licenses_ucsb_ip"):
                continue
            if after:
                try:
                    if not v.get("founded") or int(v["founded"]) < int(after):
                        continue
                except ValueError:
                    pass
            out.append(v)
        out = out[:limit]

        body = json.dumps({"meta": bundle.get("meta", {}), "count": len(out),
                           "ventures": out}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(body)
