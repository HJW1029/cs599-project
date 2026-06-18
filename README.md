# TravelMind Agent

## 项目简介

TravelMind Agent 是一个面向城市出行场景的地图选点式旅游推荐系统。用户在地图上选择当前位置或目标地点后，系统查询周边真实 POI 数据，并结合地点类型、直线距离、评分估计和用户偏好，生成景点、美食、文化、休闲等推荐结果及简短游览路线。

本项目重点解决旅游搜索中的三个问题：地点信息分散、推荐结果缺少解释、用户需要在地图与攻略之间反复切换。系统以 Agentic AI 工作流组织推荐过程，使“选点、检索、筛选、排序、解释、记录”形成完整闭环。

## 方向

方向一：Agentic AI 原生开发。

## 技术栈

- AI IDE：Trae CN
- 后端框架：Python、FastAPI
- Agent 设计：工具调用式推荐流程、状态化任务编排
- 地图服务：Leaflet、OpenStreetMap
- POI 数据：OpenStreetMap Overpass API
- 地理编码：Nominatim
- 记忆机制：SQLite
- 可观测性：Agent trace JSON
- 测试工具：pytest、FastAPI TestClient

## 核心功能

- 地图选点：支持点击地图、拖拽选点。
- 地名搜索：支持通过地名、城市、景点或地址定位地图。
- 当前位置定位：支持浏览器定位授权后的当前位置选点。
- 周边 POI 查询：调用 OpenStreetMap 公开数据查询附近真实地点。
- 偏好过滤：根据景点、美食、文化、购物、休闲等类别筛选推荐结果。
- 推荐排序：结合直线距离、评分估计和用户偏好计算推荐分。
- 推荐解释：为每个推荐地点给出简短推荐理由。
- 地图标注：推荐结果在地图上以编号和地点名称同步展示。
- 历史记录：保存用户偏好和推荐历史。
- 执行追踪：每次推荐生成 trace 文件，便于分析 Agent 执行过程。

## Agentic AI 设计要素

- **工具调用**：POI 查询工具、地理编码工具、距离计算工具、记忆存储工具。
- **状态管理**：推荐流程按照“读取偏好 -> 查询 POI -> 过滤排序 -> 生成理由 -> 构造路线 -> 保存记录 -> 输出 trace”执行。
- **记忆机制**：SQLite 保存用户偏好与历史推荐记录。
- **多步推理**：从用户选点和偏好出发，完成候选召回、类型过滤、距离计算、评分排序和推荐解释。
- **可观测性**：`traces/` 目录记录 Agent 每次执行的关键步骤和结果摘要。

## 目录结构

```text
cs599-project/
├── docs/                  # 项目报告提纲与架构说明
│   └── CS599_大作业报告.pdf # 最终课程报告
├── specs/                 # Product Spec / Architecture Spec / API Spec
├── src/travelmind/        # 系统源码
│   ├── api.py             # FastAPI 接口与静态页面服务
│   ├── agent.py           # 推荐 Agent 主流程
│   ├── memory.py          # SQLite 记忆模块
│   ├── llm.py             # 推荐理由生成模块
│   ├── tools/             # POI、地理编码、距离计算工具
│   └── static/            # 前端地图页面
├── tests/                 # 单元测试与接口测试
├── traces/                # Agent 执行轨迹目录
├── requirements.txt       # Python 依赖
├── pytest.ini             # 测试配置
└── README.md              # 项目入口说明
```

## 环境搭建

课程开发环境使用 `D:\anaconda\envs\sam2`：

```powershell
cd F:\AgenticAI
D:\anaconda\envs\sam2\python.exe -m pip install -r requirements.txt
```

## 启动步骤

```powershell
cd F:\AgenticAI
D:\anaconda\envs\sam2\python.exe -m uvicorn travelmind.api:app --app-dir src --reload --host 127.0.0.1 --port 8000
```

启动后访问：

```text
http://127.0.0.1:8000
```

## 配置说明

项目通过环境变量读取配置，不在代码中硬编码密钥。可参考 `.env.example` 创建本地 `.env` 文件：

```text
TRAVELMIND_LLM_API_KEY=
TRAVELMIND_LLM_BASE_URL=https://api.deepseek.com/chat/completions
TRAVELMIND_LLM_MODEL=deepseek-chat
TRAVELMIND_LLM_TIMEOUT=15

TRAVELMIND_OVERPASS_URL=https://overpass-api.de/api/interpreter
TRAVELMIND_OVERPASS_TIMEOUT=8
```

`.env`、数据库文件、缓存文件和运行生成的 trace JSON 已在 `.gitignore` 中排除。

## 测试

```powershell
cd F:\AgenticAI
D:\anaconda\envs\sam2\python.exe -m pytest -q
```

当前测试覆盖：

- 距离计算
- 推荐过滤与排序
- 无真实 POI 时不生成虚假地点
- API 健康检查
- 推荐接口
- 地名搜索接口

## 开源依赖与参考

- Leaflet 1.9.4：地图交互组件。
- OpenStreetMap：地图瓦片与开放地理数据。
- Overpass API：周边 POI 查询。
- Nominatim：地名搜索与地理编码。
- 参考项目：
  - `kbhujbal/Multi-Agent-AI-Travel-Advisor`
  - `gyoomei/mimoroute`

## 项目状态

- [x] Proposal
- [x] MVP
- [x] Specs
- [x] Test
- [x] Final report
