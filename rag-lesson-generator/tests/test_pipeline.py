import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.evaluator import Evaluator
from src.generator import Generator
from src.memory import Memory
from src.mock_llm_client import MockLLMClient
from src.pipeline import Pipeline

RUBRIC_PATH = os.path.join(os.path.dirname(__file__), "..", "rubric", "rubric.json")


def load_rubric():
    with open(RUBRIC_PATH) as f:
        return json.load(f)


def build_pipeline(tmp_memory_path):
    rubric = load_rubric()
    llm = MockLLMClient()
    generator = Generator(llm)
    evaluator = Evaluator(llm, rubric)
    memory = Memory(path=tmp_memory_path)
    return Pipeline(generator, evaluator, memory, rubric), memory


def test_loop_fails_then_passes_with_mock():
    with tempfile.TemporaryDirectory() as tmp:
        mem_path = os.path.join(tmp, "memory.json")
        pipeline, memory = build_pipeline(mem_path)
        result = pipeline.run("RAG (Retrieval-Augmented Generation)")

        assert result["attempts_made"] == 2
        assert result["shipped_clean"] is True
        assert result["rejection_log"][0]["overall_pass"] is False
        assert len(result["rejection_log"][0]["failed_checks"]) > 0
        assert result["rejection_log"][1]["overall_pass"] is True


def test_evaluator_parses_valid_json():
    rubric = load_rubric()
    llm = MockLLMClient()
    evaluator = Evaluator(llm, rubric)
    result = evaluator.evaluate("some lesson with an embedding and a vector store search")
    assert "results" in result
    assert "overall_pass" in result
    assert isinstance(result["overall_pass"], bool)


def test_memory_persists_and_surfaces_hints_after_threshold():
    with tempfile.TemporaryDirectory() as tmp:
        mem_path = os.path.join(tmp, "memory.json")
        pipeline, memory = build_pipeline(mem_path)

        # Run twice - same mock failure pattern both times, so failure
        # counts for e.g. 'no_unexplained_jargon' should reach the
        # threshold and a hint should appear.
        pipeline.run("RAG (Retrieval-Augmented Generation)")
        pipeline.run("RAG (Retrieval-Augmented Generation)")

        hints = memory.frequent_failure_hints()
        assert "no_unexplained_jargon" in hints


def test_pipeline_terminates_within_max_retries():
    with tempfile.TemporaryDirectory() as tmp:
        mem_path = os.path.join(tmp, "memory.json")
        pipeline, _ = build_pipeline(mem_path)
        result = pipeline.run("RAG (Retrieval-Augmented Generation)")
        # 1 generate + at most 2 regenerations = 3 max attempts
        assert result["attempts_made"] <= 3


if __name__ == "__main__":
    test_loop_fails_then_passes_with_mock()
    test_evaluator_parses_valid_json()
    test_memory_persists_and_surfaces_hints_after_threshold()
    test_pipeline_terminates_within_max_retries()
    print("All tests passed.")
