"""Tests for the image flagging script: response-to-rows mapping, enum rejection, skip
handling, unsupported formats, MIME sniffing and resume. No network: the HTTP sender is
replaced."""
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import flag_images as fl  # noqa: E402

JPEG = b"\xff\xd8\xff\xe0fakejpeg"
PNG = b"\x89PNG\r\n\x1a\nfake"
BMP = b"BMfakebitmap"
GIF = b"GIF89afakegif"
RID = "mreq_" + "a" * 32


def make_dataset(images):
    """images: list of (listing_id, kind, position, bytes)."""
    d = tempfile.mkdtemp()
    rows = []
    for lid, kind, pos, data in images:
        rel = f"photos/{lid}/{kind}-{pos}.bin"
        os.makedirs(os.path.join(d, "photos", lid), exist_ok=True)
        with open(os.path.join(d, rel), "wb") as f:
            f.write(data)
        rows.append({"listing_id": lid, "kind": kind, "position": pos, "url": f"https://x/{lid}/{kind}{pos}",
                     "path": rel, "sha256": "", "bytes": len(data), "status": "ok"})
    with open(os.path.join(d, "images-manifest.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["listing_id", "kind", "position", "url", "path", "sha256", "bytes", "status"])
        w.writeheader()
        w.writerows(rows)
    return d


def flag(value, conf="high", unc=None, obs="seen"):
    return {"value": value, "observation": obs, "confidence": conf, "uncertainty": unc}


def photo_entry(index, room="kitchen", light="bright", **extra):
    e = {"index": index, "skip": False, "skip_reason": None, "room": flag(room), "light": flag(light),
         "size_tricks": [], "defects": [], "missing": [], "floorplan_notes": [], "sqm_estimate": None}
    e.update(extra)
    return e


def error_response(status=400):
    return status, {"x-middleware-request-id": RID}, json.dumps({"error": {"message": "bad image"}})


def sender_for(entries, status=200, calls=None):
    def send(url, headers, payload):
        if calls is not None:
            calls.append((url, headers, json.loads(payload)))
        body = {"candidates": [{"content": {"parts": [{"text": json.dumps(entries)}]}}],
                "modelVersion": "gemini-3.5-flash-lite",
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15}}
        return status, {"x-middleware-request-id": RID}, json.dumps(body)
    return send


class SniffTests(unittest.TestCase):
    def test_mime_comes_from_magic_bytes(self):
        self.assertEqual(fl.sniff_mime(JPEG), "image/jpeg")
        self.assertEqual(fl.sniff_mime(PNG), "image/png")
        self.assertEqual(fl.sniff_mime(b"RIFF\x00\x00\x00\x00WEBPVP8 "), "image/webp")
        self.assertEqual(fl.sniff_mime(b"GIF89a...."), "image/gif")
        self.assertEqual(fl.sniff_mime(b"\x00\x00\x00\x18ftypheic"), "image/heic")
        self.assertEqual(fl.sniff_mime(b"\x00\x00\x00\x18ftypmif1"), "image/heif")
        self.assertIsNone(fl.sniff_mime(BMP))

    def test_extension_is_ignored(self):
        d = make_dataset([("rm-1", "photo", 0, PNG)])  # file is named .bin
        body, sent, unsupported = fl.build_body(d, fl.load_images(d)["rm-1"])
        self.assertEqual(body["contents"][0]["parts"][1]["inlineData"]["mimeType"], "image/png")
        self.assertEqual((len(sent), unsupported), (1, []))


class RequestTests(unittest.TestCase):
    def test_unsupported_image_left_out_and_recorded_rest_still_flagged(self):
        d = make_dataset([("rm-1", "photo", 0, JPEG), ("rm-1", "photo", 1, BMP), ("rm-1", "photo", 2, JPEG)])
        calls = []
        lines = fl.flag_listing(d, "k", "rm-1", fl.load_images(d)["rm-1"],
                                sender_for([photo_entry(0), photo_entry(1, room="bedroom")], calls=calls))
        parts = calls[0][2]["contents"][0]["parts"]
        self.assertEqual([p["text"] for p in parts if "text" in p], ["Image 0 (photo):", "Image 1 (photo):"])
        status = lines[-1]
        self.assertEqual([(u["url"], u["reason"]) for u in status["unsupported_format"]],
                         [("https://x/rm-1/photo1", "unsupported_format")])
        # index 1 in the request is the third manifest image
        rooms = {r["source_photo"]: r["value"] for r in lines[:-1] if r["field"] == "room"}
        self.assertEqual(rooms, {"https://x/rm-1/photo0": "kitchen", "https://x/rm-1/photo2": "bedroom"})

    def test_gif_goes_into_request_with_gif_mime_type(self):
        d = make_dataset([("rm-1", "floorplan", 0, GIF)])
        calls = []
        fl.flag_listing(d, "k", "rm-1", fl.load_images(d)["rm-1"], sender_for([photo_entry(0)], calls=calls))
        self.assertEqual(calls[0][2]["contents"][0]["parts"][1]["inlineData"]["mimeType"], "image/gif")

    def test_gif_rejected_with_400_is_resent_without_gif(self):
        d = make_dataset([("rm-1", "photo", 0, JPEG), ("rm-1", "floorplan", 0, GIF)])
        calls = []
        ok = sender_for([photo_entry(0)], calls=calls)

        def send(url, headers, payload):
            if not calls:
                calls.append((url, headers, json.loads(payload)))
                return error_response()
            return ok(url, headers, payload)

        lines = fl.flag_listing(d, "k", "rm-1", fl.load_images(d)["rm-1"], send)
        self.assertEqual(len(calls), 2)
        mimes = [[p["inlineData"]["mimeType"] for p in c[2]["contents"][0]["parts"] if "inlineData" in p] for c in calls]
        self.assertEqual(mimes, [["image/jpeg", "image/gif"], ["image/jpeg"]])
        status = lines[-1]
        self.assertEqual([(u["url"], u["reason"]) for u in status["unsupported_format"]],
                         [("https://x/rm-1/floorplan0", "rejected_by_model")])
        self.assertEqual(status["images_sent"], 1)
        self.assertTrue([r for r in lines[:-1] if r["field"] == "room"])

    def test_400_without_gif_is_not_resent(self):
        d = make_dataset([("rm-1", "photo", 0, JPEG)])
        n = []
        def send(url, headers, payload):
            n.append(1)
            return error_response()
        with self.assertRaises(fl.MubitError):
            fl.flag_listing(d, "k", "rm-1", fl.load_images(d)["rm-1"], send)
        self.assertEqual(len(n), 1)

    def test_400_twice_fails_listing_and_writes_nothing(self):
        d = make_dataset([("rm-1", "photo", 0, JPEG), ("rm-1", "floorplan", 0, GIF)])
        out = os.path.join(d, "o.jsonl")
        n = []
        def send(url, headers, payload):
            n.append(1)
            return error_response()
        s = fl.run(d, "k", out, workers=1, sender=send)
        self.assertEqual((len(n), s["ok"], len(s["failed"])), (2, 0, 1))
        self.assertEqual(fl.completed(out), set())
        with open(out, encoding="utf-8") as f:
            self.assertEqual(f.read(), "")

    def test_uncertainty_is_required_in_flag_schema(self):
        self.assertIn("uncertainty", fl._flag_schema()["required"])
        self.assertTrue(fl._flag_schema()["properties"]["uncertainty"]["nullable"])

    def test_request_settings_and_key_header(self):
        d = make_dataset([("rm-1", "photo", 0, JPEG)])
        calls = []
        fl.flag_listing(d, "secret-key", "rm-1", fl.load_images(d)["rm-1"], sender_for([photo_entry(0)], calls=calls))
        url, headers, body = calls[0]
        self.assertIn("gemini-3.5-flash-lite:generateContent", url)
        self.assertEqual(headers["x-goog-api-key"], "secret-key")
        cfg = body["generationConfig"]
        self.assertEqual((cfg["temperature"], cfg["responseMimeType"]), (0, "application/json"))
        self.assertEqual(cfg["mediaResolution"], "MEDIA_RESOLUTION_MEDIUM")
        self.assertIn("responseSchema", cfg)
        self.assertIn("thinkingConfig", cfg)

    def test_photos_sent_before_floorplans(self):
        d = make_dataset([("rm-1", "floorplan", 0, JPEG), ("rm-1", "photo", 0, JPEG)])
        _, sent, _ = fl.build_body(d, fl.load_images(d)["rm-1"])
        self.assertEqual([r["kind"] for r in sent], ["photo", "floorplan"])


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.d = make_dataset([("rm-1", "photo", 0, JPEG), ("rm-1", "photo", 1, JPEG), ("rm-1", "floorplan", 0, JPEG)])
        self.images = fl.load_images(self.d)["rm-1"]

    def run_entries(self, entries):
        return fl.flag_listing(self.d, "k", "rm-1", self.images, sender_for(entries))

    def test_photo_and_floorplan_rows_match_contract(self):
        photo = photo_entry(0, defects=[flag("mould on ceiling", "medium", "could be shadow")],
                            missing=[flag("no storage")], size_tricks=[flag("wide angle")])
        plan = {"index": 2, "skip": False, "skip_reason": None, "room": None, "light": None, "size_tricks": [],
                "defects": [], "missing": [], "floorplan_notes": [flag("open plan"), flag("odd shape")],
                "sqm_estimate": flag(58.5)}
        lines = self.run_entries([photo, photo_entry(1, room="garden", light="poor"), plan])
        rows = lines[:-1]
        keys = {"flag_id", "listing_id", "scope", "field", "value", "observation", "source_photo",
                "confidence", "uncertainty", "room", "corrected_text"}
        self.assertTrue(all(set(r) == keys for r in rows))
        fields = sorted((r["source_photo"][-6:], r["field"]) for r in rows)
        self.assertEqual(fields.count(("photo0", "room")), 1)
        self.assertEqual(fields.count(("photo0", "light")), 1)
        defect = next(r for r in rows if r["field"] == "defects")
        self.assertEqual((defect["value"], defect["uncertainty"], defect["room"], defect["scope"]),
                         ("mould on ceiling", "could be shadow", "kitchen", "photo"))
        self.assertIsNone(defect["corrected_text"])
        notes = [r for r in rows if r["field"] == "floorplan_notes"]
        self.assertEqual(len(notes), 2)
        sqm = next(r for r in rows if r["field"] == "sqm_estimate")
        self.assertEqual((sqm["value"], sqm["scope"], sqm["room"], sqm["source_photo"]),
                         (58.5, "listing", None, "https://x/rm-1/floorplan0"))
        self.assertTrue(all(r["room"] is None for r in rows if r["scope"] == "listing"))
        self.assertTrue(all(r["room"] for r in rows if r["scope"] == "photo"))

    def test_null_sqm_gives_no_row(self):
        plan = {"index": 2, "skip": False, "room": None, "light": None, "floorplan_notes": [flag("x")],
                "sqm_estimate": flag(None)}
        lines = self.run_entries([photo_entry(0), photo_entry(1), plan])
        self.assertFalse([r for r in lines[:-1] if r["field"] == "sqm_estimate"])

    def test_flag_ids_are_deterministic_and_unique(self):
        e = [photo_entry(0, defects=[flag("a"), flag("b")]), photo_entry(1)]
        a = [r["flag_id"] for r in self.run_entries(e)[:-1]]
        b = [r["flag_id"] for r in self.run_entries(e)[:-1]]
        self.assertEqual(a, b)
        self.assertEqual(len(a), len(set(a)))

    def test_bad_enums_are_rejected_and_logged_others_kept(self):
        entries = [photo_entry(0, room="attic", light="bright"),
                   photo_entry(1, light="dazzling", defects=[flag("crack", conf="certain"), flag("stain")])]
        lines = self.run_entries(entries)
        status = lines[-1]
        reasons = sorted(r["reason"] for r in status["rejected"])
        # photo 0: room and light rows both carry the bad room; photo 1: bad light and bad confidence
        self.assertEqual(len(reasons), 4)
        self.assertTrue(any("room 'attic'" in r for r in reasons))
        self.assertTrue(any("light value 'dazzling'" in r for r in reasons))
        self.assertTrue(any("confidence 'certain'" in r for r in reasons))
        kept = {(r["source_photo"][-6:], r["field"], r["value"]) for r in lines[:-1]}
        self.assertIn(("photo1", "defects", "stain"), kept)
        self.assertNotIn(("photo1", "light", "dazzling"), kept)
        self.assertFalse([k for k in kept if k[0] == "photo0" and k[1] == "room"])

    def test_check_row_rejects_contract_breaks(self):
        good = {"scope": "photo", "field": "light", "value": "ok", "observation": "o", "confidence": "low",
                "uncertainty": None, "room": "hallway"}
        self.assertIsNone(fl.check_row(good))
        for change in ({"scope": "house"}, {"field": "sqm_estimate"}, {"room": None}, {"value": ""},
                       {"uncertainty": 3}, {"confidence": "none"}):
            self.assertIsNotNone(fl.check_row(dict(good, **change)), change)
        listing = dict(good, scope="listing", field="sqm_estimate", value=40, room=None)
        self.assertIsNone(fl.check_row(listing))
        self.assertIsNotNone(fl.check_row(dict(listing, room="kitchen")))
        self.assertIsNotNone(fl.check_row(dict(listing, value="40")))
        self.assertIsNotNone(fl.check_row(dict(listing, value=True)))

    def test_skipped_photo_has_no_flags_and_is_recorded(self):
        skip = {"index": 0, "skip": True, "skip_reason": "agent logo"}
        lines = self.run_entries([skip, photo_entry(1)])
        status = lines[-1]
        self.assertEqual(status["skipped"], [{"url": "https://x/rm-1/photo0", "reason": "agent logo"}])
        self.assertFalse([r for r in lines[:-1] if r["source_photo"].endswith("photo0")])
        self.assertTrue([r for r in lines[:-1] if r["source_photo"].endswith("photo1")])

    def test_unanswered_image_is_recorded(self):
        status = self.run_entries([photo_entry(0)])[-1]
        self.assertEqual(sorted(status["unanswered"]), ["https://x/rm-1/floorplan0", "https://x/rm-1/photo1"])

    def test_status_carries_request_id_usage_and_model_version(self):
        status = self.run_entries([photo_entry(0), photo_entry(1)])[-1]
        self.assertEqual(status["record_type"], "listing_status")
        self.assertEqual(status["request_id"], RID)
        self.assertEqual(status["usage"]["promptTokenCount"], 10)
        self.assertEqual(status["model_version"], "gemini-3.5-flash-lite")


class RunTests(unittest.TestCase):
    def test_resume_skips_complete_listings_and_retries_failed(self):
        d = make_dataset([("rm-1", "photo", 0, JPEG), ("rm-2", "photo", 0, JPEG)])
        out = os.path.join(d, "photo_flags.jsonl")
        sent_ids = []

        def flaky(url, headers, payload):
            sent_ids.append(1)
            if len(sent_ids) == 2:
                return 500, {"x-middleware-request-id": RID}, json.dumps({"error": {"message": "boom"}})
            return sender_for([photo_entry(0)])(url, headers, payload)

        s = fl.run(d, "k", out, workers=1, sender=flaky)
        self.assertEqual((s["ok"], len(s["failed"])), (1, 1))
        with open(out, encoding="utf-8") as f:
            first = [json.loads(line) for line in f]
        self.assertEqual({r["listing_id"] for r in first}, {"rm-1"})  # failed listing wrote nothing
        s = fl.run(d, "k", out, workers=1, sender=sender_for([photo_entry(0)]))
        self.assertEqual((s["already_done"], s["ok"], len(s["failed"])), (1, 1, 0))
        with open(out, encoding="utf-8") as f:
            ids = [json.loads(line)["listing_id"] for line in f if '"listing_status"' in line]
        self.assertEqual(sorted(ids), ["rm-1", "rm-2"])
        before = len(sent_ids)
        s = fl.run(d, "k", out, workers=1, sender=flaky)
        self.assertEqual((s["ok"], len(sent_ids)), (0, before))

    def test_limit_and_listing_selection(self):
        d = make_dataset([("rm-1", "photo", 0, JPEG), ("rm-2", "photo", 0, JPEG), ("rm-3", "photo", 0, JPEG)])
        out = os.path.join(d, "o.jsonl")
        s = fl.run(d, "k", out, workers=1, limit=2, sender=sender_for([photo_entry(0)]))
        self.assertEqual((s["selected"], s["ok"]), (2, 2))
        out2 = os.path.join(d, "o2.jsonl")
        s = fl.run(d, "k", out2, workers=1, only=["rm-3"], sender=sender_for([photo_entry(0)]))
        self.assertEqual((s["selected"], s["ok"]), (1, 1))
        self.assertEqual(fl.completed(out2), {"rm-3"})

    def test_unparseable_response_is_a_failure_not_an_empty_listing(self):
        d = make_dataset([("rm-1", "photo", 0, JPEG)])
        out = os.path.join(d, "o.jsonl")

        def junk(url, headers, payload):
            body = {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]}
            return 200, {"x-middleware-request-id": RID}, json.dumps(body)

        s = fl.run(d, "k", out, workers=1, sender=junk)
        self.assertEqual((s["ok"], len(s["failed"])), (0, 1))
        self.assertEqual(fl.completed(out), set())


class KeyTests(unittest.TestCase):
    def test_key_read_from_env_file_when_variable_unset(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, ".env")
        with open(path, "w", encoding="utf-8") as f:
            f.write("OTHER=1\nMUBIT_API_KEY='mbt_abc'\n")
        saved = os.environ.pop("MUBIT_API_KEY", None)
        try:
            self.assertEqual(fl.load_env_key(path), "mbt_abc")
            self.assertIsNone(fl.load_env_key(os.path.join(d, "missing")))
            os.environ["MUBIT_API_KEY"] = "from_env"
            self.assertEqual(fl.load_env_key(path), "from_env")
        finally:
            os.environ.pop("MUBIT_API_KEY", None)
            if saved is not None:
                os.environ["MUBIT_API_KEY"] = saved


if __name__ == "__main__":
    unittest.main()
