"""Download every listing photo and floorplan once, and write a manifest.

Reads the image URLs of kinds `photo` and `floorplan` from listings.sqlite
(table listing_media) and saves each to photos/<listing_id>/<kind>-<position>.<ext>.
An image whose file already exists is not fetched again, so an interrupted run
resumes. Files are written under a temporary name and renamed, so a killed run never
leaves a partial file that a later run would skip. Nothing is written outside photos/.

A failed image (HTTP error, timeout, non-image content type) is recorded in the
manifest with a status starting "failed" and does not stop the run. A later run tries
the failed images once more.

images-manifest.csv has one row per image, sorted by listing_id, kind, position:
listing_id, kind, position, url, path (relative to the dataset directory), sha256,
bytes, status ("ok" or "failed: <reason>"). A failed row has an empty path, sha256
and bytes. Rows do not say whether a file was downloaded or already there, so the
manifest is the same after a second run.

The photos/ directory is gitignored. The manifest is committed.

Usage (from the dataset/ directory):
  python3 -I -B scripts/fetch_images.py --dataset . [--workers 8] [--timeout 30]
"""
import argparse
import concurrent.futures
import csv
import glob
import hashlib
import os
import re
import sqlite3
import sys
import urllib.parse
import urllib.request

KINDS = ("photo", "floorplan")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
EXT_BY_TYPE = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}
URL_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
USER_AGENT = "Mozilla/5.0 (compatible; haka-dataset-fetch/1.0)"
MAX_BYTES = 20 * 1024 * 1024
FIELDS = ["listing_id", "kind", "position", "url", "path", "sha256", "bytes", "status"]


def load_media(db_path):
    con = sqlite3.connect(db_path)
    try:
        marks = ",".join("?" * len(KINDS))
        return con.execute(
            "SELECT listing_id, kind, position, url FROM listing_media "
            f"WHERE kind IN ({marks}) ORDER BY listing_id, kind, position", KINDS).fetchall()
    finally:
        con.close()


def target_stem(photos_dir, listing_id, kind, position):
    """Path without extension. Refuses ids that could leave photos_dir."""
    if not ID_RE.match(str(listing_id)) or kind not in KINDS or not isinstance(position, int) or position < 0:
        raise ValueError(f"unsafe media key: {listing_id!r} {kind!r} {position!r}")
    stem = os.path.join(photos_dir, listing_id, f"{kind}-{position}")
    root = os.path.realpath(photos_dir)
    if os.path.commonpath([root, os.path.realpath(stem)]) != root:
        raise ValueError(f"path escapes photos dir: {stem!r}")
    return stem


def existing_file(stem):
    for p in sorted(glob.glob(glob.escape(stem) + ".*")):
        if not p.endswith(".part") and os.path.isfile(p):
            return p
    return None


def url_ext(url):
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    return ext if ext in URL_EXTS else None


def download(url, timeout):
    """Return (bytes, content_type). Raises on HTTP error, timeout or oversize."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        data = resp.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("too large")
    return data, ctype


def fetch_one(dataset, photos_dir, item, timeout, opener=download):
    """Return (row, downloaded). Never raises for a per-image failure."""
    listing_id, kind, position, url = item
    row = {"listing_id": listing_id, "kind": kind, "position": position, "url": url,
           "path": "", "sha256": "", "bytes": "", "status": ""}
    try:
        stem = target_stem(photos_dir, listing_id, kind, position)
        path = existing_file(stem)
        downloaded = False
        if path is None:
            data, ctype = opener(url, timeout)
            if not ctype.startswith("image/"):
                raise ValueError(f"content type {ctype or 'missing'}")
            ext = url_ext(url) or EXT_BY_TYPE.get(ctype, ".jpg")
            path = stem + ext
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
            downloaded = True
        with open(path, "rb") as f:
            blob = f.read()
        row.update(path=os.path.relpath(path, dataset), sha256=hashlib.sha256(blob).hexdigest(),
                   bytes=len(blob), status="ok")
        return row, downloaded
    except Exception as e:  # recorded, not fatal
        code = getattr(e, "code", None)
        reason = f"http {code}" if code else (str(e) or type(e).__name__)
        row["status"] = "failed: " + reason.replace("\n", " ")
        return row, False


def write_manifest(path, rows):
    rows = sorted(rows, key=lambda r: (r["listing_id"], r["kind"], r["position"]))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def run(dataset, workers, timeout, opener=download):
    photos_dir = os.path.join(dataset, "photos")
    items = load_media(os.path.join(dataset, "listings.sqlite"))
    rows, downloaded = [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for row, was_downloaded in ex.map(lambda i: fetch_one(dataset, photos_dir, i, timeout, opener), items):
            rows.append(row)
            downloaded += was_downloaded
    write_manifest(os.path.join(dataset, "images-manifest.csv"), rows)
    failed = [r for r in rows if r["status"] != "ok"]
    return {"total": len(rows), "downloaded": downloaded,
            "skipped": len(rows) - len(failed) - downloaded, "failed": failed,
            "bytes": sum(r["bytes"] for r in rows if r["status"] == "ok")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dataset", default=".", help="dataset directory (default .)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=float, default=30)
    a = ap.parse_args()
    s = run(a.dataset, a.workers, a.timeout)
    print(f"total {s['total']}  downloaded {s['downloaded']}  skipped {s['skipped']}  "
          f"failed {len(s['failed'])}  bytes {s['bytes']}")
    for r in s["failed"]:
        print(f"FAILED {r['listing_id']} {r['kind']}-{r['position']} {r['url']} {r['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
