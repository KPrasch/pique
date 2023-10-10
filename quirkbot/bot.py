import asyncio
import datetime
from asyncio import Queue
from collections import defaultdict
from typing import Dict, List

from discord.ext import commands
from discord.ext import tasks
from web3 import Web3, HTTPProvider

from quirkbot import defaults
from quirkbot.embeds import make_status_embed
from quirkbot.events import (
    Event,
    EventType,
    _load_web3_event_types,
    send_event_message
)
from quirkbot.log import LOGGER
from quirkbot.subscribers import _get_subscribers, Subscriber
from quirkbot.utils import get_infura_url


class QuirkBot(commands.Cog):
    def __init__(
        self,
        bot,
        name: str,
        providers: Dict[int, HTTPProvider],
        events: Dict[str, EventType],
        loop_interval: int,
        batch_size: int,
        subscribers: List[Subscriber] = None,
    ):

        self.bot = bot
        self.name = name
        self.events = events
        self.providers = providers
        self.batch_size = batch_size

        self.lock = asyncio.Lock()
        self.task_queue = Queue()

        self.events_processed = 0
        self._subscribers = subscribers or []

        self.latest_scanned_blocks: Dict[int, int] = defaultdict(int)
        self.loop_interval = loop_interval
        self.check_web3_events.change_interval(seconds=self.loop_interval)
        self.start_time = datetime.datetime.now()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.process_queue())
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
        self.bot.loop.create_task(self.initialize_check_web3_events_thread())
        LOGGER.info(f"Bot is active!")
        LOGGER.info(
            f"{len(self._subscribers)} Subscribers; "
            f"{len(self.events)} Events; "
            f"{len(self.providers)} Providers"
        )

    @property
    def uptime(self):
        if self.start_time is None:
            return "Bot is not active"
        else:
            return datetime.datetime.now() - self.start_time

    @classmethod
    def from_config(cls, config: Dict, bot):
        try:

            # top-level keys
            quirk = config["quirk"]
            events = config["events"]
            web3 = config["web3"]
            bot_config = config["bot"]

            # nested keys
            name = quirk["name"]
            infura_api_key = web3["infura"]
            chain_ids = {contract["chain_id"] for contract in events}
            subscribers_data = bot_config["subscribers"]

        except KeyError as e:
            message = "missing required key in configuration file: (quirk|web3|bot|events)."
            LOGGER.error(message)
            raise e

        batch_size = quirk.get("batch_size", defaults.BATCH_SIZE)
        loop_interval = quirk.get("loop_interval", defaults.LOOP_INTERVAL)

        providers = {
            cid: Web3.HTTPProvider(get_infura_url(cid, infura_api_key))
            for cid in chain_ids
        }
        events = _load_web3_event_types(config, providers=providers)
        instance = cls(
            bot=bot,
            name=name,
            loop_interval=loop_interval,
            batch_size=batch_size,
            providers=providers,
            events=events,
            subscribers=subscribers_data
        )
        return instance

    def initialize_check_web3_events_thread(self):
        self.bot.loop.create_task(self.initialize_check_web3_events())

    async def initialize_check_web3_events(self):
        self.check_web3_events.start()

    async def process_queue(self):
        while True:
            task = await self.task_queue.get()
            await task
            self.task_queue.task_done()
            await asyncio.sleep(0.1)  # Adjust as necessary

    async def fetch_events(self, event_type, start_block, batch_size=100):
        async with self.lock:
            # Lock to prevent simultaneous scans
            try:
                latest_block = event_type.w3.eth.block_number
                end_block = min(start_block + batch_size, latest_block)

                # If there's nothing new, just return
                if end_block <= start_block:
                    return

                LOGGER.info(f"Fetching events from {start_block} to {end_block}")
                events = event_type.get_logs(fromBlock=start_block, toBlock=end_block)
                num_new_events = len(events)
                if num_new_events > 0:
                    LOGGER.info(f"Found {num_new_events} new events")
                    await self.handle_events(events)

                self.latest_scanned_blocks[event_type.w3.eth.chain_id] = end_block
                self.events_processed += num_new_events
            except Exception as e:
                LOGGER.error(f"Error in check_web3_events: {e}")

    async def handle_events(self, events: List[Dict]):
        for event_data in events:
            event = Event.from_attr_dict(event_data)
            for subscriber in self._subscribers:
                task = send_event_message(subscriber, event)
                self.task_queue.put_nowait(task)

    @tasks.loop(seconds=None)
    async def check_web3_events(self):
        try:
            LOGGER.info("Next round of web3 event checking.")
            for event_type in self.events:  # Iterate over all event types
                LOGGER.info(f"Scanning {event_type.name}|{event_type.address[:8]}")
                # Identify the starting block for scanning based on the last scanned block
                start_block = self.latest_scanned_blocks[event_type.w3.eth.chain_id] + 1
                latest_block = event_type.w3.eth.block_number

                # Batch fetching logic
                while start_block <= latest_block:
                    await self.fetch_events(event_type, start_block, self.batch_size)
                    start_block += self.batch_size  # Update the start block for the next batch

                await asyncio.sleep(0.1)  # be kind to the API
        except Exception as e:
            LOGGER.error(f"Error in check_web3_events: {e}")

    @commands.command()
    async def status(self, ctx):
        try:
            embed = await make_status_embed(ctx=ctx, w3c=self)
            await ctx.send(embed=embed)
        except Exception as e:
            LOGGER.error(f"Error in status: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)  # Restrict to admins
    async def set_loop_interval(self, ctx, interval: int):
        """Sets the interval for the event checking loop."""

        # Validation for the new interval (for example, it should be greater than 0)
        if interval <= 0:
            await ctx.send("Interval must be greater than zero.")
            return

        self.check_web3_events.change_interval(seconds=interval)
        await ctx.send(f"Loop interval has been set to {interval} seconds.")

