"""
Thin wrapper around the Google Gemini API.

The rest of the application only interacts with LLMClient.complete(),
so generator.py, evaluator.py and pipeline.py do not need to know
which LLM provider is being used.
"""

import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()


class LLMClient:
    def __init__(
        self,
        model: str = "gemini-3.6-flash",
        max_tokens: int = 5000,
    ):
        self.model = model
        self.max_tokens = max_tokens

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Add GEMINI_API_KEY to the .env file."
            )

        self._client = genai.Client(api_key=api_key)

    def complete(
        self,
        system: str,
        user: str,
        retries: int = 2,
    ) -> str:

        last_err = None

        for attempt in range(retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=[
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "text": (
                                        f"System instructions:\n{system}\n\n"
                                        f"User request:\n{user}"
                                    )
                                }
                            ],
                        }
                    ],
                    config={
                        "max_output_tokens": self.max_tokens,
                    },
                )

                if response.text:
                    return response.text

                raise RuntimeError("Gemini returned an empty response.")

            except Exception as e:
                last_err = e

                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))

        raise RuntimeError(
            f"LLM call failed after {retries + 1} attempts: {last_err}"
        )