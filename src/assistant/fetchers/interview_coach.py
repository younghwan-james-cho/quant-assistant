# src/assistant/fetchers/interview_coach.py
from __future__ import annotations
import random
from typing import List
from pydantic import BaseModel
from assistant.utils.logging import logger


class InterviewProblem(BaseModel):
    question: str
    category: str
    source: str
    difficulty: str


PROBLEMS_DATABASE = [
    InterviewProblem(
        question="You have a 3-gallon jug and a 5-gallon jug. How can you measure out exactly 4 gallons?",
        category="Brain Teaser",
        source="Heard on the Street",
        difficulty="medium",
    ),
    InterviewProblem(
        question="What is the expected number of coin flips to get two consecutive heads (HH)?",
        category="Statistics",
        source="QuantNet Forum",
        difficulty="medium",
    ),
    InterviewProblem(
        question="Implement a function to find the square root of a number without using any built-in power or root functions.",
        category="Coding",
        source="Jane Street Interview",
        difficulty="hard",
    ),
    InterviewProblem(
        question="A drawer contains 10 black socks and 10 white socks. If you pull socks one by one without looking, what is the minimum number you must pull to guarantee a matching pair?",
        category="Brain Teaser",
        source="Heard on the Street",
        difficulty="easy",
    ),
    InterviewProblem(
        question="Explain the difference between covariance and correlation.",
        category="Statistics",
        source="Two Sigma Interview",
        difficulty="easy",
    ),
    # Add more problems here
]


def fetch_qr_problems(count: int = 2) -> List[InterviewProblem]:
    """Fetch daily QR interview practice problems from a static list.

    Returns a list of ``InterviewProblem`` objects ordered randomly.  When the
    request exceeds the catalogue size the function falls back to all available
    problems.  Failures return an empty list so downstream renderers can still
    operate.
    """
    try:
        if count > len(PROBLEMS_DATABASE):
            count = len(PROBLEMS_DATABASE)
        return random.sample(PROBLEMS_DATABASE, count)
    except Exception as e:
        logger.warning(f"Failed to fetch QR problems: {e}")
        return []
