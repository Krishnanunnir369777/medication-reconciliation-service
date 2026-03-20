import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "med_recon_db")

client: AsyncIOMotorClient = None
db = None

async def init_db():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Create indexes for Patients
    await db["patients"].create_index("clinic_id")
    
    # Create indexes for Conflicts
    await db["conflicts"].create_index([("patient_id", 1), ("status", 1)])
    await db["conflicts"].create_index("status")
    
    # Create indexes for Snapshots
    await db["medication_lists"].create_index([("patient_id", 1), ("timestamp", -1)])

async def get_db():
    if db is None:
        raise RuntimeError("Database not initialized")
    yield db

async def close_db():
    global client
    if client:
        client.close()
