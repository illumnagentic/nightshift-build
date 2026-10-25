# Photo flags: full run

Date: 2026-10-25. Metadata only; no response bodies, no key.

## Command

From `dataset/`, in the background, key from the repo-root `.env`:

```
python3 -I -B scripts/flag_images.py
```

Output line: `selected 635  already done 30  ok 605  failed 0`. Exit 0. The 30 already done were
the listings from the earlier pilot runs, which used the same script, so no rerun was needed.
No listing failed, so no second pass was made. Wall time about 30 minutes at 4 workers.

## Counts

| Item | Count |
| ---- | ----- |
| Listings flagged / total | 635 / 635 (635 status lines, 635 distinct, none duplicated) |
| Listings without flags | 0 |
| Images sent | 6,841 (6,169 photos + 672 floorplans) |
| Photos with flags | 6,044 distinct URLs (6,045 `room` rows: one URL appears twice in the dump) |
| Images skipped by the model | 126 |
| Images the model left unanswered | 2 (one photo and one floorplan, both in rm-90723729) |
| Floorplans read (distinct floorplan URLs with listing flags) | 665 of 672 |
| `unsupported_format` (GIF fallbacks) | 0 |
| Rows rejected by enum validation | 0 |
| Failed listings | 0 |

Skip reasons, free text from the model, grouped: duplicate of another image (about 70),
exterior or local-area stock shots, aerial views and CGI renderings (about 40), maps and
site plans (7), agent logo or promotional text (2), energy performance chart (1), planning
document where a floorplan was expected (1), other non-property images (a few). The 7
floorplans without listing flags are covered by these skips, the one unanswered floorplan, and
possibly floorplans with nothing readable.

## Flags by field (14,684 rows)

| Scope | Field | Rows |
| ----- | ----- | ---- |
| photo | room | 6,045 |
| photo | light | 6,045 |
| photo | size_tricks | 331 |
| photo | defects | 546 |
| photo | missing | 81 |
| listing | floorplan_notes | 1,010 |
| listing | sqm_estimate | 626 |

`sqm_estimate` values are numbers (as in the pilot); every other `value` is text.

Room values: living_room 1,546; bedroom 1,171; kitchen 1,139; exterior 748; garden 461;
bathroom 461; hallway 274; other 245.

Light: bright 4,254; ok 1,763; poor 28; none 0.

Confidence: high 13,056; medium 1,592; low 36.

Uncertainty: null 13,401; set 1,283 (8.7 percent).

Listings with at least one `defects` row: 159 of 635. The other 476 have none, which reads
as "none seen".

## Request IDs

635 distinct, one per listing.

- First in file (pilot, rm-137220284): `mreq_01a1709d10027e50bd1a8f67b9ac1585`
- Last in file: `mreq_01a170bcf3f2701299e974c874f84c6d`
- Lowest and highest are the same two IDs (IDs sort by time).

## Tokens and cost

All 635 listings: 3,970,404 prompt tokens, 1,378,774 output tokens, no thinking tokens
(`thoughtsTokenCount` absent). This run alone (605 listings): 3,782,791 prompt and
1,314,252 output; the other 30 listings are the pilot's 187,613 and 64,522.

Price assumptions as in the earlier pilot evidence, because no published price for
`gemini-3.5-flash-lite` was confirmed (US$ per million tokens, input / output, US$1 =
GBP 0.77):

| Assumed price | USD | GBP |
| ------------- | --- | --- |
| 2.5 Flash-Lite: 0.10 / 0.40 | 0.95 | 0.73 |
| 2.5 Flash: 0.30 / 2.50 | 4.64 | 3.57 |

Both are under the GBP 5 limit. Token use tracked the pilot extrapolation closely (3.97 M
and 1.37 M against 3.97 M and 1.37 M estimated). Running totals were checked about every
ten minutes during the run; the Flash-rate figure peaked at its final value.

The Mubit console cost page was not read: there is no console access from this session.
The costs above are estimates from measured tokens at assumed prices, not measured spend.

## Validation of `dataset/photo_flags.jsonl`

Checked by script over all 14,684 flag rows and 635 status lines:

- every row has exactly the eleven contract keys (`flag_id`, `listing_id`, `scope`,
  `field`, `value`, `observation`, `source_photo`, `confidence`, `uncertainty`, `room`,
  `corrected_text`);
- `scope` is `photo` or `listing`; `field` is in the contract list for its scope;
- `light` values are in `none, poor, ok, bright`; `confidence` in `high, medium, low`;
- `room` is one of the eight contract values on every photo-scope row and `null` on every
  listing-scope row; `room`-field values are also in that list;
- `flag_id` is unique across all rows;
- `corrected_text` is `null` on every row;
- exactly one `listing_status` line per listing, 635 in all.

Zero violations on all checks.

## Weaknesses carried over from the pilot

Light is mostly `bright` (70 percent), confidence is almost always high (89 percent) and
low confidence is rare (36 rows). Defect rows exist for about a quarter of listings.
These flags are soft curator input and users can correct them later.
