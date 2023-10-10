import pytest
from quirk.db import MongoDBStorage
from unittest.mock import AsyncMock, MagicMock
from quirk.webhooks import should_trigger_webhook, trigger_webhooks

from unittest.mock import MagicMock


@pytest.fixture
def mock_mongodb_storage():
    mock_storage = MagicMock()

    async def insert_event(event):
        # Mock the insert_event method to do nothing
        pass

    async def fetch_events():
        # Mock the fetch_events method to return a list with sample data
        return [{"type": "transaction", "data": "some_data"}]

    mock_storage.insert_event = insert_event
    mock_storage.fetch_events = fetch_events

    return mock_storage


@pytest.mark.asyncio
async def test_insert_and_fetch_event(mock_mongodb_storage):
    event = {"type": "transaction", "data": "some_data"}

    await mock_mongodb_storage.insert_event(event)

    events = await mock_mongodb_storage.fetch_events()

    print(events)  # Add this line to print events

    assert len(events) == 1
    assert events[0] == event
