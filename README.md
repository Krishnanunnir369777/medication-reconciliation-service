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
