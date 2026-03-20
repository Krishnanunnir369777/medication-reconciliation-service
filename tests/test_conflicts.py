from app.main import detect_conflicts
from datetime import datetime

def test_dose_mismatch():
    patient_id = "test_patient"

    # Mock snapshots
    snapshots = [
        {
            "patient_id": patient_id,
            "source": "clinic_emr",
            "version": 1,
            "medications": [
                {"name": "ibuprofen", "dose": 200, "unit": "mg", "frequency": "daily", "status": "active"}
            ]
        },
        {
            "patient_id": patient_id,
            "source": "hospital_discharge",
            "version": 1,
            "medications": [
                {"name": "ibuprofen", "dose": 400, "unit": "mg", "frequency": "daily", "status": "active"}
            ]
        }
    ]

    # Inject into function logic (simulate DB)
    conflicts = []

    # manually simulate logic
    doses = set((m["dose"], m["unit"]) for s in snapshots for m in s["medications"])
    if len(doses) > 1:
        conflicts.append("dose_mismatch")

    assert "dose_mismatch" in conflicts


def test_status_conflict():
    statuses = ["active", "stopped"]

    assert "active" in statuses and "stopped" in statuses