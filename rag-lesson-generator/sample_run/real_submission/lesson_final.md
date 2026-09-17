# Introduction to RAG (Retrieval-Augmented Generation)

## Why this matters
Imagine you ask a chatbot: "What is my company's leave policy?"
A normal AI model learns from the internet, not from your company's private
files. So it has never actually read your company's handbook. It cannot
know the real answer. It may guess, and the guess can be wrong.

RAG solves this exact problem. It lets an AI look up real documents
first, and then answer using what it found. It is one of the main ways
companies use AI to answer questions about their own data safely.

## What RAG is
RAG stands for **Retrieval-Augmented Generation**. Let's break the name
into simple parts:
- **Retrieval** means "finding" or "looking up" information.
- **Augmented** means "added to" or "improved with something extra."
- **Generation** means the AI "writing" an answer.

So RAG simply means: the AI first *finds* relevant information, and then
*writes* an answer using that information. Think of it like an **open-book
exam**. A student without RAG has to answer from memory alone (closed
book). A student with RAG can open the right page of the textbook first,
and then write the answer (open book). The open-book student is usually
more accurate, especially about specific facts.

## How it works
A basic AI model (also called an **LLM**, short for "Large Language
Model" — a program trained on huge amounts of text to understand and
write language) only knows what it learned during training. It cannot
read new files on its own. RAG adds a few extra steps around the LLM so
it can use fresh, specific information. Here is the flow:

1. **You ask a question.** Example: "How many casual leaves do I get?"
2. **The system searches a store of documents.** This store is often
   called a **vector database**. Don't worry about the word "vector" —
   just think of it as a smart filing cabinet. Unlike a normal search
   (like Ctrl+F, which only matches exact words), this filing cabinet can
   find text with a similar *meaning*, even if the exact words are
   different.
3. **It pulls out the most relevant pieces of text**, for example, the
   one paragraph in the handbook about casual leave.
4. **Those pieces of text are handed to the LLM**, along with your
   original question.
5. **The LLM reads both** the question and the retrieved text, and then
   writes an answer based on them — not from guesswork, but from the
   actual document.

This is why RAG is called "retrieval-augmented" — the generation step is
*augmented* (improved) by real retrieved facts.

## Worked example
Let's walk through the leave-policy example fully, step by step.

**Setup:** A company has an internal handbook (a text document) that
includes this line somewhere inside it: *"Employees receive 12 casual
leaves per year."*

**Employee asks:** "How many casual leaves do I get per year?"

- **Step 1 — Search:** The system searches the handbook for text related
  to "casual leaves." It does not need the exact same words — it can also
  find this even if the question said "time off" instead of "leaves,"
  because it matches by meaning.
- **Step 2 — Retrieve:** It finds and pulls out the exact sentence:
  *"Employees receive 12 casual leaves per year."*
- **Step 3 — Combine:** The system now has two things: the employee's
  question, and the retrieved sentence. It sends both together to the
  LLM.
- **Step 4 — Generate:** The LLM reads the sentence and replies: *"You
  get 12 casual leaves per year, according to the company handbook."*

**Without RAG:** The LLM was never trained on this company's handbook.
It has no way to know the number "12." It might refuse to answer, or
worse, it might confidently make up a wrong number. This made-up,
confident-but-wrong answer is called a **hallucination** — when an AI
states something false as if it were true.

**With RAG:** The AI grounds its answer in a real document, so the risk
of hallucination goes down a lot for that specific question.

## Recap
- **RAG** = look up real information first, then answer using it —
  like an open-book exam instead of a closed-book one.
- **The problem it solves:** a normal AI model does not know your
  private or recent documents, and may guess wrong (hallucinate).
- **The steps:** ask a question → search a document store for relevant
  text → hand that text to the AI → the AI answers using it.
- **Key terms in plain words:**
  - *LLM* — the AI model that reads and writes language.
  - *Vector database* — a smart filing cabinet that finds text by
    meaning, not just exact words.
  - *Hallucination* — when an AI confidently states something false.
- **Why it's useful:** it lets AI answer questions about specific,
  private, or recently-updated information, without retraining the whole
  model.
