from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from travelmind.config import settings
from travelmind.llm import LLMReasoner
from travelmind.memory import TravelMemory
from travelmind.schemas import (
    ItineraryStop,
    POI,
    Recommendation,
    RecommendationRequest,
    RecommendationResponse,
    UserPreferences,
)
from travelmind.tools.poi import fetch_nearby_pois


@dataclass
class AgentStep:
    name: str
    status: str
    detail: dict


class TravelMindAgent:
    """A small agentic workflow: perceive location, call POI tool, rank, explain, remember."""

    def __init__(
        self,
        memory: TravelMemory | None = None,
        trace_dir: Path | None = None,
        reasoner: LLMReasoner | None = None,
    ) -> None:
        self.memory = memory or TravelMemory()
        self.trace_dir = trace_dir or settings.trace_dir
        self.reasoner = reasoner or LLMReasoner()
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    def recommend(self, request: RecommendationRequest, user_id: str = "default") -> RecommendationResponse:
        trace_id = str(uuid.uuid4())
        steps: list[AgentStep] = []

        preferences = self._merge_preferences(request.preferences, user_id)
        steps.append(AgentStep("load_memory", "ok", {"preferences": preferences.model_dump()}))

        radius_m = int(preferences.max_distance_km * 1000)
        pois, used_fallback = fetch_nearby_pois(request.location.lat, request.location.lng, radius_m)
        steps.append(
            AgentStep(
                "poi_search_tool",
                "ok",
                {"count": len(pois), "radius_m": radius_m, "used_fallback_data": used_fallback},
            )
        )

        ranked = self._rank_pois(pois, preferences)[: request.limit]
        steps.append(AgentStep("rank_candidates", "ok", {"selected": [item.poi.name for item in ranked]}))

        enhanced = self._enhance_reasons(ranked, preferences, request.location.label)
        steps.append(
            AgentStep(
                "llm_reasoning",
                "ok" if enhanced else "fallback",
                {"enabled": self.reasoner.enabled, "enhanced_count": len(ranked) if enhanced else 0},
            )
        )

        itinerary = self._build_itinerary(ranked, preferences)
        steps.append(AgentStep("build_itinerary", "ok", {"stops": [stop.name for stop in itinerary]}))

        result = RecommendationResponse(
            center=request.location,
            recommendations=ranked,
            itinerary=itinerary,
            trace_id=trace_id,
            used_fallback_data=used_fallback,
        )
        self.memory.save_preferences(preferences, user_id=user_id)
        self.memory.save_history(request.location, result, user_id=user_id)
        self._write_trace(trace_id, request, result, steps)
        return result

    def _merge_preferences(self, request_preferences: UserPreferences, user_id: str) -> UserPreferences:
        return request_preferences

    def _rank_pois(self, pois: list[POI], preferences: UserPreferences) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        selected_categories = set(preferences.categories)
        for poi in pois:
            if poi.distance_km > preferences.max_distance_km:
                continue
            if selected_categories and poi.category not in selected_categories:
                continue
            distance_score = max(0.0, 1 - poi.distance_km / max(preferences.max_distance_km, 0.1))
            rating_score = (poi.rating - 3.5) / 1.5
            score = round(0.55 + 0.3 * distance_score + 0.15 * rating_score, 3)
            recommendations.append(
                Recommendation(
                    poi=poi,
                    score=score,
                    reason=self._reason_for(poi),
                    suggested_duration_minutes=self._duration_for(poi.category, preferences.pace),
                )
            )
        return sorted(recommendations, key=lambda item: item.score, reverse=True)

    def _enhance_reasons(
        self,
        recommendations: list[Recommendation],
        preferences: UserPreferences,
        center_label: str | None,
    ) -> bool:
        reasons = self.reasoner.generate_reasons(recommendations, preferences, center_label=center_label)
        if not reasons:
            return False
        for recommendation, reason in zip(recommendations, reasons):
            recommendation.reason = reason
        return True

    def _reason_for(self, poi: POI) -> str:
        category_text = {
            "scenic": "适合拍照、散步和城市观景",
            "culture": "适合了解城市历史与文化",
            "food": "适合安排餐饮休息",
            "shopping": "适合购买伴手礼或逛街",
            "leisure": "适合轻松休闲和慢节奏停留",
        }[poi.category]
        return (
            f"{poi.name} 直线距离约 {self._format_distance(poi.distance_km)}，评分估计 {poi.rating:.1f}，"
            f"符合你的兴趣偏好；该地点{category_text}。"
        )

    def _format_distance(self, distance_km: float) -> str:
        if distance_km < 1:
            return f"{round(distance_km * 1000):.0f}m"
        return f"{distance_km:.2f}km"

    def _duration_for(self, category: str, pace: str) -> int:
        base = {"scenic": 60, "culture": 75, "food": 50, "shopping": 55, "leisure": 45}.get(category, 50)
        multiplier = {"relaxed": 1.25, "balanced": 1.0, "intensive": 0.8}[pace]
        return int(round(base * multiplier / 5) * 5)

    def _build_itinerary(
        self, recommendations: list[Recommendation], preferences: UserPreferences
    ) -> list[ItineraryStop]:
        limit = {"relaxed": 3, "balanced": 4, "intensive": 5}[preferences.pace]
        selected = sorted(recommendations[:limit], key=lambda item: item.poi.distance_km)
        return [
            ItineraryStop(
                order=index,
                name=item.poi.name,
                category=item.poi.category,
                distance_km=item.poi.distance_km,
                suggested_duration_minutes=item.suggested_duration_minutes,
            )
            for index, item in enumerate(selected, start=1)
        ]

    def _write_trace(
        self,
        trace_id: str,
        request: RecommendationRequest,
        result: RecommendationResponse,
        steps: list[AgentStep],
    ) -> None:
        payload = {
            "trace_id": trace_id,
            "request": request.model_dump(),
            "steps": [step.__dict__ for step in steps],
            "result_summary": {
                "recommendation_count": len(result.recommendations),
                "itinerary_count": len(result.itinerary),
                "used_fallback_data": result.used_fallback_data,
            },
        }
        trace_path = self.trace_dir / f"{trace_id}.json"
        trace_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
