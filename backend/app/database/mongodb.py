"""A small async repository that transparently uses Motor or local persistent fallback."""
from collections import defaultdict
import json
from pathlib import Path
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import get_settings


class Database:
    def __init__(self) -> None:
        self.client = None
        self.db = None
        self.memory: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.storage_file = Path(__file__).resolve().parent / "local_storage.json"

    async def connect(self) -> None:
        settings = get_settings()
        if settings.mongodb_url:
            try:
                self.client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=1200)
                await self.client.admin.command("ping")
                self.db = self.client[settings.mongodb_db]
                return
            except Exception:
                self.client = self.db = None
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.memory = defaultdict(list, data)
            except Exception:
                pass

    def _persist(self) -> None:
        if self.db is None:
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump(dict(self.memory), f, indent=2)
            except Exception:
                pass

    async def close(self) -> None:
        if self.client:
            self.client.close()

    async def insert(self, collection: str, item: dict) -> dict:
        if self.db is not None:
            await self.db[collection].insert_one(item)
        else:
            self.memory[collection].append(item.copy())
            self._persist()
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
            self.memory[collection] = [x for x in self.memory[collection] if not all(x.get(k) == v for k, v in query.items())]
            self.memory[collection].append(item.copy())
            self._persist()
        return item


db = Database()
