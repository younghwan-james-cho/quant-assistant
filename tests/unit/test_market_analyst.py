import asyncio
from unittest.mock import AsyncMock

from assistant.analyzers.market_analyst import generate_market_summary
from assistant.utils.dto import PriceSnapshot, VixClose


def test_generate_market_summary_prompts_with_quotes_and_vix() -> None:
    async def _run() -> None:
        client = AsyncMock()
        response = AsyncMock()
        response.status = 200
        response.reason = "OK"
        response.json = AsyncMock(return_value={"message": {"content": "Summary"}})
        client.post = AsyncMock(return_value=response)

        quotes = [PriceSnapshot(symbol="SPY", price=432.1, as_of="2024-10-01")]
        vix = VixClose(date="2024-10-01", close=13.2)

        summary = await generate_market_summary(client, quotes, vix)

        assert summary == "Summary"
        sent_payload = client.post.await_args.kwargs["json"]
        user_message = next(m for m in sent_payload["messages"] if m["role"] == "user")
        assert "SPY" in user_message["content"]
        assert "13.2" in user_message["content"]

    asyncio.run(_run())
