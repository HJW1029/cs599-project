from __future__ import annotations

import hashlib
from typing import Any

import requests

from travelmind.config import settings
from travelmind.schemas import Category, POI
from travelmind.tools.geo import haversine_km


OSM_CATEGORY_RULES: list[tuple[Category, str, set[str]]] = [
    ("scenic", "tourism", {"attraction", "viewpoint", "theme_park", "zoo", "aquarium"}),
    ("culture", "tourism", {"museum", "gallery", "artwork", "information"}),
    ("culture", "historic", {"monument", "memorial", "castle", "archaeological_site", "wayside_shrine"}),
    ("food", "amenity", {"restaurant", "cafe", "fast_food", "food_court", "bar", "pub"}),
    ("shopping", "shop", {"mall", "department_store", "souvenir", "supermarket", "convenience"}),
    ("leisure", "leisure", {"park", "garden", "sports_centre", "playground", "stadium"}),
    ("leisure", "amenity", {"library", "theatre", "cinema", "arts_centre", "community_centre"}),
]

OVERPASS_FALLBACK_URLS: list[str] = []


def fetch_nearby_pois(lat: float, lng: float, radius_m: int = 3000) -> tuple[list[POI], bool]:
    """Fetch POIs from Overpass. Returns (pois, used_fallback_data)."""
    queries = _build_overpass_queries(lat, lng, radius_m)
    urls = [settings.overpass_url, *[url for url in OVERPASS_FALLBACK_URLS if url != settings.overpass_url]]
    collected: list[POI] = []
    for url in urls:
        for query_index, query in enumerate(queries):
            try:
                response = requests.post(
                    url,
                    data={"data": query},
                    timeout=settings.overpass_timeout_seconds,
                    headers={"User-Agent": "TravelMindAgent/0.1"},
                )
                response.raise_for_status()
                data = response.json()
                collected.extend(_parse_overpass_elements(data.get("elements", []), lat, lng))
            except (requests.RequestException, ValueError):
                continue
            if query_index >= 2 and len(_dedupe_pois(collected)) >= 30:
                break
        pois = _dedupe_pois(collected)
        if pois:
            return pois, False
    return [], True


def fallback_pois(lat: float, lng: float) -> list[POI]:
    seeds = [
        ("城市观景台", "scenic", 0.006, 0.002, {"tourism": "viewpoint"}),
        ("历史文化博物馆", "culture", -0.004, 0.005, {"tourism": "museum"}),
        ("本地特色餐厅", "food", 0.003, -0.006, {"amenity": "restaurant"}),
        ("城市公园", "leisure", -0.006, -0.004, {"leisure": "park"}),
        ("文创街区", "shopping", 0.008, -0.002, {"shop": "souvenir"}),
        ("艺术展览馆", "culture", -0.008, 0.002, {"tourism": "gallery"}),
    ]
    pois: list[POI] = []
    for index, (name, category, dlat, dlng, tags) in enumerate(seeds, start=1):
        poi_lat = lat + dlat
        poi_lng = lng + dlng
        distance = haversine_km(lat, lng, poi_lat, poi_lng)
        pois.append(
            POI(
                id=f"fallback-{index}",
                name=name,
                category=category,  # type: ignore[arg-type]
                lat=poi_lat,
                lng=poi_lng,
                distance_km=round(distance, 2),
                rating=_estimated_rating(name, tags),
                source="fallback",
                tags=tags,
            )
        )
    return pois


def _build_overpass_queries(lat: float, lng: float, radius_m: int) -> list[str]:
    values_by_key: dict[str, set[str]] = {}
    for _, key, values in OSM_CATEGORY_RULES:
        values_by_key.setdefault(key, set()).update(values)
    queries = []
    for key, values in values_by_key.items():
        pattern = "|".join(sorted(values))
        body = "\n".join(
            [
                f'node["name"]["{key}"~"{pattern}"](around:{radius_m},{lat},{lng});',
                f'way["name"]["{key}"~"{pattern}"](around:{radius_m},{lat},{lng});',
            ]
        )
        queries.append(f"[out:json][timeout:8];({body});out center tags 20;")
    return queries


def _dedupe_pois(pois: list[POI]) -> list[POI]:
    deduped: dict[str, POI] = {}
    for poi in pois:
        deduped.setdefault(poi.id, poi)
    return sorted(deduped.values(), key=lambda poi: poi.distance_km)


def _parse_overpass_elements(elements: list[dict[str, Any]], center_lat: float, center_lng: float) -> list[POI]:
    pois: list[POI] = []
    seen: set[str] = set()
    for element in elements:
        tags = {str(k): str(v) for k, v in element.get("tags", {}).items()}
        name = tags.get("name") or tags.get("name:zh") or tags.get("name:en")
        if not name:
            continue
        category = _category_from_tags(tags)
        if not category:
            continue
        lat = element.get("lat") or element.get("center", {}).get("lat")
        lng = element.get("lon") or element.get("center", {}).get("lon")
        if lat is None or lng is None:
            continue
        poi_id = f"osm-{element.get('type', 'node')}-{element.get('id')}"
        if poi_id in seen:
            continue
        seen.add(poi_id)
        distance = haversine_km(center_lat, center_lng, float(lat), float(lng))
        pois.append(
            POI(
                id=poi_id,
                name=name,
                category=category,
                lat=float(lat),
                lng=float(lng),
                distance_km=round(distance, 2),
                rating=_estimated_rating(name, tags),
                source="openstreetmap",
                tags=tags,
            )
        )
    return sorted(pois, key=lambda poi: poi.distance_km)


def _category_from_tags(tags: dict[str, str]) -> Category | None:
    for category, key, values in OSM_CATEGORY_RULES:
        if tags.get(key) in values:
            return category
    if "tourism" in tags or "historic" in tags:
        return "culture"
    if "amenity" in tags:
        return "food" if tags["amenity"] in {"restaurant", "cafe", "fast_food", "bar", "pub"} else "leisure"
    if "leisure" in tags:
        return "leisure"
    if "shop" in tags:
        return "shopping"
    return None


def _estimated_rating(name: str, tags: dict[str, str]) -> float:
    """OSM has no universal rating field, so create a deterministic demo rating."""
    digest = hashlib.sha1((name + repr(sorted(tags.items()))).encode("utf-8")).hexdigest()
    raw = int(digest[:4], 16) / 0xFFFF
    base = 4.0 + raw * 0.8
    if tags.get("tourism") in {"museum", "attraction"} or tags.get("historic"):
        base += 0.1
    return round(min(base, 4.9), 1)
