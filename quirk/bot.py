import asyncio
from collections import defaultdict
from typing import Dict, List

from discord.ext import commands
from discord.ext import tasks
from web3 import Web3, HTTPProvider

from quirk.embeds import create_event_embed, make_status_embed
from quirk.events import Event, EventType
from quirk.log import LOGGER
from quirk.subscribers import _get_subscribers, Subscriber
from quirk.utils import _load_web3_event_types, async_lock, log_event, get_infura_url


async def send_event_message(subscriber, event):
    LOGGER.info(f"Sending event #{event.id[:8]} to channel #{subscriber.channel_id}")
    embed = create_event_embed(event)
    await subscriber.channel.send(embed=embed)


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
        self.event_metadata = {
            (name, _type.address): _type for name, _type in self.events.items()
        }
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
            f"{len(self._subscribers)} Subscribers;"
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
            for name, event_type in self.events.items():
                latest_block = event_type.w3.eth.block_number
                start_block = self.latest_scanned_blocks[event_type.w3.eth.chain_id] + 1
                LOGGER.info(
                    f"Checking for events between blocks {start_block} and {latest_block}"
                )
                await self.fetch_events(event_type, start_block)

    @commands.command()
    async def start(self, ctx):
        if not self.check_web3_events.is_running():
            self.check_web3_events.start()
            await ctx.send("Started checking for web3 events.")
        else:
            await ctx.send("Web3 event check is already running.")

    @commands.command()
    async def stop(self, ctx):
        if self.check_web3_events.is_running():
            self.check_web3_events.stop()
            await ctx.send("Stopped checking for web3 events.")
        else:
            await ctx.send("Web3 event check is not currently running.")

    @commands.command()
    async def status(self, ctx):
        embed = await make_status_embed(ctx=ctx, w3c=self)
        await ctx.send(embed=embed)

    @commands.command()
    async def subscribe(self, ctx, channel_id: int, event_type: str):
        LOGGER.info(f"Subscribing from {event_type} events in channel {channel_id}")
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send(f"Could not find channel with ID {channel_id}")
            return
        if event_type not in self.events.keys():
            await ctx.send(f"Could not find event type {event_type}")
            return
        subscriber = Subscriber(
            channel_id=channel_id,
            name=event_type,
            description=f"Subscribed to {event_type} events",
            channel=channel,
        )
        self._subscribers.append(subscriber)
        await ctx.send(
            f"Subscribed to {event_type} events in channel {channel.mention}"
        )

    @commands.command()
    async def unsubscribe(self, ctx, channel_id: int, event_type: str):
        LOGGER.info(f"Unsubscribing from {event_type} events in channel {channel_id}")
        channel = self.bot.get_channel(channel_id)
        if not channel:
            LOGGER.info(f"Could not find channel with ID {channel_id}")
            await ctx.send(f"Could not find channel with ID {channel_id}")
            return
        if event_type not in self.events.keys():
            LOGGER.info(f"Could not find event type {event_type}")
            await ctx.send(f"Could not find event type {event_type}")
            return
        subscriber = Subscriber(
            channel_id=channel_id,
            name=event_type,
            description=f"Subscribed to {event_type} events",
            channel=channel,
        )
        LOGGER.info(f"Removing subscriber {subscriber}")
        self._subscribers = [
            s for s in self._subscribers if s.channel_id != subscriber.channel_id
        ]
        await ctx.send(
            f"Unsubscribed from {event_type} events in channel {channel.mention}"
        )
        LOGGER.info(f"Removed subscriber {subscriber}")
