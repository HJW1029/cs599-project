# API Spec: TravelMind Agent

## GET /api/health

健康检查。

### Response

```json
{
  "status": "ok",
  "service": "travelmind-agent"
}
```

## GET /api/preferences

读取默认用户偏好。

## POST /api/preferences

保存默认用户偏好。

### Request

```json
{
  "categories": ["scenic", "culture", "food"],
  "max_distance_km": 3.0,
  "pace": "balanced"
}
```

## POST /api/recommend

根据地图选点生成推荐。

### Request

```json
{
  "location": {
    "lat": 30.2741,
    "lng": 120.1551,
    "label": "杭州"
  },
  "preferences": {
    "categories": ["scenic", "culture", "food"],
    "max_distance_km": 3.0,
    "pace": "balanced"
  },
  "limit": 8
}
```

### Response

```json
{
  "center": {
    "lat": 30.2741,
    "lng": 120.1551,
    "label": "杭州"
  },
  "recommendations": [
    {
      "poi": {
        "id": "osm-node-1",
        "name": "Example",
        "category": "scenic",
        "lat": 30.27,
        "lng": 120.15,
        "distance_km": 0.8,
        "rating": 4.6,
        "source": "openstreetmap",
        "tags": {}
      },
      "score": 0.91,
      "reason": "Example 距离约 0.80km，评分估计 4.6，符合你的兴趣偏好；该地点适合拍照、散步和城市观景。",
      "suggested_duration_minutes": 60
    }
  ],
  "itinerary": [],
  "trace_id": "uuid",
  "used_fallback_data": false
}
```

## GET /api/history

读取最近 5 次推荐历史。
