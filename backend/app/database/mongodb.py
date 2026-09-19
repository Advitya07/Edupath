"""A small async repository that transparently uses Motor or demo memory."""
from collections import defaultdict
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import get_settings


class Database:
    def __init__(self) -> None:
        self.client = None
        self.db = None
        self.memory: dict[str, list[dict[str, Any]]] = defaultdict(list)

    async def connect(self) -> None:
        settings = get_settings()
        if not settings.mongodb_url:
            return
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=1200)
            await self.client.admin.command("ping")
            self.db = self.client[settings.mongodb_db]
        except Exception:
            self.client = self.db = None

    async def close(self) -> None:
        if self.client:
            self.client.close()

    async def insert(self, collection: str, item: dict) -> dict:
        if self.db is not None:
            await self.db[collection].insert_one(item)
        else:
            self.memory[collection].append(item.copy())
        return item

    async def find_one(self, collection: str, query: dict) -> dict | None:
        if self.db is not None:
            return await self.db[collection].find_one(query, {"_id": 0})
        return next((x.copy() for x in self.memory[collection] if all(x.get(k) == v for k, v in query.items())), None)

    async def find_all(self, collection: str) -> list[dict]:
        if self.db is not None:
            return await self.db[collection].find({}, {"_id": 0}).to_list(None)
        return [item.copy() for item in self.memory[collection]]

    async def upsert(self, collection: str, query: dict, item: dict) -> dict:
        if self.db is not None:
            await self.db[collection].update_one(query, {"$set": item}, upsert=True)
        else:
            current = await self.find_one(collection, query)
            if current:
                self.memory[collection].remove(next(x for x in self.memory[collection] if all(x.get(k) == v for k, v in query.items())))
            self.memory[collection].append(item.copy())
        return item


db = Database()
