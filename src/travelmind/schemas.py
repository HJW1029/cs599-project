from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Category = Literal["scenic", "food", "culture", "shopping", "leisure"]


class UserPreferences(BaseModel):
    categories: list[Category] = Field(default_factory=lambda: ["scenic", "culture", "food"])
    max_distance_km: float = 3.0
    pace: Literal["relaxed", "balanced", "intensive"] = "balanced"


class Location(BaseModel):
    lat: float
    lng: float
    label: str | None = None


class RecommendationRequest(BaseModel):
    location: Location
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    limit: int = Field(default=8, ge=1, le=20)


class POI(BaseModel):
    id: str
    name: str
    category: Category
    lat: float
    lng: float
    distance_km: float
    rating: float
    source: str
    tags: dict[str, str] = Field(default_factory=dict)


class Recommendation(BaseModel):
    poi: POI
    score: float
    reason: str
    suggested_duration_minutes: int


class ItineraryStop(BaseModel):
    order: int
    name: str
    category: Category
    distance_km: float
    suggested_duration_minutes: int


class RecommendationResponse(BaseModel):
    center: Location
    recommendations: list[Recommendation]
    itinerary: list[ItineraryStop]
    trace_id: str
    used_fallback_data: bool
