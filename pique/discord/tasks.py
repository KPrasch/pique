from pique.discord.embeds import create_event_embed
from pique.log import LOGGER


async def send_event_message(subscriber, event):
    LOGGER.info(f"Sending event #{event.id[:8]} to channel #{subscriber.channel_id}")
    embed = create_event_embed(event)
    await subscriber.channel.send(embed=embed)
