# backend/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL   = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "gas_predictor")

client = None
db     = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db     = client[DATABASE_NAME]
    await client.admin.command("ping")
    print(f"✅ Connected to MongoDB: {DATABASE_NAME}")

async def close_db():
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed")

def get_db():
    return db