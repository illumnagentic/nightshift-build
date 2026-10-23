---
name: mubit-task-design
description: Shape this project's LLM calls so Mubit groups them into one task and actually trains an adapter, and know what Mubit can and cannot do with corrections. Use when writing or changing a system prompt, deciding where user preferences, taste, lessons or feedback go in a prompt, choosing session/user metadata, planning the persona batch or overnight training, planning the "correction turns into a model update" demo, reading a task or adapter status in the Mubit console (`Collecting examples`, `Below target`, `Prompt only`, `Can't train`, `Waiting: today's training limit`), or when someone assumes Mubit memory, lessons, recordOutcome, user_id scopes or a ~2-minute adapter.
---

# Mubit task design

Read from `https://docs.mubit.ai/llms-full.txt` (gateway docs) on 23 Oct 2026, plus a
probe of `api.mubit.ai` without a key. No training has been run from this repo. Re-check before relying on anything marked _inference_.

## How an adapter happens (documented)

1. Every call through the gateway is recorded (see `mubit-gateway`).
2. Calls are grouped into a **task**. Mubit picks **kept examples** from a task's calls.
3. At **25 kept examples** (default; the console count is the truth) Mubit reviews them,
   trains an **adapter** (a small open-weight model for that one task), and tests it.
4. **The test compares the adapter's answers with the provider model's answers.** A
   version that matches closely enough is `Passed`.
5. A passing version can be compared side by side in the console's **Try models**.

**Read point 4 twice.** On the current docs, the adapter learns to imitate our frontier
model on this task. Nothing documented feeds a correction or a swipe into training.

## What makes one task — get this wrong and nothing trains

Calls are one task when **all** of these match:

- the instructions (system prompt: Anthropic `system`; OpenAI `system`/`developer`
  messages; Gemini `systemInstruction`)
- tools, tool choice, output format (JSON schema)
- the model (date suffixes and `-latest` ignored)

Not counted: user/assistant messages, `temperature`, `max_tokens`.
Whitespace, numbers, dates, times and IDs in the instructions don't split a task.
**Any other changing word does.**

Rules for the curator call:

- **The system prompt is a constant.** One string, defined once, never templated with
  anything but numbers or IDs.
- **Everything per user goes in the user message:** stated preferences, learned taste,
  lessons, past swipes, the listing JSON. If one user's taste goes in the system prompt,
  each user becomes their own task, and none reaches 25 examples.
- **Fix the model ID and the output schema** before collecting examples. Changing either
  starts a new task from zero.
- `@mubit-ai/sdk/learn` injects memory into the **system** message by default
  (`injectionPosition: "system"`). That breaks task grouping. Another reason not to use it.
- Keep each request compact. Over-long examples fail with `examples too long to train on`.
  Send structured listing fields, not raw API dumps.

Check: open **Tasks** in the console after the first ~10 calls. There should be one task
for the curator, not one per user or per listing. If there are several, diff their prompts.

## Sessions decide the test set

Mubit holds back test cases **by session** (a conversation's calls). Session ID is the
first present of: `metadata.thread_id`, `metadata.session_id`, `metadata.conversation_id`,
Anthropic `metadata.user_id`, OpenAI Responses `prompt_cache_key`. Otherwise it is derived
from the instructions plus the first user message.

- OpenAI: send `metadata.session_id` (e.g. one per swipe session).
- Anthropic: only `metadata.user_id` exists; it makes **all of a user's calls one session**.
- Gemini: no field. The session comes from instructions + first user message, so each
  single-turn curator call is likely its own session (_inference_).
- Values over 200 characters are hashed.

## Waits, limits and results

| You see                                    | Meaning                                                                                                                                                                                       | Action                 |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| `Collecting examples`, `12 of 25 examples` | Not enough kept examples                                                                                                                                                                      | Send more varied calls |
| `Waiting for more examples: k of n`        | Too few to keep some back for testing                                                                                                                                                         | Send more, new inputs  |
| `Waiting: today's training limit`          | Daily cap, resets 00:00 UTC = 01:00 London on both Sat 24 and Sun 25 Oct (clocks go back later, at 02:00 BST Sun). Hit it Saturday and you get one more slot before the Sunday 10:00 deadline | Wait                   |
| `Waiting: the pause between trainings`     | Cool-down                                                                                                                                                                                     | Wait                   |
| `Waiting for new examples` / `Can't train` | Training failed; retries only on **new** examples, no retry button                                                                                                                            | Send new calls         |
| `Passed`                                   | Close enough to the provider model                                                                                                                                                            | Compare in Try models  |
| `Below target`                             | Not close enough; shows the % and the % needed                                                                                                                                                | More examples          |
| `Malformed tool calls`                     | Some tool calls were broken                                                                                                                                                                   | More examples          |
| `Prompt only`                              | Base model with the prompt did as well; **can't be tried**                                                                                                                                    | More examples          |

Other limits:

- **Training must be switched on for the workspace.** Until it is, there is no **Adapters** page.
- **3 adapter starts per organisation per UTC day** in Try models; the first start takes minutes.
- Try models has a daily call cap per organisation.
- Try models calls are `not stored · trains nothing`.
- **There is no model ID for an adapter.** The app cannot call one by name. The docs show
  no way for our Worker to get answers from an adapter.

No training time is documented. The "about 2 minutes" in our product doc comes from the
marketing site, not the docs. Plan the demo as if it could take hours, with a pre-trained
fallback.

## Unverified surfaces — do not build on these without a live check

- **Memory, lessons, outcomes, reflection** (`remember`, `recall`, `recordOutcome`,
  `user_id` scopes, `@mubit-ai/sdk`, `mubit-sdk` on PyPI). The SDK posts to
  `/v2/control/*`. On 23 Oct 2026, `POST https://api.mubit.ai/v2/control/context` answered
  `404 unknown_route`. Mubit's own published integration skill links to docs pages
  (`/sdk/llm-providers`, `/concepts/runs-and-scopes`, `/patterns/outcome-attribution-loop`)
  that now 404, and to `console.mubit.ai`; the gateway docs use `app.mubit.ai`.
  The memory service may live elsewhere, or may be retired. Ask.
- **"Rate this reply: Good/Bad"** exists in the console's Requests panel. The docs don't
  say whether it affects training, and show no API for it.
- **"Served by"** in Requests and the marketing line "switching over only when it does
  better" suggest a passing adapter may one day answer live calls. The docs never say it does.
- **Images.** Nothing documents whether adapters take image input.

Re-probe:

```bash
curl -s -X POST https://api.mubit.ai/v2/control/context -H 'content-type: application/json' -d '{}'
```

## Questions for the organisers (merge with §10 of docs/product-idea-high-level.md)

1. Does a passing adapter ever serve our live calls, or only Try models? If only Try
   models, the "Jordan after training" demo cannot run through our app. If adapters only
   run in Try models, can we download one (`mubit.ai/pricing.md`: "Download your models.
   No export fee"), in what format, and serve it ourselves?
2. How does a human verdict (a swipe, a correction) reach training? Is Good/Bad rating
   available as an API, and does it change which examples are kept?
3. Is the memory / lessons API (`/v2/control/*`, `@mubit-ai/sdk`) live for the event, and
   at what endpoint?
4. Is training switched on for hackathon workspaces? Are the daily training limit, pause,
   3 starts/day and Try models cap relaxed?
5. How long does training actually take at 25 examples?
6. Which base models do adapters use, and do any take images?

## Inferences (labelled as such)

- If the correction or learned taste is written into the **user message**, the frontier
  model answers better, and an adapter trained on those calls copies that better answer.
  That would make the correction reach the adapter indirectly. Plausible, not documented.
