from typing import TypedDict, Optional

from discord import TextChannel

from pique.discord.embeds import create_event_embed
from pique.log import LOGGER
from pique.subscriptions import Subscriber


class DiscordSubscriberDict(TypedDict):
    name: str
    description: str
    channel_id: int


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
        LOGGER.debug(f">>>>> Sending event #{event.id[:8]} to subscriber {self.name}")
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
