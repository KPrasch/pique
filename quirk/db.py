from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorClient


class StorageInterface(ABC):
    @abstractmethod
    async def insert_event(self, event: dict):
        pass

    @abstractmethod
    async def fetch_events(self):
        pass


class MongoDBStorage(StorageInterface):
    def __init__(self, db_client: AsyncIOMotorClient):
        # Use the provided database client
        self.db_client = db_client

        # Create or access a database named 'quirk'
        self.db = self.db_client["quirk"]

        # Create or access a collection named 'events'
        self.events_collection = self.db["events"]

    async def insert_event(self, event: dict):
        # Async insert
        self.events_collection.insert_one(event)

    async def fetch_events(self):
        # Async fetch
        events = []
        async for document in self.events_collection.find():
            events.append(document)
        return events
