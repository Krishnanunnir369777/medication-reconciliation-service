from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime, timezone

class MedicationItem(BaseModel):
    name: str
    dose: float
    unit: str
    form: Optional[str] = None
    status: Literal["active", "stopped"] = "active"

class MedicationListPayload(BaseModel):
    patient_id: str
    source: Literal["clinic_emr", "hospital_discharge", "patient_reported"]
    medications: List[MedicationItem]

class MongoModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

class Patient(MongoModel):
    id: str = Field(alias="_id")
    name: str
    dob: str
    clinic_id: str
    current_medications: List[MedicationItem] = []

class MedicationSnapshot(MongoModel):
    id: str = Field(alias="_id")
    patient_id: str
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    medications: List[MedicationItem]

class ResolutionInfo(BaseModel):
    resolved_by: str
    resolution_reason: str
    chosen_source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Conflict(MongoModel):
    id: str = Field(alias="_id")
    patient_id: str
    medication_name: str
    conflict_type: Literal["dose_mismatch", "class_conflict", "status_conflict"]
    description: str
    sources: List[str]
    status: Literal["unresolved", "resolved"] = "unresolved"
    resolution: Optional[ResolutionInfo] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResolutionPayload(BaseModel):
    resolved_by: str
    resolution_reason: str
    chosen_source: str
