from asyncio import Queue

from pique.config import PiqueConfig
from pique.discord.bot import PiqueBot
from pique.scanner.scanner import EventScanner
from pique.subscriptions import SubscriptionManager


async def _run_internal_services(config: PiqueConfig):
    event_queue = Queue()
    services = load_internal_services(config=config, event_queue=event_queue)
    for service in services:
        service.start()
    return services


async def run_discord_bot(config):
    scanner, manager = await _run_internal_services(config)
    bot = PiqueBot(
        name=config.name,
        command_prefix=config.discord.command_prefix,
        token=config.discord.token,
        event_scanner=scanner,
        subscription_manager=manager,
    )
    await bot.start()


def load_internal_services(config: PiqueConfig, event_queue: Queue) -> tuple:
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

    return scanner, subscription_manager
