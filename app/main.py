from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from datetime import datetime, timedelta
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uuid
import json

# -----------------------------
# LOAD ENV
# -----------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI not found in .env")

client = MongoClient(MONGO_URI)
db = client["medsync"]

patients_col = db["patients"]
snapshots_col = db["snapshots"]
conflicts_col = db["conflicts"]

app = FastAPI(title="Medication Reconciliation Service")

# -----------------------------
# LOAD RULES
# -----------------------------
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

class ResolveRequest(BaseModel):
    reason: str
    resolved_by: str

# -----------------------------
# HELPERS
# -----------------------------
def normalize(med):
    return {
        "name": med.name.lower().strip(),
        "dose": med.dose,
        "unit": med.unit.lower().strip(),
        "frequency": med.frequency.lower().strip(),
        "status": med.status.lower().strip()
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

    # Get latest snapshot per source
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

        # -----------------------------
        # 1. DOSE MISMATCH
        # -----------------------------
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
                    "resolution_reason": None,
                    "resolved_at": None,
                    "created_at": datetime.utcnow()
                })

        # -----------------------------
        # 2. MISSING IN SOURCE
        # -----------------------------
        if len(present_sources) < len(sources):
            conflicts.append({
                "_id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "type": "missing_in_source",
                "description": f"{drug} missing in some sources",
                "medications": [drug],
                "sources": sources,
                "resolved": False,
                "resolution_reason": None,
                "resolved_at": None,
                "created_at": datetime.utcnow()
            })

        # -----------------------------
        # 3. STOPPED VS ACTIVE
        # -----------------------------
        statuses = [m["status"] for m in source_data.values()]
        if "stopped" in statuses and "active" in statuses:
            conflicts.append({
                "_id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "type": "stopped_in_source",
                "description": f"{drug} stopped in one source but active in another",
                "medications": [drug],
                "sources": present_sources,
                "resolved": False,
                "resolution_reason": None,
                "resolved_at": None,
                "created_at": datetime.utcnow()
            })

    # -----------------------------
    # 4. CLASS CONFLICT
    # -----------------------------
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
                    "resolution_reason": None,
                    "resolved_at": None,
                    "created_at": datetime.utcnow()
                })

    return conflicts

# -----------------------------
# ENDPOINTS
# -----------------------------

# ✅ INGEST
@app.post("/ingest")
def ingest(data: IngestRequest):

    # Validate source
    if data.source not in ["clinic_emr", "hospital_discharge", "patient_reported"]:
        raise HTTPException(400, "Invalid source")

    if not patients_col.find_one({"_id": data.patient_id}):
        raise HTTPException(404, "Patient not found")

    # Proper versioning
    last = snapshots_col.find_one(
        {"patient_id": data.patient_id, "source": data.source},
        sort=[("version", -1)]
    )

    version = 1 if not last else last["version"] + 1

    snapshot = {
        "_id": str(uuid.uuid4()),
        "patient_id": data.patient_id,
        "source": data.source,
        "medications": [m.dict() for m in data.medications],
        "created_at": datetime.utcnow(),
        "version": version
    }

    snapshots_col.insert_one(snapshot)

    # Detect conflicts
    new_conflicts = detect_conflicts(data.patient_id)

    # Deduplicate conflicts
    for c in new_conflicts:
        exists = conflicts_col.find_one({
            "patient_id": c["patient_id"],
            "type": c["type"],
            "description": c["description"],
            "resolved": False
        })
        if not exists:
            conflicts_col.insert_one(c)

    return {
        "message": "Data ingested",
        "version": version,
        "conflicts_found": len(new_conflicts)
    }

# ✅ REPORT 1
@app.get("/clinic/{clinic}/conflicts")
def get_conflicts(clinic: str):

    patients = list(patients_col.find({"clinic": clinic}))
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

    return list(conflicts_col.aggregate(pipeline))

# ✅ RESOLVE CONFLICT
@app.post("/resolve/{conflict_id}")
def resolve(conflict_id: str, data: ResolveRequest):

    conflicts_col.update_one(
        {"_id": conflict_id},
        {"$set": {
            "resolved": True,
            "resolution_reason": data.reason,
            "resolved_by": data.resolved_by,
            "resolved_at": datetime.utcnow()
        }}
    )

    return {"message": "Conflict resolved"}
