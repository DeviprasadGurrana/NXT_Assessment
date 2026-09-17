"""
The agentic loop: generate -> evaluate -> (regenerate on any fail) -> ship.

Why this is "agentic" and not just "a prompt":
- The system makes its own decision (ship or retry) based on structured
  evaluator output, without a human in the loop.
- It maintains state across attempts (the rejection log) and feeds that
  state back into its own next action (the regenerate prompt).
- It has a hard termination condition (MAX_RETRIES) so it always finishes
  even if the content never fully clears the bar - it ships the best
  attempt and clearly flags it as "shipped with known issues" rather than
  looping forever or crashing.
"""

import json
import os

MAX_RETRIES = 2  # generate = attempt 1, then up to 2 regenerations = attempt 3 max


class Pipeline:
    def __init__(self, generator, evaluator, memory, rubric: dict):
        self.generator = generator
        self.evaluator = evaluator
        self.memory = memory
        self.rubric = rubric

    def run(self, topic: str) -> dict:
        rejection_log = []
        lesson = None
        final_eval = None
        shipped = False

        for attempt_num in range(1, MAX_RETRIES + 2):  # 1, 2, 3
            if attempt_num == 1:
                lesson = self.generator.generate(topic)
            else:
                failed_checks = self._failed_checks(final_eval)
                hints = self.memory.frequent_failure_hints()
                lesson = self.generator.regenerate(topic, failed_checks, memory_hints=hints)

            evaluation = self.evaluator.evaluate(lesson)
            final_eval = evaluation
            failed_checks = self._failed_checks(evaluation)

            rejection_log.append(
                {
                    "attempt": attempt_num,
                    "overall_pass": evaluation["overall_pass"],
                    "failed_checks": failed_checks,
                    "lesson_snapshot": lesson,
                }
            )

            if evaluation["overall_pass"]:
                shipped = True
                break

            if attempt_num == MAX_RETRIES + 1:
                # Loop terminates here regardless of outcome - ship best
                # available attempt, flagged, rather than retry forever.
                shipped = False
                break

        self.memory.record_run(topic, rejection_log, final_pass=shipped)

        return {
            "topic": topic,
            "final_lesson": lesson,
            "shipped_clean": shipped,
            "attempts_made": len(rejection_log),
            "rejection_log": rejection_log,
            "final_evaluation": final_eval,
        }

    def _failed_checks(self, evaluation: dict) -> list:
        by_id = {c["id"]: c for c in self.rubric["checks"]}
        failed = []
        for r in evaluation["results"]:
            if not r["pass"]:
                failed.append(
                    {
                        "id": r["id"],
                        "dimension": by_id.get(r["id"], {}).get("dimension", r["id"]),
                        "reason": r["reason"],
                    }
                )
        return failed

    @staticmethod
    def write_outputs(result: dict, out_dir: str) -> None:
        os.makedirs(out_dir, exist_ok=True)

        lesson_path = os.path.join(out_dir, "lesson_final.md")
        with open(lesson_path, "w") as f:
            f.write(result["final_lesson"])

        log_path = os.path.join(out_dir, "rejection_log.json")
        with open(log_path, "w") as f:
            log_for_file = [
                {
                    "attempt": a["attempt"],
                    "overall_pass": a["overall_pass"],
                    "failed_checks": a["failed_checks"],
                }
                for a in result["rejection_log"]
            ]
            json.dump(
                {
                    "topic": result["topic"],
                    "shipped_clean": result["shipped_clean"],
                    "attempts_made": result["attempts_made"],
                    "log": log_for_file,
                },
                f,
                indent=2,
            )

        drafts_dir = os.path.join(out_dir, "draft_history")
        os.makedirs(drafts_dir, exist_ok=True)
        for a in result["rejection_log"]:
            with open(os.path.join(drafts_dir, f"attempt_{a['attempt']}.md"), "w") as f:
                f.write(a["lesson_snapshot"])
