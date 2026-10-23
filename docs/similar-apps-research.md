

**Similar-project research and differentiation**

**Directly read Devpost descriptions**

**I BROKE THE GAME at Vercel Hackathon by winning two tracks at the same time.**

**It was Vercel \#ZeroToAgent Hackathon London.** 

**The rules stated "choose ONE OF these". I won both anyway.**

**Here is what I built.** 

**Rentry is an agent that finds you the best place to rent.**

**More than 60% of the Hackathon audience confirmed this is relevant to them.**

**I built it with Vercel Workflows, bridghtdata.com and Mubit. Shoutout to them for sponsoring this Hackathon.**

**The point it, that's my entire tech stack, nothing more.** 

**BrightData fetches public listing property data, Mubit manages long-term agent memory. Vercel Workflow runs the agent.** 

**Simplicity and usability is what made my product stood out in a room of more than 100 cracked engineers.**

**The GitHub repo is public. Star it before you fork. https\://lnkd.in/eNme\_56t**

**Try Rentry at https\://lnkd.in/ea-h\_jbz**

**Shoutout to Yijin Liu, Richard Lao and Waseef Mohammad Khan for peer support in my build time.**

**Shoutout to Oscar Falemara for organising amazing event.**

**https\://www\.linkedin.com/posts/shumeng-liu-932a9a201\_zerotoagent-activity-7456601952278261760-VTnS?utm\_source=share\&utm\_medium=member\_ios\&rcm=ACoAAAZxluUBQprUQV-A-SyXH1cpAvC-tBreD38**

**Cubi Estate — Dmitro Taranenko**

• Conversational property search, normalised features from listing text, ranking, comparisons and explanations.

• Overlap: natural-language discovery and structured listing intelligence.

• Source: [https\://devpost.com/software/cubi-estate](https://devpost.com/software/cubi-estate)

• LinkedIn — creator profile: [https\://www\.linkedin.com/in/dmitrytaranenko/](https://www.linkedin.com/in/dmitrytaranenko/)

• Match basis: the public LinkedIn search result explicitly identifies Dmytro Taranenko as founder of Cubi.estate. The Devpost page uses the spelling Dmitro. This is a profile link, not a verified hackathon announcement.

**Estetia / Rust AI — project page associated with Ayesha Zaheer**

• Conversational recommendations within a property marketplace.

• The write-up says the hackathon demo temporarily used dummy property data when the backend was unavailable.

• Overlap: prepared-data property demo and conversational search.

• Source: [https\://devpost.com/software/estetia](https://devpost.com/software/estetia)

• LinkedIn — search link: [https\://www\.linkedin.com/search/results/all/?keywords=%22Ayesha+Zaheer%22+%22Estetia%22](https://www.linkedin.com/search/results/all/?keywords=%22Ayesha+Zaheer%22+%22Estetia%22)

• Status: no creator profile or project post could be reliably matched. This link opens a LinkedIn search, not a verified profile; same-name profiles were not attributed to this project.

**Advanced IA real estate property searches / Smart Property Search — Héctor Fernández**

• Bedrock image analysis, descriptions/embeddings, semantic search and visual similarity.

• Overlap: preprocessing property photographs to enable visual discovery.

• Source: [https\://devpost.com/software/advanced-ia-real-estate-property-searches](https://devpost.com/software/advanced-ia-real-estate-property-searches)

• LinkedIn — creator profile: [https\://es.linkedin.com/in/hectorfernandezdev](https://es.linkedin.com/in/hectorfernandezdev)

• Match basis: public search identifies Héctor Fernández as creator of Cloud para Todos, the same channel linked by the project demo. This is a corroborated creator-profile lead, not a verified project announcement.

These are self-reported project capabilities, not independently tested implementations.

**LinkedIn leads, not fully verified findings**  
• Mac OBrien: search excerpt mentions preferences and instant property deep dives. [https\://www\.linkedin.com/posts/macobrien08\_had-an-amazing-and-a-little-stressful-activity-7391548470970433536-pE1l](https://www.linkedin.com/posts/macobrien08_had-an-amazing-and-a-little-stressful-activity-7391548470970433536-pE1l)

• John Foong: Domain AI hackathon post surfaced in search.

[https\://www\.linkedin.com/posts/johnfoong\_ai-hackathon-generativeai-activity-7113109616799989760-9UfC](https://www.linkedin.com/posts/johnfoong_ai-hackathon-generativeai-activity-7113109616799989760-9UfC)

Full LinkedIn retrieval failed. No authenticated LinkedIn research was performed. The coding-profile browser could not launch; existing browser sessions or credentials from other profiles were not accessed.

**Supported conclusion**  
Natural-language property search and image-based discovery already have close examples. This limited search does not establish market-wide saturation or prove that the proposed learning interaction is unique.

**Recommended differentiator**  
***“It learns your deal-breakers without inventing new ones.”***

A rejected home may contain many desirable features. The system should identify the actual cause of rejection rather than treating every co-occurring feature as disliked.

Demo example:

21\. Reject a renovated home.

22\. Clarify: kitchen appearance or lack of dining space?

23\. User: “Old cupboards are fine. I need room for a table.”

24\. Confirm: “Prioritise dining space; don’t penalise dated cupboards.”

25\. Recommend an unseen home with dated cupboards and a suitable layout.

The specificity of the lesson—not merely a different next card—is the memorable moment.

**7\. Product and interaction priorities**  
The user's stated priorities are a beautiful, smooth, fully functioning frontend; gamified and nuanced feedback; and a learning loop supported by suitable data.

**Primary experience**  
An Explore interface with occasional Compare moments. Keep the user-facing journey focused:

**Explore → identify what works/doesn’t → confirm the lesson → see it applied.**

**Recommended interaction set**  
**A. Keep this, change that**

Apply “Love this”, “Could live with this”, “Deal-breaker” or “Not sure” to an individual photo or summary point. Preserve feature-level feedback independently of the whole-property decision.

**B. Occasional compromise comparison**

Offer two suitable options with a visible trade-off, allowing A, B, Neither or Not enough information. Multiple differing features confound the choice; do not silently infer the reason. Add an optional follow-up.

**C. Did I understand you?**

Present a proposed lesson with Yes, Edit and Not quite. This supplies validation while making learning tangible.

Build A and C first; add B only after the core loop works.

**What-I-learned receipt**  
A short receipt records:

• Original feedback.

• Proposed preference.

• Supporting photo/field where relevant.

• Whether it is a soft preference or hard requirement.

• Confirm/edit controls.

Avoid an interruption after every swipe. Surveys should be optional, concise and undoable.

**Personalised summary structure**  
• **Works for you:** evidence-linked matches to confirmed preferences.

• **The compromise:** acceptable trade-offs, not generic negatives.

• **Worth checking:** uncertainty and useful questions for the agent.

A dated kitchen may be an acceptable compromise, not a poor fit. Allow feedback such as “This isn’t a compromise for me.”

**Visual polish and completion**  
Use motion to connect feedback, memory and later recommendations. Do not introduce waits purely for animation. Include undo, responsive behaviour, keyboard alternatives, reduced-motion support, loading, errors and no-suitable-matches states. The learning state must be real, not a decorative progress indicator.

Do not reward liking properties, completing compulsory rounds or preserving a streak. Reward clarity and useful discovery.

**8\. Evidence, vision and factual boundaries**

**Suitable visual observations**  
• Limited visible clearance around a bed.

• Neighbouring windows overlooking a garden.

• Possible staining worth asking about.

• No window visible in the supplied bathroom photograph.

**Unsupported conclusions to avoid**  
• A definitive damp diagnosis.

• Unsafe wiring inferred from photographs.

• “No bathroom window” merely because none appears in one photo.

• Freehold tenure inferred visually.

Keep **observation, source photo, uncertainty and follow-up question** separate. Model confidence is not automatically a calibrated probability.

Verified facts, visual observations, user preferences and inferred fit should remain distinct data categories. Unknown tenure stays unknown. Define commute destination, time assumptions and transport mode. Enforce hard constraints in code; ask before relaxing them if no suitable matches exist.

**9\. Learning architecture**

**Layer 1: personal memory**  
Immediate, editable and reversible user-specific preferences. Distinguish must-haves from soft preferences and temporary choices. A raw swipe is ambiguous; explicit reasons and confirmations are stronger signals.

**Layer 2: shared curation improvement**  
Improve the recurring task:

*Given a user profile and property evidence, assess fit, acceptable compromises and uncertainty accurately.*

Learn how to interpret feedback, avoid overgeneralisation, use evidence and express trade-offs. Do not promote one person's tastes into universal preferences.

For the weekend, train the text curator using prepared image metadata. Do not also attempt vision-model fine-tuning.

**Three meanings of learning**  
26\. **Memory:** relevant facts are stored and supplied to later calls; weights are unchanged.

27\. **Lessons/prompt adaptation:** reusable guidance changes future context; weights may remain unchanged.

28\. **Model training:** examples change model/adapter parameters for a recurring task.

Mubit's public changelog documents memory/reflection/lesson mechanisms. The event's model-update contract remains to be confirmed.

**10\. Data shape and correction quality**

**Recommendation: structured envelope plus natural language**  
JSON improves validation, attribution and reproducibility; it does not inherently make the model smarter. Preserve the user's own words alongside normalised fields so the schema does not erase nuance.

Example application record—not a verified Mubit request format:

{  
 "decision\_id": "assessment\_041",  
 "property\_id": "property\_018",  
 "target": {  
   "type": "summary\_point",  
   "id": "kitchen\_condition"  
 },  
 "raw\_feedback": "Old cupboards are fine. I need room for a table.",  
 "proposed\_preference": {  
   "attribute": "kitchen\_dining\_space",  
   "importance": "strong\_preference",  
   "statement": "Prefers a kitchen with space for a dining table."  
 },  
 "user\_confirmed": true,  
 "corrected\_summary": "Dated cupboards are acceptable; dining space needs checking."  
}  
Store the actual decision input, profile version, evidence, original output and model/update attribution alongside the record. Keep user-specific data scoped appropriately; do not put identifiable personal feedback into shared training without an appropriate permission and minimisation approach.

**Distinguish feedback types**  
• **Preference correction:** “I don’t mind dated cupboards.”

• **Evidence correction:** “That photo is a utility room.”

• **Requirement change:** “My budget has increased.”

They require different handling, not a single generic dislike label.

**Supervised examples**  
Input context → reviewed desired output.

Example: a profile accepts cosmetic renovation; the property has dated cupboards. Correct an assessment that wrongly treats that as a mismatch.

**Preference examples**  
Same input context → preferred model response and rejected model response.

A user choosing property A over B is useful preference information, but is not automatically a preferred/rejected pair of curator responses. Define the output being optimised first.

A model-written correction is a candidate until reviewed or confirmed; the model must not manufacture ground truth.

**11\. Evaluation and demo proof**  
Increasing right swipes is a product signal, not isolated evidence of model improvement. It can result from changing memory, filtering, better later candidates, novelty or changed user behaviour.

**Controlled comparison**  
Use the same unseen candidate pool and evidence:

29\. Base curator \+ initial brief.

30\. Base curator \+ learned personal memory.

31\. Updated curator \+ the same learned personal memory.

Compare 2 versus 3 to isolate the model-update contribution. Hold other instructions, tools and selection conditions fixed.

**Metrics**  
• Acceptance among top recommendations.

• Hard-constraint violations.

• Unsupported summary claims.

• Correct capture of rejection reasons.

• Soft preferences incorrectly promoted to hard constraints.

• Repetition of known mismatches.

• Preservation of acceptable co-occurring features.

Keep feedback/training properties separate from evaluation properties; guard against duplicate listings leaking across the split. Use separately collected human preferences or explicitly declared persona rules, not the curator's own labels. Label synthetic tests as synthetic, not proof of real-user satisfaction. Repeated evaluation is more informative than one flattering example.

**Live demo sequence**  
32\. Enter the natural-language brief.

33\. Show factually eligible properties.

34\. Give feature-level rejection feedback.

35\. Confirm the precise lesson and supporting evidence.

36\. Show correction attribution and its learning destination.

37\. Demonstrate personalisation on an unseen property.

38\. Show Mubit update provenance and controlled shared-model evaluation.

Do not claim that an immediate memory change proves a weight update. If training cannot complete within the live slot, use a real completed update with recorded provenance and disclose the timing. Keep a backup recording of the genuine path.

**12\. MVP and deferred scope**

**Keep**  
• One location; either sales or rentals.

• Small permitted dataset with held-out properties.

• Compact vision schema and prepared metadata.

• One commute destination with explicit assumptions.

• Explore cards, details and feature-level feedback.

• Editable personal memory and learning receipts.

• One recurring Mubit curator task.

• Honest before/after dashboard.

**Defer**  
• Daily ingestion.

• Price-drop and sold-status monitoring.

• Feedback controls everywhere.

• Multiple commute destinations or elaborate simulation.

• Vision-model training.

• A general-purpose property marketplace.

**13\. Suggested architecture, ownership and checkpoints**  
The original shared architecture remains a reasonable proposal: Python/FastAPI backend, SQLite decision/outcome logging, React/Vite frontend, and SSE or WebSocket events where useful. It is not an implemented system.

Every LLM decision needs an identifier and preserved input/output. Route every LLM call through the permitted Mubit path. For property preferences, user confirmation supplies the subjective label; code enforces factual constraints. Do not apply the original simulator/referee rule as if code could objectively decide a person's taste.

**Ownership**  
• **Person A:** Mubit integration, data preparation, curator, correction handling and evaluation.

• **Person B:** frontend, interactions, complete user journey, demo narrative and backup video.

Agree the API contract early. Frontend mocks are a development aid, not evidence of final integration.

**Checkpoints from the original schedule**  
• Friday: agree the contract/story; get one genuine Mubit call working.

• Saturday morning: decision → feedback → confirmed correction; simple frontend.

• Saturday 13:00: real frontend/backend connection and one visible logged correction.

• Saturday afternoon: batch/update path and held-out evaluation; then visual enhancement.

• Saturday evening: full genuine loop; start any required batch.

• Sunday 06:00: feature freeze.

• Final hours: fix blockers, rehearse and submit before the stated deadline.

Do not spend the weekend polishing an unconnected shell. Prioritise one beautiful complete path over many unfinished features.

**14\. Remaining decisions and research**  
• Confirm actual event rules and Mubit training semantics.

• Secure listing/photo reuse permission and a fallback dataset.

• Choose sales or rentals, location and feasible candidate coverage.

• Define the vision schema and manual review approach.

• Specify the curator input/output and correction adapter.

• Design the held-out test and user-confirmed reference labels.

• Decide how private user preferences are separated from shared training.

• Complete deeper comparable-project research if useful; authenticated LinkedIn requires a separately authorised coding-profile session with user-handled login, not transferred passwords or cookies.

• Validate business demand independently; commercial plausibility is not customer validation.

**15\. Source register**

**Commercial workflow grounding**  
• Salesforce, field-service management guide: [https\://www\.salesforce.com/service/field-service-management/guide/](https://www.salesforce.com/service/field-service-management/guide/)

• Bringg, route optimisation overview: [https\://www\.bringg.com/resources/blog/route-optimization](https://www.bringg.com/resources/blog/route-optimization)

• Microsoft, verified helpdesk and social-engineering risks: [https\://learn.microsoft.com/en-us/entra/verified-id/helpdesk-with-verified-id](https://learn.microsoft.com/en-us/entra/verified-id/helpdesk-with-verified-id)

• Klaviyo, email/SMS A/B testing: [https\://www\.klaviyo.com/blog/ab-testing-email](https://www.klaviyo.com/blog/ab-testing-email)

• Braze, experience optimisation: [https\://www\.braze.com/resources/articles/experience-optimization](https://www.braze.com/resources/articles/experience-optimization)

Vendor materials support the existence of workflows and constraints, not independent evidence of ROI for the proposed agents.

**Learning mechanisms**  
• Mubit changelog: [https\://docs.mubit.ai/changelog](https://docs.mubit.ai/changelog)

• Supervised fine-tuning guide: [https\://platform.openai.com/docs/guides/supervised-fine-tuning](https://platform.openai.com/docs/guides/supervised-fine-tuning)

• Direct preference optimisation guide: [https\://platform.openai.com/docs/guides/direct-preference-optimization](https://platform.openai.com/docs/guides/direct-preference-optimization)

The latter two illustrate training-data concepts; they are not a recommendation to bypass Mubit or evidence of what the event supports.

**Comparable projects and LinkedIn leads**  
See Section 6 for individual links and evidence limitations.

**Final recommendation**  
Pursue the property curator if the data and model-update gates are cleared. Use frontend quality to make nuanced, confirmed learning visible—not to conceal an ordinary filter or memory update.

**Product promise:** “A property curator that learns your deal-breakers without inventing new ones.”

**Interaction promise:** “Teach it the compromise you’ll make—not just the house you’ll like.”

**Proof standard:** an unseen-property improvement backed by correctly attributed corrections, with personal memory held constant when measuring the shared model update.

