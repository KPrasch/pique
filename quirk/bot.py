import asyncio
from collections import defaultdict
from typing import Dict, List

from discord.ext import commands
from discord.ext import tasks
from web3 import Web3, HTTPProvider

from quirk.embeds import make_status_embed
from quirk.events import (
    Event,
    EventType,
    log_event,
    _load_web3_event_types,
    send_event_message
)
from quirk.log import LOGGER
from quirk.subscribers import _get_subscribers, Subscriber
from quirk.utils import async_lock, get_infura_url


class QuirkBot(commands.Cog):
    def __init__(
        self,
        bot,
        providers: Dict[int, HTTPProvider],
        events: Dict[str, EventType],
        subscribers: List[Subscriber] = None,
    ):
        self.bot = bot
        self.events = events
        self.providers = providers

        self.events_processed = 0
        self._subscribers = subscribers or []
        self.latest_scanned_blocks: Dict[int, int] = defaultdict(int)

        self.lock = asyncio.Lock()

    @commands.Cog.listener()
    async def on_ready(self):
        for chain_id, provider in self.providers.items():
            w3 = Web3(provider)
            w3.middleware_onion.clear()
            self.latest_scanned_blocks[chain_id] = w3.eth.block_number
            LOGGER.info(
                f"Latest block on chain {chain_id}: {self.latest_scanned_blocks[chain_id]}"
            )

        self._subscribers = _get_subscribers(
            bot=self.bot, subscribers=self._subscribers
        )
        self.bot.loop.create_task(self.initialize_check_web3_events())
        LOGGER.info(f"Bot is active!")
        LOGGER.info(
            f"{len(self._subscribers)} Subscribers; "
            f"{len(self.events)} Events; "
            f"{len(self.providers)} Providers"
        )

    @classmethod
    def from_config(cls, config: Dict, bot):
        infura_api_key = config["web3_endpoints"]["infura"]
        chain_ids = {contract["chain_id"] for contract in config["publishers"]}
        providers = {
            cid: Web3.HTTPProvider(get_infura_url(cid, infura_api_key))
            for cid in chain_ids
        }
        subscribers_data = config["bot"]["subscribers"]
        events = _load_web3_event_types(config, providers=providers)
        instance = cls(
            bot=bot, providers=providers, events=events, subscribers=subscribers_data
        )
        return instance

    async def initialize_check_web3_events(self):
        await self.bot.wait_until_ready()
        self.check_web3_events.start()

    async def fetch_events(self, event_type, start_block):
        try:
            events = event_type.get_logs(fromBlock=start_block)
            num_new_events = len(events)
            if num_new_events > 0:
                LOGGER.info(f"Found {num_new_events} new events")
                await self.handle_events(events)
        except Exception as e:
            LOGGER.error(f"Error in check_web3_events: {e}")
        finally:
            self.latest_scanned_blocks[
                event_type.w3.eth.chain_id
            ] = event_type.w3.eth.block_number
            self.events_processed += 1

    async def handle_events(self, events):
        for event_data in events:
            event = Event.from_attr_dict(event_data)
            log_event(event)
            for subscriber in self._subscribers:
                self.bot.loop.create_task(send_event_message(subscriber, event))

    @tasks.loop(seconds=30)
    async def check_web3_events(self):
        LOGGER.info("Next round of web3 event checking.")
        async with async_lock(self.lock):
            for event_type in self.events:
                event_name = event_type.name
                chain_id = event_type.chain_id
                contract_address = event_type.address
                latest_block = event_type.w3.eth.block_number
                start_block = self.latest_scanned_blocks[event_type.w3.eth.chain_id] + 1
                LOGGER.info(
                    f"Checking for {event_name} {contract_address[:8]}@{chain_id} "
                    f"between blocks {start_block} and {latest_block}"
                )
                await self.fetch_events(event_type, start_block)

    @commands.command()
    async def status(self, ctx):
        embed = await make_status_embed(ctx=ctx, w3c=self)
        await ctx.send(embed=embed)
