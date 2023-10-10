import asyncio
from pathlib import Path

import click
import discord
from discord.ext import commands

from quirkbot.bot import QuirkBot
from quirkbot.config import load_config
from quirkbot.log import LOGGER


@click.command()
@click.option(
    "--config-file",
    required=False,
    default="quirkbot.yml",
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
        path = Path(config_file)
        config = load_config(path)
        command_prefix = config["bot"]["prefix"]
        LOGGER.info(f"Loaded configuration {path.absolute()}.")

        # Create bot instance
        bot = commands.Bot(command_prefix=command_prefix, intents=intents)
        await bot.add_cog(QuirkBot.from_config(config=config, bot=bot))
        LOGGER.info(f"Added cog to bot.")
        await bot.start(config["bot"]["token"])

    LOGGER.info("Starting Up...")
    asyncio.run(main())


if __name__ == "__main__":
    quirkbot()
