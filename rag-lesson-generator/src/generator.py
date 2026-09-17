from src.prompts import (
    GENERATOR_SYSTEM_PROMPT,
    GENERATOR_USER_PROMPT_TEMPLATE,
    REGENERATE_USER_PROMPT_TEMPLATE,
)


class Generator:
    def __init__(self, llm_client):
        self.llm = llm_client

    def generate(self, topic: str) -> str:
        """First-draft generation, no feedback yet."""
        user_prompt = GENERATOR_USER_PROMPT_TEMPLATE.format(topic=topic)
        return self.llm.complete(GENERATOR_SYSTEM_PROMPT, user_prompt)

    def regenerate(self, topic: str, failed_checks: list, memory_hints: str = "") -> str:
        """Regenerate using specific failure reasons fed back into the prompt.

        This is the core of the "regenerate" step: we do not just say
        'try again'. We hand the model the exact checkpoint IDs and the
        evaluator's stated reasons, so it edits precisely what broke.
        """
        feedback_lines = [
            f"- [{c['id']}] {c['reason']}" for c in failed_checks
        ]
        user_prompt = REGENERATE_USER_PROMPT_TEMPLATE.format(
            topic=topic,
            failure_feedback="\n".join(feedback_lines),
            memory_hints=memory_hints,
        )
        return self.llm.complete(GENERATOR_SYSTEM_PROMPT, user_prompt)
