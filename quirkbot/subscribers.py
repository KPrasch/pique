from typing import TypedDict, NamedTuple, List, Optional, Any

from quirkbot.log import LOGGER


class SubscriberDict(TypedDict):
    channel_id: int
    name: str
    description: str


class Subscriber(NamedTuple):
    channel_id: int
    name: str
    description: str
    channel: Optional[Any] = None


def _get_subscribers(bot, subscribers: List[SubscriberDict]) -> List[Subscriber]:
    LOGGER.info(f"Loading subscribers: {', '.join(s.get('name') for s in subscribers)}")
    result: List[Subscriber] = list()
    for subscriber_data in subscribers:
        channel = bot.get_channel(int(subscriber_data["channel_id"]))
        if not channel:
            LOGGER.error(f"Could not find channel with ID {subscriber_data['channel_id']}")
            raise ValueError(f"Could not find channel with ID {subscriber_data['channel_id']}")
        else:
            LOGGER.info(f"Found channel {channel.name} with ID {channel.id}")
        subscriber = Subscriber(
            channel_id=subscriber_data["channel_id"],
            name=subscriber_data["name"],
            description=subscriber_data["description"],
            channel=channel,
        )
        result.append(subscriber)
    return result
