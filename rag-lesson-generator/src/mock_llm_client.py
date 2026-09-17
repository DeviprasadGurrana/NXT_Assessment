"""
Deterministic mock LLM used for --mock runs (no API key needed).

Why this exists: it lets you demo the FULL loop mechanics -
(generate -> evaluate -> detect fail -> feed reasons back -> regenerate ->
pass -> ship) end to end, offline, in seconds, without spending API calls.
It is NOT a substitute for a real run - the real run against the live
Anthropic API is what should go in your submission/video. This mock is
useful for: unit tests, CI, and quickly proving the control flow is wired
correctly before you point it at a real key.

It simulates one realistic failure mode on the first draft (unexplained
jargon + missing "why it matters"), then produces a clean second draft,
so the evaluator has something real to catch.
"""


class MockLLMClient:
    def __init__(self, *_, **__):
        self.calls = 0

    def complete(self, system: str, user: str, retries: int = 2) -> str:
        self.calls += 1
        if "EVALUATE" in system.upper() or "evaluator" in system.lower() and "checkpoints" in system.lower():
            return self._mock_eval(user)
        if "Your previous draft FAILED" in user:
            return self._mock_lesson_v2(user)
        return self._mock_lesson_v1(user)

    # ------------------------------------------------------------------
    def _mock_lesson_v1(self, user: str) -> str:
        # Deliberately flawed: unexplained jargon ("embedding", "vector
        # store") and never says WHY RAG matters - only WHAT and HOW.
        return """# Introduction to RAG

## What it is
RAG is a technique where an LLM uses an embedding to search a vector store
before it generates a response.

## How it works
The user query is embedded, matched against the vector store via cosine
similarity, and the top-k chunks are concatenated into the context window.

## Example
A support bot retrieves a chunk from the vector store and answers the user.

## Recap
- RAG retrieves chunks
- Then generates an answer
"""

    def _mock_lesson_v2(self, user: str) -> str:
        return """# Introduction to RAG (Retrieval-Augmented Generation)

## Why this matters
Imagine you ask a chatbot a question about your company's leave policy.
A normal AI model only knows what it learned during training. It has
never seen your company's documents. So it may guess, and guess wrong.
RAG fixes this by letting the AI look up real documents before answering.

## What RAG is
RAG stands for Retrieval-Augmented Generation. In simple words: the AI
first "retrieves" (finds) relevant information, and then "generates"
(writes) an answer using that information. It is like an open-book exam
instead of a closed-book exam.

## How it works
1. You ask a question.
2. The system searches a store of documents to find the most relevant
   pieces of text. Think of this like using Ctrl+F, but smarter - it finds
   text with a similar *meaning*, not just matching words.
3. Those relevant pieces of text are handed to the AI model along with
   your question.
4. The AI reads both your question and the retrieved text, and writes an
   answer based on them.

## Worked example
Say a company has an internal handbook. An employee asks a chatbot:
"How many casual leaves do I get per year?"
- Step 1: The chatbot searches the handbook for text about "casual leave".
- Step 2: It finds the exact paragraph that lists the leave policy.
- Step 3: It gives that paragraph to the AI model along with the question.
- Step 4: The AI reads the paragraph and replies: "You get 12 casual
  leaves per year, based on the handbook."
Without RAG, the AI would have to guess, because it was never trained on
this company's handbook.

## Recap
- RAG = look up real information first, then answer using it.
- It solves the problem of AI not knowing your specific documents.
- Steps: search for relevant text -> give it to the AI -> AI answers.
- It is like giving the AI an open book instead of asking it to answer
  from memory alone.
"""

    def _mock_eval(self, user: str) -> str:
        if "embedding" in user and "search a vector store" in user:
            # This is v1 - fail it on jargon + missing "why" + no worked example.
            return """{
  "results": [
    {"id": "accurate_grounded", "pass": true, "reason": "The retrieval/generation description is technically correct."},
    {"id": "beginner_friendly_language", "pass": false, "reason": "Sentence 'RAG is a technique where an LLM uses an embedding to search a vector store' is dense and uses undefined jargon in one breath."},
    {"id": "teaches_by_example", "pass": false, "reason": "The example section mentions a support bot but never walks through the steps - it's a one-line summary, not a worked example."},
    {"id": "no_unexplained_jargon", "pass": false, "reason": "Terms 'embedding', 'vector store', 'cosine similarity', 'context window' are all used with zero plain-language explanation."},
    {"id": "covers_key_points", "pass": false, "reason": "The lesson explains WHAT and HOW but never explains WHY RAG matters or what problem it solves."},
    {"id": "coherent_teaching_flow", "pass": false, "reason": "No motivation/why section before the concept, and the recap is only two words per bullet, not a real summary."}
  ],
  "overall_pass": false
}"""
        return """{
  "results": [
    {"id": "accurate_grounded", "pass": true, "reason": "Retrieve-then-generate description is correct and no invented statistics are present."},
    {"id": "beginner_friendly_language", "pass": true, "reason": "Sentences are short and use everyday words like 'look up' and 'open-book exam'."},
    {"id": "teaches_by_example", "pass": true, "reason": "The leave-policy example is walked through step by step (Step 1-4)."},
    {"id": "no_unexplained_jargon", "pass": true, "reason": "RAG, retrieve, and generate are all explained in plain language at first use."},
    {"id": "covers_key_points", "pass": true, "reason": "WHAT, WHY, and HOW are each present as explicit sections."},
    {"id": "coherent_teaching_flow", "pass": true, "reason": "Order is why -> what -> how -> example -> recap, and a real bullet recap closes the lesson."}
  ],
  "overall_pass": true
}"""
