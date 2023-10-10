from datetime import datetime

import aiohttp

from quirk.log import LOGGER

FILTERS = {
    "contract_address": lambda e, v: e["contract_address"] == v,
    "event_types": lambda e, v: e["type"] in v,
    "block_numbers": lambda e, v: e["block_number"] in v,
    "value_threshold": lambda e, v: e["value"] >= v,
    "status": lambda e, v: e["status"] == v,
    "from_address": lambda e, v: e["from"] == v,
    "to_address": lambda e, v: e["to"] == v,
    "after_time": lambda e, v: datetime.fromtimestamp(e["timestamp"])
    >= datetime.fromisoformat(v),
    "before_time": lambda e, v: datetime.fromtimestamp(e["timestamp"])
    <= datetime.fromisoformat(v),
    "data_fields": lambda e, v: all(
        key in e["data"] and e["data"][key] == value for key, value in v.items()
    ),
}


async def trigger_webhooks(event, webhooks_config):
    async with aiohttp.ClientSession() as session:
        for webhook_config in webhooks_config:
            if should_trigger_webhook(event, webhook_config):
                await send_webhook(session, webhook_config, event)


def should_trigger_webhook(event, webhook_config):
    for key, value in webhook_config.items():
        if key in FILTERS:
            if not FILTERS[key](event, value):
                return False
    return True


async def send_webhook(session, webhook_config, event):
    webhook_url = webhook_config["url"]
    headers = {"Content-Type": "application/json"}

    # Construct the payload. This could be customized based on what
    # the webhook expects.
    payload = {
        "event_type": event["type"],
        "data": event["data"],
    }

    response = await session.post(webhook_url, headers=headers, json=payload)

    if response.status != 200:
        LOGGER.warn(f"Failed to send webhook, status code: {response.status}")
