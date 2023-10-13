import asyncio

import click

from pique.config import PiqueConfig
from pique.constants import defaults
from pique.log import LOGGER
from pique.services import run_discord_bot


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
    LOGGER.setLevel(log_level.upper())
    config = PiqueConfig.from_file(filepath=config_file)
    task = run_discord_bot(config=config)
    asyncio.run(task)


if __name__ == "__main__":
    pique()
