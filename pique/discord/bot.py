import datetime

from discord import Intents
from discord.ext import commands

from pique.discord.embeds import make_status_embed, make_contract_embed
from pique.log import LOGGER
from pique.scanner.scanner import EventScanner
from pique.subscriptions import DiscordSubscriber, SubscriptionManager


class PiqueCog(commands.Cog):
    def __init__(
        self,
        name: str,
        token: str,
        command_prefix: str,
        event_scanner: EventScanner,
        subscription_manager: SubscriptionManager,
    ):
        intents = Intents.default()
        intents.typing = True
        intents.messages = True
        LOGGER.info(f"Limited intents to {intents}")
        self.bot = commands.Bot(command_prefix=command_prefix, intents=intents)
        self.name = name
        self.__token = token
        self.scanner = event_scanner
        self.subscription_manager = subscription_manager
        self.start_time = datetime.datetime.now()
        LOGGER.debug(f"Initialized {self.name}")

    @property
    def uptime(self):
        if self.start_time is None:
            return "Bot is not active"
        else:
            return datetime.datetime.now() - self.start_time

    async def start(self):
        await self.bot.add_cog(self)
        LOGGER.debug(f"Starting Bot...")
        await self.bot.start(self.__token)

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self._connect_subscriber_channels()
            LOGGER.info(f"Bot is active!")
        except Exception as e:
            LOGGER.error(f"Error in on_ready: {e}")

    @commands.command()
    async def status(self, ctx):
        LOGGER.debug(f"Status requested by {ctx.author.display_name}")
        try:
            embed = await make_status_embed(ctx=ctx, w3c=self)
            await ctx.send(embed=embed)
        except Exception as e:
            LOGGER.error(f"Error in status: {e}")

    @commands.command()
    async def contract(self, ctx, address: str):
        LOGGER.debug(f"Contract requested by {ctx.author.display_name}")
        try:
            for event in self.scanner.events:
                LOGGER.debug(f"Checking {event._type.address} == {address}")
                if event._type.address.lower() == address.lower():
                    LOGGER.debug(f"Found contract {address}")
                    break
            else:
                LOGGER.debug(f"Contract {address} not found")
                await ctx.send(f"Contract {address} not found")
                return

            abi = event._type.contract_abi
            contract = event.w3.eth.contract(address=address, abi=abi)
        except Exception as e:
            LOGGER.error(f"Error in contract: {e}")
            await ctx.send(f"Error in contract: {e}")
            return
        try:
            embed = await make_contract_embed(ctx=ctx, contract=contract)
            await ctx.send(embed=embed)
        except Exception as e:
            LOGGER.error(f"Error in contract: {e}")

    def _connect_subscriber_channels(self):
        for subscriber in self.subscription_manager.subscribers:

            # skip non-discord subscribers
            if not isinstance(subscriber, DiscordSubscriber):
                continue

            # connect the channel
            channel = self.bot.get_channel(subscriber.channel_id)
            if not channel:
                LOGGER.error(f"Could not find channel with ID {subscriber.channel_id}")
                continue

            # set the channel
            LOGGER.info(f"Found channel {channel.name} with ID {channel.id}")
            subscriber.channel = channel

            # subscribe to events
            for event in self.scanner.events:
                # subscribe to all events by default
                # TODO: allow for more granular subscription
                self.subscription_manager.subscribe(event=event, subscriber=subscriber)
