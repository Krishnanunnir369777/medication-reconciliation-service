from pymongo import MongoClient
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

# -----------------------------
# LOAD ENV
# -----------------------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["medsync"]

patients_col = db["patients"]
snapshots_col = db["snapshots"]
conflicts_col = db["conflicts"]

# -----------------------------
# CLEAN OLD DATA (IMPORTANT)
# -----------------------------
patients_col.delete_many({})
snapshots_col.delete_many({})
conflicts_col.delete_many({})

print("Old data cleared...")

# -----------------------------
# CREATE PATIENTS (15 patients)
# -----------------------------
patients = []

for i in range(1, 16):
    patients.append({
        "_id": f"p{i}",
        "name": f"Patient {i}",
        "clinic": "Clinic X" if i % 2 == 0 else "Clinic Y"
    })

patients_col.insert_many(patients)

print("Patients inserted...")

# -----------------------------
# HELPER MEDICATION DATA
# -----------------------------
def med(name, dose):
    return {
        "name": name,
        "dose": dose,
        "unit": "mg",
        "frequency": "daily",
        "status": "active"
    }

# -----------------------------
# CREATE SNAPSHOTS
# -----------------------------
snapshots = []

for i in range(1, 16):
    pid = f"p{i}"

    # Source 1: clinic_emr
    snapshots.append({
        "_id": str(uuid.uuid4()),
        "patient_id": pid,
        "source": "clinic_emr",
        "medications": [
            med("ibuprofen", 200),
        ],
        "version": 1,
        "created_at": datetime.utcnow()
    })

    # Source 2: hospital_discharge (introduce conflicts for some)
    snapshots.append({
        "_id": str(uuid.uuid4()),
        "patient_id": pid,
        "source": "hospital_discharge",
        "medications": [
            med("ibuprofen", 400 if i % 2 == 0 else 200),  # dose mismatch for even patients
            med("warfarin", 5) if i % 3 == 0 else med("ibuprofen", 200)
        ],
        "version": 1,
        "created_at": datetime.utcnow()
    })

    # Source 3: patient_reported
    snapshots.append({
        "_id": str(uuid.uuid4()),
        "patient_id": pid,
        "source": "patient_reported",
        "medications": [
            med("ibuprofen", 200),
        ],
        "version": 1,
        "created_at": datetime.utcnow()
    })

snapshots_col.insert_many(snapshots)

print("Snapshots inserted...")

# -----------------------------
# NOTE
# -----------------------------
print("Seed completed successfully!")
print(" Now run your API and ingest again to generate conflicts")