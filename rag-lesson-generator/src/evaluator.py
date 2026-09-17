import json

from src.prompts import (
    EVALUATOR_SYSTEM_PROMPT,
    EVALUATOR_USER_PROMPT_TEMPLATE,
)


class Evaluator:
    def __init__(self, llm_client, rubric: dict):
        self.llm = llm_client
        self.rubric = rubric

    def evaluate(self, lesson: str) -> dict:
        rubric_checks = [
            {
                "id": check["id"],
                "dimension": check["dimension"],
                "statement": check["statement"],
                "pass_rule": check["pass_rule"],
            }
            for check in self.rubric["checks"]
        ]

        system = EVALUATOR_SYSTEM_PROMPT.format(
            rubric_checks=json.dumps(rubric_checks, indent=2)
        )

        user = EVALUATOR_USER_PROMPT_TEMPLATE.format(
            lesson=lesson
        )

        raw = self.llm.complete(system, user)

        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> dict:
        """Parse Gemini evaluator response and validate its structure."""

        cleaned = raw.strip()

        # Remove Markdown code fences if Gemini returns ```json ... ```
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        # Try normal JSON first.
        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError:
            # Gemini can occasionally return escaped JSON:
            # {\n  \"results\": [...]\n}
            try:
                unescaped = cleaned.encode("utf-8").decode("unicode_escape")
                data = json.loads(unescaped)

            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                raise ValueError(
                    "Evaluator did not return valid JSON.\n"
                    f"Parser error: {error}\n"
                    f"Raw output:\n{raw}"
                ) from error

        # Validate the response structure.
        if not isinstance(data, dict):
            raise ValueError(
                "Evaluator response must be a JSON object."
            )

        if "results" not in data:
            raise ValueError(
                "Evaluator JSON is missing 'results'."
            )

        if "overall_pass" not in data:
            raise ValueError(
                "Evaluator JSON is missing 'overall_pass'."
            )

        if not isinstance(data["results"], list):
            raise ValueError(
                "Evaluator 'results' must be a list."
            )

        if not isinstance(data["overall_pass"], bool):
            raise ValueError(
                "Evaluator 'overall_pass' must be true or false."
            )

        return data

