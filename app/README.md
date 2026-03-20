# 🏥 Medication Reconciliation & Conflict Reporting Service

> Backend / Data Engineering · FastAPI + MongoDB  
> Author: Krishnanunni R

---

## 📌 Overview

This project implements a backend service to reconcile medication lists from multiple healthcare sources (clinic EMR, hospital discharge, patient-reported data), detect conflicts, and provide reporting for clinicians.

The system supports:
- Ingestion of medication data from multiple sources
- Versioned storage of medication snapshots
- Conflict detection using rule-based logic
- Aggregation/reporting APIs
- Conflict resolution with audit trail

---

## 🧠 Problem Understanding

In real-world healthcare systems, medication data often comes from multiple sources and may conflict due to:
- Different dosages
- Inconsistent statuses (active vs stopped)
- Dangerous drug combinations

This system aims to:
✔ Consolidate data  
✔ Detect inconsistencies  
✔ Provide actionable insights  

---

## 🏗️ Architecture Overview

Client → FastAPI → Services (Business Logic) → MongoDB


### Components:

- **FastAPI (`main.py`)**
  - Handles API requests
  - Input validation using Pydantic
  - Calls service layer

- **Service Layer (`services.py`)**
  - Normalization logic
  - Conflict detection engine
  - Rule-based validation

- **Database (MongoDB Atlas)**
  - Stores patients, snapshots, conflicts

---

## 📂 Project Structure

app/
├── main.py # API routes
├── services.py # Business logic
├── models.py # Data models
├── db.py # MongoDB connection
├── conflict_rules.json # Rule engine

seed/
└── seed_data.py # Synthetic dataset generator

tests/
├── test_conflicts.py
├── test_validation.py
└── test_reports.py

requirements.txt
README.md


---

## 🗄️ MongoDB Schema

### 1. Patients Collection

```json
{
  "_id": "p1",
  "name": "John Doe",
  "clinic": "Clinic X"
}


2. Snapshots Collection (Versioned)
{
  "_id": "uuid",
  "patient_id": "p1",
  "source": "clinic_emr",
  "version": 1,
  "medications": [...],
  "created_at": "timestamp"
}

✔ Stores full history
✔ Enables longitudinal tracking
3. Conflicts Collection
{
  "_id": "uuid",
  "patient_id": "p1",
  "type": "dose_mismatch",
  "description": "...",
  "sources": ["clinic_emr", "hospital"],
  "resolved": false,
  "created_at": "timestamp"
}
⚡ Indexing Strategy

patients._id → fast lookup

snapshots.patient_id → query history

conflicts.patient_id + resolved → fast filtering

conflicts.created_at → time-based reports

⚙️ Core Features
✅ 1. Ingestion API
POST /ingest

✔ Stores new snapshot
✔ Automatically increments version
✔ Triggers conflict detection

✅ 2. Normalization

Lowercases medication names

Standardizes units

Avoids duplicate mismatch issues

✅ 3. Conflict Detection

Implemented in services.py

Detects:

✔ Dose mismatch
✔ Status conflict (active vs stopped)
✔ Missing in source
✔ Drug class conflicts (via rules JSON)

✅ 4. Rule Engine

Uses conflict_rules.json

Example:

{
  "drug_classes": {
    "nsaids": ["ibuprofen"],
    "anticoagulants": ["warfarin"]
  },
  "class_conflicts": [
    ["nsaids", "anticoagulants"]
  ]
}

✔ Easily extendable
✔ No external dependency

✅ 5. Reporting APIs
🔹 Conflicts by Clinic
GET /clinic/{clinic}/conflicts

✔ Returns unresolved conflicts per clinic

🔹 Aggregation Report
GET /reports/last-30-days

✔ Finds patients with ≥2 conflicts
✔ Uses MongoDB aggregation

✅ 6. Conflict Resolution
POST /resolve/{conflict_id}

Stores:

Resolution reason

Timestamp

✔ Provides auditability

🌱 Seed Data
python seed/seed_data.py

✔ Generates 15 patients
✔ Multiple sources
✔ Prepares realistic testing dataset

🧪 Testing

Run:

pytest
Includes:

✔ Conflict detection tests
✔ API validation tests
✔ Aggregation tests

🚀 Setup Instructions
git clone <repo>
cd project

pip install -r requirements.txt

# Add .env file
MONGO_URI=your_mongodb_connection

# Run seed
python seed/seed_data.py

# Start server
uvicorn app.main:app --reload

Open:

http://127.0.0.1:8000/docs
🎯 Demo Workflow

Ingest medication data

Introduce conflicting data

View conflicts

Resolve conflict

Verify resolution

⚖️ Assumptions

No single source is considered "truth"

All sources are treated equally

Conflict resolution is manual (clinician-driven)

🔄 Versioning Strategy

✔ Each ingestion creates a new snapshot
✔ No updates to old snapshots
✔ Enables full history tracking

⚖️ Trade-offs
Denormalization vs References

Used separate collections

Avoided embedding large documents

Pros:

✔ Scalable
✔ Flexible querying

Cons:

❌ Requires joins (lookup)

Document Size

Snapshots store full medication lists

May grow large over time

Extensibility

✔ Rule-based system allows easy updates
✔ Schema supports future ML integration

⚠️ Known Limitations

No real drug database integration

No authentication

Limited validation rules

Aggregation not fully grouped by clinic

🔮 Future Improvements

Integrate real drug databases

Add UI dashboard

Add authentication & roles

Improve aggregation per clinic

Add streaming ingestion

🤖 AI Usage
Used for:

Boilerplate generation

Debugging MongoDB connection

Structuring APIs

Manual Changes:

Refined conflict detection logic

Improved schema design

Added versioning strategy
