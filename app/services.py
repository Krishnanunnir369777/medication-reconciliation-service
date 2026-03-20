import json
import uuid
import os
from typing import List
from datetime import datetime

from app.models import MedicationItem, Conflict, Patient, MedicationListPayload

# Load rules
RULES_PATH = os.path.join(os.path.dirname(__file__), "rules.json")

def load_rules():
    with open(RULES_PATH, "r") as f:
        return json.load(f)

rules = load_rules()


# -----------------------------
# NORMALIZATION
# -----------------------------
def normalize_medication(item: MedicationItem) -> MedicationItem:
    item.name = item.name.lower().strip()
    item.unit = item.unit.lower().strip()
    item.status = item.status.lower().strip()
    return item


# -----------------------------
# CONFLICT DETECTION
# -----------------------------
def detect_conflicts(patient: Patient, new_list: MedicationListPayload) -> List[Conflict]:
    conflicts = []

    # Existing active medications
    active_meds = {m.name: m for m in patient.current_medications}

    # Track active drug classes
    active_classes = set()
    for name in active_meds:
        if name in rules.get("drugs", {}):
            active_classes.add(rules["drugs"][name]["class"])

    # Normalize incoming meds
    new_meds = [normalize_medication(m) for m in new_list.medications]

    for new_med in new_meds:
        name = new_med.name

        # -----------------------------
        # 1. STATUS CONFLICT
        # -----------------------------
        if name in active_meds:
            active_med = active_meds[name]

            if active_med.status != new_med.status:
                conflicts.append(Conflict(
                    _id=str(uuid.uuid4()),
                    patient_id=patient.id,
                    medication_name=name,
                    conflict_type="status_conflict",
                    description=f"Status mismatch: currently {active_med.status}, reported as {new_med.status}.",
                    sources=["current_state", new_list.source],
                    resolved=False,
                    created_at=datetime.utcnow()
                ))

            # -----------------------------
            # 2. DOSE MISMATCH
            # -----------------------------
            elif active_med.status == "active" and new_med.status == "active":
                if active_med.dose != new_med.dose or active_med.unit != new_med.unit:
                    conflicts.append(Conflict(
                        _id=str(uuid.uuid4()),
                        patient_id=patient.id,
                        medication_name=name,
                        conflict_type="dose_mismatch",
                        description=f"Dose mismatch: {active_med.dose}{active_med.unit} vs {new_med.dose}{new_med.unit}.",
                        sources=["current_state", new_list.source],
                        resolved=False,
                        created_at=datetime.utcnow()
                    ))

        # -----------------------------
        # 3. CLASS CONFLICT
        # -----------------------------
        if new_med.status == "active" and name in rules.get("drugs", {}):
            med_class = rules["drugs"][name]["class"]

            for combo in rules.get("blacklisted_combinations", []):
                if med_class in combo:

                    # Find conflicting class
                    other_classes = [c for c in combo if c != med_class]

                    for other_class in other_classes:
                        if other_class in active_classes:

                            # Find drugs in that class
                            conflicting_drugs = [
                                n for n in active_meds
                                if rules["drugs"].get(n, {}).get("class") == other_class
                            ]

                            for other in conflicting_drugs:
                                conflicts.append(Conflict(
                                    _id=str(uuid.uuid4()),
                                    patient_id=patient.id,
                                    medication_name=name,
                                    conflict_type="class_conflict",
                                    description=f"Class conflict: {name} ({med_class}) conflicts with {other} ({other_class}).",
                                    sources=["current_state", new_list.source],
                                    resolved=False,
                                    created_at=datetime.utcnow()
                                ))

    return conflicts