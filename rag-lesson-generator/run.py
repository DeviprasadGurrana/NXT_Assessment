#!/usr/bin/env python3
"""
Self-Evaluating Lesson Content Generator - CLI entry point.

Usage:
    export GEMINI_API_KEY=sk-ant-...
    python run.py --topic "RAG (Retrieval-Augmented Generation)"

    # Offline demo, no API key needed, deterministic (shows a fail then a pass):
    python run.py --topic "RAG (Retrieval-Augmented Generation)" --mock

    # See accumulated memory stats across all past runs:
    python run.py --stats
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.evaluator import Evaluator
from src.generator import Generator
from src.memory import Memory
from src.pipeline import Pipeline

RUBRIC_PATH = os.path.join(os.path.dirname(__file__), "rubric", "rubric.json")


def load_rubric() -> dict:
    with open(RUBRIC_PATH) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Self-evaluating lesson generator")
    parser.add_argument("--topic", type=str, help="Topic to generate a beginner lesson for")
    parser.add_argument("--mock", action="store_true", help="Run offline with a deterministic mock LLM (no API key)")
    parser.add_argument("--out", type=str, default="outputs", help="Output directory")
    parser.add_argument("--stats", action="store_true", help="Print memory stats and exit")
    parser.add_argument("--model", type=str, default="gemini-3.6-flash", help="Anthropic model name")
    args = parser.parse_args()

    memory = Memory()

    if args.stats:
        print(json.dumps(memory.stats(), indent=2))
        return

    if not args.topic:
        parser.error("--topic is required unless --stats is passed")

    if args.mock:
        from src.mock_llm_client import MockLLMClient

        llm = MockLLMClient()
    else:
        from src.llm_client import LLMClient

        llm = LLMClient(model=args.model)

    rubric = load_rubric()
    generator = Generator(llm)
    evaluator = Evaluator(llm, rubric)
    pipeline = Pipeline(generator, evaluator, memory, rubric)

    print(f"Generating lesson for topic: {args.topic}")
    result = pipeline.run(args.topic)

    for attempt in result["rejection_log"]:
        status = "PASS - shipped" if attempt["overall_pass"] else "FAIL"
        print(f"\nAttempt {attempt['attempt']}: {status}")
        for fc in attempt["failed_checks"]:
            print(f"  - [{fc['id']}] {fc['reason']}")

    Pipeline.write_outputs(result, args.out)
    print(f"\nFinal lesson written to: {os.path.join(args.out, 'lesson_final.md')}")
    print(f"Rejection log written to: {os.path.join(args.out, 'rejection_log.json')}")
    print(f"Shipped clean (all checks passed): {result['shipped_clean']}")


if __name__ == "__main__":
    main()
