from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_invalid_source():
    response = client.post("/ingest", json={
        "patient_id": "p1",
        "source": "invalid_source",
        "medications": []
    })

    assert response.status_code == 400


def test_missing_patient():
    response = client.post("/ingest", json={
        "patient_id": "unknown",
        "source": "clinic_emr",
        "medications": []
    })

    assert response.status_code == 404