
"""Gemini API wrapper for ClearWater chatbot explanations."""

import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env", override=False)


def ask_llm(prompt):
    """Send a prompt to Gemini and return its text response."""

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60000),
    )

    started = time.perf_counter()
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        answer = (response.text or "").strip()
        if not answer:
            raise RuntimeError("Gemini returned an empty response.")

        logger.info(
            "Gemini response generated in %.2f seconds",
            time.perf_counter() - started,
        )
        return answer

    except Exception:
        logger.exception("Gemini request failed")
        raise
