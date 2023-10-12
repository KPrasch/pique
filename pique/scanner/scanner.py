import asyncio
from asyncio import Queue
from typing import List

from pique.log import LOGGER
from pique.scanner.events import EventContainer, Event


class EventScanner:
    def __init__(
        self, events, providers, batch_size, start_block, loop_interval, queue: Queue
    ):
        self.queue = queue
        self.events = events
        self.providers = providers
        self.batch_size = batch_size
        self.start_block = start_block
        self.loop_interval = loop_interval
        self.events_processed = 0

        self._subscribers = set()
        # Initialize the loop for web3 event checking
        asyncio.create_task(self.initialize_check_web3_events())

    async def initialize_check_web3_events(self):
        while True:
            await self.check_web3_events()
            await asyncio.sleep(self.loop_interval)  # Delay for loop_interval seconds

    # async def process_queue(self):
    #     LOGGER.debug(f"Starting process_queue thread")
    #     while True:
    #         task = await self.task_queue.get()
    #         LOGGER.debug(f"Processing event #{task.id[:8]}")
    #         # await task
    #         # self.task_queue.task_done()
    #         # await asyncio.sleep(0.1)

    async def fetch_events(
        self, event_container: EventContainer, start_block: int, batch_size: int
    ) -> None:
        LOGGER.info(
            f"Fetching events for {event_container.name}|{event_container.address[:8]}"
        )
        async with event_container.lock:
            try:
                latest_block = event_container.w3.eth.block_number
                end_block = min(start_block + batch_size, latest_block)
                if end_block <= start_block:
                    return

                LOGGER.debug(
                    f"Fetching from block {start_block} to {end_block} for event: {event_container.name}"
                )
                events = event_container.get_logs(
                    fromBlock=start_block, toBlock=end_block
                )
                num_new_events = len(events)
                if num_new_events > 0:
                    LOGGER.info(f"Found {num_new_events} new events")
                    await self.handle_events(events=events)

                event_container.latest_scanned_block = end_block
                self.events_processed += num_new_events
            except Exception as e:
                LOGGER.error(f"Error in check_web3_events: {e}")

    async def handle_events(self, events: List[Event]) -> None:
        LOGGER.debug(f"Handling {len(events)} events")
        for event in events:
            await self.queue.put(event)
            LOGGER.debug(f"Added event #{event.id[:8]} to task queue")
            LOGGER.debug(f"Task queue size: {self.queue.qsize()}")

    async def check_web3_events(self):
        LOGGER.debug("Next round of web3 event checking.")
        try:
            for event_container in self.events:
                LOGGER.debug(
                    f"Scanning {event_container.name}|{event_container.address[:8]}"
                )
                start_block = event_container.latest_scanned_block + 1
                latest_block = event_container.w3.eth.block_number
                LOGGER.debug(f"Latest block: {latest_block}")

                while start_block <= latest_block:
                    LOGGER.debug(
                        f"Fetching events from {start_block} to {start_block + self.batch_size}"
                    )
                    await self.fetch_events(
                        event_container, start_block, self.batch_size
                    )
                    LOGGER.debug(
                        f"Finished fetching events from {start_block} to {start_block + self.batch_size}"
                    )
                    start_block += self.batch_size
                LOGGER.debug(
                    f"Finished scanning {event_container.name}|{event_container.address[:8]}"
                )

                await asyncio.sleep(0.1)
        except Exception as e:
            LOGGER.error(f"Error in check_web3_events: {e}")

    def start(self):
        """Start the EventScanner background tasks."""
        # asyncio.create_task(self.process_queue())
        asyncio.create_task(self.initialize_check_web3_events())
