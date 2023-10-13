import asyncio
from abc import ABC, abstractmethod
from asyncio import Queue
from typing import List
from typing import Optional

from discord import TextChannel

from pique.config import PiqueConfig
from pique.constants import _throttle
from pique.discord.embeds import create_event_embed
from pique.log import LOGGER


class Subscriber(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def notify(self, event):
        raise NotImplementedError


class DiscordSubscriber(Subscriber):
    _NAME = "discord"

    def __init__(
        self, channel_id: int, channel: Optional[TextChannel] = None, *args, **kwargs
    ):
        self.channel = channel
        self.channel_id = int(channel_id)
        self._type = self._NAME
        super().__init__(*args, **kwargs)

    async def notify(self, event):
        try:
            LOGGER.info(f"Sending event #{event.id[:8]} to channel #{self.channel}")
            embed = create_event_embed(event)
            await self.channel.send(embed=embed)
        except Exception as e:
            LOGGER.error(f"Error in notify: {e}")

    @classmethod
    def from_config(cls, config: dict):
        name = config.get("name")
        description = config.get("description")
        channel_id = config.get("channel_id")
        return cls(
            name=name,
            description=description,
            channel_id=channel_id,
        )


class SubscriptionManager:
    def __init__(self, event_queue: Queue, subscribers: List[DiscordSubscriber]):
        self.subscriptions = {}
        self.event_queue = event_queue
        self.subscribers = subscribers

    @classmethod
    def from_config(
        cls, event_queue: Queue, config: PiqueConfig
    ) -> "SubscriptionManager":
        subscribers_data, subscribers = list(), list()
        discord_subscribers_data = config.discord.subscribers
        subscribers_data.extend(discord_subscribers_data)
        for subscriber_data in subscribers_data:
            # TODO: Add more subscriber types and make this more generic
            subscriber = DiscordSubscriber.from_config(subscriber_data)
            subscribers.append(subscriber)
        return cls(event_queue=event_queue, subscribers=subscribers)

    async def notify(self, event):
        try:
            if event.name not in self.subscriptions:
                return
            LOGGER.debug(f"Found {len(self.subscriptions[event.name])} subscribers")
            for subscriber in self.subscriptions[event.name]:
                LOGGER.debug(f"Sending event #{event.id[:8]} to subscribers")
                await subscriber.notify(event)
        except Exception as e:
            LOGGER.error(f"Error in notify: {e}")

    async def process_queue(self):
        while True:
            event = await self.event_queue.get()
            LOGGER.debug(f"Processing event #{event.id[:8]}")
            await self.notify(event)
            self.event_queue.task_done()
            await asyncio.sleep(_throttle.PUBLISHER)

    def start(self):
        asyncio.create_task(self.process_queue())

    def subscribe(self, event, subscriber):
        if event not in self.subscriptions:
            self.subscriptions[event.name] = []
        self.subscriptions[event.name].append(subscriber)

    def unsubscribe(self, event, subscriber):
        if event not in self.subscriptions:
            return
        self.subscriptions[event.name].remove(subscriber)
