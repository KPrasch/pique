import asyncio
from abc import ABC, abstractmethod
from asyncio import Queue
from typing import List

from pique.config import PiqueConfig
from pique.log import LOGGER


class Subscriber(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def notify(self, event):
        raise NotImplementedError


class SubscriptionManager:
    def __init__(self, event_queue: Queue, subscribers: List[Subscriber]):
        self.subscriptions = {}
        self.event_queue = event_queue
        self.subscribers = subscribers

    @classmethod
    def from_config(
        cls, event_queue: Queue, config: PiqueConfig
    ) -> "SubscriptionManager":
        subscribers_data, subscribers = list(), list()
        discord_subscribers_data = config.discord["subscribers"]
        subscribers_data.extend(discord_subscribers_data)
        for subscriber_data in subscribers_data:
            from pique.discord.subscriber import DiscordSubscriber

            subscriber = DiscordSubscriber.from_config(subscriber_data)
            subscribers.append(subscriber)
        return cls(event_queue=event_queue, subscribers=subscribers)

    async def notify(self, event):
        try:
            LOGGER.debug(f"Sending event #{event.id[:8]} to subscribers")
            for subscriber in self.subscribers:
                LOGGER.debug(
                    f"Sending event #{event.id[:8]} to subscriber {subscriber.name}"
                )
                await subscriber.notify(event)
                LOGGER.info(
                    f"Sent event #{event.id[:8]} to subscriber {subscriber.name}"
                )
        except Exception as e:
            LOGGER.error(f"Error in notify: {e}")

    async def process_queue(self):
        while True:
            event = await self.event_queue.get()
            LOGGER.debug(f"Processing event #{event.id[:8]}")
            await self.notify(event)
            self.event_queue.task_done()
            await asyncio.sleep(0.2)

    def start(self):
        asyncio.create_task(self.process_queue())

    def subscribe(self, event, callback):
        if event not in self.subscriptions:
            self.subscriptions[event] = []
        self.subscriptions[event].append(callback)

    def unsubscribe(self, event, callback):
        if event not in self.subscriptions:
            return
        self.subscriptions[event].remove(callback)
