# src/assistant/analyzers/career_advisor.py
from __future__ import annotations
import random
from typing import Optional

from assistant.config import settings
from assistant.utils.async_http import AsyncHttpClient
from assistant.utils.logging import logger

TOPICS = [
    "Kalman filters in statistical arbitrage",
    "Market microstructure analysis for high-frequency trading",
    "The use of Transformers for time-series forecasting",
    "Reinforcement learning for optimal trade execution",
    "Volatility modeling with GARCH and its variants",
]


async def generate_growth_suggestion(
    client: AsyncHttpClient, context_hint: Optional[str] = None
) -> str:
    """Uses Ollama to generate a topic for professional growth anchored to current market themes."""
    try:
        topic = context_hint or random.choice(TOPICS)
        url = f"{settings.OLLAMA_ENDPOINT}/api/chat"

        system_prompt = "You are a senior quantitative researcher mentoring a graduate student. Your tone is encouraging and informative."
        user_prompt = (
            f"Please provide a concise, 3-paragraph summary on the topic of '{topic}'. "
            "Explain why it is important for a modern quantitative researcher and suggest one practical, high-quality resource (e.g., a key research paper, a GitHub repository, or an online course) to learn more."
        )
        if context_hint:
            user_prompt += "\n\nTie the recommendation back to the current market catalyst mentioned so the reader can relate the skill to today's environment."

        payload = {
            "model": settings.analyzer_settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        response = await client.post(url, json=payload)
        data = await response.json()
        return data["message"]["content"]
    except Exception as e:
        logger.error(f"Failed to generate growth suggestion: {e}")
        return "A career growth suggestion was not available for today."
