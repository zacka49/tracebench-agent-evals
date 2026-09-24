from fastapi.testclient import TestClient

from tracebench.api import create_app


def test_health_and_scripted_run(tmp_path):
    client = TestClient(create_app(tmp_path))
    assert client.get("/health").json() == {"status": "ok"}
    response = client.post(
        "/runs",
        json={
            "suite": "api-test",
            "provider": "scripted",
            "model": "control",
            "case_count": 1,
            "variants": ["controls_and_recovery"],
            "conditions": ["clean"],
            "repeats": 1,
            "limits": {"tool_calls": 12, "wall_seconds": 10},
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    assert client.get(f"/runs/{run_id}").json()["episode_count"] == 1
