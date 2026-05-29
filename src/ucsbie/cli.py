#!/usr/bin/env python3
"""
ucsbie — UCSB Innovation & Entrepreneurship data CLI
====================================================
One tool, two public data domains, agent-friendly output:

  tech       Available technologies for licensing (UCOP techtransfer portal)
  startups   UCSB ventures (TIA Startup Database)

Designed for agents AND humans. JSON is the default output (stable, documented
schema below); CSV and table formats are also available. No browser needed —
it speaks HTTP directly, including the techtransfer portal's ASP.NET AJAX paging.

DEPENDENCIES
    Python 3.8+  and  `requests`   (pip install requests)

QUICK START
    # Technologies
    ucsbie tech list --campus SB --all                      # all available techs
    ucsbie tech list --campus SB --all --details            # + full records
    ucsbie tech get 34770                                    # one full record
    ucsbie tech categories --campus SB
    ucsbie tech search "quantum" --campus SB --details

    # Startups / ventures
    ucsbie startups list                                     # all UCSB ventures
    ucsbie startups list --filter licensed                  # only those licensing UCSB IP
    ucsbie startups list --status Active --industry Healthcare

    # Anything as CSV or a file
    ucsbie tech list --campus SB --all --format csv --out tech.csv
    ucsbie startups list --format json --out ventures.json

JSON SCHEMAS  (stable keys; lists stay lists)
    tech list (basic)   {id, title, url}
    tech list --details / get
        {id, title, url, uc_case, inventors[], description, advantages,
         patent_status, categories[], patents[{country,type,number,dated,case}],
         patent_numbers[]}
    tech categories     {category, count, top_level}
    startups list
        {company, about, status, website, founding_year, founders[],
         industry, capital_raised, capital_raised_musd, licenses_ucsb_ip, source}

CAMPUS CODES (tech only)
    SB Santa Barbara · B Berkeley · LA Los Angeles · SD San Diego · SF San Francisco
    D Davis · I Irvine · R Riverside · SC Santa Cruz · M Merced · ALL = whole system

CONTACT (for downstream use)  innovation@ucsb.edu
"""

import argparse
import csv
import html as _html
import io
import json
import math
import re
import sys
import time

try:
    import requests
except ImportError:
    sys.stderr.write("ERROR: this tool needs the 'requests' package.\n"
                     "Install it with:  pip install requests\n")
    sys.exit(2)

TT_BASE = "https://techtransfer.universityofcalifornia.edu"
TT_LIST = TT_BASE + "/Default?RunSearch=true&campus={campus}"
TT_DETAIL = TT_BASE + "/NCD/{tid}.html"
STARTUP_URL = "https://tia.ucsb.edu/startup-database/"
CONTACT = "innovation@ucsb.edu"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

TOP_LEVEL = {
    "Agriculture & Animal Science", "Biotechnology", "Communications", "Computer",
    "Energy", "Engineering", "Environment", "Imaging", "Materials & Chemicals",
    "Medical", "Nanotechnology", "Optics and Photonics", "Research Tools",
    "Security and Defense", "Semiconductors", "Sensors & Instrumentation",
    "Transportation", "Veterinary",
}

_TAG_RE = re.compile(r"<[^>]+>")


# ============================ HTTP helpers ================================== #
def make_session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    return s


def _get(session, url, timeout=30, retries=3):
    last = None
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed for {url}: {last}")


def _post(session, url, data, headers=None, timeout=30, retries=3):
    last = None
    for attempt in range(retries):
        try:
            r = session.post(url, data=data, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"POST failed for {url}: {last}")


def _clean(s):
    return _html.unescape(_TAG_RE.sub("", s or "")).replace("\xa0", " ").strip()


def _money_to_musd(raw):
    if not raw:
        return None
    m = re.search(r"\$?\s*([\d,.]+)\s*([MBK]?)", raw)
    if not m:
        return None
    try:
        val = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    mult = {"B": 1000.0, "M": 1.0, "K": 0.001, "": 1.0}.get(m.group(2), 1.0)
    return round(val * mult, 4)


def _year(raw):
    m = re.match(r"^\s*(\d{4})\s*$", raw or "")
    return int(m.group(1)) if m else None


def _split_people(raw):
    if not raw or raw == "-":
        return []
    parts = re.split(r"\s*(?:&|,| and )\s*", raw)
    return [p.strip() for p in parts if p.strip()]


# ============================ TECHNOLOGIES ================================== #
_INPUT_RE = re.compile(r'<input[^>]*\bname="([^"]+)"[^>]*\bvalue="([^"]*)"[^>]*>', re.I)
_INPUT_RE2 = re.compile(r'<input[^>]*\bvalue="([^"]*)"[^>]*\bname="([^"]+)"[^>]*>', re.I)
_ROW_RE = re.compile(r"""href=['"][^'"]*?/NCD/(\d+)\.html['"][^>]*>(.*?)</a>""", re.I | re.S)
_TOTAL_RE = re.compile(r'(\d[\d,]*)\s+Technolog', re.I)
_CAT_RE = re.compile(r'lblCategoryName"[^>]*>(.*?)</span>.*?lblCatCount"[^>]*>\[(\d+)\]', re.I | re.S)
_PB_RE = re.compile(r'PostBackOptions\(&quot;([^&]+)&quot;|PostBackOptions\("([^"]+)"')


def _all_form_fields(html):
    fields = {}
    for m in _INPUT_RE.finditer(html):
        fields[m.group(1)] = m.group(2)
    for m in _INPUT_RE2.finditer(html):
        fields.setdefault(m.group(2), m.group(1))
    return fields


def _ajax_hidden(text):
    out = {}
    for name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
        m = re.search(r"\|hiddenField\|" + re.escape(name) + r"\|([^|]*)\|", text)
        if m:
            out[name] = m.group(1)
    return out


def _parse_rows(html):
    seen, rows = set(), []
    for m in _ROW_RE.finditer(html):
        tid = m.group(1)
        title = _clean(m.group(2))
        if tid in seen or not title:
            continue
        seen.add(tid)
        rows.append({"id": tid, "title": title, "url": TT_DETAIL.format(tid=tid)})
    return rows


def _parse_total(html):
    m = _TOTAL_RE.search(_TAG_RE.sub(" ", html))
    return int(m.group(1).replace(",", "")) if m else None


def _find_postback_target(html, needle):
    for m in _PB_RE.finditer(html):
        target = m.group(1) or m.group(2)
        if target and needle.lower() in target.lower():
            return target
    return None


def _find_input_name(html, suffix):
    m = re.search(r'name="([^"]*' + re.escape(suffix) + r')"', html)
    return m.group(1) if m else None


def _update_panel_id(html):
    m = re.search(r"_initialize\([^,]+,\s*'[^']+',\s*\[\s*'t([^']+)'", html)
    return m.group(1) if m else "ctl00$ContentPlaceHolder1$ucNCDList$upList"


def _total_pages(html):
    m = re.search(r'lblTotalPages"[^>]*>\s*(\d+)\s*<', html)
    return int(m.group(1)) if m else None


def _merge(rows, new):
    have = {r["id"] for r in rows}
    for r in new:
        if r["id"] not in have:
            have.add(r["id"])
            rows.append(r)
    return rows


def _maybe_filter(rows, keyword):
    if not keyword:
        return rows
    k = keyword.lower()
    return [r for r in rows if k in r["title"].lower() or k == r["id"]]


def fetch_tech_list(session, campus, keyword=None, fetch_all=False,
                    max_pages=60, verbose=False):
    url = TT_LIST.format(campus=campus)
    html = _get(session, url)
    total = _parse_total(html)
    rows = _parse_rows(html)
    if verbose:
        sys.stderr.write(f"[ucsbie] tech page 1: {len(rows)} rows; total {total}\n")
    if not fetch_all:
        return _maybe_filter(rows, keyword), total

    fields = _all_form_fields(html)
    panel = _update_panel_id(html)
    next_tgt = _find_postback_target(html, "ucPagination$nextPage") \
        or "ctl00$ContentPlaceHolder1$ucNCDList$ucPagination$nextPage"
    go_tgt = next_tgt.rsplit("$", 1)[0] + "$btnGo"
    pg_field = _find_input_name(html, "ucPagination$txtPageNumber") \
        or "ctl00$ContentPlaceHolder1$ucNCDList$ucPagination$txtPageNumber"
    sm_field = "ctl00$ScriptManager1"
    total_pages = _total_pages(html) or math.ceil((total or len(rows)) / max(1, len(rows)))
    headers = {"X-MicrosoftAjax": "Delta=true", "X-Requested-With": "XMLHttpRequest",
               "Referer": url}

    page = 2
    while page <= total_pages and page <= max_pages:
        payload = dict(fields)
        payload[pg_field] = str(page)
        payload[sm_field] = panel + "|" + go_tgt
        payload["__EVENTTARGET"] = go_tgt
        payload["__EVENTARGUMENT"] = ""
        payload["__ASYNCPOST"] = "true"
        resp = _post(session, url, payload, headers=headers)
        before = len(rows)
        rows = _merge(rows, _parse_rows(resp))
        fields.update(_ajax_hidden(resp))
        if verbose:
            sys.stderr.write(f"[ucsbie] tech page {page}/{total_pages}: "
                             f"+{len(rows) - before} (total {len(rows)})\n")
        if (total and len(rows) >= total) or len(rows) == before:
            break
        page += 1
    return _maybe_filter(rows, keyword), total


def fetch_categories(session, campus):
    html = _get(session, TT_LIST.format(campus=campus))
    cats, seen = [], {}
    for m in _CAT_RE.finditer(html):
        name = _clean(m.group(1))
        count = int(m.group(2))
        key = name.lower()
        if key in seen:
            if count > cats[seen[key]]["count"]:
                cats[seen[key]]["count"] = count
            continue
        seen[key] = len(cats)
        cats.append({"category": name, "count": count, "top_level": name in TOP_LEVEL})
    return cats


def fetch_tech_detail(session, tid):
    html = _get(session, TT_DETAIL.format(tid=tid))
    title = None
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if m:
        title = _clean(m.group(1))
    if not title:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        title = _clean(m.group(1)) if m else None

    def section(*labels):
        for lab in labels:
            m = re.search(re.escape(lab) + r"\s*</[^>]+>(.*?)(?:<h\d|<strong|$)",
                          html, re.I | re.S)
            if m:
                txt = _clean(re.sub(r"\s+", " ", _TAG_RE.sub(" ", m.group(1))))
                if txt:
                    return txt[:1500]
        return None

    cats, seen = [], set()
    for c in re.findall(r'hlCategories[0-9_]*"[^>]*>([^<]+)</a>', html):
        c = _clean(c)
        if c and c not in seen:
            seen.add(c)
            cats.append(c)

    inventors = []
    mi = re.search(r"<h3>\s*Inventors\s*</h3>(.*?)</ul>", html, re.I | re.S)
    if mi:
        for li in re.findall(r"<li[^>]*>(.*?)</li>", mi.group(1), re.S):
            name = _clean(li)
            if name:
                inventors.append(name)

    mc = re.search(r"UC Case\s*([0-9][0-9\-]+)", html, re.I)
    uc_case = mc.group(1) if mc else None
    case_year = int(uc_case[:4]) if uc_case and uc_case[:4].isdigit() else None

    patents = []
    pm = re.search(r"Patent Status\s*</h3>(.*?)</table>", html, re.I | re.S)
    if pm:
        header = None
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", pm.group(1), re.S):
            cells = [_clean(re.sub(r"\s+", " ", _TAG_RE.sub(" ", c)))
                     for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
            cells = [c for c in cells if c]
            if not cells:
                continue
            if header is None and any(k in " ".join(cells)
                                      for k in ("Country", "Number", "Type")):
                header = [c.lower() for c in cells]
                continue
            if header and len(cells) >= 2:
                patents.append(dict(zip(header, cells)))
    patent_numbers = sorted({p.get("number", "").strip() for p in patents if p.get("number")}
                            or set(re.findall(r"\bUS\s?\d{7,8}\b", html)))

    return {
        "id": str(tid), "title": title, "url": TT_DETAIL.format(tid=tid),
        "uc_case": uc_case, "case_year": case_year, "inventors": inventors,
        "description": section("Full Description", "Brief Description", "Background"),
        "advantages": section("Advantages", "Suggested uses", "Applications"),
        "patent_status": section("Patent Status", "Patent Information"),
        "categories": cats, "patents": patents, "patent_numbers": patent_numbers,
    }


def enrich_with_details(session, rows, delay=0.15, verbose=False):
    keys = ("uc_case", "case_year", "inventors", "description", "advantages",
            "patent_status", "categories", "patents", "patent_numbers")
    n = len(rows)
    for i, r in enumerate(rows, 1):
        try:
            d = fetch_tech_detail(session, r["id"])
            for k in keys:
                r[k] = d.get(k)
        except Exception as e:  # noqa: BLE001
            r["error"] = str(e)
        if verbose and (i % 25 == 0 or i == n):
            sys.stderr.write(f"[ucsbie] details {i}/{n}\n")
        if delay:
            time.sleep(delay)
    return rows


# ============================ STARTUPS ===================================== #
def fetch_startups(session, which="all", status=None, industry=None, verbose=False):
    html = _get(session, STARTUP_URL)
    aff_idx = html.find("Affiliated Startups")
    rows = []
    for m in re.finditer(r"<table", html):
        start = m.start()
        end = html.find("</table>", start)
        table = html[start:end]
        licensed = start < aff_idx if aff_idx > 0 else True
        body = re.search(r"<tbody>(.*?)</tbody>", table, re.S)
        body = body.group(1) if body else table
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
            cells = [_clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(cells) < 8 or not cells[0]:
                continue
            rows.append({
                "company": cells[0], "about": cells[1], "status": cells[2],
                "website": cells[3] if cells[3] not in ("", "-") else None,
                "founding_year": _year(cells[4]),
                "founders": _split_people(cells[5]),
                "industry": cells[6],
                "capital_raised": cells[7] if cells[7] not in ("", "-") else None,
                "capital_raised_musd": _money_to_musd(cells[7]),
                "licenses_ucsb_ip": licensed,
                "source": STARTUP_URL,
            })
    if verbose:
        sys.stderr.write(f"[ucsbie] startups parsed: {len(rows)}\n")
    if which == "licensed":
        rows = [r for r in rows if r["licenses_ucsb_ip"]]
    elif which == "affiliated":
        rows = [r for r in rows if not r["licenses_ucsb_ip"]]
    if status:
        rows = [r for r in rows if (r["status"] or "").lower() == status.lower()]
    if industry:
        k = industry.lower()
        rows = [r for r in rows if k in (r["industry"] or "").lower()]
    return rows


# ============================ OUTPUT ======================================= #
def emit(records, fmt, out_path=None, columns=None):
    single = isinstance(records, dict)
    if single:
        records = [records]
    if fmt == "json":
        text = json.dumps(records[0] if single else records,
                          indent=2, ensure_ascii=False)
    elif fmt == "csv":
        cols = columns or (list(records[0].keys()) if records else [])
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in records:
            w.writerow({c: _flat(r.get(c, "")) for c in cols})
        text = buf.getvalue()
    else:
        cols = columns or (list(records[0].keys()) if records else [])
        widths = {c: min(70, max(len(c), *(len(_flat(r.get(c, ""))) for r in records))
                         if records else len(c)) for c in cols}
        lines = [" | ".join(c.ljust(widths[c]) for c in cols),
                 "-+-".join("-" * widths[c] for c in cols)]
        for r in records:
            lines.append(" | ".join(_flat(r.get(c, ""))[:widths[c]].ljust(widths[c])
                                    for c in cols))
        text = "\n".join(lines)

    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text + ("" if text.endswith("\n") else "\n"))
        sys.stderr.write(f"[ucsbie] wrote {len(records)} record(s) -> {out_path}\n")
    else:
        print(text)


def _flat(v):
    if isinstance(v, (list, tuple)):
        return "; ".join(_flat(x) for x in v)
    if isinstance(v, dict):
        return " ".join(f"{k}={x}" for k, x in v.items())
    return "" if v is None else str(v)


TECH_DETAIL_COLS = ["id", "title", "uc_case", "case_year", "inventors", "categories",
                    "description", "advantages", "patent_numbers", "url"]
STARTUP_COLS = ["company", "status", "founding_year", "industry", "founders",
                "capital_raised", "capital_raised_musd", "licenses_ucsb_ip",
                "website", "about"]


# ============================ CLI ========================================== #
def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--format", choices=["json", "csv", "table"], default="json")
    common.add_argument("--out", help="write to file instead of stdout")
    common.add_argument("--campus", default="SB", help="campus code (tech only); ALL = system")
    common.add_argument("-v", "--verbose", action="store_true")

    p = argparse.ArgumentParser(prog="ucsbie", parents=[common],
                                description="UCSB I&E data CLI (technologies + startups).")
    dom = p.add_subparsers(dest="domain", required=True)

    # tech domain
    tech = dom.add_parser("tech", parents=[common], help="available technologies")
    tsub = tech.add_subparsers(dest="cmd", required=True)
    tl = tsub.add_parser("list", parents=[common], help="list technologies")
    tl.add_argument("--all", action="store_true", help="paginate through every result")
    tl.add_argument("--keyword", help="filter titles by keyword")
    tl.add_argument("--details", action="store_true", help="fetch full record per technology")
    tl.add_argument("--delay", type=float, default=0.15)
    ts = tsub.add_parser("search", parents=[common], help="keyword search (all pages)")
    ts.add_argument("terms")
    ts.add_argument("--details", action="store_true")
    ts.add_argument("--delay", type=float, default=0.15)
    tsub.add_parser("categories", parents=[common], help="category facets + counts")
    tg = tsub.add_parser("get", parents=[common], help="full detail for one technology")
    tg.add_argument("techid")

    # startups domain
    st = dom.add_parser("startups", parents=[common], help="UCSB ventures")
    ssub = st.add_subparsers(dest="cmd", required=True)
    sl = ssub.add_parser("list", parents=[common], help="list ventures")
    sl.add_argument("--filter", choices=["all", "licensed", "affiliated"],
                    default="all", help="licensed = licenses UCSB IP")
    sl.add_argument("--status", help="filter by status (Active/Acquired/Inactive)")
    sl.add_argument("--industry", help="filter by industry substring")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    campus = "" if str(args.campus).upper() == "ALL" else args.campus
    session = make_session()
    try:
        if args.domain == "tech":
            if args.cmd == "list":
                rows, total = fetch_tech_list(session, campus, keyword=args.keyword,
                                              fetch_all=args.all, verbose=args.verbose)
                cols = ["id", "title", "url"]
                if args.details:
                    enrich_with_details(session, rows, delay=args.delay, verbose=args.verbose)
                    cols = TECH_DETAIL_COLS
                emit(rows, args.format, args.out, columns=cols)
            elif args.cmd == "search":
                rows, _ = fetch_tech_list(session, campus, keyword=args.terms,
                                          fetch_all=True, verbose=args.verbose)
                cols = ["id", "title", "url"]
                if args.details:
                    enrich_with_details(session, rows, delay=args.delay, verbose=args.verbose)
                    cols = TECH_DETAIL_COLS
                emit(rows, args.format, args.out, columns=cols)
            elif args.cmd == "categories":
                emit(fetch_categories(session, campus), args.format, args.out,
                     columns=["category", "count", "top_level"])
            elif args.cmd == "get":
                emit(fetch_tech_detail(session, args.techid), args.format, args.out)

        elif args.domain == "startups":
            if args.cmd == "list":
                rows = fetch_startups(session, which=args.filter, status=args.status,
                                      industry=args.industry, verbose=args.verbose)
                emit(rows, args.format, args.out, columns=STARTUP_COLS)
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"ERROR: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
