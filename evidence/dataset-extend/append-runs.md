# Append runs of normalise.py --append

Counts only. Each run overwrites `dataset/reports/normalise-report.txt`, so the
report on disk describes the latest run; this file keeps both.

## Run 1 (24 Oct, first fetch)

- existing listings kept unchanged: 398
- new records built from raw/rapidapi: 163
- dropped before building (rejection and thin rules): 6 (all thin, no tenure)
- dropped, duplicate by id: 0
- dropped, duplicate by delivery point: 0
- dropped, duplicate by geo (coords 4dp + beds + price): 2
- dropped, duplicate by photo: 0
- dropped by sanitise: 0
- added: 161
- final: 559
- new by postcode area: CB 20, CM 19, TN 19, BN 19, OX 19, KT 18, SE 12, SW 10, CR 10, N 10, W 5

## Run 2 (24 Oct, after the 250k-700k top-up)

- existing listings kept unchanged: 559 (first 559 lines byte-identical to run 1 output)
- new records built from raw/rapidapi: 239 (includes the 161 added in run 1)
- dropped before building (rejection and thin rules): 10 (all thin, no tenure)
- dropped, duplicate by id: 161 (the run 1 records)
- dropped, duplicate by delivery point: 0
- dropped, duplicate by geo: 2
- dropped, duplicate by photo: 0
- dropped by sanitise: 0
- added: 76
- final: 635
- new by postcode area: CB 9, BN 9, TN 9, CM 9, KT 8, SE 8, OX 8, N 6, CR 5, W 4, SW 1
- price of the 76 new: median 450000; 250-400k 7, 400-550k 42, 550-700k 5, 700-900k 22, 900k-1.2m 0
- price of all 635: median 700000; 250-400k 74, 400-550k 142, 550-700k 79, 700-900k 150, 900k-1.2m 190
- a third run on a copy of the dataset adds 0 and leaves listings.jsonl and listings.csv identical
