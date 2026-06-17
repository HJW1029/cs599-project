# TravelMind Agent 架构说明

TravelMind Agent 采用“前端地图交互 + 后端 Agent 工作流 + 外部 POI 工具 + 本地记忆”的结构。

前端使用 Leaflet 展示 OpenStreetMap 地图。用户点击地图后，前端把经纬度、搜索半径、兴趣偏好和游玩节奏发送给 FastAPI 后端。

后端的 `TravelMindAgent` 不直接把用户请求交给大模型，而是采用可测试的工具调用式工作流：

1. 读取用户历史偏好。
2. 调用 POI Search Tool 获取附近地点。
3. 使用 Geo Tool 计算距离。
4. 根据评分估计、距离和兴趣偏好排序。
5. 生成推荐理由。
6. 生成半日游路线。
7. 保存用户偏好、历史记录和 trace。

这种实现保证 Demo 在没有商业地图 API Key 和 LLM API Key 的情况下也能运行，同时仍然具备 Agentic AI 的核心结构：状态流转、工具调用、记忆、可观测和多步决策。
