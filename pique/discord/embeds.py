from collections import defaultdict

from discord import Embed
from web3.contract import Contract

from pique._utils import bytes_to_hex, find_read_functions_without_input
from pique.constants.networks import NETWORKS
from pique.log import LOGGER


def _inline_code(text):
    return f"`{text}`"


def _etherscan_link(network, explorer, path, text):
    base_url = f"https://{network}.{explorer}"
    return f"[{text}]({base_url}/{path})"


def _get_name(chain_id: int) -> str:
    chain_data = NETWORKS.get(chain_id)
    if chain_data:
        return chain_data.get("name", "Unknown Chain")
    else:
        return f"Unknown Chain ({chain_id})"


def pretty_format_blocks(latest_scanned_blocks):
    formatted_blocks = [
        f"{_get_name(chain_id)}: {block_number}"
        for chain_id, block_number in latest_scanned_blocks.items()
    ]
    return ", ".join(formatted_blocks)


def add_event_args_fields(embed, event):
    for key, val in event.args.items():
        embed.add_field(name=key, value=_inline_code(str(val)), inline=False)


def format_uptime(raw_uptime):
    return (
        f"{raw_uptime.days}D "
        f"{raw_uptime.seconds // 3600}H "
        f"{(raw_uptime.seconds // 60) % 60}M "
        f"{raw_uptime.seconds % 60}S"
    )


async def make_contract_embed(ctx, contract: Contract):
    embed = Embed(
        title=f"Contract",
        description=f"Contract Address: {contract.address}",
        color=000000,
    )
    constant_functions = find_read_functions_without_input(contract.abi)
    for function_name, details in constant_functions.items():
        contract_function = getattr(contract.functions, function_name)
        try:
            output = contract_function().call()
        except Exception as e:
            LOGGER.error(f"Error calling function {function_name}: {e}")
            embed.add_field(
                name=function_name, value=f"Error calling function: {e}", inline=False
            )
            continue
        if isinstance(output, bytes):
            output = output.hex()
        embed.add_field(name=function_name, value=output, inline=False)
    embed.set_footer(text=f"Contract requested by: {ctx.author.display_name}")
    return embed


async def make_status_embed(w3c, ctx):
    embed = Embed(title=f"{w3c.name} Status", color=000000, description="")
    scanner, manager = w3c.scanner, w3c.subscription_manager
    embed.add_field(name="Processed", value=scanner.events_processed, inline=True)
    embed.add_field(name="Subscribers", value=len(manager.subscribers), inline=True)
    embed.add_field(name="Events", value=len(scanner.events), inline=True)
    embed.add_field(name="Loop Interval", value=scanner.loop_interval, inline=True)
    embed.add_field(name="Batch Size", value=scanner.batch_size, inline=True)

    uptime = format_uptime(w3c.uptime)
    embed.add_field(name="Uptime", value=uptime, inline=True)

    contract_events = defaultdict(list)
    for event_type in scanner.events:
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


def get_field_values(event, base_url):
    contract_address_link = _etherscan_link(event.contract_address, "address", base_url)
    transaction_hash_link = _etherscan_link(event.tx_hash.hex(), "tx", base_url)
    block_number_link = _etherscan_link(event.block_number, "block", base_url)

    return {
        "Contract Address": (contract_address_link, False),
        "Transaction Hash": (transaction_hash_link, False),
        "Block Number": (block_number_link, True),
        "Transaction Index": (event.tx_index, True),
        "Log Index": (event.log_index, True),
    }


def add_predefined_fields(embed, event, network, explorer):
    contract_link = _etherscan_link(
        network, explorer, f"address/{event.contract_address}", event.contract_address
    )
    tx_link = _etherscan_link(
        network, explorer, f"tx/{event.tx_hash.hex()}", event.tx_hash.hex()
    )
    block_link = _etherscan_link(
        network, explorer, f"block/{event.block_number}", str(event.block_number)
    )
    embed.add_field(name="Contract Address", value=contract_link, inline=False)
    embed.add_field(name="Transaction Hash", value=tx_link, inline=False)
    embed.add_field(name="Block Number", value=block_link, inline=True)
    embed.add_field(name="Transaction Index", value=str(event.tx_index), inline=True)
    embed.add_field(name="Log Index", value=str(event.log_index), inline=True)


def create_event_embed(event: "Event"):
    network, explorer = NETWORKS[event.chain_id]

    embed = Embed(
        title=f"New {event.contract_name} {event.event_type} Event",
        description=event.description,
        color=event.color,
        timestamp=event.timestamp or None,
    )

    # Add fields to the embed
    add_predefined_fields(embed, event, network, explorer)
    add_event_args_fields(embed, event)

    LOGGER.debug(f"Created embed for event: {event}")
    return embed
