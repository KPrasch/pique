from pique.discord.embeds import create_event_embed
from pique.log import LOGGER
from pique.subscribers.subscribers import Subscriber


class DiscordSubscriber(Subscriber):

    def __init__(self, channel):
        self.channel = channel
        self.channel_id = channel.id

    async def notify(self, event):
        LOGGER.info(f"Sending event #{event.id[:8]} to channel #{self.channel.id}")
        embed = create_event_embed(event)
        await self.channel.send(embed=embed)
