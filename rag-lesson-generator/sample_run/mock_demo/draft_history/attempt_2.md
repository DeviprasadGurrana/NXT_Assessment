# Introduction to RAG (Retrieval-Augmented Generation)

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
