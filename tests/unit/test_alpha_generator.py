import asyncio
import json
from unittest.mock import AsyncMock

from assistant.analyzers.alpha_generator import AlphaIdea, generate_alpha_idea
from assistant.fetchers.news_fetcher import NewsArticle
from assistant.utils.dto import PaperItem


def test_generate_alpha_idea_builds_prompt_and_parses_response() -> None:
    async def _run() -> None:
        client = AsyncMock()
        response = AsyncMock()
        response.status = 200
        response.reason = "OK"
        payload = {"title": "Test Idea", "insight": "Test Insight", "python_code": "print(1)"}
        response.json = AsyncMock(return_value={"message": {"content": json.dumps(payload)}})
        client.post = AsyncMock(return_value=response)

        news = [NewsArticle(title="Headline", url="https://example.com")]
        papers = [PaperItem(title="Paper", authors=["Doe"], year=2024, url="https://paper")]

        result = await generate_alpha_idea(client, "Markets rallied.", news, papers)

        assert isinstance(result, AlphaIdea)
        assert result.title == "Test Idea"
        assert result.insight == "Test Insight"
        assert result.python_code == "print(1)"

        assert client.post.await_count == 1
        sent_payload = client.post.await_args.kwargs["json"]
        user_message = next(m for m in sent_payload["messages"] if m["role"] == "user")
        assert "Headline" in user_message["content"]
        assert "Paper" in user_message["content"]

    asyncio.run(_run())
