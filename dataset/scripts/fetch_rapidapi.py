"""Fetch for-sale listings from the unofficial "UK Real Estate Rightmove" API
on RapidAPI (provider ntd119).

Keys: RAPID_API_KEY, RAPIDAPI_KEY and RAPIDAPI_KEY_2, read from the environment,
dataset/.env or the repository-root .env (real environment variables win, then
dataset/.env, then the root .env). Key values are never printed, logged or
written anywhere.

Budget: every call is appended to raw/rapidapi/_calls.log (metadata only, no
key). A key is not used once it has made --cap calls (default 250) in the
current calendar month according to that log. HTTP 429/403 stops the run.

Endpoints (from the RapidAPI playground, 23 Oct 2026):
  GET /auto-complete                 location (place name) -> data[i].locationIdentifier
  GET /buy/property-for-sale         identifier (required, e.g. REGION^93965), page,
                                     min_price, max_price, min_bedroom, max_bedroom,
                                     property_type (Detached,SemiDetached,Terraced,Flat,...),
                                     do_not_show_retirement_home, do_not_show_buying_schemes,
                                     has_include_under_offer_sold_stc, sort_by, ...
  GET /buy/property-for-sale/detail  id (required)

Usage (from the dataset/ directory):
  python3 -I scripts/fetch_rapidapi.py --dataset . budget
  python3 -I scripts/fetch_rapidapi.py --dataset . autocomplete --query Brighton
  python3 -I scripts/fetch_rapidapi.py --dataset . probe --identifier 'REGION^93965'
  python3 -I scripts/fetch_rapidapi.py --dataset . search --identifier 'REGION^93965' --pages 1 [--flats]
                                       [--min-price 250000] [--max-price 700000] [--sort VALUE]
  python3 -I scripts/fetch_rapidapi.py --dataset . details --max 50 [--identifier 'REGION^93965']
                                       [--min-price 250000] [--max-price 700000]

--min-price and --max-price must lie within the listing rules' price range
(rm.MIN_PRICE to rm.MAX_PRICE). On `search` they set the API price band; on
`details` they skip search cards priced outside the band. --sort is passed to
the API as sort_by unchecked, as the accepted values are not documented.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rm_common as rm  # noqa: E402

HOST = "uk-real-estate-rightmove.p.rapidapi.com"
KEY_VARS = ("RAPID_API_KEY", "RAPIDAPI_KEY", "RAPIDAPI_KEY_2")


def load_dotenv(path):
    """Minimal KEY=value reader. Does not override variables already set."""
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


class Client:
    def __init__(self, ds, cap, delay):
        self.raw = os.path.join(ds, "raw", "rapidapi")
        os.makedirs(self.raw, exist_ok=True)
        self.log_path = os.path.join(self.raw, "_calls.log")
        self.cap = cap
        self.delay = delay
        self.last = 0.0
        self.ctx = rm.ssl_context()
        self.keys = [(var, os.environ.get(var)) for var in KEY_VARS if os.environ.get(var)]

    def used(self):
        month = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")
        counts = {var: 0 for var in KEY_VARS}
        if os.path.exists(self.log_path):
            for line in open(self.log_path, encoding="utf-8"):
                r = json.loads(line)
                if r.get("ts", "").startswith(month) and r.get("key") in counts:
                    counts[r["key"]] += 1
        return counts

    def pick_key(self):
        used = self.used()
        for var, val in self.keys:
            if used[var] < self.cap:
                return var, val
        return None, None

    def call(self, endpoint, params, rel_path):
        dest = os.path.join(self.raw, rel_path)
        if os.path.exists(dest):
            with open(dest, encoding="utf-8") as f:
                return json.load(f)
        var, val = self.pick_key()
        if not var:
            raise SystemExit("budget exhausted: every key has made %d calls this month" % self.cap)
        wait = self.delay - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        url = "https://%s%s?%s" % (HOST, endpoint, urllib.parse.urlencode(params))
        req = urllib.request.Request(url, headers={
            "x-rapidapi-key": val, "x-rapidapi-host": HOST, "User-Agent": rm.USER_AGENT})
        status, body, remaining = None, b"", None
        try:
            with urllib.request.urlopen(req, timeout=60, context=self.ctx) as r:
                status, body = r.status, r.read()
                remaining = r.headers.get("x-ratelimit-requests-remaining")
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read()
            remaining = e.headers.get("x-ratelimit-requests-remaining")
        except urllib.error.URLError as e:
            status = "error: %s" % e.reason
        self.last = time.monotonic()
        rec = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "key": var,
               "endpoint": endpoint, "params": params, "status": status, "bytes": len(body),
               "ratelimit_remaining": remaining,
               "path": "raw/rapidapi/" + rel_path if status == 200 else None}
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("  %s %s -> %s (%d bytes, key=%s, provider says remaining=%s)"
              % (endpoint, params, status, len(body), var, remaining))
        if status in (401, 403, 429):
            raise SystemExit("stopped: HTTP %s %s" % (status, body[:200].decode("utf-8", "replace")))
        if status != 200:
            return None
        data = json.loads(body)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return data


def known_ids(ds):
    """Rightmove ids already in listings.jsonl (stored as rm-<id>)."""
    path = os.path.join(ds, "listings.jsonl")
    if not os.path.exists(path):
        return set()
    return {json.loads(line)["id"][3:] for line in open(path, encoding="utf-8") if line.strip()}


def price_band(min_price=None, max_price=None):
    """Price band within the listing rules' range; None means the rule's limit."""
    lo = rm.MIN_PRICE if min_price is None else min_price
    hi = rm.MAX_PRICE if max_price is None else max_price
    if not (rm.MIN_PRICE <= lo <= hi <= rm.MAX_PRICE):
        raise ValueError("price band %s-%s must satisfy %d <= min <= max <= %d"
                         % (lo, hi, rm.MIN_PRICE, rm.MAX_PRICE))
    return lo, hi


def search_params(identifier, page, flats, min_price=None, max_price=None, sort=None):
    lo, hi = price_band(min_price, max_price)
    p = {"identifier": identifier, "page": str(page), "min_price": str(lo),
         "max_price": str(hi), "do_not_show_retirement_home": "true",
         "do_not_show_buying_schemes": "true"}
    if sort:
        p["sort_by"] = sort
    if flats:
        p.update({"property_type": "Flat", "min_bedroom": "1", "max_bedroom": "3"})
    return p


def search_path(params):
    h = hashlib.sha1(json.dumps(params, sort_keys=True).encode()).hexdigest()[:10]
    safe = params["identifier"].replace("^", "_")
    return "search/%s_p%s_%s.json" % (safe, params["page"], h)


def search_ids(raw, known, identifier=None, min_price=None, max_price=None):
    """Search ids worth a detail call: card passes the listing rules and the
    price band, the property is not already in listings.jsonl and was not
    already scraped directly (that page has the same data)."""
    lo, hi = price_band(min_price, max_price)
    ids, skipped = [], {"card_rule": 0, "price_band": 0, "already_scraped": 0, "known": 0}
    scraped = os.path.join(os.path.dirname(raw), "rightmove", "property")
    prefix = (identifier.replace("^", "_") + "_p") if identifier else ""
    for path in sorted(glob.glob(os.path.join(raw, "search", prefix + "*.json"))):
        data = json.load(open(path, encoding="utf-8"))
        for item in (data.get("data") or []):
            pid = item.get("id") if isinstance(item, dict) else None
            if pid is None or str(pid) in ids:
                continue
            if rm.card_rejection(item):
                skipped["card_rule"] += 1
            elif not lo <= item["price"]["amount"] <= hi:
                skipped["price_band"] += 1
            elif str(pid) in known:
                skipped["known"] += 1
            elif os.path.exists(os.path.join(scraped, "%s.html.gz" % pid)):
                skipped["already_scraped"] += 1
            else:
                ids.append(str(pid))
    print("detail candidates: %d; skipped: %s" % (len(ids), skipped))
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--cap", type=int, default=250, help="max calls per key per month (free tier ~300)")
    ap.add_argument("--delay", type=float, default=1.5)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("budget")
    p = sub.add_parser("probe")
    p.add_argument("--identifier", required=True)
    s = sub.add_parser("search")
    s.add_argument("--identifier", required=True)
    s.add_argument("--pages", type=int, default=1)
    s.add_argument("--flats", action="store_true")
    s.add_argument("--min-price", type=int)
    s.add_argument("--max-price", type=int)
    s.add_argument("--sort", help="passed through as sort_by; accepted values are not documented")
    ac = sub.add_parser("autocomplete")
    ac.add_argument("--query", required=True)
    d = sub.add_parser("details")
    d.add_argument("--max", type=int, default=20)
    d.add_argument("--min-price", type=int, help="skip cards priced below this")
    d.add_argument("--max-price", type=int, help="skip cards priced above this")
    d.add_argument("--identifier", help="only ids from searches for this location, e.g. REGION^1114")
    a = ap.parse_args()
    if a.cmd in ("search", "details"):
        try:
            price_band(a.min_price, a.max_price)
        except ValueError as e:
            ap.error(str(e))

    load_dotenv(os.path.join(a.dataset, ".env"))
    load_dotenv(os.path.join(a.dataset, "..", ".env"))
    c = Client(a.dataset, a.cap, a.delay)
    for var in KEY_VARS:
        print("%s: %s" % (var, "set" if os.environ.get(var) else "not set"))
    print("calls this month per key:", c.used(), "cap:", a.cap)
    if a.cmd == "budget":
        return
    if not c.keys:
        raise SystemExit("no RapidAPI key set; nothing fetched")

    if a.cmd == "autocomplete":
        slug = "".join(ch if ch.isalnum() else "_" for ch in a.query.lower())
        data = c.call("/auto-complete", {"location": a.query}, "autocomplete/%s.json" % slug)
        for item in (data or {}).get("data") or []:
            if isinstance(item, dict):
                print(item.get("locationIdentifier"), "|", item.get("displayName"))
    elif a.cmd == "probe":
        params = search_params(a.identifier, 1, True)
        data = c.call("/buy/property-for-sale", params, search_path(params))
        ids = [str(x["id"]) for x in (data or {}).get("data") or [] if isinstance(x, dict) and x.get("id")]
        print("search returned keys:", list((data or {}).keys()), "ids:", len(ids))
        if ids:
            det = c.call("/buy/property-for-sale/detail", {"id": ids[0]}, "detail/%s.json" % ids[0])
            print("detail returned keys:", list((det or {}).keys()))
    elif a.cmd == "search":
        for page in range(1, a.pages + 1):
            params = search_params(a.identifier, page, a.flats, a.min_price, a.max_price, a.sort)
            c.call("/buy/property-for-sale", params, search_path(params))
    elif a.cmd == "details":
        done = 0
        for pid in search_ids(c.raw, known_ids(a.dataset), a.identifier, a.min_price, a.max_price):
            if done >= a.max:
                break
            if os.path.exists(os.path.join(c.raw, "detail", "%s.json" % pid)):
                continue
            c.call("/buy/property-for-sale/detail", {"id": pid}, "detail/%s.json" % pid)
            done += 1
    print("calls this month per key:", c.used())


if __name__ == "__main__":
    main()
