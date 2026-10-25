"""Tests for the image download script: skip-if-exists, failure recording, path
validation and manifest rows. No network: the downloader is replaced."""
import csv
import os
import sqlite3
import sys
import tempfile
import unittest
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import fetch_images as fi  # noqa: E402

JPEG = b"\xff\xd8\xff\xe0fakejpeg"


def make_dataset(rows):
    d = tempfile.mkdtemp()
    con = sqlite3.connect(os.path.join(d, "listings.sqlite"))
    con.execute("CREATE TABLE listing_media (listing_id TEXT, kind TEXT, position INTEGER, url TEXT)")
    con.executemany("INSERT INTO listing_media VALUES (?,?,?,?)", rows)
    con.commit()
    con.close()
    return d


def manifest(d):
    with open(os.path.join(d, "images-manifest.csv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class FetchImagesTests(unittest.TestCase):
    def test_downloads_and_writes_manifest_sorted(self):
        d = make_dataset([("rm-2", "photo", 0, "https://x/b.jpeg"), ("rm-1", "floorplan", 0, "https://x/a.png"),
                          ("rm-1", "epc", 0, "https://x/epc.png"), ("rm-1", "photo", 1, "https://x/c.jpeg")])
        s = fi.run(d, 2, 5, opener=lambda u, t: (JPEG, "image/jpeg"))
        self.assertEqual((s["total"], s["downloaded"], s["skipped"], len(s["failed"])), (3, 3, 0, 0))
        rows = manifest(d)
        self.assertEqual([(r["listing_id"], r["kind"], r["position"]) for r in rows],
                         [("rm-1", "floorplan", "0"), ("rm-1", "photo", "1"), ("rm-2", "photo", "0")])
        self.assertEqual(rows[0]["path"], "photos/rm-1/floorplan-0.png")
        self.assertEqual(rows[0]["bytes"], str(len(JPEG)))
        self.assertEqual(len(rows[0]["sha256"]), 64)
        self.assertEqual({r["status"] for r in rows}, {"ok"})
        leftovers = [f for _, _, fs in os.walk(os.path.join(d, "photos")) for f in fs if f.endswith(".part")]
        self.assertEqual(leftovers, [])

    def test_second_run_downloads_nothing_and_manifest_is_identical(self):
        d = make_dataset([("rm-1", "photo", 0, "https://x/a.jpeg")])
        fi.run(d, 1, 5, opener=lambda u, t: (JPEG, "image/jpeg"))
        with open(os.path.join(d, "images-manifest.csv"), "rb") as f:
            first = f.read()

        def boom(u, t):
            raise AssertionError("must not download")
        s = fi.run(d, 1, 5, opener=boom)
        self.assertEqual((s["downloaded"], s["skipped"]), (0, 1))
        with open(os.path.join(d, "images-manifest.csv"), "rb") as f:
            self.assertEqual(f.read(), first)

    def test_partial_file_is_not_treated_as_existing(self):
        d = make_dataset([("rm-1", "photo", 0, "https://x/a.jpeg")])
        os.makedirs(os.path.join(d, "photos", "rm-1"))
        with open(os.path.join(d, "photos", "rm-1", "photo-0.jpeg.part"), "wb") as f:
            f.write(b"half")
        s = fi.run(d, 1, 5, opener=lambda u, t: (JPEG, "image/jpeg"))
        self.assertEqual(s["downloaded"], 1)

    def test_failures_are_recorded_not_fatal(self):
        d = make_dataset([("rm-1", "photo", 0, "https://x/404.jpeg"), ("rm-1", "photo", 1, "https://x/slow.jpeg"),
                          ("rm-1", "photo", 2, "https://x/page.jpeg"), ("rm-1", "photo", 3, "https://x/ok.jpeg")])

        def opener(u, t):
            if "404" in u:
                raise urllib.error.HTTPError(u, 404, "Not Found", {}, None)
            if "slow" in u:
                raise TimeoutError("timed out")
            if "page" in u:
                return b"<html>", "text/html"
            return JPEG, "image/jpeg"
        s = fi.run(d, 2, 5, opener=opener)
        self.assertEqual((s["downloaded"], len(s["failed"])), (1, 3))
        by_pos = {r["position"]: r for r in manifest(d)}
        self.assertEqual(by_pos["0"]["status"], "failed: http 404")
        self.assertEqual(by_pos["1"]["status"], "failed: timed out")
        self.assertEqual(by_pos["2"]["status"], "failed: content type text/html")
        self.assertEqual((by_pos["0"]["path"], by_pos["0"]["sha256"], by_pos["0"]["bytes"]), ("", "", ""))
        self.assertEqual(by_pos["3"]["status"], "ok")
        self.assertFalse(os.path.exists(os.path.join(d, "photos", "rm-1", "photo-0.jpeg")))

    def test_unsafe_listing_ids_are_rejected_and_nothing_is_written_outside(self):
        d = make_dataset([("../evil", "photo", 0, "https://x/a.jpeg"), ("a/b", "photo", 0, "https://x/a.jpeg"),
                          ("", "photo", 0, "https://x/a.jpeg"), (".hidden", "photo", 0, "https://x/a.jpeg")])
        called = []
        s = fi.run(d, 1, 5, opener=lambda u, t: called.append(u) or (JPEG, "image/jpeg"))
        self.assertEqual((s["downloaded"], len(s["failed"]), called), (0, 4, []))
        self.assertTrue(all(r["status"].startswith("failed: unsafe media key") for r in manifest(d)))
        self.assertFalse(os.path.exists(os.path.join(d, "photos")))
        self.assertFalse(os.path.exists(os.path.join(d, "..", "evil")))

    def test_extension_from_url_else_content_type(self):
        d = make_dataset([("rm-1", "photo", 0, "https://x/noext"), ("rm-1", "photo", 1, "https://x/a.jpeg?w=1")])
        fi.run(d, 1, 5, opener=lambda u, t: (JPEG, "image/webp"))
        paths = [r["path"] for r in manifest(d)]
        self.assertEqual(paths, ["photos/rm-1/photo-0.webp", "photos/rm-1/photo-1.jpeg"])


if __name__ == "__main__":
    unittest.main()
