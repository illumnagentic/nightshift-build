# Image download evidence

Date: 2026-10-25. Metadata only.

Command (from `dataset/`, 8 workers, 30 s timeout):

    python3 -I -B scripts/fetch_images.py --dataset .

Source: `listing_media` rows of kind `photo` (6,169) and `floorplan` (672) = 6,841
images. Kind `epc` is not fetched.

| Run | Downloaded | Skipped (already on disk) | Failed |
| --- | ---------- | ------------------------- | ------ |
| 1 (first, over 10 min) | 6,687 | 0 | 154 |
| 2 (retry of failures, 39 s) | 153 | 6,687 | 1 |
| 3 (retry of failure) | 1 | 6,840 | 0 |
| 4 (confirmation) | 0 | 6,841 | 0 |

Run 4 downloaded nothing new, and `images-manifest.csv` is byte-identical before and
after it.

Run 1 failures, all transient and none HTTP errors: 122 `timed out`, 32 `Temporary
failure in name resolution` (the machine's DNS dropped out for part of the run). Run 2
left one `timed out` (rm-93077127 photo-3), fetched on run 3. No image is permanently
failing; failures were retried only by re-running the script, three times in all.

Totals after run 4: 6,841 files, 811,739,341 bytes (791 MiB on disk), 0 leftover
`.part` files. Manifest `dataset/images-manifest.csv`: 6,841 rows, all status `ok`.

File types by magic bytes: 6,606 JPEG, 215 PNG, 20 GIF (all floorplans). Gemini's
documented image types are PNG, JPEG, WebP, HEIC and HEIF, so the GIFs need handling
in the flag-script step.

Tests: `python3 -I -B -m unittest discover -s tests` from `dataset/`: 129 tests, OK,
exit 0 (6 are new, in `tests/test_fetch_images.py`, no network).

Git: `dataset/photos/` is ignored (`git check-ignore` confirms). `git status` shows no
image file tracked or untracked.
