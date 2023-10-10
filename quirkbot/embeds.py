from collections import defaultdict

from discord import Embed
from web3 import Web3

from quirkbot.networks import NETWORKS


async def make_status_embed(w3c, ctx):
    embed = Embed(
        title=f"{w3c.name} Status",
        color=000000,
        # description="Current status of the bot."
    )

    pretty_blocks = ", ".join(f"{NETWORKS.get(k, k)}: {v}" for k, v in w3c.latest_scanned_blocks.items())
    embed.add_field(
        name="Latest Scanned Blocks",
        value=pretty_blocks,
        inline=False
    )
    embed.add_field(name="Processed", value=w3c.events_processed, inline=True)
    embed.add_field(name="Subscribers", value=len(w3c._subscribers), inline=True)
    embed.add_field(name="Events", value=len(w3c.events), inline=True)
    embed.add_field(name="Loop Interval", value=w3c.loop_interval, inline=True)
    embed.add_field(name="Batch Size", value=w3c.batch_size, inline=True)

    raw_uptime = w3c.uptime
    pretty_up_time = (f"{raw_uptime.days}D "
                      f"{raw_uptime.seconds // 3600}H "
                      f"{(raw_uptime.seconds // 60) % 60}M "
                      f"{raw_uptime.seconds % 60}S")
    embed.add_field(name="Uptime", value=pretty_up_time, inline=True)

    contract_events = defaultdict(list)
    for event_type in w3c.events:
        contract_events[event_type.address].append(event_type.name)

    human_readable_events = []
    for address in sorted(contract_events.keys()):  # Sorting contracts by address
        events = sorted(contract_events[address])  # Sorting events within each contract
        event_lines = "\n".join(f"• {event}" for event in events)
        contract_line = f"---\nContract: [0x{address}...](https://etherscan.io/address/{address})\n{event_lines}"
        human_readable_events.append(contract_line)

    embed.add_field(
        name="Tracked Events",
        value="\n".join(human_readable_events),
        inline=False,
    )

    embed.set_footer(text=f"Status requested by: {ctx.author.display_name}")
    return embed

def create_event_embed(event_instance):
    embed = Embed(
        title=f"New {event_instance.event_type} Event",
        description="",  # event_instance.description or str(),
        color=0x00FF00,  # You can choose your own color here
        timestamp=event_instance.timestamp or None,  # Optional: add a timestamp
    )

    # embed.set_footer(text="Powered by QuirkBot", icon_url="your_bot_icon_url_here")  # Optional: add a footer
    # embed.set_thumbnail(url="your_thumbnail_url_here")  # Optional: add a thumbnail

    embed.add_field(name="Block Number", value=event_instance.block_number, inline=True)
    embed.add_field(name="Log Index", value=event_instance.log_index, inline=True)
    embed.add_field(
        name="Transaction Index", value=event_instance.tx_index, inline=True
    )
    embed.add_field(
        name="Transaction Hash", value=event_instance.tx_hash.hex(), inline=False
    )
    embed.add_field(
        name="Contract Address", value=event_instance.contract_address, inline=False
    )
    embed.add_field(
        name="Block Hash", value=event_instance.block_hash.hex(), inline=False
    )
    embed.add_field(name="From", value=event_instance.from_address, inline=False)
    embed.add_field(name="To", value=event_instance.to_address, inline=False)
    embed.add_field(
        name="Value", value=Web3.from_wei(event_instance.value, "ether"), inline=False
    )

    return embed
