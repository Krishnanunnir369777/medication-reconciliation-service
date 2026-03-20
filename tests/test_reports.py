from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_reports_endpoint():
    response = client.get("/reports/last-30-days")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_clinic_conflicts():
    response = client.get("/clinic/Clinic X/conflicts")

    assert response.status_code == 200