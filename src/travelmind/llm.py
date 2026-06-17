from __future__ import annotations

import json

import requests

from travelmind.config import settings
from travelmind.schemas import Recommendation, UserPreferences


class LLMReasoner:
    """OpenAI-compatible client for improving recommendation reasons."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self.base_url = base_url or settings.llm_base_url
        self.model = model or settings.llm_model
        self.timeout_seconds = timeout_seconds or settings.llm_timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate_reasons(
        self,
        recommendations: list[Recommendation],
        preferences: UserPreferences,
        center_label: str | None = None,
    ) -> list[str] | None:
        if not self.enabled or not recommendations:
            return None

        compact_items = [
            {
                "name": item.poi.name,
                "category": item.poi.category,
                "distance_km": item.poi.distance_km,
                "rating": item.poi.rating,
                "score": item.score,
                "fallback_reason": item.reason,
            }
            for item in recommendations
        ]
        prompt = (
            "你是旅游推荐智能体。请根据用户兴趣、直线距离、评分和地点类型，为每个地点生成一句中文推荐理由。"
            "要求：每条 35-70 字，必须明确写“直线距离”或评分信息，语气自然，不要编造门票、营业时间、步行距离、驾车距离或不存在的事实。"
            "只返回 JSON 数组，数组长度必须和输入地点数量一致，每个元素是字符串。"
        )
        user_payload = {
            "center_label": center_label or "地图选点",
            "preferences": preferences.model_dump(),
            "items": compact_items,
        }
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                    ],
                    "temperature": 0.4,
                    "max_tokens": 800,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = _parse_json_array(content)
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
            return None

        if len(parsed) != len(recommendations) or not all(isinstance(item, str) for item in parsed):
            return None
        return [item.strip() for item in parsed if item.strip()]


def _parse_json_array(content: str) -> list[str]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return json.loads(text)
