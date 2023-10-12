import asyncio
from asyncio import Queue
from pathlib import Path

import click
import discord as _discord
from discord.ext import commands

from pique.config import load_config, PiqueConfig
from pique.constants import defaults
from pique.discord.bot import PiqueBot
from pique.log import LOGGER
from pique.scanner.scanner import EventScanner
from pique.subscriptions import SubscriptionManager


@click.command()
@click.option(
    "--config-file",
    required=False,
    default=defaults.DEFAULT_CONFIG_FILEPATH,
    type=click.Path(exists=True),
    help="Path to the YAML configuration file",
)
@click.option(
    "--log-level",
    required=False,
    default=defaults.DEFAULT_LOG_LEVEL,
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    help="Logging level",
)
def pique(config_file: str, log_level: str):
    # set logging level
    LOGGER.setLevel(log_level.upper())

    async def main():
        # Set up Discord bot intents
        intents = _discord.Intents.default()
        intents.typing = True
        intents.messages = True
        LOGGER.info(f"Limited intents to {intents}")

        # Load configuration
        try:
            path = Path(config_file)
            config = load_config(path)
            discord = config["discord"]
            token = discord["token"]
            command_prefix = discord["command_prefix"]
            LOGGER.info(f"Loaded configuration {path.absolute()}.")
        except KeyError as e:
            message = (
                "missing required key in configuration file: (pique|web3|bot|events)."
            )
            LOGGER.error(message)
            raise e

        # Create bot instance
        bot = commands.Bot(command_prefix=command_prefix, intents=intents)

        config = PiqueConfig.from_dict(config)
        event_queue = Queue()

        scanner = EventScanner(
            events=config.events,
            providers=config.providers,
            batch_size=config.batch_size,
            start_block=config.start_block,
            loop_interval=config.loop_interval,
            queue=event_queue,
        )

        subscription_manager = SubscriptionManager.from_config(
            config=config,
            event_queue=event_queue,
        )

        _pique = PiqueBot(
            bot=bot,
            name=config.name,
            event_scanner=scanner,
            subscription_manager=subscription_manager,
        )

        scanner.start()
        subscription_manager.start()
        
        await bot.add_cog(_pique)
        LOGGER.debug(f"Starting Bot...")
        await bot.start(token)

    asyncio.run(main())


if __name__ == "__main__":
    pique()
