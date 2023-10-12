import asyncio
from pathlib import Path

import click
from discord.ext import commands
import discord as _discord

from pique import defaults
from pique.bot import PiqueBot
from pique.config import load_config
from pique.log import LOGGER


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
            message = "missing required key in configuration file: (pique|web3|bot|events)."
            LOGGER.error(message)
            raise e

        # Create bot instance
        bot = commands.Bot(command_prefix=command_prefix, intents=intents)
        await bot.add_cog(PiqueBot.from_config(config=config, bot=bot))
        LOGGER.debug(f"Starting Bot...")
        await bot.start(token)

    asyncio.run(main())


if __name__ == "__main__":
    pique()
