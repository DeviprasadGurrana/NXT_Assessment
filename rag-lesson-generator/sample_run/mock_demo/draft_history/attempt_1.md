# Introduction to RAG

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
