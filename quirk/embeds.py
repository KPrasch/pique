from discord import Embed
from web3 import Web3


async def make_status_embed(w3c, ctx):
    embed = Embed(
        title="Bot Status",
        color=0x00FF00,  # You can choose your own color
        description="Current status of the bot.",
    )
    # Add fields to the embed
    embed.add_field(name="Latest Scanned Block", value=w3c.latest_scanned_block, inline=True)
    embed.add_field(name="Events Processed", value=w3c.events_processed, inline=True)

    human_readable_events = [f"{name}: {event_type.address}" for name, event_type in w3c.events.items()]
    embed.add_field(name="Tracked Events", value=', '.join(human_readable_events), inline=False)
    embed.set_footer(text="Status requested by: {}".format(ctx.author.display_name))

    return embed


def create_event_embed(event_instance):
    embed = Embed(
        title=f"New {event_instance.event_type} Event",
        description="",  # event_instance.description or str(),
        color=0x00FF00,  # You can choose your own color here
        timestamp=event_instance.timestamp or None  # Optional: add a timestamp
    )

    # embed.set_footer(text="Powered by QuirkBot", icon_url="your_bot_icon_url_here")  # Optional: add a footer
    # embed.set_thumbnail(url="your_thumbnail_url_here")  # Optional: add a thumbnail

    embed.add_field(name="Block Number", value=event_instance.block_number, inline=True)
    embed.add_field(name="Log Index", value=event_instance.log_index, inline=True)
    embed.add_field(name="Transaction Index", value=event_instance.tx_index, inline=True)
    embed.add_field(name="Transaction Hash", value=event_instance.tx_hash.hex(), inline=False)
    embed.add_field(name="Contract Address", value=event_instance.contract_address, inline=False)
    embed.add_field(name="Block Hash", value=event_instance.block_hash.hex(), inline=False)
    embed.add_field(name="From", value=event_instance.from_address, inline=False)
    embed.add_field(name="To", value=event_instance.to_address, inline=False)
    embed.add_field(name="Value", value=Web3.from_wei(event_instance.value, 'ether'), inline=False)

    return embed
