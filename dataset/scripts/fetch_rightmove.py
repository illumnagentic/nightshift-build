"""Fetch for-sale search pages and property pages from rightmove.co.uk.

Polite and re-runnable:
- checks robots.txt before every URL and refuses disallowed paths;
- one request at a time, --delay seconds apart (default 2.5);
- descriptive User-Agent, no login, no cookies kept, no CAPTCHA handling;
- stops on HTTP 403/429 or a challenge page instead of retrying around it;
- skips any page already saved under raw/rightmove/, so a re-run only
  fetches what is missing.

Raw pages are saved gzip-compressed and otherwise untouched.
Every request is appended to raw/rightmove/_manifest.jsonl.

Usage (from the dataset/ directory):
  python3 -I scripts/fetch_rightmove.py --raw raw/rightmove [--areas Islington,Hackney]
        [--max-details N] [--delay 2.5] [--list-plan]
"""
import argparse
import datetime as dt
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rm_common as rm  # noqa: E402

# (Rightmove location slug, kind, pages). Slugs are resolved to REGION ids by
# fetching the public /property-for-sale/<slug>.html page once.
PLAN = [
    # Inner/middle London (mostly Zone 1-3), 1-3 bed flats
    ("Islington", "flats", 1), ("Hackney", "flats", 1), ("Lambeth", "flats", 1),
    ("Camden", "flats", 1), ("Southwark", "flats", 1), ("Tower-Hamlets", "flats", 1),
    ("Wandsworth", "flats", 1), ("Lewisham", "flats", 1),
    # London houses
    ("Lewisham", "houses", 1), ("Waltham-Forest", "houses", 1), ("Ealing", "houses", 1),
    # Commuter belt, any type (Guildford and Chelmsford come from RapidAPI instead)
    ("St-Albans", "any", 1), ("Watford", "any", 1), ("Reading", "any", 1),
]

KIND_PARAMS = {
    "flats": {"propertyTypes": "flat", "minBedrooms": "1", "maxBedrooms": "3", "maxPrice": "800000"},
    "houses": {"propertyTypes": "detached,semi-detached,terraced", "maxPrice": "1200000"},
    "any": {"maxPrice": "1200000"},
}
COMMON_PARAMS = {
    "minPrice": str(rm.MIN_PRICE),
    "dontShow": "sharedOwnership,retirement",
    "includeSSTC": "false",
    "sortType": "6",  # newest listed first; the default sort is highest price
}

BLOCK_MARKERS = ("captcha", "Just a moment...", "Access Denied", "cf-challenge")


class Blocked(Exception):
    pass


class Fetcher:
    def __init__(self, raw_dir, delay):
        self.raw = raw_dir
        self.delay = delay
        self.last = 0.0
        self.count = 0
        self.ctx = rm.ssl_context()
        self.robots = urllib.robotparser.RobotFileParser()
        req = urllib.request.Request(rm.BASE + "/robots.txt", headers={"User-Agent": rm.USER_AGENT})
        with urllib.request.urlopen(req, timeout=30, context=self.ctx) as r:
            self.robots.parse(r.read().decode("utf-8", errors="replace").splitlines())
        self.last = time.monotonic()
        self.count += 1
        self.manifest = open(os.path.join(raw_dir, "_manifest.jsonl"), "a", encoding="utf-8")

    def get(self, url, rel_path):
        """Fetch url into raw/<rel_path>.gz unless it is already there."""
        dest = os.path.join(self.raw, rel_path + ".gz")
        if os.path.exists(dest):
            return rm.read_gz(dest)
        if not self.robots.can_fetch(rm.USER_AGENT, url):
            raise Blocked("robots.txt disallows " + url)
        wait = self.delay - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={
            "User-Agent": rm.USER_AGENT,
            "Accept": "text/html",
            "Accept-Language": "en-GB",
        })
        fetched_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        status, body = None, b""
        try:
            with urllib.request.urlopen(req, timeout=40, context=self.ctx) as r:
                status, body = r.status, r.read()
        except urllib.error.HTTPError as e:
            status = e.code
        except urllib.error.URLError as e:
            status = "error: %s" % e.reason
        self.last = time.monotonic()
        self.count += 1
        text = body.decode("utf-8", errors="replace")
        has_data = "__PAGE_MODEL" in text or "__NEXT_DATA__" in text
        blocked = status in (403, 429) or (
            status == 200 and not has_data and any(m.lower() in text[:20000].lower() for m in BLOCK_MARKERS))
        rec = {"url": url, "path": "raw/rightmove/" + rel_path + ".gz", "status": status,
               "bytes": len(body), "fetched_at": fetched_at, "blocked": blocked}
        self.manifest.write(json.dumps(rec) + "\n")
        self.manifest.flush()
        if blocked:
            raise Blocked("blocked or challenged (status %s) at %s" % (status, url))
        if status != 200:
            print("  skip: HTTP %s %s" % (status, url), file=sys.stderr)
            return None
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with gzip.open(dest, "wb") as f:
            f.write(body)
        return text


def resolve_region(f, slug):
    html = f.get("%s/property-for-sale/%s.html" % (rm.BASE, slug), "locations/%s.html" % slug)
    if not html:
        return None
    sr = rm.search_json(html)
    loc = (sr or {}).get("location") or {}
    if loc.get("locationType") and loc.get("id"):
        return "%s^%s" % (loc["locationType"], loc["id"])
    return None


def search_url(location_id, kind, index):
    params = {"locationIdentifier": location_id, "index": str(index), **COMMON_PARAMS, **KIND_PARAMS[kind]}
    return rm.BASE + "/property-for-sale/find.html?" + urllib.parse.urlencode(params)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="raw/rightmove directory")
    ap.add_argument("--areas", help="comma-separated slugs to restrict the plan to")
    ap.add_argument("--max-details", type=int, default=1000)
    ap.add_argument("--delay", type=float, default=2.5)
    ap.add_argument("--list-plan", action="store_true")
    ap.add_argument("--resolve", help="comma-separated slugs: print their location identifiers and stop "
                                      "(used to get identifiers for fetch_rapidapi.py)")
    a = ap.parse_args()
    if a.resolve:
        f = Fetcher(a.raw, a.delay)
        for slug in a.resolve.split(","):
            print(slug, resolve_region(f, slug))
        return
    if a.delay < 2.0:
        sys.exit("delay below 2 s is not allowed")
    plan = PLAN
    if a.areas:
        keep = set(a.areas.split(","))
        plan = [p for p in PLAN if p[0] in keep]
    if a.list_plan:
        for p in plan:
            print(*p)
        return
    os.makedirs(a.raw, exist_ok=True)
    f = Fetcher(a.raw, a.delay)
    wanted = []  # property ids in plan order
    seen = set()
    try:
        for slug, kind, pages in plan:
            loc = resolve_region(f, slug)
            if not loc:
                print("could not resolve location %s" % slug, file=sys.stderr)
                continue
            for page in range(pages):
                idx = page * 24
                html = f.get(search_url(loc, kind, idx), "search/%s_%s_newest_%d.html" % (slug, kind, idx))
                sr = rm.search_json(html) if html else None
                cards = (sr or {}).get("properties") or []
                kept = 0
                for c in cards:
                    if c["id"] in seen:
                        continue
                    seen.add(c["id"])
                    if rm.card_rejection(c) is None:
                        wanted.append(c["id"])
                        kept += 1
                print("%s %s idx=%d: %d cards, %d kept" % (slug, kind, idx, len(cards), kept))
        for n, pid in enumerate(wanted[: a.max_details], 1):
            f.get("%s/properties/%d" % (rm.BASE, pid), "property/%d.html" % pid)
            if n % 25 == 0:
                print("details %d/%d (requests this run: %d)" % (n, min(len(wanted), a.max_details), f.count))
    except Blocked as e:
        print("STOPPED: %s" % e, file=sys.stderr)
    print("done. requests made this run: %d; candidate listings: %d" % (f.count, len(wanted)))


if __name__ == "__main__":
    main()
