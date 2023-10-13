import datetime

from discord import Intents
from discord.ext import commands

from pique.discord.embeds import make_status_embed
from pique.log import LOGGER
from pique.scanner.scanner import EventScanner
from pique.subscriptions import DiscordSubscriber, SubscriptionManager


class PiqueBot(commands.Cog):
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
        self.bot = commands.Bot(
            command_prefix=command_prefix,
            intents=intents
        )
        self.name = name
        self.__token = token
        self.scanner = event_scanner
        self.subscription_manager = subscription_manager
        self.start_time = datetime.datetime.now()
        LOGGER.debug(f"Initialized {self.name}")

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

    def _connect_subscriber_channels(self):
        for subscriber in self.subscription_manager.subscribers:
            if not isinstance(subscriber, DiscordSubscriber):
                continue

            channel = self.bot.get_channel(subscriber.channel_id)
            if not channel:
                LOGGER.error(f"Could not find channel with ID {subscriber.channel_id}")
                continue

            LOGGER.info(f"Found channel {channel.name} with ID {channel.id}")
            subscriber.channel = channel

            for event in self.scanner.events:
                # subscribe to all events
                self.subscription_manager.subscribe(event=event, subscriber=subscriber)

    @property
    def uptime(self):
        if self.start_time is None:
            return "Bot is not active"
        else:
            return datetime.datetime.now() - self.start_time

    @commands.command()
    async def status(self, ctx):
        LOGGER.debug(f"Status requested by {ctx.author.display_name}")
        try:
            embed = await make_status_embed(ctx=ctx, w3c=self)
            await ctx.send(embed=embed)
        except Exception as e:
            LOGGER.error(f"Error in status: {e}")
