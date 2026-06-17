from __future__ import annotations

import requests

from travelmind.config import settings


def search_places(query: str, limit: int = 6) -> list[dict]:
    text = query.strip()
    if not text:
        return []
    response = requests.get(
        settings.nominatim_url,
        params={
            "q": text,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": limit,
            "accept-language": "zh-CN,zh,en",
        },
        headers={"User-Agent": "TravelMindAgent/0.1"},
        timeout=10,
    )
    response.raise_for_status()
    results = []
    for item in response.json():
        results.append(
            {
                "label": item.get("display_name", ""),
                "lat": float(item["lat"]),
                "lng": float(item["lon"]),
                "type": item.get("type", ""),
                "category": item.get("category", ""),
            }
        )
    return results
