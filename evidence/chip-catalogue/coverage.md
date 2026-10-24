# Chip catalogue coverage

- Date: 2026-10-24
- Source: `dataset/listings.sqlite` on `main` at `658c6b5`, 635 listings.
- Rules counted: the offered-when and featured-when rules in the Chip catalogue section
  of `docs/api-contract.md`, in their pre-photo-flag form. No photo flags exist yet, so
  no flag clause is counted.
- Metadata only. No listing rows are reproduced.

## Counts per chip

"offered on" is the number of the 635 listings whose rule offers the chip, before the
per-card cap. "featured on" is the number where the chip counts as a feature the
listing clearly has. "in the 8 sent" is the number of listings where the chip survives
the cap of 8 (featured first, then priority), with no commute chip on the card.

| chip_id | offered on | featured on | in the 8 sent |
| ------- | ---------: | ----------: | ------------: |
| `garden` | 418 | 312 | 412 |
| `parking` | 264 | 264 | 264 |
| `natural_light` | 635 | 108 | 515 |
| `balcony_terrace` | 124 | 124 | 124 |
| `station_access` | 635 | 383 | 558 |
| `area_busyness` | 635 | 68 | 343 |
| `space` | 635 | 283 | 438 |
| `kitchen` | 635 | 257 | 381 |
| `layout` | 635 | 123 | 172 |
| `condition` | 635 | 147 | 148 |
| `price_value` | 635 | 635 | 635 |
| `bathrooms` | 635 | 310 | 296 |
| `floor_level` | 135 | 135 | 123 |
| `building_amenities` | 99 | 99 | 81 |
| `lease` | 225 | 225 | 183 |
| `service_charge` | 207 | 207 | 143 |
| `energy_efficiency` | 635 | 170 | 128 |
| `home_office` | 561 | 57 | 43 |
| `building_style` | 140 | 140 | 93 |
| `commute` | per user | per user | per user |

`commute` depends on the user's postcode and on TfL returning minutes, so it has no
per-listing count here. It is offered on a card when `commute.minutes` is not null.

Flag-dependent chips, pre-photo-flag rule:

- `garden`: offered on 418 listings (house types, or a garden mention). Once flags exist it also
  offers on any listing with a photo flag in room `garden`. The count with flags is not yet known.
- `natural_light`, `space`, `condition`: offered on all 635 either way. Flags change
  only whether the chip is featured. Featured counts above are the pre-flag counts.

## Chips offered on fewer than 20 listings

None. The smallest are `building_amenities` (99), `balcony_terrace` (124) and
`floor_level` (135). All are kept.

## Chips dropped

`council_tax` (506 offered) was in the first draft and dropped. It is never featured and
sits last in priority, so with a cap of 8 it reached no card in the 635 (0 of 635).

## Per-card chip counts before the cap

| Case | min | median | max |
| ---- | --: | -----: | --: |
| offered, no commute chip | 10 | 13 | 18 |
| offered, with commute chip | 11 | 14 | 19 |
| featured, no commute chip | 1 | 6 | 13 |
| featured, with commute chip | 2 | 7 | 14 |

Every card offers at least 10 chips, so a cap is needed. The median number of featured
chips is 6 to 7. A cap of 8 holds every featured chip on most cards. Featured chips
exceed 8 on 117 of 635 cards (182 with a commute chip). On those cards the lowest-priority
featured chips are cut.

## Query

Run with `python3 -I chips.py dataset/listings.sqlite`. `has(text, pattern)` is a
case-insensitive regex search over the key_features entries joined by newlines.
Each chip row is `(chip_id, priority, offered, featured)`; a featured of `None` means
featured whenever offered. Commute is added by the second `cards(True)` call.

```python
import sqlite3, json, re, statistics, sys
db = sqlite3.connect(sys.argv[1])
db.row_factory = sqlite3.Row
HOUSE = {"house", "terraced", "semi_detached", "end_of_terrace", "detached", "bungalow"}
FLATLIKE = {"flat", "maisonette", "other", None}
def has(text, pat): return re.search(pat, text, re.I) is not None
# (chip_id, priority, offered(l,t,near), featured(l,t,near) or None = always when offered)
def lease_ok(l): return l["tenure"] in ("leasehold", "share_of_freehold")
CHIPS = [
 ("garden", 1, lambda l,t,n: has(t, r"garden") or l["property_type"] in HOUSE, lambda l,t,n: has(t, r"garden")),
 ("parking", 2, lambda l,t,n: has(t, r"parking|garage|driveway|off[- ]street|car ?port|car ?park"), None),
 ("natural_light", 3, lambda l,t,n: True, lambda l,t,n: has(t, r"\b(bright|light|sunny|airy|south[- ]facing)\b")),
 ("balcony_terrace", 4, lambda l,t,n: has(t, r"balcon|roof terrace") or (has(t, r"\bterrace\b") and l["property_type"] in FLATLIKE), None),
 ("station_access", 7, lambda l,t,n: n is not None, lambda l,t,n: n <= 0.8 or has(t, r"station|tube|underground|\bdlr\b|overground")),
 ("area_busyness", 8, lambda l,t,n: True, lambda l,t,n: has(t, r"quiet|peaceful|tranquil|cul[- ]de[- ]sac|vibrant|bustling|lively|high street|village")),
 ("space", 9, lambda l,t,n: True, lambda l,t,n: has(t, r"spacious|generous|large|ample|\bhuge\b|sq\.? ?ft|sq\.? ?m\b|sqm")),
 ("kitchen", 10, lambda l,t,n: True, lambda l,t,n: has(t, r"kitchen")),
 ("layout", 11, lambda l,t,n: True, lambda l,t,n: has(t, r"open[- ]plan")),
 ("condition", 12, lambda l,t,n: True, lambda l,t,n: has(t, r"refurbish|renovat|modern|newly|new build|immaculate|redecorat|updating|in need of")),
 ("price_value", 5, lambda l,t,n: True, None),
 ("bathrooms", 13, lambda l,t,n: True, lambda l,t,n: has(t, r"en[- ]?suite|bathroom|shower room|wet room")),
 ("floor_level", 14, lambda l,t,n: l["floor_level"] is not None and l["property_type"] in FLATLIKE, None),
 ("building_amenities", 15, lambda l,t,n: l["property_type"] in ("flat","maisonette") and has(t, r"concierge|porter|\bgym\b|\blifts?\b|communal|residents|swimming|lounge"), None),
 ("lease", 16, lambda l,t,n: lease_ok(l) and l["lease_years_remaining"] is not None, None),
 ("service_charge", 17, lambda l,t,n: lease_ok(l) and l["service_charge_gbp_pa"] is not None, None),
 ("energy_efficiency", 18, lambda l,t,n: l["epc_current"] is not None, lambda l,t,n: l["epc_current"] in "ABEFG"),
 ("home_office", 19, lambda l,t,n: has(t, r"study|office|home working|work(ing)? from home") or (l["bedrooms"] or 0) >= 2, lambda l,t,n: has(t, r"study|office|home working|work(ing)? from home")),
 ("building_style", 20, lambda l,t,n: has(t, r"period|victorian|georgian|edwardian|character|original|art deco|new build|purpose[- ]built|contemporary"), None),
]
def cards(commute):
    out = []
    for l in db.execute("select * from listings"):
        t = "\n".join(json.loads(l["key_features"]))
        n = db.execute("select min(distance_km) from listing_stations where listing_id=?", (l["id"],)).fetchone()[0]
        offered = [(p, c, (f is None) or f(l,t,n)) for c,p,o,f in CHIPS if o(l,t,n)]
        if commute: offered.append((6, "commute", True))
        offered.sort(key=lambda x: (not x[2], x[0]))
        out.append(offered)
    return out
base = cards(False)
for c, *_ in CHIPS:
    print(c, sum(any(x[1]==c for x in o) for o in base), "featured", sum(any(x[1]==c and x[2] for x in o) for o in base), "top8", sum(any(x[1]==c for x in o[:8]) for o in base))
for label, cs in (("no commute", base), ("with commute", cards(True))):
    k = [len(o) for o in cs]; f = [sum(x[2] for x in o) for o in cs]
    print(label, "offered min/median/max", min(k), statistics.median(k), max(k), "featured min/median/max", min(f), statistics.median(f), max(f), "featured>8:", sum(x>8 for x in f))
```
