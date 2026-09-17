"""
Cross-run memory.

Design choice: memory is a flat JSON file (memory/memory_store.json), not a
database or vector store. Why: the thing worth remembering here is small
and structured - "which checkpoints tend to fail, and for which topics" -
not large unstructured text that needs semantic search. A JSON counter is
simpler, fully inspectable in a diff/PR review, and good enough at this
scale (a take-home project, not a production content pipeline).

SELF-EVOLVING BEHAVIOUR:
Every run appends its rejection log to memory. If a specific checkpoint id
has failed at least FREQUENT_FAIL_THRESHOLD times across all runs so far
(this run included), the memory module hands back a short "hint" string
that gets injected into the NEXT regenerate prompt, e.g.:
    "Heads up: 'no_unexplained_jargon' has failed repeatedly across past
    runs. Pay extra attention to defining every technical term."
This is a light-weight, auditable form of "learning from repeated
failures to sharpen prompts" - it doesn't silently rewrite the rubric
(the rubric is a design artifact a human should own), but it does nudge
the generator prompt based on real accumulated evidence.
"""

import json
import os
from collections import Counter
from datetime import datetime, timezone

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "memory", "memory_store.json")
FREQUENT_FAIL_THRESHOLD = 2  # a check that has failed this many times across history earns a hint


class Memory:
    def __init__(self, path: str = MEMORY_PATH):
        self.path = path
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                return json.load(f)
        return {"runs": []}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def record_run(self, topic: str, rejection_log: list, final_pass: bool) -> None:
        self._data["runs"].append(
            {
                "topic": topic,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "final_pass": final_pass,
                "attempts": rejection_log,
            }
        )
        self._save()

    def frequent_failure_hints(self) -> str:
        """Look across ALL past runs' failed checks and surface a hint for
        any checkpoint that has failed often, so the next regeneration
        prompt can pay extra attention to it."""
        counter = Counter()
        for run in self._data["runs"]:
            for attempt in run["attempts"]:
                for check in attempt.get("failed_checks", []):
                    counter[check["id"]] += 1

        frequent = [cid for cid, n in counter.items() if n >= FREQUENT_FAIL_THRESHOLD]
        if not frequent:
            return ""
        lines = [
            f"MEMORY (from past runs): the checkpoint '{cid}' has failed "
            f"{counter[cid]} time(s) across history - pay extra attention to it."
            for cid in frequent
        ]
        return "\n".join(lines)

    def stats(self) -> dict:
        total = len(self._data["runs"])
        passed = sum(1 for r in self._data["runs"] if r["final_pass"])
        fail_counter = Counter()
        for run in self._data["runs"]:
            for attempt in run["attempts"]:
                for check in attempt.get("failed_checks", []):
                    fail_counter[check["id"]] += 1
        return {
            "total_runs": total,
            "runs_that_shipped": passed,
            "most_common_failures": fail_counter.most_common(),
        }
