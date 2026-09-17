# Self-Evaluating Lesson Content Generator

An agentic system that **generates** a beginner lesson on a topic,
**evaluates** it against a hard pass/fail rubric, and **regenerates** it
(up to 2 retries) until it clears every checkpoint or the retry budget
runs out — the same loop a content team would run before a human ever
reviews the draft.

Submission topic: **Introduction to RAG (Retrieval-Augmented Generation)**
Target learner: 12th-grade graduate in India, non-English-medium
background, limited English vocabulary, zero prior AI/ML knowledge.

---

## 1. What's in this repo

```
rubric/rubric.json          the 6 hard pass/fail checkpoints + rationale
src/prompts.py               generator + evaluator prompt templates
src/generator.py             generation + feedback-driven regeneration
src/evaluator.py             LLM-as-judge, forced structured JSON output
src/memory.py                cross-run memory + "frequent failure" hints
src/pipeline.py              the agent loop itself (orchestration)
src/llm_client.py            real Anthropic API client
src/mock_llm_client.py       deterministic offline mock (no API key)
run.py                       CLI entry point
sample_run/real_submission/  the actual submitted lesson + its rejection log
sample_run/mock_demo/        a full --mock run's output, for a quick offline demo
memory/memory_store.json     created on first run; persists across runs
```

## 2. Setup

```bash
git clone <this-repo>
cd rag-lesson-generator
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## 3. Run it

```bash
# Full run against the live Anthropic API
python run.py --topic "RAG (Retrieval-Augmented Generation)"

# Any other topic works too - the system is topic-agnostic
python run.py --topic "What is a neural network?"

# Offline demo, no API key needed - deterministic, shows a real FAIL then a PASS
python run.py --topic "RAG (Retrieval-Augmented Generation)" --mock

# See what memory has learned across all past runs
python run.py --stats
```

Each run writes:
- `outputs/lesson_final.md` — the lesson that shipped (or the last attempt, if none passed)
- `outputs/rejection_log.json` — what failed on each attempt, and why
- `outputs/draft_history/attempt_N.md` — every draft, for audit

## 4. Architecture & design reasoning

**Why a plain Python loop instead of LangGraph/n8n?**
The control flow here is genuinely simple: generate → check all N rubric
items → branch on "any fail?" → regenerate-with-feedback or ship. A graph
framework adds real value when there are multiple conditional paths,
parallel branches, or human-in-the-loop nodes. Here there is one loop
with one exit condition. Plain Python keeps every decision inspectable
in `pipeline.py` with no framework indirection — which matters more for a
take-home review than framework familiarity does. The design is still
provider/framework-agnostic: `LLMClient` is the only file that would
change to run this inside LangGraph nodes or an n8n HTTP node instead.

**Why hard pass/fail checks instead of a 1–10 score?**
A numeric score ("7/10, ship it") hides *which* thing is wrong and lets
borderline-bad content slip through when the model rounds generously.
Hard boolean checks force the evaluator to commit to a decision per
dimension, and force the orchestrator's ship/retry decision to be
mechanical (`all(pass)`) rather than an arbitrary threshold like "ship
if score > 6."

**Why feed back *specific* failure reasons instead of just "try again"?**
Blind retries tend to fix one thing and break another, or just rephrase
the same mistake. Passing the exact failed checkpoint IDs + the
evaluator's stated reason lets the generator make a targeted edit and
explicitly instructs it not to touch sections that already passed.

**Why does memory store *failure patterns*, not the lessons themselves?**
The brief asks for memory that "learns from feedback + logs" across
runs. Storing full lesson text long-term doesn't obviously make future
generations better — the model doesn't need to have "seen" the old
lesson. What *is* useful signal is: which rubric dimensions keep failing
across many different topics. If `no_unexplained_jargon` fails
repeatedly, that's a sign the generator's system prompt or the rubric's
wording for that check needs sharpening — not that any single topic was
mishandled. `memory.py` surfaces that as a short hint string injected
into future regeneration prompts once a checkpoint has failed
`FREQUENT_FAIL_THRESHOLD` (default 2) times across history. This is
intentionally a *nudge*, not a silent rewrite of the rubric — the rubric
itself stays a human-owned artifact you'd revise deliberately after
reading the stats (`python run.py --stats`).

**Why a hard MAX_RETRIES=2 instead of looping until it passes?**
An infinite or unbounded retry loop can spin forever (and burn API
budget) on a topic the current prompt genuinely can't handle well. The
loop always terminates after 3 total attempts (1 generate + 2
regenerate) and ships the best available attempt, explicitly flagged as
`shipped_clean: false` in the rejection log if nothing ever passed — so
a human reviewer knows to look closer, instead of the system silently
shipping a failing draft as if it had passed.

**Why is the evaluator instructed that "unsure" = FAIL?**
The brief explicitly asks for *no partial credit*. An evaluator that
defaults to PASS when uncertain quietly reintroduces partial credit
through leniency. Defaulting uncertainty to FAIL keeps the bar hard in
practice, not just on paper.

## 5. The rubric (`rubric/rubric.json`)

Six checkpoints, each with a concrete pass_rule and fail_examples so the
evaluator prompt isn't judging against a vague adjective:

| id | dimension |
|---|---|
| `accurate_grounded` | accurate & grounded — zero factual errors, zero invented stats |
| `beginner_friendly_language` | short sentences, everyday words |
| `teaches_by_example` | at least one fully walked-through example |
| `no_unexplained_jargon` | every technical term defined at first use |
| `covers_key_points` | WHAT + WHY + HOW all explicitly present |
| `coherent_teaching_flow` | logical build order + a real recap |

## 6. Known limitations / what I'd do with more time

- The evaluator is a single LLM call judging all 6 checks at once. A more
  robust (but slower/costlier) version would run one focused evaluator
  call per checkpoint, so each judgment gets the model's full attention
  and checks can't "leak" leniency into each other.
- There's no automated readability metric (e.g. Flesch-Kincaid) backing
  `beginner_friendly_language` — it's currently judged only by the LLM's
  own sense of "simple." Adding a computed readability score as a second,
  non-LLM signal would make that check less subjective.
- Memory currently only tracks checkpoint failure *counts*, not
  *which topics* correlate with which failures. A larger version could
  surface topic-specific hints (e.g. "technical topics tend to fail
  `no_unexplained_jargon` more than conceptual ones").
