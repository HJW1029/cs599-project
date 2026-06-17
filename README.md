# TravelMind Agent

## 项目简介

TravelMind Agent 是一个基于地图选点的城市周边景点智能推荐系统。用户在地图上选择地点后，系统会查询附近 POI，结合距离、类型、评分估计和用户偏好生成推荐理由与短途游路线。

## 方向

方向一：Agentic AI 原生开发。

## 技术栈

- AI IDE: Trae CN / Codex
- Backend: Python, FastAPI
- Agent: tool-calling style workflow, stateful recommendation pipeline
- Map: Leaflet, OpenStreetMap
- POI Data: OpenStreetMap Overpass API with local fallback data
- Memory: SQLite
- Test: pytest, FastAPI TestClient

## 开源依赖与参考

- Leaflet: 用于地图交互，前端静态资源已放入 `src/travelmind/static/vendor/`，来源于 Leaflet 1.9.4。
- OpenStreetMap: 地图瓦片与 POI 数据来源。
- Overpass API: 用于查询 OpenStreetMap 周边 POI。
- 选题与 Agent 架构参考方向：`kbhujbal/Multi-Agent-AI-Travel-Advisor`。
- 地图 POI 查询参考方向：`gyoomei/mimoroute`。

## 目录结构

```text
cs599-project/
├── docs/                  # 报告与架构文档
├── specs/                 # Product / Architecture / API Specs
├── src/travelmind/        # 后端与前端静态资源
├── tests/                 # 单元测试与 API 测试
├── traces/                # Agent 执行轨迹输出目录
├── requirements.txt
└── README.md
```

## 环境搭建

本项目默认使用课程环境说明中的 Python 环境：

```powershell
D:\anaconda\envs\sam2\python.exe -m pip install -r requirements.txt
```

## 启动步骤

```powershell
D:\anaconda\envs\sam2\python.exe -m uvicorn travelmind.api:app --app-dir src --reload --host 127.0.0.1 --port 8000
```

浏览器访问：

```text
http://127.0.0.1:8000
```

## 环境变量

项目不会硬编码 API Key。可选配置：

```text
TRAVELMIND_LLM_API_KEY=你的大模型 API Key
TRAVELMIND_LLM_BASE_URL=https://api.deepseek.com/chat/completions
TRAVELMIND_LLM_MODEL=deepseek-chat
TRAVELMIND_LLM_TIMEOUT=15

TRAVELMIND_DB_PATH=data/travelmind.sqlite3
TRAVELMIND_TRACE_DIR=traces
TRAVELMIND_OVERPASS_URL=https://overpass-api.de/api/interpreter
```

如果你的大模型服务兼容 OpenAI Chat Completions 接口，只需要改 `TRAVELMIND_LLM_BASE_URL` 和 `TRAVELMIND_LLM_MODEL`。没有配置 Key 时，系统会自动使用本地规则生成推荐理由。

## 项目状态

- [x] Proposal
- [x] MVP
- [ ] Final report
