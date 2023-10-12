import datetime

import discord
from discord.ext import commands

from pique.discord.embeds import make_status_embed
from pique.discord.subscriber import DiscordSubscriber
from pique.log import LOGGER
from pique.scanner.scanner import EventScanner
from pique.subscriptions import SubscriptionManager


class PiqueBot(commands.Cog):
    def __init__(
        self,
        bot,
        name: str,
        event_scanner: EventScanner,
        subscription_manager: SubscriptionManager,
    ):
        self.bot = bot
        self.name = name
        self.scanner = event_scanner
        self.subscription_manager = subscription_manager
        self.start_time = datetime.datetime.now()
        LOGGER.debug(f"Initialized {self.name}")

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            LOGGER.debug(f"Starting {self.name} services...")
            self._load_discord_subscribers()
            self.scanner.start()
            self.subscription_manager.start()
            LOGGER.info(f"Bot is active!")
        except Exception as e:
            LOGGER.error(f"Error in on_ready: {e}")

    def _get_channel(self, channel_id: int) -> discord.TextChannel:
        channel = self.bot.get_channel(channel_id)
        if channel:
            LOGGER.info(f"Found channel {channel.name} with ID {channel.id}")
            return channel
        message = f"Could not find channel with ID {channel_id}"
        LOGGER.error(message)

    def _load_discord_subscribers(self):
        for subscriber in self.subscription_manager.subscribers:
            if subscriber._type != DiscordSubscriber._NAME:
                continue
            subscriber.channel = self._get_channel(subscriber.channel_id)

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
