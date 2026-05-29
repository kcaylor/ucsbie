"""GET /api/categories — UCSB technology category facets with counts.

Counts are over top-level fields; they overlap (a technology can carry several),
so they sum to more than the unique technology count.
Returns JSON: { meta, count, categories: [{category, count}] }.
"""
import json, os
from collections import Counter
from http.server import BaseHTTPRequestHandler

DATA = os.path.join(os.path.dirname(__file__), "..", "public", "data", "technologies.json")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        bundle = json.load(open(DATA))
        c = Counter()
        for t in bundle["technologies"]:
            for f in (t.get("fields") or []):
                c[f] += 1
        cats = [{"category": k, "count": v} for k, v in c.most_common()]
        body = json.dumps({"meta": bundle.get("meta", {}), "count": len(cats),
                           "categories": cats}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(body)
