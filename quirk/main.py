import asyncio
from pathlib import Path

import discord
from discord.ext import commands

from quirk.bot import QuirkBot
from quirk.log import LOGGER
from quirk.utils import load_config


async def main():
    # Set up Discord bot intents
    intents = discord.Intents.default()
    intents.typing = True
    intents.messages = True
    LOGGER.info(f"Limited intents to {intents}")

    # Load configuration
    path = Path("conf.yml")
    config = load_config(path)
    command_prefix = config["bot"]["prefix"]
    LOGGER.info(f"Loaded configuration {path.absolute()}.")

    # Create bot instance
    bot = commands.Bot(command_prefix=command_prefix, intents=intents)
    await bot.add_cog(QuirkBot.from_config(config=config, bot=bot))
    LOGGER.info(f"Added cog to bot.")
    await bot.start(config["bot"]["token"])


if __name__ == "__main__":
    LOGGER.info("Starting Up...")
    asyncio.run(main())
