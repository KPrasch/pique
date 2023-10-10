import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from quirk.webhooks import should_trigger_webhook, trigger_webhooks


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    async def handle_request(request):
        return web.json_response({}, status=200)

    app = web.Application()
    app.router.add_post('/webhook.url', handle_request)
    return app


@pytest.fixture
async def mock_session(app, loop):
    async with TestServer(app) as server:
        mock_post = AsyncMock()
        mock_post.return_value.__aenter__.return_value.status = 200
        with patch('aiohttp.ClientSession.post', mock_post):
            yield server, loop, mock_post


def test_should_trigger_webhook():
    event = {"type": "transaction", "data": "some_data"}
    webhook_config = {"type": "transaction"}
    assert should_trigger_webhook(event, webhook_config) is True


@pytest.mark.asyncio
async def test_trigger_webhooks(app, mock_session):
    async for server, loop, mock_post in mock_session:
        event = {"type": "transaction", "data": "some_data"}
        webhooks_config = [{"url": f"{server.make_url('/webhook.url')}"}]

        await trigger_webhooks(event, webhooks_config)

        assert mock_post.called
        mock_post.assert_called_once_with(
            f"{server.make_url('/webhook.url')}",
            json={'event_type': event['type'], 'data': event['data']},
            headers={'Content-Type': 'application/json'}
        )

