import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def test():
    url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    print(f"Connecting to: {url}")
    client = AsyncIOMotorClient(url)
    await client.admin.command("ping")
    print("✅ MongoDB connection works!")
    client.close()

asyncio.run(test())