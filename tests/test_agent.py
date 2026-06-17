from pathlib import Path

from travelmind.agent import TravelMindAgent
from travelmind.memory import TravelMemory
from travelmind.schemas import Location, POI, RecommendationRequest, UserPreferences
from travelmind.tools.geo import haversine_km


def test_haversine_distance_is_reasonable() -> None:
    distance = haversine_km(30.2741, 120.1551, 30.2841, 120.1551)
    assert 1.0 < distance < 1.2


def test_agent_saves_trace_for_recommendations(tmp_path: Path, monkeypatch) -> None:
    def fake_fetch(lat: float, lng: float, radius_m: int):
        from travelmind.tools.poi import fallback_pois

        return fallback_pois(lat, lng), True

    monkeypatch.setattr("travelmind.agent.fetch_nearby_pois", fake_fetch)
    memory = TravelMemory(tmp_path / "memory.sqlite3")
    agent = TravelMindAgent(memory=memory, trace_dir=tmp_path / "traces")
    request = RecommendationRequest(
        location=Location(lat=30.2741, lng=120.1551, label="杭州"),
        preferences=UserPreferences(categories=["food", "culture"], max_distance_km=3.0, pace="balanced"),
        limit=5,
    )

    response = agent.recommend(request)

    assert response.used_fallback_data is True
    assert response.recommendations
    assert response.itinerary
    assert (tmp_path / "traces" / f"{response.trace_id}.json").exists()
    assert any(item.poi.category == "food" for item in response.recommendations)


def test_food_preference_filters_non_food_results(tmp_path: Path, monkeypatch) -> None:
    def fake_fetch(lat: float, lng: float, radius_m: int):
        pois = [
            POI(
                id="food-1",
                name="湖边餐厅",
                category="food",
                lat=lat,
                lng=lng + 0.001,
                distance_km=0.2,
                rating=4.5,
                source="test",
            ),
            POI(
                id="shop-1",
                name="便利超市",
                category="shopping",
                lat=lat,
                lng=lng + 0.002,
                distance_km=0.1,
                rating=4.9,
                source="test",
            ),
            POI(
                id="culture-1",
                name="城市博物馆",
                category="culture",
                lat=lat,
                lng=lng + 0.003,
                distance_km=0.1,
                rating=4.9,
                source="test",
            ),
        ]
        return pois, False

    monkeypatch.setattr("travelmind.agent.fetch_nearby_pois", fake_fetch)
    memory = TravelMemory(tmp_path / "memory.sqlite3")
    agent = TravelMindAgent(memory=memory, trace_dir=tmp_path / "traces")
    request = RecommendationRequest(
        location=Location(lat=30.2741, lng=120.1551, label="杭州"),
        preferences=UserPreferences(categories=["food"], max_distance_km=3.0, pace="balanced"),
        limit=5,
    )

    response = agent.recommend(request)

    assert response.recommendations
    assert {item.poi.category for item in response.recommendations} == {"food"}


def test_no_real_pois_does_not_generate_fake_results(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("travelmind.agent.fetch_nearby_pois", lambda lat, lng, radius_m: ([], True))
    memory = TravelMemory(tmp_path / "memory.sqlite3")
    agent = TravelMindAgent(memory=memory, trace_dir=tmp_path / "traces")
    request = RecommendationRequest(
        location=Location(lat=30.2741, lng=120.1551, label="杭州"),
        preferences=UserPreferences(categories=["food"], max_distance_km=3.0, pace="balanced"),
        limit=5,
    )

    response = agent.recommend(request)

    assert response.used_fallback_data is True
    assert response.recommendations == []
    assert response.itinerary == []
