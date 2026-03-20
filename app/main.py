from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import json

app = FastAPI()

# MongoDB connection
from pymongo import MongoClient

client = MongoClient("mongodb+srv://krishnanunnir503_db_user:4kwX28sdKlTgO15z@cluster0.3mxzzer.mongodb.net/")
db = client["medsync"]

patients_col = db["patients"]
snapshots_col = db["snapshots"]
conflicts_col = db["conflicts"]

# Load rules
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "conflict_rules.json")) as f:
    rules = json.load(f)

# -----------------------------
# MODELS
# -----------------------------
class Medication(BaseModel):
    name: str
    dose: float
    unit: str
    frequency: str
    status: str = "active"

class IngestRequest(BaseModel):
    patient_id: str
    source: str
    medications: list[Medication]

# -----------------------------
# HELPERS
# -----------------------------
def normalize(med):
    return {
        "name": med.name.lower().strip(),
        "dose": med.dose,
        "unit": med.unit.lower().strip(),
        "frequency": med.frequency.lower().strip(),
        "status": med.status.lower()
    }

def get_drug_class(name):
    for cls, drugs in rules["drug_classes"].items():
        if name in drugs:
            return cls
    return None

# -----------------------------
# CONFLICT DETECTION
# -----------------------------
def detect_conflicts(patient_id):
    snapshots = list(snapshots_col.find({"patient_id": patient_id}))
    if len(snapshots) < 2:
        return []

    latest_by_source = {}
    for s in snapshots:
        src = s["source"]
        if src not in latest_by_source or s["version"] > latest_by_source[src]["version"]:
            latest_by_source[src] = s

    meds_by_source = {
        src: [normalize(type("obj", (), m)) for m in snap["medications"]]
        for src, snap in latest_by_source.items()
    }

    conflicts = []
    drug_map = {}

    # Build drug map
    for source, meds in meds_by_source.items():
        for med in meds:
            drug_map.setdefault(med["name"], {})
            drug_map[med["name"]][source] = med

    sources = list(meds_by_source.keys())

    for drug, source_data in drug_map.items():
        present_sources = list(source_data.keys())

        # Dose mismatch
        if len(present_sources) > 1:
            doses = set((m["dose"], m["unit"]) for m in source_data.values())
            if len(doses) > 1:
                conflicts.append({
                    "_id": str(uuid.uuid4()),
                    "patient_id": patient_id,
                    "type": "dose_mismatch",
                    "description": f"Dose mismatch for {drug}",
                    "medications": [drug],
                    "sources": present_sources,
                    "resolved": False,
                    "created_at": datetime.utcnow()
                })

        # Missing in source
        if len(present_sources) < len(sources):
            conflicts.append({
                "_id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "type": "missing_in_source",
                "description": f"{drug} missing in some sources",
                "medications": [drug],
                "sources": sources,
                "resolved": False,
                "created_at": datetime.utcnow()
            })

        # Stopped conflict
        statuses = [m["status"] for m in source_data.values()]
        if "stopped" in statuses and "active" in statuses:
            conflicts.append({
                "_id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "type": "stopped_in_source",
                "description": f"{drug} stopped in one source, active in another",
                "medications": [drug],
                "sources": present_sources,
                "resolved": False,
                "created_at": datetime.utcnow()
            })

    # Class conflict
    for source, meds in meds_by_source.items():
        classes = [(m["name"], get_drug_class(m["name"])) for m in meds]
        classes = [c for c in classes if c[1]]

        for a, b in rules["class_conflicts"]:
            has_a = [m for m in classes if m[1] == a]
            has_b = [m for m in classes if m[1] == b]

            if has_a and has_b:
                conflicts.append({
                    "_id": str(uuid.uuid4()),
                    "patient_id": patient_id,
                    "type": "class_conflict",
                    "description": f"{a} conflicts with {b}",
                    "medications": [has_a[0][0], has_b[0][0]],
                    "sources": [source],
                    "resolved": False,
                    "created_at": datetime.utcnow()
                })

    return conflicts

# -----------------------------
# ENDPOINTS
# -----------------------------

# ✅ INGEST
@app.post("/ingest")
def ingest(data: IngestRequest):
    if not patients_col.find_one({"_id": data.patient_id}):
        raise HTTPException(404, "Patient not found")

    version = snapshots_col.count_documents({
        "patient_id": data.patient_id,
        "source": data.source
    }) + 1

    snapshot = {
        "_id": str(uuid.uuid4()),
        "patient_id": data.patient_id,
        "source": data.source,
        "medications": [m.dict() for m in data.medications],
        "created_at": datetime.utcnow(),
        "version": version
    }

    snapshots_col.insert_one(snapshot)

    new_conflicts = detect_conflicts(data.patient_id)
    if new_conflicts:
        conflicts_col.insert_many(new_conflicts)

    return {"message": "Data ingested", "conflicts_found": len(new_conflicts)}

# ✅ REPORT 1
@app.get("/clinic/{clinic}/conflicts")
def get_conflicts(clinic: str):
    patients = patients_col.find({"clinic": clinic})
    patient_ids = [p["_id"] for p in patients]

    conflicts = list(conflicts_col.find({
        "patient_id": {"$in": patient_ids},
        "resolved": False
    }))

    return conflicts

# ✅ REPORT 2
@app.get("/reports/last-30-days")
def report():
    last_30_days = datetime.utcnow() - timedelta(days=30)

    pipeline = [
        {"$match": {"created_at": {"$gte": last_30_days}}},
        {"$group": {"_id": "$patient_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 2}}}
    ]

    result = list(conflicts_col.aggregate(pipeline))
    return result

# ✅ RESOLVE CONFLICT
@app.post("/resolve/{conflict_id}")
def resolve(conflict_id: str, reason: str):
    conflicts_col.update_one(
        {"_id": conflict_id},
        {"$set": {
            "resolved": True,
            "resolution_reason": reason,
            "resolved_at": datetime.utcnow()
        }}
    )
    return {"message": "Conflict resolved"}