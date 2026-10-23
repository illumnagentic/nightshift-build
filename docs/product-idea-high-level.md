# **Night Shift Hackathon – Idea: Property Swipe Agent**

**Event:** Mubit Night Shift, London, 23–25 Oct. Hacking runs Fri 19:30 → Sun 10:00 (about 39.5 hours including the clock change). Team of two.

**The brief:** route every LLM call through Mubit and show a **correction turning into a model update** for a recurring task.

**Judging (equal weight):** Use of Mubit · Usefulness · Technical execution · Demo.

**Confirmed from mubit.ai:** Mubit has two layers. **Layer 1** (attribution, lessons, memory) works with any model, including GPT and Claude. **Layer 2** (calibration) turns lessons into an **adapter on an open-weight model**, takes **about 2 minutes to train**, and is versioned and reversible. Mubit wants outcomes from a verifier the model can't grade: a test, an application check, or a human.

## **1\. The Idea at a Glance**

| One-line pitch | Tell it what you want in plain English. Swipe. It learns what you *actually* want when buying, and gets faster at it with every buyer. |
| :---- | :---- |
| **Market** | **For sale** (not rent). Sale listings usually carry EPC, floorplans, tenure, council tax, and richer detail — more signals for the curator to get wrong, then learn. |
| **Flow** | Sign up / log in → preferences in natural language (including where you work / commute) → code filters the hard limits → structured photo \+ floorplan \+ EPC flags (already in D1) → the curator scores listings → deck mixes **top picks \+ exploration cards** → swipe and feedback → learning for that user\_id. |
| **Exploration cards** | About **1 in 5** cards is a borderline listing the curator scored low. If the user swipes right, that corrects a false exclude. Without this, you only learn from cards the model already liked showing. |
| **Accounts** | Minimal: username \+ hashed password. Each account has its own prefs, swipe history, favourites, and Mubit user\_id. Needed so we can demo a **new user** live, not just clear localStorage. |
| **Recurring LLM task** | **The curator:** for each candidate listing, decide include or exclude, a score, reasons, and the SWOT bullets for the card. |
| **Learning signal** | Swipe right or left, a quick checkbox survey on left swipes, feedback on any element (a photo, a bullet, the commute), and removals from favourites with a reason. |
| **What it learns** | Mostly **the user's unstated taste**, not fixing mistakes. Matching stated preferences is easy once photos are already structured text. The hard part is finding what the user never said. |
| **Two-layer split (settled)** | **User memory** learns this person's taste from the first swipe. **Curator adapter** learns, across users, how to discover unstated preferences in fewer swipes. That adapter is the model update. Taste alone is not. |
| **Best-fit track** | Own your intelligence layer (curator moves from a closed model to an adapted open model). Fast refresh is secondary (new listings daily in production; frozen dump for the weekend). |

### **User journey examples**

| Who | What they say | What they never say | What happens |
| :---- | :---- | :---- | :---- |
| **Alex** (first-time buyer) | "2-bed flat to buy, Zone 2, under £550k, work near King's Cross, max 40 min commute. Prefer EPC C or better." | Hates ground floors. Needs a bright living room. Rejects leasehold with a short lease. Won't take damp even if the price looks good. | Signs up → types prefs → swipes. Early cards include ground floors, EPC E, and dark living rooms. Left swipes \+ checkboxes ("floor", "light", "EPC", "tenure", "condition"). By card 8–12 the deck stops offering short-lease / low-EPC ground floors. Favourites fill with brighter freehold or long-lease flats. **Layer 1:** Alex's taste, mid-session. |
| **Jordan** (new buyer, after overnight training) | Similar brief: "2-bed to buy, Zone 2, under £550k, near King's Cross." | Same hidden pattern family as many personas: ground floor \+ poor EPC \+ dark living room \= reject. | Creates a **new account** on stage. Same sale listing pool. With the updated curator, a good match appears in \~5 swipes instead of \~14. Dashboard shows "swipes until first great find." Card SWOT can cite EPC / floorplan facts. **Layer 2:** adapter learned across buyers, not Jordan's memory. |
| **Sam** (returns later) | Already has an account. Opens the app, already logged in. | Last week removed a favourite: "service charge too high" / "too noisy on the high street." | Deck respects prior lessons without retyping everything. Can refine prefs ("budget is now £600k", "I'll accept EPC D if freehold"). Removals from favourites are delayed corrections. |
| **Judge** (live demo) | Types their own prefs in 20 seconds, or picks a seeded demo account. | Whatever they feel while swiping. | Log in as seeded "demo\_base" vs create "judge1". Swipe 5–10 cards. Survey on left swipes. See favourites \+ dashboard. Optional: second account to show cold-start after the adapter. |

**Demo script (short):** (1) Log in as Alex — deck already reflects learned taste. (2) Register Jordan — empty memory, updated curator — count swipes to first keep. (3) Show the chart: base vs updated. That is both Mubit layers in under two minutes.

## **2\. Pros**

* Highly useful: London renting and buying is painful and recurring, and every judge has felt it.  
* Swiping is the fastest correction mechanism possible: about two seconds per signal.  
* A live demo judges take part in: they swipe, the model updates in about 2 minutes, and the next deck is better.  
* Sale listings give more checkable signals than rent: EPC, floorplans, tenure, council tax — plus photo flags (damp, tiny rooms, light, wide-angle tricks).  
* The commute check through the TfL API is a calculated fact, not an LLM guess.  
* A natural backend/frontend split: the swipe UI is substantial frontend work, and the curator plus Mubit is substantial backend work.  
* Every part of Mubit has a clear role (memory, attribution, adapter, cost reduction).  
* Listings source exists: unofficial Rightmove API on RapidAPI. Offline SQLite dump means the demo does not depend on that API staying up.

## **3\. Cons**

* The Rightmove API is unofficial. Fine for a hackathon if we say so; not a real product feed.  
* Judges will ask "why not just add the swipe reasons to the prompt?" The two-layer split answers it, but the pitch has to say it in the first 20 seconds.  
* Without exploration cards, you only get feedback on what the curator already chose to show. Exploration is in the build cut for that reason.  
* Real human corrections are slow to collect. We need simulated users to reach enough volume.  
* Persona taste is not real human taste, so simulated results are only a proxy.  
* Unofficial Rightmove data is fine for a POC; say so if judges ask. Not a production feed.  
* Easy to overbuild the UI. Keep the frontend minimal; the learning loop is the product.

## **4\. SWOT**

| Strengths | Relatable problem, best demo, fastest correction UX, a product someone would actually use. Learning split is designed, not vague. |
| :---- | :---- |
| **Weaknesses** | The two-layer story is subtle and has to be explained clearly in under a minute. Unofficial listings data. |
| **Opportunities** | The cost story (closed curator vs adapted open model) fits "Own your intelligence layer". Extends to jobs, dating, second-hand cars: any "find me the right one" search. |
| **Threats** | Property portals are adding AI search. Judges may see "Tinder for flats" as a gimmick if the learning isn't visible. RapidAPI free tier is only 300 requests/month. |

## **5\. Fit With Judging Criteria (1 \= weak, 5 \= strong)**

| Criterion | Score | Why |
| :---- | :---- | :---- |
| **Use of Mubit** | 4→5 | Both layers with clear roles. Hits 5 if a **new account** live shows fewer swipes to first great find after the adapter update. |
| **Usefulness** | 5 | A real, painful, recurring task. |
| **Technical execution** (5 \= low risk) | 4 | Data prep is automatable. Remaining risk is Mubit adapter timing and keeping the UI cut. |
| **Demo** | 5 | Judges swipe live and watch the deck improve. |
| **Total** | **18 / 20** | Level with Village Guard, stronger on usefulness. |

## **6\. How Mubit Fits**

### **Two layers, two kinds of learning**

|  | This user's taste | The curator's skill |
| :---- | :---- | :---- |
| **Learns** | "Hates ground floors, needs light, Northern line is fine." | **How to work out unstated preferences in fewer swipes**: what "quiet" or "bright" means in practice, which preferences come together. |
| **Mubit layer** | Layer 1: memory and lessons, live from the first swipe. | Layer 2: **adapter update** on an open model (the scored "model update"). |
| **Learns from** | This user's swipes. | Swipes across **all** users, real and simulated. |

Do not pitch this as "it learns my taste." That is memory. Pitch it as: **the curator gets better at discovering anyone's hidden taste in fewer swipes.**

### **Which calls go through Mubit**

| Call | Model | Gets an update? |
| :---- | :---- | :---- |
| Curator: include or exclude, score, SWOT bullets | Open model served through Mubit | **Yes, adapter.** This is the trained recurring task. |
| Photo flags (structured JSON) | Cheap vision model, cached per photo. Route through Mubit if the rules require it. | No adapter unless Mubit serves an open vision model. Lessons / prompt only. |
| Survey follow-up question | Any small model | No. It only asks; the human gives the verdict. |
| Condensing swipe feedback into a one-sentence lesson | Any small text model | No. Its output feeds user memory. Keep the raw structured correction too. |
| Simulated user personas swiping | Any small model | No. They generate training data. |

### **Where feedback goes**

| Feedback on | Corrects | Stored as |
| :---- | :---- | :---- |
| Whether the card should have been shown | The curator | Adapter training example (listing \+ preferences → correct decision \+ reason) |
| A card bullet (EPC, tenure, floorplan note) | The curator's SWOT writing | Adapter training example |
| A photo ("missed the damp") or floorplan ("that's a box room") | Photo / floorplan flag prompt | Lesson / prompt improvement |
| Taste the user never stated (short lease, EPC, service charge) | This user's profile | User-scoped memory |

**Rule:** every card is one logged curator decision with an ID. All feedback attaches to that ID and to the exact element (photo, bullet, commute). Store the raw feedback, the structured correction and the one-sentence summary. The sentence alone is not enough to train an adapter.

### **How we measure improvement**

* **Headline:** swipes until the first great find for a **new account** (empty Mubit memory), base curator vs updated curator.  
* **High-quality find:** a card swiped right and **not later removed** from favourites.  
* **Supporting:** high-quality finds per 20 cards on the same listing pool, how often a card breaks a stated requirement, how often exploration cards turn out to be hits.  
* **Cost and latency:** curator on a closed model vs the adapted open model.

## **7\. Technical Approach**

**Scope, recalibrated:** this is not the biggest idea if we cut it. Prep (pull listings → describe photos → SQLite) is a batch script, not the product. The product is two agents \+ a minimal swipe UI \+ Mubit. Unofficial listings data is good enough for a hackathon POC.

### **What actually has to work**

1. **Prep (automatable):** pull N listings → Gemini flags photos → write SQLite/D1. Run once Friday night.  
2. **Two agents:** (A) user taste memory via Mubit Layer 1, (B) curator via Mubit Layer 2 adapter.  
3. **Exploration in the deck:** \~1 in 5 cards from below the usual cut, tagged in the API.  
4. **Light auth:** username \+ hashed password → session → user\_id for D1 and Mubit.  
5. **Minimal frontend:** login/register, preference box, swipe deck, checkbox survey, favourites, before/after dashboard (incl. exploration hit rate).

### **Proposed stack (Cloudflare)**

* **Backend:** [Cloudflare Python Workers](https://developers.cloudflare.com/workers/languages/python/) with FastAPI (supported). Mubit SDK called from the Worker.  
* **DB:** **D1** (SQLite on Cloudflare). Tables: users, sessions, listings, photo\_flags, decisions, feedback, favourites. Preferences stored per user.  
* **Auth:** username \+ password (hash with a standard library, e.g. bcrypt/argon2). Session cookie or token. No email, OAuth, or roles. Seed 2–3 demo accounts before Sunday.  
* **Frontend:** Vite \+ React. Cloudflare Next.js only if someone already wants SSR; a swipe deck does not need it.  
* **Local:** wrangler / pywrangler dev \+ local D1 so both teammates run the same stack.  
* **Docker (optional):** only if Windows vs Mac fights you. Wrap Node \+ uv \+ wrangler so docker compose up is identical for both. Skip if wrangler dev is already clean.  
* **Deploy:** same Worker \+ D1 to Cloudflare for the Sunday demo so you are not tied to one laptop. Shared cloud D1 beats two divergent local DBs.  
* **Repo:** /worker \+ /web. API contract in the first hour.  
* **Photo \+ listing assets:** Rightmove CDN URLs for the POC, or R2 if hotlinking breaks.

**Stack caveat:** confirm the Mubit Python SDK runs cleanly in Python Workers. If it fights the runtime, fall back to a tiny FastAPI host and keep the Vite frontend. Do not spend Saturday debugging Workers packaging.

### **Why accounts are in the cut (not a stretch)**

* **Layer 1 demo:** log in as Alex — deck already reflects that account's swipes.  
* **Layer 2 demo:** register a brand-new user (empty memory) — measure swipes until first great find on the updated curator.  
* Without accounts, "new user" is fake (clearing storage). With accounts, judges can create one themselves.  
* Overnight persona batch still supplies training volume. New human accounts prove the result; they are not the only training source.

### **Data: offline listings dump**

* Pull **200–400 London \+ agglomeration for-sale listings** from the unofficial Rightmove API on RapidAPI ([uk-real-estate-rightmove](https://rapidapi.com/ntd119/api/uk-real-estate-rightmove/pricing)). Use the sales / for-sale channel, not to-let.  
* Prefer listings that include **EPC \+ floorplan \+ photos**. Drop thin listings in the prep script so the demo always has rich cards.  
* Free tier: 300 requests/month. Details-per-listing will blow that. **Pro is \$15 for the month**. Cancel after.  
* Script: for-sale search → details → store EPC/tenure/council tax → Gemini JSON on room photos \+ floorplan → insert into D1. Live app never calls RapidAPI or Gemini for photos again.  
* **Before Friday:** playground: one for-sale search \+ one details call. Confirm EPC, floorplans, photos. Raw JSON dump \= research.

### **Photo pipeline: image → structured flags. Not Decopy. Not RAG.**

The curator already knows which listing it is scoring. There is nothing to retrieve. Do not chunk long photo essays into a vector store. Mubit already does recall.

Rejected: Decopy image summariser (no batch API, no system prompt, video-style essays, not routed through Mubit). Rejected: Decopy essay → second model to extract metadata (two hops; the extractor cannot look back at the photo).

**Do this instead:** photo → capable vision model → JSON flags, cached on the listing.

\# Per room photo  
listing\_id, photo\_id  
room: bathroom  
light: none \| poor \| ok \| bright  
size\_tricks: \[wide-angle\]  
defects: \[mould on ceiling\]  
missing: \[no extractor\]  
confidence: high  
skip: true if agent logo

\# Per listing (from sale fields \+ floorplan image)  
epc\_rating: C  
epc\_potential: B  
tenure: leasehold \| freehold \| share\_of\_freehold  
lease\_years\_remaining: 87 \| null  
council\_tax\_band: D  
floorplan\_notes: \[box room labelled as bedroom, kitchen smaller than living room\]  
sqm\_estimate: 58 \| null

Analyse **6–8 room photos** per listing plus **1 floorplan image** when present. Skip duplicates and agent logos. Store EPC / tenure / council tax from the listing JSON when the API returns them (code, not vision). 300 sales × \~8 images ≈ 2,400 vision calls, once.

### **Photo models (Oct 2026 prices)**

| Model | Cost for \~2,100 photos | Use it? |
| :---- | :---- | :---- |
| **Gemini 3.5 Flash-Lite** (gemini-3.5-flash-lite) | **Free** on the Gemini API free tier. Paid: about $0.30/1Minputtokens,~$0.0004 per image. Whole batch well under $2,often~$1\. | **Default.** Built for high-volume extraction. Structured JSON. Fast. |
| **Gemini 3.8 Flash** | Also free-tier eligible. Paid input \$0.75 / 1M until end of 2026\. Still a few dollars for the batch. | If Flash-Lite misses damp / size tricks on a sample of 20 photos. |
| **GPT-4o-mini** | \~\$0.15 / 1M input. A typical photo is cheap; whole batch a few dollars. | Backup if Gemini rate-limits, or if we already have OpenAI credits at check-in. |
| Claude Haiku 4.5 | \~\$1 / 1M input. Several dollars to low tens for 2,100 photos. | Only if Gemini and GPT-mini flags are weak on a 20-photo test. |
| Claude Sonnet / Decopy | Tens of dollars, or unusable (Decopy is a browser tool, not an API). | No. |
| Local: Ollama \+ Qwen2.5-VL / LLaVA | Free if a laptop GPU can run it. | Emergency fallback. Quality and JSON discipline are worse. Fine if the venue Wi-Fi dies. |

**Pick:** Gemini 3.5 Flash-Lite. Test 20 listing photos before Friday in Google AI Studio (that is research, not project code). If flags look good, that is the weekend model. If Mubit serves an open vision model, switch the same prompt onto it so photo calls count as routed.

### **Pipeline**

| Step | Done by | Notes |
| :---- | :---- | :---- |
| 1\. Parse the preference text into hard limits \+ soft preferences | LLM | Max price, bedrooms, area, workplace, commute, min EPC, tenure rules |
| 2\. Filter on hard limits | Code | Price, beds, EPC floor, lease length if stated. The LLM never sees listings that break them |
| 3\. Commute time | Code \+ TfL Journey Planner API | Cached per listing and workplace pair. A fact, not a guess |
| 4\. Photo flags | Gemini Flash-Lite (or Mubit open vision) | Once per photo, JSON only, cached in SQLite |
| 5\. Curate | Open model via Mubit | Score every candidate that passed hard filters. Rank by score. |
| 6\. Build deck | Code | \~80% top-scored cards \+ \~20% **exploration** from a lower band (e.g. ranks 20–40). Tag each card source: ranked \| exploration. |
| 7\. Swipe, survey, feedback | Human or simulated persona | Checkboxes first, at most one LLM follow-up. Exploration right-swipes are high-value corrections. |
| 8\. Learn | Mubit | User memory instantly. Adapter batch across users (about 2 minutes) |

### **Exploration cards (in the cut)**

* **Problem:** swipes only score what was shown. A great flat the curator ranked 35th never gets feedback, so the adapter never learns that miss.  
* **Rule:** for every 5 cards in the deck, 4 are the highest scores that still pass hard filters; 1 is drawn from a borderline band (below the usual cut, still legal).  
* **UI:** look like a normal card. Optional subtle label in the detail view ("exploratory pick") for us/judges — not required on the face of the card.  
* **Outcomes:**  
  * Right swipe on exploration → strong correction: "you under-ranked this." Adapter \+ user memory.  
  * Left swipe on exploration → confirms the low rank (still useful).  
* **Metric:** track exploration hit rate (right swipes / exploration cards shown). Rising hit rate after the adapter update is a second proof next to "swipes until first great find."  
* **Personas:** simulated users must also see exploration cards so overnight training includes false-exclude corrections.

### **Key endpoints**

register · login · logout · set preferences · get deck (includes exploration tags) · swipe · feedback (on any element) · favourites (add, remove with reason) · run simulated batch · train / update · stats (base vs updated, exploration hit rate)

### **Frontend options (pick by time left)**

The **dashboard** (base vs updated, swipes until first great find, cost comparison) is required in every version.

| Level | What it looks like | Effort |
| :---- | :---- | :---- |
| **Simple** | Login/register, preference box, swipe deck (hero photo \+ SWOT bullets including EPC/tenure), checkbox survey, favourites, dashboard | About half a day to a day |
| **Medium** | Card detail: all photos, floorplan, EPC badge, photo flags, feedback on any element, commute on a map | About 1 day |
| **Full** | Favourites change tracking, live "model updating…" moment, side-by-side closed vs open-model cost | 1.5+ days |

### **Cut for the weekend**

* **Build:** offline listings, photo flags, username/password auth, preferences, hard filters, curator, **exploration cards (\~1 in 5\)**, swipe deck, survey, favourites, dashboard, seeded demo accounts.  
* **If time allows:** commute times, feedback on every element, Docker compose for identical local runs.  
* **Pitch only:** daily listing updates, change tracking on favourites, full auth polish.

## **8\. Work Distribution**

|  | Person A: Backend & Mubit | Person B: Frontend & Demo |
| :---- | :---- | :---- |
| **Owns** | Worker/API, D1 schema, auth (register/login), prep script, hard filters, both agents \+ Mubit, personas, training, stats, wrangler deploy | Minimal Vite UI: login, swipe deck, survey, favourites, dashboard, demo flow, pitch, backup video |
| **Fri 19:30–23:00** | Together: agree the API contract and the demo story. A runs prep \+ auth \+ one curator call through Mubit. B builds login \+ swipe shell on mock data. |  |
| **Sat morning** | Photo flags done, curator scores → deck with exploration mix, swipes \+ decision IDs \+ source tag | Login/register, swipe, survey, favourites wired to real API |
| **Sat 13:00** | Checkpoint 1: register a user, swipe (including at least one exploration card in the deck), feedback reaches Mubit under that user\_id. |  |
| **Sat afternoon** | Simulated personas (with exploration), first adapter update, base-vs-updated \+ exploration hit rate | Card detail view, dashboard (include exploration metric) |
| **Sat evening** | Checkpoint 2: full loop works live. Start the overnight persona batch. |  |
| **Sat night → Sun 06:00** | Commute tool if time, tuning (take turns sleeping) | Polish, write the pitch, record a backup video |
| **Sun 06:00–10:00** | Feature freeze at 06:00. Rehearse the demo three times. Submit before 10:00. |  |

## **9\. Before Friday (research only, no code)**

* RapidAPI playground: one **for-sale** search \+ one details call. Confirm photos, floorplan, EPC, tenure, council tax, lat/lon.  
* If the dump is allowed: download raw listing JSON. Do not write the importer yet.  
* Get a TfL API key and check what the Journey Planner returns.  
* Write 10–20 persona briefs: what they say vs what they secretly want.  
* In Google AI Studio, run 20 listing photos through Gemini 3.5 Flash-Lite with the JSON prompt. Keep examples that work.  
* Design the survey checkboxes and the card layout on paper.  
* Sketch the API contract and demo script on paper (Alex → Jordan → chart).  
* Decide: wrangler-only local, or Docker compose for both machines.

## **10\. Questions for the Organisers**

* When do API keys and early-access docs arrive?  
* Which open-weight models are available for adapters? Is there an open **vision** model?  
* How many corrections does an adapter update need? Is it really about 2 minutes to train?  
* Can one agent have several adapters (e.g. per user), or is it one per agent?  
* Do Gemini / Claude calls through Mubit count as "routed" for the rules?  
* Can we bring a frozen listings dump, or does ingesting data count as project code?  
* How long is the demo slot?

## **11\. Verdict**

* **Build this — for sale, not rent.** Richer fields (EPC, floorplan, tenure) make curator mistakes and improvements easier to show. Path: RapidAPI for-sale → D1 → Gemini photo/floorplan flags → curator.  
* **Lead the pitch with the two layers:** log in as Alex (memory), register Jordan (new user \+ adapter). Show the swipes-until-first-great-find chart.  
* **Auth is in the cut:** username \+ password, local wrangler, deploy to CF for a shared demo DB. Docker only if local setup fights you.  
* **Photo model:** Gemini 3.5 Flash-Lite, structured JSON, cached. Not Decopy. Not RAG.  
* **Remaining risk:** Mubit adapter timing, and whether the Mubit Python SDK is happy on Workers. Stick to the minimal UI. Unofficial data is fine for the POC.

