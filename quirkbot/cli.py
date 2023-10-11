import asyncio
from pathlib import Path

import click
import discord
from discord.ext import commands

from quirkbot import defaults
from quirkbot.bot import QuirkBot
from quirkbot.config import load_config
from quirkbot.log import LOGGER


@click.command()
@click.option(
    "--config-file",
    required=False,
    default=defaults.DEFAULT_CONFIG_FILEPATH,
    type=click.Path(exists=True),
    help="Path to the YAML configuration file",
)
def quirkbot(config_file: str):
    async def main():

        # Set up Discord bot intents
        intents = discord.Intents.default()
        intents.typing = True
        intents.messages = True
        LOGGER.info(f"Limited intents to {intents}")

        # Load configuration
        try:
            path = Path(config_file)
            config = load_config(path)
            quirk = config["quirk"]
            token = config["quirk"]["discord"]
            command_prefix = quirk["command_prefix"]
            LOGGER.info(f"Loaded configuration {path.absolute()}.")
        except KeyError as e:
            message = "missing required key in configuration file: (quirk|web3|bot|events)."
            LOGGER.error(message)
            raise e

        # Create bot instance
        bot = commands.Bot(command_prefix=command_prefix, intents=intents)
        await bot.add_cog(QuirkBot.from_config(config=config, bot=bot))
        LOGGER.debug(f"Starting Bot...")
        await bot.start(token)

    asyncio.run(main())


if __name__ == "__main__":
    quirkbot()
