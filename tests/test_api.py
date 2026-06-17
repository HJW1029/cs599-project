from fastapi.testclient import TestClient

from travelmind.api import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_recommend_endpoint(monkeypatch) -> None:
    def fake_fetch(lat: float, lng: float, radius_m: int):
        from travelmind.tools.poi import fallback_pois

        return fallback_pois(lat, lng), True

    monkeypatch.setattr("travelmind.agent.fetch_nearby_pois", fake_fetch)
    response = client.post(
        "/api/recommend",
        json={
            "location": {"lat": 30.2741, "lng": 120.1551, "label": "杭州"},
            "preferences": {
                "categories": ["scenic", "culture", "food"],
                "max_distance_km": 3.0,
                "pace": "balanced",
            },
            "limit": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["recommendations"]) <= 3
    assert payload["trace_id"]


def test_search_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        "travelmind.api.search_places",
        lambda q, limit=6: [{"label": "杭州西湖", "lat": 30.25, "lng": 120.14, "type": "lake", "category": "natural"}],
    )
    response = client.get("/api/search?q=西湖")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "杭州西湖"
