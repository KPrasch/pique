import asyncio
import datetime
from asyncio import Queue
from typing import Dict, List

from discord.ext import commands
from discord.ext import tasks
from web3 import Web3, HTTPProvider

from pique import defaults
from pique._utils import get_infura_url
from pique.embeds import make_status_embed
from pique.events import (
    EventContainer,
    _load_config_events,
    send_event_message,
    Event
)
from pique.log import LOGGER
from pique.subscribers import _get_subscribers, Subscriber


class PiqueBot(commands.Cog):
    def __init__(
        self,
        bot,
        name: str,
        batch_size: int,
        start_block: int,
        loop_interval: int,
        events: List[EventContainer],
        providers: Dict[int, HTTPProvider],
        subscribers: List[Subscriber] = None
    ):

        self.bot = bot
        self.name = name
        self.events = events
        self.providers = providers
        self.batch_size = batch_size
        self.start_block = start_block

        self.task_queue = Queue()

        self.events_processed = 0
        self._subscribers_data = subscribers or []
        self._subscribers = None

        self.loop_interval = loop_interval
        self.check_web3_events.change_interval(seconds=self.loop_interval)
        self.start_time = datetime.datetime.now()
        LOGGER.debug(f"Initialized {self.name}")

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            LOGGER.debug(f"Starting {self.name} services...")
            for chain_id, provider in self.providers.items():
                LOGGER.debug(f"Initializing web3 for chain {chain_id}")
                w3 = Web3(provider)
                w3.middleware_onion.clear()
            self._subscribers = _get_subscribers(bot=self.bot, subscribers=self._subscribers_data)
            self.bot.loop.create_task(self.process_queue())
            self.bot.loop.create_task(self.initialize_check_web3_events_thread())
            LOGGER.info(f"Bot is active!")
            LOGGER.info(
                f"{len(self._subscribers)} Subscribers; "
                f"{len(self.events)} Events; "
                f"{len(self.providers)} Providers"
            )
        except Exception as e:
            LOGGER.error(f"Error in on_ready: {e}")

    @property
    def uptime(self):
        if self.start_time is None:
            return "Bot is not active"
        else:
            return datetime.datetime.now() - self.start_time

    @classmethod
    def from_config(cls, config: Dict, bot):
        try:

            # required top-level keys
            pique_config = config["pique"]
            contracts_config = config["contracts"]
            contracts = contracts_config["track"]
            discord_config = config["discord"]

            # required nested keys
            name = pique_config["name"]
            infura_api_key = contracts_config["infura"]
            chain_ids = {contract["chain_id"] for contract in contracts}
            subscribers_data = discord_config["subscribers"]

        except KeyError as e:
            message = "missing required key in configuration file."
            LOGGER.error(message)
            raise e

        # optional fields
        batch_size = contracts_config.get("batch_size", defaults.BATCH_SIZE)
        loop_interval = contracts_config.get("loop_interval", defaults.LOOP_INTERVAL)
        start_block = contracts_config.get("start_block", defaults.START_BLOCK)

        providers = {
            cid: Web3.HTTPProvider(get_infura_url(cid, infura_api_key))
            for cid in chain_ids
        }
        events = _load_config_events(contracts, providers=providers)

        instance = cls(
            bot=bot,
            name=name,
            loop_interval=loop_interval,
            batch_size=batch_size,
            providers=providers,
            events=events,
            subscribers=subscribers_data,
            start_block=start_block
        )
        return instance

    async def initialize_check_web3_events_thread(self):
        self.bot.loop.create_task(self.initialize_check_web3_events())
        LOGGER.debug(f"Initialized check_web3_events thread")

    async def initialize_check_web3_events(self):
        self.check_web3_events.start()
        LOGGER.debug(f"Started check_web3_events thread")

    async def process_queue(self):
        LOGGER.debug(f"Starting process_queue thread")
        while True:
            task = await self.task_queue.get()
            await task
            self.task_queue.task_done()
            await asyncio.sleep(0.1)  # Adjust as necessary

    async def fetch_events(self, event_container: EventContainer, start_block: int, batch_size: int) -> None:
        LOGGER.info(f"Fetching events for {event_container.name}|{event_container.address[:8]}")
        async with event_container.lock:
            # Lock to prevent simultaneous scans of the same event type, block range, and chain
            try:
                latest_block = event_container.w3.eth.block_number
                end_block = min(start_block + batch_size, latest_block)

                # If there's nothing new, just return
                if end_block <= start_block:
                    return

                LOGGER.debug(f"Fetching from block {start_block} to {end_block} for event: {event_container.name}")
                events = event_container.get_logs(fromBlock=start_block, toBlock=end_block)
                num_new_events = len(events)
                if num_new_events > 0:
                    LOGGER.info(f"Found {num_new_events} new events")
                    await self.handle_events(events=events)

                event_container.latest_scanned_block = end_block
                self.events_processed += num_new_events
            except Exception as e:
                LOGGER.error(f"Error in check_web3_events: {e}")

    async def handle_events(self, events: List[Event]) -> None:
        LOGGER.debug(f"Handling {len(events)} events")
        for event in events:
            for subscriber in self._subscribers:
                task = send_event_message(subscriber, event)
                self.task_queue.put_nowait(task)
                LOGGER.debug(f"Adding task for event: {event} at block: {event.block_number}")

    @tasks.loop(seconds=defaults.LOOP_INTERVAL)
    async def check_web3_events(self):
        LOGGER.debug("Next round of web3 event checking.")
        try:
            for event_container in self.events:  # Iterate over all event types
                LOGGER.debug(f"Scanning {event_container.name}|{event_container.address[:8]}")
                # Identify the starting block for scanning based on the last scanned block
                start_block = event_container.latest_scanned_block + 1
                latest_block = event_container.w3.eth.block_number

                # Batch fetching logic
                while start_block <= latest_block:
                    await self.fetch_events(event_container, start_block, self.batch_size)
                    start_block += self.batch_size  # Update the start block for the next batch

                await asyncio.sleep(0.1)  # be kind to the API
        except Exception as e:
            LOGGER.error(f"Error in check_web3_events: {e}")

    @commands.command()
    async def status(self, ctx):
        LOGGER.debug(f"Status requested by {ctx.author.display_name}")
        try:
            embed = await make_status_embed(ctx=ctx, w3c=self)
            await ctx.send(embed=embed)
        except Exception as e:
            LOGGER.error(f"Error in status: {e}")
