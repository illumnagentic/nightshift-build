# Photo flags: script, test call, pilot

Date: 2026-10-25. Metadata only; no response bodies, no key.

## Commands

From `dataset/`:

```
python3 -I -B scripts/flag_images.py --limit 1 --out <scratch file>   # test calls
python3 -I -B scripts/flag_images.py --limit 10                       # first pilot
python3 -I -B scripts/flag_images.py --listing <id> ...               # second run: same 10 plus 20 GIF listings
python3 -I -B -m unittest discover -s tests                           # exit 0, Ran 151 tests, OK
```

22 of the 151 tests are in `tests/test_flag_images.py`. No network in any test.

## Settings used

- Model: `gemini-3.5-flash-lite`. Mubit served it (200), `modelVersion` in the reply is
  `gemini-3.5-flash-lite`. No `starter_credit_model` refusal.
- Media resolution: `MEDIA_RESOLUTION_MEDIUM` (medium rather than low so floorplan text
  stays readable).
- Thinking: `thinkingConfig {"thinkingLevel": "minimal"}`. Accepted (200). `thoughtsTokenCount`
  is absent from usage, so no thinking tokens were spent.
- temperature 0, `responseMimeType` application/json with a `responseSchema`,
  `maxOutputTokens` 16384, request timeout 300 s, 4 workers.
- Flag schema: `value`, `observation`, `confidence` and `uncertainty` are all required
  (`uncertainty` stays nullable). The system instruction asks for minor visible defects
  (worn or stained carpet, scuffed walls, dated or tired fittings, cracks, damp marks,
  clutter) with low confidence when unsure, and for uncertainty to name what limits the
  judgement (angle, lighting, editing, part of the room in view), null only when nothing
  does. No target number of defects is given.

## Test call (one listing, rm-137220284, 8 images)

Three calls on this listing while fixing the first prompt and schema. All 200.

| Request ID | Result |
| ---------- | ------ |
| `mreq_01a170906d3a7a029b19c46059eba9cf` | Worked, but only `room` flags came back: `light` and the lists were missing (all keys optional in the schema). |
| `mreq_01a17090e9df76a0acc9e7d0de34bd8c` | Same, after a prompt change alone. Prompt wording did not fix it. |
| `mreq_01a1709157097f53b550a3527dd7a805` | Fixed: every key required in the response schema (null or empty when not applicable). 6 room, 6 light, 2 floorplan_notes, 1 sqm_estimate, 1 photo skipped. |

## GIF handling

Google's documented image types exclude GIF. The script sends a GIF as `image/gif`. If a
call returns HTTP 400 and the request held a GIF, it resends once without the GIFs and
records each dropped GIF in `unsupported_format` with reason `rejected_by_model`. Any other
failure still fails the listing. Types that are not sendable at all are recorded as
`unsupported_format` (tested with a BMP). Tests cover: GIF mimeType in the body; 400 then 200
(one resend, GIF listed, flags written); 400 with no GIF (no resend, listing fails); 400
twice (listing fails, nothing written).

Live result over the 20 listings that have `floorplan-0.gif`: all 20 returned 200 on the
first call. 20 accepted, 0 fell back, 0 `unsupported_format` entries, 0 unanswered, 0 rows
rejected. All 20 produced a `sqm_estimate` and floorplan_notes.

Request IDs of the 20 GIF listings:

```
rm-169724360 mreq_01a1709d503f717187aa2af13d303806
rm-163196021 mreq_01a1709d50257e70b9b618d0b785377e
rm-170691149 mreq_01a1709d5ca27381a1105621aa8cdeef
rm-173691080 mreq_01a1709d656f77d08e35d616d0fa01e2
rm-92074377  mreq_01a1709d6d2a77618a4f42e709b77b40
rm-87892545  mreq_01a1709d6a6975509288201c24dc8223
rm-92773530  mreq_01a1709d7ab5742092ad0afbc410e414
rm-93473145  mreq_01a1709d831d77018fa427b5c2655739
rm-93935772  mreq_01a1709d91917982b51ea94cad264bb8
rm-93740826  mreq_01a1709d8e337073aa4bfc193212b997
rm-94011657  mreq_01a1709d97487eb3b07dbb0449540d28
rm-94272732  mreq_01a1709da33673f19f08a1f3e24db152
rm-94445649  mreq_01a1709dae717413b15ead20b2f85ac5
rm-94479252  mreq_01a1709daed77f238e692f653bea8d27
rm-94522671  mreq_01a1709db2f4760393787a3a22b2e4d3
rm-94649271  mreq_01a1709dbc3b7913b26e1970dc9e348a
rm-94660578  mreq_01a1709dc85a7722a2ca830c40e20bc6
rm-94679172  mreq_01a1709dd15f76309794643c9d9f3454
rm-94663827  mreq_01a1709dce977b72a4841b2d73ac7c8e
rm-94679541  mreq_01a1709ddd9378a3974f2cea4d62f3b8
```

Eye check of GIF floorplan outputs (images viewed from `dataset/photos/`):

- rm-93473145: output "fourth floor apartment, combined reception/kitchen, a bathroom, two
  bedrooms along a corridor", area 59.18. Plan: exactly that, "59.18 Sq M". Correct.
- rm-94679172: output "second floor flat, reception room, kitchen, bedroom, bathroom", area
  36.23. Plan: one bedroom, "390 Sq Ft - 36.23 Sq M". Correct.
- rm-169724360: output "lower ground floor, two bedrooms, reception, kitchen/dining room,
  two bathrooms, patio garden", area 90.67. Plan: two bedrooms, two shower rooms, patio
  garden, "976 Sq Ft - 90.67 Sq M". Correct.
- All 20 sqm_estimate observations quote an area printed on the plan, none is a guess.
  The earlier single-GIF check (rm-163196021, 130.1) had one bedroom-count error; the
  re-run output for that listing was not re-read against the plan.

## Pilot: first 10 listings in id order, before and after the prompt and schema change

Same 10 listings both times. The first run's file is kept outside the repo. One listing
(rm-162613295) timed out once on the first run and was retried; the second run had no
failures (30 of 30 listings ok).

| Pilot, 10 listings | Before | After |
| ------------------ | ------ | ----- |
| flag rows | 228 | 223 |
| room | 93 | 93 |
| light | 93 | 93 |
| floorplan_notes | 17 | 15 |
| sqm_estimate | 10 | 10 |
| size_tricks | 8 | 5 |
| missing | 7 | 7 |
| defects | 0 | 0 |
| light bright / ok / poor / none | 66 / 27 / 0 / 0 | 75 / 17 / 1 / 0 |
| confidence high / medium / low | 194 / 34 / 0 | 208 / 15 / 0 |
| uncertainty null / set | 225 / 3 | 211 / 12 |
| images sent, skipped, rejected | 105, 2, 0 | 105, 2, 0 |
| prompt tokens / output tokens | 60,287 / 19,860 | 60,907 / 20,733 |

The earlier version of this file said uncertainty was null on every row. That was wrong:
3 of 228 rows had text.

Result on the pilot 10: the prompt change did not produce defect flags or low confidence
there. Uncertainty text went from 3 to 12 rows. Light became a little more varied (one
`poor`). These 10 listings may simply have no visible defects.

The 20 GIF listings (194 photos, 20 floorplans) were run with the new prompt only:

| 20 GIF listings | After |
| --------------- | ----- |
| flag rows | 463 |
| room / light | 194 / 194 |
| floorplan_notes / sqm_estimate | 28 / 20 |
| size_tricks / defects / missing | 11 / 16 / 0 |
| light bright / ok / poor / none | 127 / 65 / 2 / 0 |
| confidence high / medium / low | 421 / 41 / 1 |
| uncertainty null / set | 425 / 38 |
| images sent, skipped, rejected | 219, 5, 0 |

Pilot request IDs, one per listing (second run):

```
rm-137220284 mreq_01a1709d10027e50bd1a8f67b9ac1585
rm-139581518 mreq_01a1709d104571b0a97bdc89bf43515c
rm-159169196 mreq_01a1709d10427182a4098f4e0ae533c5
rm-159931904 mreq_01a1709d102b7393bebfe97a0ccf2425
rm-160404692 mreq_01a1709d26577022a5e45114b7880cfc
rm-160604786 mreq_01a1709d2d2c7270a83378d38b6c11f4
rm-160908077 mreq_01a1709d35ae7a41aace051e7a9d7c37
rm-162003173 mreq_01a1709d36037bd292c7cbc2574f3939
rm-162015011 mreq_01a1709d428370008e0cfe8d615dea37
rm-162613295 mreq_01a1709d49e37ef3bbb631c23b5e9e82
```

Output file `dataset/photo_flags.jsonl` now holds these 30 listings (686 flag rows, 30
status lines).

## Defect rows read against the photos

All 16 defect rows are in the GIF-listing set; none in the pilot 10. Checked:

- rm-94649271 photo-5 (bedroom): "damp marks" (peeling wallpaper, staining near window and
  ceiling, high confidence) and "dated or tired fittings". Image: peeling, stained wallpaper
  by the window, stained ceiling tiles, dated carpet. Correct.
- rm-93935772 photo-7: "cracks" ("hairline cracks on the ceiling plaster", medium,
  uncertainty "difficult to gauge depth"). Image: several fine cracks across the ceiling
  around a plaster rose. Correct, and the uncertainty is sensible.
- rm-94663827 photo-7 (bedroom): "stained_carpet", "noticeable dark stain near the right side
  of the bed", confidence high, uncertainty null. Image: a faint darker patch on the carpet
  at the bottom right edge. Real but faint, so high confidence overstates it. This is the
  weak case.

Some defect values are not plain phrases (`dead_plants`, `weathered_paving`,
`stained_carpet` use underscores); the contract says short text, so they are valid.

## Tokens and cost

Totals over all 30 listings of the second run: 187,613 prompt tokens, 64,522 output tokens
(324 images: 579 prompt tokens per image). Per listing: about 6,254 prompt and 2,151
output. Extrapolated to 635 listings: about 3.97 M prompt and 1.37 M output tokens. The
earlier 10-listing figures were 3.83 M and 1.26 M.

Price: I could not confirm a published price for `gemini-3.5-flash-lite`. It is newer than
my knowledge, and Mubit's console cost figure was not read. The figures below are
assumptions, not measurements. Reference prices are Google's published rates for the
Gemini 2.5 line as I know them (US$ per million tokens, input / output), converted at
US$1 = GBP 0.77:

| Assumed price | Per listing | 635 listings |
| ------------- | ----------- | ------------ |
| 2.5 Flash-Lite: 0.10 / 0.40 | US$0.0015 | US$0.94, about GBP 0.72 |
| 2.5 Flash: 0.30 / 2.50 | US$0.0073 | US$4.6, about GBP 3.5 |

Both are under the GBP 5 limit. Break-even is about 1.4 times the Flash rate, so the limit
holds for any Flash-Lite-class price but not for a model priced well above Flash. The
real figure should be read from the Mubit console cost page before and after the full run.
Time: about 10 s per listing, so about 25 to 30 minutes at 4 workers.

## Plausibility, flags read against the images (first pilot)

- rm-160908077 photo-2: flags living_room, bright, "French doors opening to patio, fireplace,
  and sofas". Image: lounge with two sets of French doors onto a patio, marble fireplace,
  sofas. Correct.
- rm-160908077 photo-4: flags `other` (dining area), bright. Image: dining table by a large
  sunlit window. Correct. The contract has no dining room, so `other` is the only fit.
- rm-160908077 photo-9: flags bathroom, light `ok`, "cloakroom/WC, no visible exterior
  window" and a `missing: window` flag. Image: under-stairs WC with no window. Correct.
- rm-162003173 photo-2: flags living_room, bright, size_tricks `mirror`, missing `furniture`.
  Image: empty room, wall mirror, three windows. Correct.
- rm-139581518 photo-4: skipped as "duplicate of image 0". Image: same virtually staged
  living room as photo-0 with different furniture. A fair near-duplicate.
- sqm_estimate rows in the pilot 10 are all areas printed on the floorplan; none are the
  model's own guesses.

Judgement: plausible and mostly accurate on room, light, defects (when present) and floorplan
area. Remaining weaknesses:

- Light is still mostly `bright` (202 of 287 photos across both sets). Estate-agent photos are
  shot to look bright, so this may be real, but it separates listings little.
- Confidence is almost never low (1 row in 686). The model rates nearly everything high or
  medium even when told low is expected for ambiguous photos.
- Uncertainty text is set on about 7 percent of rows (50 of 686); high-confidence defect rows
  often have null uncertainty.
- A listing with no defect flags means "none seen", not "none exist".
- `size_tricks` is nearly always "wide-angle lens".

## Test output

```
cd dataset && python3 -I -B -m unittest discover -s tests
Ran 151 tests
OK            (exit 0)
```
