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

Healthcare systems often maintain inconsistent medication lists across multiple sources. This leads to:
- Incorrect dosages
- Conflicting medication status
- Dangerous drug combinations

This system:
✔ Consolidates multiple sources  
✔ Detects inconsistencies  
✔ Enables clinical decision support  

---

## 🏗️ System Architecture

```mermaid
flowchart LR
    A[Client / Swagger UI] --> B[FastAPI Server]
    B --> C[Service Layer]
    C --> D[MongoDB]

    subgraph Backend
        B -->|Calls| C
        C -->|Stores Data| D
    end

    subgraph Database
        D --> P[Patients]
        D --> S[Snapshots]
        D --> C2[Conflicts]
    end
```
## Data Flow

```mermaid
flowchart TD
    A[POST /ingest] --> B[Normalize Data]
    B --> C[Store Snapshot]
    C --> D[Detect Conflicts]
    D --> E[Store Conflicts]

    E --> F[GET /clinic/conflicts]
    E --> G[GET /reports]

    H[POST /resolve] --> I[Update Conflict]
```

## Conflict Detection Logic

```mermaid
flowchart TD
    A[Incoming Medications] --> B[Normalize]
    B --> C[Compare with Existing Data]

    C --> D{Conflict Type}
    D -->|Dose mismatch| E[Create Conflict]
    D -->|Status conflict| E
    D -->|Class conflict| E

    E --> F[Save to DB]
```

## ⚙️ Features

## 1. Ingestion API
Stores medication snapshots
Maintains version history
Triggers conflict detection

## 2.Conflict Detection
Detects:
Dose mismatch
Status conflict
Missing medications
Drug class conflicts

## 3.Reporting APIs
/clinic/{clinic}/conflicts
/reports/last-30-days

## 4.Conflict Resolution
Stores:
Resolution reason
Timestamp
Resolved status

# Swagger UI
![Swagger UI](screenshots/swagger.png) 
## Ingest
![Ingest UI](screenshots/ingest.png)
# Conflicts
![Conflicts](screenshots/conflicts.png)
# MongoDB Collections
![MongoDB](screenshots/mongodb.png)
# Resolve
![Resolve](screenshots/resolve.png)
![Resolve](screenshots/resolved_1.png)


## ⚖️ Assumptions:
- No single source is considered ground truth
- All sources treated equally
- Conflict resolution is manual

## 🔄 Versioning Strategy:
- Each ingest creates a new snapshot
- No overwrite
- Full history maintained

## ⚖️ Trade-offs:
- Denormalization vs References
- Used separate collections for scalability

Pros:
- ✔ Flexible
- ✔ Scalable
  
Cons:
- ❌ Requires joins

## Extensibility:
- Rule-based system
- Easy to extend

## ⚠️ Known Limitations
- No real drug database
- No authentication
- Basic validation
- Aggregation not fully clinic-grouped

## 🔮 Future Improvements
- Add UI dashboard
- Integrate drug database
- Add authentication
- Improve reporting

## 🤖 AI Usage
Used for:
- Boilerplate generation
- Debugging
- Structuring APIs
