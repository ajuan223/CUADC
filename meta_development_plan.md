# 🛩️ Striker 项目开发顺序元规划 (Meta Development Plan)

> **创建日期**: 2026-04-12 · **基于**: init愿景.md v2.2
> **目的**: 为 AI Agent 实现提供有序的开发路线图，避免熵增和灾难性依赖冲突
>
> **v2.2 变更**: 新增场地配置 (Field Profile) 贯穿 Phase 0/1/2/5/8，
> SCAN 扫场状态 + 单程投弹流（扫场完成→投弹点决策→投放），
> 移除 RETURN 状态，新增 field-profile-rules Skill。
>
> **v3.0 变更**: 简化任务主链，删除 LOITER/FORCED_STRIKE/APPROACH 状态和弹道解算主流程。
> 视觉系统输入语义从"靶标"变为"投弹点"。新增兜底中点计算。

---

## 核心原则

1. **依赖链严格排序** — 下游不能依赖未实现的上游
2. **每个 Phase 可独立验证** — 完成即可测试，不留"半成品"
3. **基础设施先于业务逻辑** — 工具链、规范、骨架优先
4. **接口先于实现** — Protocol/ABC 先定义，具体实现后补
5. **模拟环境先于真机** — SITL 验证贯穿始终

---

## 总览：依赖关系图

```
Phase 0: 项目脚手架 + 工具链
    │
    ├──▶ Phase 1: AI 治理体系 (AGENTS.md + Skills + CHARTER.md)
    │
    ├──▶ Phase 2: 配置系统 + 场地配置 + 异常层次 + 日志框架
    │        │
    │        ├──▶ Phase 3: 通信层 (MAVLink Adapter)
    │        │        │
    │        │        ├──▶ Phase 4: 状态机引擎 + 安全监控
    │        │        │        │
    │        │        │        ├──▶ Phase 5: 飞行指令层 + 扫场+降落序列 + 业务状态
    │        │        │        │        │
    │        │        │        │        ├──▶ Phase 6: 外部解算链路 + 投弹点跟踪 + 兜底中点
    │        │        │        │        │        │
    │        │        │        │        │        └──▶ Phase 7: 投弹系统 (释放机构)
    │        │        │        │        │
    │        │        │        │        └──▶ Phase 8: 全任务集成 + CI/CD
    │        │        │        │
    │        │        │        └──▶ Phase 4b: 遥测日志 + GCS 上报
    │        │        │
    │        │        └──▶ Phase 3b: SITL 环境搭建 (并行)
    │        │
    │        └─── (所有 Phase 共享)
    │
    └──▶ Phase 1b: Capability Registry 骨架 (并行)
```

---

## Phase 0: 项目脚手架 + 工具链

### 目标
从零建立一个可构建、可测试、可 lint 的空项目骨架。

### 前置条件
- 无 (这是起点)

### 产出物

| 文件/目录 | 说明 |
|-----------|------|
| `pyproject.toml` | uv 项目配置，含 ruff/mypy/pytest 配置，workspace 定义 |
| `uv.lock` | 锁定依赖 |
| `.python-version` | `3.13` |
| `src/striker/__init__.py` | 版本号 `__version__` |
| `src/striker/__main__.py` | `python -m striker` 入口 (空壳) |
| `src/striker/py.typed` | PEP 561 类型标记 |
| `src/striker/exceptions.py` | 完整异常层次 (StrikerError → 子类) |
| `tests/conftest.py` | pytest fixtures 骨架 |
| `tests/__init__.py` | |
| `config.example.json` | 配置模板 |
| `.env.example` | 环境变量模板 |
| `.gitignore` | Python + uv + runtime_data/ + config.json |
| `README.md` | 项目说明 |
| `pkg/` 目录 | uv workspace 空骨架 (含 README.md + 占位 pyproject.toml) |
| `data/fields/sitl_default/field.json` | SITL 默认场地配置 (v2.2 新增) |
| `data/fields/README.md` | 如何创建新场地配置 (v2.2 新增) |
| `runtime_data/` 目录 | 运行时数据 (gitignored)，含 .gitkeep |
| `scripts/` 目录 | 空骨架 |
| `docs/` 目录 | 空骨架 |

### 关键决策与技术验证

> [!NOTE]
> **Python 3.13 — 经过验证的稳定选择**
> 
> 选择 3.13 而非 3.14 的原因：
> - pymavlink 的 `fastcrc` 依赖在 Python 3.14 上存在预编译 wheel 问题 ([GitHub Issue #1138](https://github.com/ardupilot/pymavlink/issues/1138))
> - 3.13 是当前最新稳定版本，pymavlink 完全兼容，无 wheel 问题
> - 3.13 已包含 TaskGroup、改进错误消息等对项目有用的特性
> - 未来 3.14 生态成熟后可平滑升级

### 具体步骤

```bash
# 1. 初始化项目 (src layout)
uv init --package ./
uv python pin 3.13

# 2. 安装核心依赖
uv add pymavlink pydantic-settings structlog

# 3. 安装开发工具
uv add --dev ruff mypy pytest pytest-asyncio

# 4. 配置 uv workspace (pkg/ 冻结包区域)
# 在根 pyproject.toml 中添加:
# [tool.uv.workspace]
# members = ["pkg/*"]
#
# pkg/ 目录结构 (初始为空占位):
# pkg/
# ├── README.md              ← 说明此目录用途和使用规则
# └── .gitkeep               ← 保证空目录被 git 跟踪
#
# 当未来实际添加 vendor 包时，每个包结构:
# pkg/{name}/
# ├── pyproject.toml         ← [project] name + version
# └── src/{name}/__init__.py

# 5. 验证工具链
uv run ruff check .
uv run mypy src/
uv run pytest
```

### 验证标准
- [x] `uv sync` 成功
- [x] `uv run python -m striker` 可执行 (打印版本号即可)
- [x] `uv run ruff check .` 通过
- [x] `uv run mypy src/ --strict` 通过
- [x] `uv run pytest` 通过 (0 tests collected OK)
- [x] pymavlink 在目标平台上可 import

### 建议 OpenSpec Change
`scaffold-phase0-foundation`

---

## Phase 1: AI 治理体系

### 目标
建立**三层渐进式治理架构 (Progressive Disclosure)**，防止 AI 代理由于指令预算溢出导致的行为降智，让后续所有的实现都有刚性约束与规范可循。

> [!IMPORTANT]
> **注入强制性 AI 编码与变更约束 (摘录自项目宪章)**
> 1. **严禁盲目落码规则**: AI 凡是新增或修改模块前，必须先调用文件搜索能力进行代码与架构调研，严禁拍脑袋直接修改代码。
> 2. **能力发现优先 (Do Not Reinvent the Wheel)**: 在动手实现通用函数前，必须强制检索并复用 `capability-registry/REGISTRY.md` 中的清单。
> 3. **分层指令预算约束**: 顶层 `AGENTS.md`（项目宪法）严格控制在 <100 行内；所有模块级的具体规范必须收敛到 `.agent/skills/{module}-rules/SKILL.md` 中，使得 AI 仅在触及相关业务目录时按需触发对应的规范 (Module Skills)。
> 4. **包治理与防腐墙**: `pkg/` 工具包的变更必须伴随版本号更迭及 `REGISTRY.md` 同步，严防 `src` 与 `pkg` 之间乃至 `pkg` 与 `pkg` 之间的双向循环依赖。

### 前置条件
- Phase 0 完成 (目录结构已存在)

### 产出物

| 文件 | 说明 |
|------|------|
| `CHARTER.md` | 项目宪章：OKR + Red Lines |
| `AGENTS.md` | AI 宪法级规范 (<100 行)：命名、类型、日志、Import 顺序、Skill 路由表 |
| `AGENTS.local.md` | 个人覆盖模板 (gitignored) |
| `.agent/skills/core-fsm-rules/SKILL.md` | 状态机编码规范 |
| `.agent/skills/comms-mavlink-rules/SKILL.md` | 通信层编码规范 |
| `.agent/skills/flight-control-rules/SKILL.md` | 飞行指令规范 |
| `.agent/skills/payload-release-rules/SKILL.md` | 载荷投弹规范 |
| `.agent/skills/vision-interface-rules/SKILL.md` | 视觉接口规范 |
| `.agent/skills/safety-monitor-rules/SKILL.md` | 安全监控规范 |
| `.agent/skills/config-system-rules/SKILL.md` | 配置系统规范 |
| `.agent/skills/field-profile-rules/SKILL.md` | 场地配置规范 (v2.2 新增) |
| `.agent/skills/testing-rules/SKILL.md` | 测试规范 |
| `.agent/skills/capability-registry/SKILL.md` | 能力注册规范 |
| `.agent/skills/capability-registry/REGISTRY.md` | 能力清单 (初始为空表) |

### 分组策略

**1a. 宪法级 (必须先完成)**
- CHARTER.md
- AGENTS.md
- AGENTS.local.md

**1b. 模块 Skills (可并行编写)**
- 9 个模块 Skill 可同时创建，它们之间无依赖 (含 v2.2 新增的 field-profile-rules)

### 验证标准
- AGENTS.md < 100 行有效指令
- 每个 SKILL.md 含：Architecture Constraints, Registration Pattern, Forbidden Patterns
- Skill 路由表覆盖所有 `src/striker/*/` 目录

### 建议 OpenSpec Change
`governance-tier1-charter` + `governance-tier2-skills`

---

## Phase 2: 配置系统 + 场地配置 + 日志框架

### 目标
实现三层配置优先级 + 场地配置加载与校验 (Field Profile) + structlog 结构化日志 + 平台检测。
这是所有业务模块的共享基础设施。

### 前置条件
- Phase 0 完成 (依赖已安装)
- Phase 1 的 `config-system-rules` SKILL 已创建

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/config/__init__.py` | |
| `src/striker/config/settings.py` | `StrikerSettings(BaseSettings)` — 三层配置 |
| `src/striker/config/field_profile.py` | `FieldProfile(BaseModel)` — 场地配置数据模型+校验 (v2.2 新增) |
| `src/striker/config/platform.py` | `detect_platform()` → RPi5 / Orin / SITL / Unknown |
| `src/striker/config/validators.py` | 配置校验器 (物理量合理范围) |
| `src/striker/telemetry/__init__.py` | |
| `src/striker/telemetry/logger.py` | structlog 全局配置 |
| `src/striker/exceptions.py` | 完整异常层次 (Phase 0 已创建，这里充实) |
| `tests/unit/test_config.py` | 配置三层优先级测试 |
| `tests/unit/test_field_profile.py` | 场地配置加载+校验测试 (v2.2 新增) |
| `tests/unit/test_platform.py` | 平台检测测试 |
| `config.example.json` | 完整配置模板 (Phase 0 已创建，这里充实，含 field 字段) |

### 关键设计要点

> **(MCP 检索自 context7) pydantic-settings 三层优先级实现**
> `pydantic-settings` 天然满足 `init defaults → json_file → env_vars` 的三层设计。此处我们通过 `settings_customise_sources` 显式保证加载顺序。

```python
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, JsonConfigSettingsSource

class StrikerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STRIKER_",
        json_file="config.json",
        json_file_encoding="utf-8",
    )
    
    # 所有字段都有代码内默认值 (Layer 1)
    serial_port: str = "/dev/serial0"
    serial_baud: int = 921600
    loiter_radius_m: float = 80.0
    loiter_timeout_s: float = 60.0          # (v2.2) 盘旋等待超时秒数
    max_scan_cycles: int = 3                # (v2.2) 最大 SCAN→LOITER 循环次数
    forced_strike_enabled: bool = True      # (v2.2) 是否启用强制投弹降级
    field: str = "sitl_default"             # (v2.2) 场地配置名称
    # ... 

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # 严格定义三层优先级顺序: init(default) < Json < env
        return (
            init_settings,
            env_settings,
            JsonConfigSettingsSource(settings_cls),
            file_secret_settings,
        )
```

> [!NOTE]
> **structlog 实战最佳实践 (MCP 检索自 context7)**
> 
> ```python
> import sys
> import structlog
> 
> # 基础配置: 包含异步上下文变量与规范时间戳
> shared_processors = [
>     structlog.contextvars.merge_contextvars, # 支持异步/线程级上下文 (如 task_id, mission_id)
>     structlog.processors.add_log_level,
>     structlog.processors.TimeStamper(fmt="iso", utc=True),
>     structlog.processors.format_exc_info,
>     structlog.processors.dict_tracebacks,
> ]
> 
> # 智能环境识别：开发环境 TTY 使用友好输出，生产环境/SITL 使用 JSON
> if sys.stderr.isatty():
>     processors = shared_processors + [structlog.dev.ConsoleRenderer()]
> else:
>     processors = shared_processors + [structlog.processors.JSONRenderer()]
> 
> structlog.configure(
>     processors=processors,
>     wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
>     cache_logger_on_first_use=True,
> )
> ```

### 验证标准
- 三层优先级：default 被 json 覆盖，json 被 env 覆盖
- `STRIKER_DRY_RUN=true` 环境变量生效
- `STRIKER_FIELD=zijingang` 选择场地配置生效 (v2.2)
- `detect_platform()` 在 SITL 环境下返回 `Platform.SITL`
- structlog 输出 JSON 格式日志
- FieldProfile 加载: 有效 field.json → 加载成功; 缺少字段 → ValidationError (v2.2)
- FieldProfile 校验: 航点在围栏外 → 拒绝加载; 跑道不在围栏内 → 拒绝 (v2.2)

### 建议 OpenSpec Change
`infra-config-logging`

---

## Phase 3: MAVLink 通信层

### 目标
实现与飞控的 MAVLink 通信（连接、心跳、消息收发），这是所有飞行控制的物理基础。

### 前置条件
- Phase 2 完成 (配置系统提供连接参数、日志框架提供 structlog)

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/comms/__init__.py` | |
| `src/striker/comms/connection.py` | `MAVLinkConnection` — 连接管理 (串口/UDP) |
| `src/striker/comms/heartbeat.py` | 心跳发送/接收 + 连接健康监控 |
| `src/striker/comms/messages.py` | 消息类型常量 + 收发封装 |
| `src/striker/comms/telemetry.py` | 遥测数据解析/缓存 (GLOBAL_POSITION_INT, VFR_HUD, WIND, ATTITUDE) |
| `tests/unit/test_connection.py` | 连接逻辑单元测试 (mock) |

### 关键设计要点

```
                    ┌──────────────────────────────┐
                    │      MAVLinkConnection       │
                    │                              │
                    │  connect(transport_url)       │
                    │  send(msg)                    │
                    │  recv_match(type, blocking)   │
                    │  wait_heartbeat()             │
                    │  is_connected: bool           │
                    │                              │
                    │  内部:                        │
                    │  • pymavlink.mavutil 封装     │
                    │  • 心跳定时器                 │
                    │  • 连接状态机                 │
                    │  • asyncio 兼容 (run_in_exec) │
                    └──────────────────────────────┘
```

> [!WARNING]
> **pymavlink 的阻塞 API 与 asyncio 的最佳集成模式**
> 
> pymavlink 源自同步上下文，**禁止**在协程中直接使用 `blocking=True`。
> 推荐的架构范式：使用独立的异步专职接收协程 (Producer) + `asyncio.Queue` 进行消息分发：

```python
import asyncio
from pymavlink import mavutil

class MAVLinkConnection:
    def __init__(self, port, baud):
        self.mav = mavutil.mavlink_connection(port, baud=baud)
        self.msg_queue = asyncio.Queue()

    async def _rx_loop(self):
        """专职无阻塞接收协程 (Producer)"""
        while True:
            # 关键点：blocking=False 避免锁死事件循环
            msg = self.mav.recv_match(blocking=False)
            if msg:
                await self.msg_queue.put(msg)
            else:
                # 无数据时必须让权，0.001~0.005s 是吞吐量和 CPU 占用的甜点
                await asyncio.sleep(0.005)
```

```

> [!TIP]
> **可靠的心跳健康监控模式 (Heartbeat Watchdog)**
> 
> 在通信层，不能仅依靠底层的 socket 存活来判断飞控连接。必须基于 MAVLink 协议层的 `HEARTBEAT` 报文实现软看门狗：
> ```python
> async def wait_heartbeat_with_watchdog(self, timeout_s=3.0):
>     """心跳看门狗：使用 asyncio.wait_for 包装特定事件等待"""
>     try:
>         # 假设我们在 parse 循环中收到 HEARTBEAT 就 trigger 此 event
>         await asyncio.wait_for(self.heartbeat_event.wait(), timeout=timeout_s)
>         self.heartbeat_event.clear()
>         self.is_connected = True
>     except asyncio.TimeoutError:
>         self.is_connected = False
>         log.warning("Heartbeat timeout, connection lost!", timeout=timeout_s)
>         # 触发重连或进入 EMERGENCY 状态
> ```

> [!NOTE]
> **遥测数据解析与状态隔离 (Mavlink Dict → Dataclass/Pydantic)**
> 
> pymavlink 解析出的报文是弱类型且常含有原始比例因子（如 `lat=1e7`）。应该在 `comms/telemetry.py` 内立刻转换为强类型的 `dataclass`，使上层业务逻辑**彻底断开与 pymavlink 报文结构的直接耦合**：
> ```python
> from dataclasses import dataclass
> 
> @dataclass
> class GeoPosition:
>     lat: float
>     lon: float
>     alt_m: float
> 
> # 在 rx_loop 的路由分支中：
> if msg.get_type() == 'GLOBAL_POSITION_INT':
>     current_pos = GeoPosition(
>         lat=msg.lat / 1e7,         # 内部完成工程单位转换
>         lon=msg.lon / 1e7,
>         alt_m=msg.alt / 1000.0
>     )
>     context.update_position(current_pos) # 向上层发布标准对象
> ```

### 并行: Phase 3b — SITL 环境搭建

此 Phase 可以与 Phase 3 同时进行：

| 文件 | 说明 |
|------|------|
| `scripts/run_sitl.sh` | 一键启动 ArduPlane SITL + MAVProxy |
| `scripts/setup_sitl.sh` | ArduPilot SITL 安装脚本 |
| `docs/sitl_setup.md` | SITL 搭建文档 |
| `tests/integration/conftest.py` | SITL fixture (自动启动/关闭) |
| `tests/integration/test_sitl_connection.py` | SITL 连通性测试 |

SITL 命令:
```bash
sim_vehicle.py -v ArduPlane --out udp:127.0.0.1:14550
```

### 验证标准
- 连接 SITL，收到 HEARTBEAT
- 遥测解析：GLOBAL_POSITION_INT → lat/lon/alt 值合理
- 心跳超时检测：断开 SITL → 5s 内检测到连接丢失
- 所有 pymavlink 调用封装在 comms/ 内，外部模块不直接 import pymavlink

### 建议 OpenSpec Change
`comms-mavlink-adapter` + `infra-sitl-environment`

---

## Phase 4: 状态机引擎 + 安全监控

### 目标
实现通用 FSM 引擎 + 全局安全监控器。这是任务编排的骨架。

### 前置条件
- Phase 3 完成 (安全监控需要读取遥测数据)
- Phase 2 完成 (配置、日志)

### 产出物

#### 4a. FSM 引擎

| 文件 | 说明 |
|------|------|
| `src/striker/core/__init__.py` | |
| `src/striker/core/machine.py` | `MissionStateMachine` — 泛化 FSM 引擎 |
| `src/striker/core/context.py` | `MissionContext` — 共享状态容器 |
| `src/striker/core/events.py` | 事件枚举 + 数据类 |
| `src/striker/core/states/__init__.py` | 状态注册表 |
| `src/striker/core/states/base.py` | `BaseState` ABC (on_enter/execute/on_exit) |
| `src/striker/core/states/init.py` | InitState (系统初始化) |
| `src/striker/core/states/override.py` | OverrideState (人工接管终态) |
| `src/striker/core/states/emergency.py` | EmergencyState (紧急降落) |
| `tests/unit/test_state_machine.py` | FSM 状态转换测试 |

> [!IMPORTANT]
> **Phase 4 只实现 FSM 引擎框架 + 3 个基础状态 (INIT, OVERRIDE, EMERGENCY)**
> 
> 业务状态 (PREFLIGHT → TAKEOFF → SCAN → LOITER → ...) 在后续 Phase 5-7 中逐步添加。
> 这样可以验证引擎本身的正确性，而不被业务逻辑干扰。

#### 4b. 安全监控

| 文件 | 说明 |
|------|------|
| `src/striker/safety/__init__.py` | |
| `src/striker/safety/monitor.py` | `SafetyMonitor` — 主循环协程 |
| `src/striker/safety/checks.py` | 各项检查：电池、GPS、心跳、空速、地理围栏 |
| `src/striker/safety/geofence.py` | 地理围栏实现 |
| `src/striker/safety/override_detector.py` | Override 模式检测 |
| `tests/unit/test_safety.py` | 安全检查测试 |

#### 4c. 遥测日志

| 文件 | 说明 |
|------|------|
| `src/striker/telemetry/flight_recorder.py` | 飞行数据 CSV 记录 |
| `src/striker/telemetry/reporter.py` | GCS 状态上报 (预留接口) |
| `tests/unit/test_telemetry.py` | 遥测记录测试 |

### FSM 引擎设计

```
  ┌───────────────────────────────────────────────┐
  │          MissionStateMachine                  │
  │                                               │
  │  states: dict[str, BaseState]   ← 注册表     │
  │  current: BaseState                           │
  │  context: MissionContext        ← 共享状态    │
  │                                               │
  │  async process_event(event: Event) → None     │
  │    1. 询问 current_state.handle(event)        │
  │    2. 如果返回 Transition → 执行转换          │
  │    3. old.on_exit() → new.on_enter()          │
  │    4. 记录转换日志                             │
  │                                               │
  │  全局拦截:                                     │
  │    OverrideEvent → 任意状态 → OVERRIDE        │
  │    EmergencyEvent → 任意状态 → EMERGENCY      │
  └───────────────────────────────────────────────┘
```

> [!NOTE]
> **FSM 引擎最佳实践: 拥抱 `python-statemachine` (MCP 检索自 context7)**
>
> 鉴于 Python 内置不提供健壮状态机，手写 FSM 容易引发竞态和回调地狱，建议引入标准的 `python-statemachine` 库并应用其异步支持：
> ```python
> from statemachine import StateMachine, State
> 
> class MissionStateMachine(StateMachine):
>     # 1. 状态注册
>     init = State('Init', initial=True)
>     preflight = State('Preflight')
>     override = State('Override', final=True)
>     
>     # 2. 转换边界 (Transitions)
>     start = init.to(preflight)
>     takeover = init.to(override) | preflight.to(override)
>     
>     def __init__(self, context_obj):
>         self.ctx = context_obj  # 上下文隔离，不污染状态机类
>         super().__init__(rtc=False) # *关键*: 异步需禁用 run-to-completion()
> 
>     # 3. 异步生命周期回调
>     async def on_enter_preflight(self):
>         await self.ctx.upload_mission_items()
>         
>     async def on_takeover(self):
>         self.ctx.log.warning("Human override triggered!")
> ```
> **重要注意**：针对异步应用，事件循环中必须显式调用 `await sm.activate_initial_state()`，否则系统无法安全捕获初始状态事件。

### 验证标准
- FSM: INIT → (event) → INIT (无转换); INIT → OverrideEvent → OVERRIDE
- SafetyMonitor: 模拟电池低 → 触发 EmergencyEvent
- Override 检测: 模拟飞控模式切换 → 触发 OverrideEvent
- CSV 飞行记录器: 写入/读回数据一致

### 建议 OpenSpec Change
`core-fsm-engine` + `safety-monitor` + `telemetry-recorder`

---

## Phase 5: 飞行指令层 + 扫场+降落序列 + 业务状态

### 目标
实现高级飞行指令 (arm/takeoff/goto/set_mode)、MAVLink Mission Upload Protocol（扫场航点+降落序列上传），
并填充全部业务状态 (PREFLIGHT → TAKEOFF → **SCAN** → LOITER → ENROUTE → APPROACH → RELEASE → **LANDING** → COMPLETED)。

> **v2.2 变更**: 新增 SCAN 扫场状态，移除 RETURN 状态（固定场地无需独立返航），
> 降落参数从 field profile 读取，新增扫场航点通过 Mission Protocol 上传到飞控。

### 前置条件
- Phase 4 完成 (FSM 引擎、安全监控)
- Phase 3 完成 (MAVLink 通信层)
- Phase 2 完成 (FieldProfile 场地配置已可加载)

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/flight/__init__.py` | |
| `src/striker/flight/controller.py` | `FlightController` — arm/takeoff/goto/set_mode/set_speed/upload_mission |
| `src/striker/flight/modes.py` | ArduPlane 模式枚举 (MANUAL, FBWA, AUTO, GUIDED, LOITER, RTL...) |
| `src/striker/flight/navigation.py` | 航线/航点管理 + MAVLink Mission Upload Protocol 封装 (v2.2) |
| `src/striker/flight/landing_sequence.py` | 降落序列生成 + 上传到飞控 (参数从 field profile 读取) |
| `src/striker/core/states/preflight.py` | PreflightState (含围栏上传+降落序列上传+scan计数器归零) |
| `src/striker/core/states/takeoff.py` | TakeoffState |
| `src/striker/core/states/scan.py` | **ScanState (v2.2 新增)** — AUTO模式执行扫场航点序列 |
| `src/striker/core/states/loiter.py` | LoiterState (含超时计时+重扫判断) |
| `src/striker/core/states/enroute.py` | EnrouteState |
| `src/striker/core/states/landing.py` | LandingState |
| `src/striker/core/states/completed.py` | CompletedState |
| `tests/unit/test_flight_controller.py` | |
| `tests/integration/test_sitl_takeoff.py` | SITL 起飞测试 |
| `tests/integration/test_sitl_scan_loiter.py` | **SITL 扫场+盘旋循环测试 (v2.2 新增)** |

### 关键设计要点

```
  ┌───────────────────────────────────────────────────────┐
  │  固定翼降落序列 (必须在起飞前上传到飞控!)              │
  │  参数来源: field profile 的 landing 节                │
  │                                                       │
  │  Mission Item 序列:                                   │
  │  [n]   DO_LAND_START  → 标记降落序列开始              │
  │  [n+1] NAV_WAYPOINT   → 进近航点 (跑道延长线上)       │
  │  [n+2] NAV_LAND       → 着陆点 + 下滑道参数           │
  │                                                       │
  │  或 ArduPlane 4.5+:                                   │
  │  AUTOLAND 模式 (简化, 但需验证 CUAV X7 固件版本)      │
  └───────────────────────────────────────────────────────┘

> [!NOTE]
> **可靠的航点编排与上传 (MAVLink Mission Micro-Protocol)**
> 
> 在 MAVLink 协议中，千万不要盲目循环发送 `MISSION_ITEM`。它要求建立一个严丝合缝的对话级状态机 (Micro-Protocol)。在 `FlightController` 中结合之前建立的 `wait_for_message`，最佳实践代码范式如下：
> 
> ```python
> async def upload_mission_items(self, items: list[mavutil.mavlink.MAVLink_mission_item_int_message]):
>     # 1. 握手阶段：清空并宣告总数
>     self.mav.mav.mission_clear_all_send(self.mav.target_system, self.mav.target_component)
>     await self.wait_for_message('MISSION_ACK')
>     
>     self.mav.mav.mission_count_send(self.mav.target_system, self.mav.target_component, len(items))
>     
>     # 2. 逐条响应飞控的请求 (飞控具有主动权)
>     for _ in range(len(items)):
>         req = await self.wait_for_message('MISSION_REQUEST_INT', timeout=2.0)
>         if not req:
>             raise MissionUploadError("Timeout waiting for mission request.")
>         
>         # 必须按飞控索要的 index (req.seq) 发送航点，而非盲目发下一个！
>         item = items[req.seq]
>         self.mav.mav.send(item)
>         
>     # 3. 终盘确认阶段
>     ack = await self.wait_for_message('MISSION_ACK', timeout=2.0)
>     if ack and ack.type != mavutil.mavlink.MAV_MISSION_ACCEPTED:
>         raise MissionUploadError(f"Mission upload rejected. Code: {ack.type}")
> ```

  ┌───────────────────────────────────────────────────────┐
  │  SCAN↔LOITER 循环 (v2.2 核心逻辑)                     │
  │                                                       │
  │  mission_current_seq 计数器 (PREFLIGHT 中归零)            │
  │  每次进入 SCAN → mission_current_seq++                   │
  │  SCAN 完成 → LOITER (等待外部解算坐标)                │
  │  LOITER 超时 (loiter_timeout_s):                      │
  │    cycle < max_scan_cycles → 回到 SCAN               │
  │    cycle >= max → 进入 FORCED_STRIKE (Phase 7)       │
  │  LOITER 收到有效坐标 → ENROUTE                       │
  └───────────────────────────────────────────────────────┘
```

### 验证标准
- SITL: ARM → AUTO (NAV_TAKEOFF) → 爬升到指定高度 → 进入 SCAN
- SITL: SCAN 模式下按照 field profile 航点序列飞行
- SITL: SCAN 完成 → 自动切换 LOITER 盘旋
- SITL: GUIDED goto → 飞到目标点
- 降落序列: Mission items 正确上传到飞控 (参数来自 field profile)
- 扫场航点: Mission Protocol 上传成功 (MISSION_ACK)
- 状态转换链: INIT → PREFLIGHT → TAKEOFF → SCAN → LOITER → ENROUTE → LANDING → COMPLETED 全链路通过
- LOITER 超时: 模拟超时 → 正确回到 SCAN → mission_current_seq 递增

### 建议 OpenSpec Change
`flight-control-layer` + `mission-states-scan-loiter` + `mission-upload-protocol`

---

## Phase 6: 外部解算链路 + 投弹点跟踪 + 兜底中点

### 目标
实现外部解算程序坐标接收、目标跟踪 (自适应频率)、坐标转换工具库、围栏内随机点生成器。

> **v2.2 变更**: “视觉链路”改称“外部解算链路”，因为实际解算是另一个程序负责，本系统仅接收结果坐标。
> 新增 point_in_polygon 和 forced_strike_point 工具，服务于强制投弹降级逻辑。

### 前置条件
- Phase 4 完成 (FSM 引擎 — 外部坐标触发 LOITER→ENROUTE 转换)
- Phase 2 完成 (配置、日志、FieldProfile 提供围栏数据)

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/vision/__init__.py` | 接收器注册表 |
| `src/striker/vision/protocol.py` | `VisionReceiver` Protocol |
| `src/striker/vision/models.py` | `GpsDropPoint` 数据类 + 校验 |
| `src/striker/vision/tcp_receiver.py` | TCP 实现 |
| `src/striker/vision/udp_receiver.py` | UDP 实现 |
| `src/striker/vision/tracker.py` | `DropPointTracker` (滑动窗口 + 自适应频率) |
| `src/striker/utils/__init__.py` | |
| `src/striker/utils/geo.py` | GPS/坐标计算 |
| `src/striker/utils/converter.py` | `CoordConverter` (公共坐标转换) |
| `src/striker/utils/point_in_polygon.py` | 点在多边形内判定 (射线法) (v2.2 新增) |
| `src/striker/utils/forced_strike_point.py` | 围栏内随机点生成器 (v2.2 新增) |
| `src/striker/utils/units.py` | 单位转换 |
| `src/striker/utils/timing.py` | 精确计时 |
| `tests/unit/test_tracker.py` | |
| `tests/unit/test_geo.py` | |
| `tests/unit/test_converter.py` | 坐标转换已知答案测试 |
| `tests/unit/test_forced_strike_point.py` | 围栏内随机点生成测试 (v2.2 新增) |

### 自适应频率策略

```
  ┌────────────────────────────────────────────────────┐
  │  DropPointTracker                                     │
  │                                                    │
  │  0 Hz (无数据)  → 维持 LOITER, last_target = None   │
  │  单次            → 立即采纳, 切 ENROUTE             │
  │  低频 (<1Hz)    → 每次更新目标, 修正航线             │
  │  高频 (>1Hz)    → 滑动窗口 N 帧加权平均              │
  │                                                    │
  │  过期检测: last_update + stale_timeout → 标记stale  │
  └────────────────────────────────────────────────────┘
```

> [!NOTE]
> **目标跟踪与平滑算法: 滑动窗口中值滤波 (Sliding Window Median Filter)**
> 
> 在实际物理系统中，外部解算模块（如视觉跟踪器）传来的坐标经常伴有高频抖动或异常跳变点（Outliers）。推荐在 `DropPointTracker` 中使用轻量级 `collections.deque` 实现抗干扰过滤：
> 
> ```python
> import collections
> import statistics
> from typing import Optional
> 
> class DropPointTracker:
>     def __init__(self, window_size: int = 5):
>         # 定长 deque 天然支持溢出淘汰，具备 O(1) 操作性能
>         self.lat_window = collections.deque(maxlen=window_size)
>         self.lon_window = collections.deque(maxlen=window_size)
>         
>     def push(self, lat: float, lon: float) -> None:
>         """TCP/UDP 每收到一帧数据，推送一次"""
>         self.lat_window.append(lat)
>         self.lon_window.append(lon)
>         
>     def get_smoothed_target(self) -> Optional[tuple[float, float]]:
>         """飞控解算层每秒或被触发时，从这里提取坐标"""
>         if not self.lat_window:
>             return None
>         # 核心降噪：使用中值滤波(Median)极其有效排除单点巨大异常坐标
>         return (
>             statistics.median(self.lat_window), 
>             statistics.median(self.lon_window)
>         )
> ```

### 验证标准
- TCP/UDP 接收器：用 mock 发送 GPS 坐标 → 正确解析
- 自适应频率：高频输入 → 输出平滑，低频 → 每条都采纳
- CoordConverter: NED(100m N, 50m E) → GPS 偏移量正确 (已知答案)
- GPS 校验：非法坐标 (lat=200) → 拒绝 + WARNING 日志
- point_in_polygon: 已知点返回正确的内外判定 (v2.2)
- forced_strike_point: 生成 1000 个随机点，100% 在围栏内且不在安全缓冲区内 (v2.2)

### 建议 OpenSpec Change
`vision-interface` + `utils-geo-converter` + `utils-forced-strike`

---

## Phase 7: 投弹系统 (弹道解算 + 释放机构 + 强制投弹)

### 目标
实现弹道解算引擎、双通道释放机构抽象 (MAVLink Servo / GPIO)，
以及强制投弹降级状态 (3 轮超时后围栏内随机点投弹)。

> **v2.2 变更**: 新增 `forced_strike.py` 状态，实现三轮超时后的强制投弹降级逻辑。
> 降级时调用 Phase 6 实现的 `forced_strike_point` 生成围栏内随机投弹点。

### 前置条件
- Phase 5 完成 (飞行指令层 — 需要遥测数据: 地速、航向、高度、风速)
- Phase 6 完成 (外部解算链路 — 需要目标坐标; forced_strike_point 工具)

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/payload/__init__.py` | 释放控制器注册表 |
| `src/striker/payload/protocol.py` | `ReleaseController` Protocol |
| `src/striker/payload/ballistics.py` | `BallisticCalculator` — 弹道解算引擎 |
| `src/striker/payload/models.py` | 物理参数数据类 |
| `src/striker/payload/mavlink_release.py` | DO_SET_SERVO 实现 |
| `src/striker/payload/gpio_release.py` | GPIO 实现 (gpiod) |
| `src/striker/core/states/approach.py` | ApproachState (投弹进近) |
| `src/striker/core/states/release.py` | ReleaseState (投弹释放) |
| `src/striker/core/states/forced_strike.py` | **ForcedStrikeState (v2.2 新增)** — 强制随机点投弹降级 |
| `tests/unit/test_ballistics.py` | **弹道已知答案测试** (最关键!) |
| `tests/unit/test_release.py` | 释放机构测试 |

### 弹道模型

> [!TIP]
> **自由落体抛物线解算与 GPS 反畸变推导 (Ballistic & WGS-84)**
> 
> 基于外部科研文献无制导投弹（Autonomous ballistic airdrop），标准的提前量解算除了考虑地速滑行（`d = v * t`），最关键的是**千万不要手动计算常数地球半径的三角函数**（易在不同维度引发严重缩放畸变）。
> **(MCP 检索自 context7 - geopy 最佳实践)**：通过 `geopy.distance.geodesic` 原生支持精准极坐标反推：
> 
> ```python
> import math
> from dataclasses import dataclass
> from geopy.distance import distance, Point
> 
> class BallisticCalculator:
>     G = 9.81  # 重力加速度
>     
>     def calculate_release_point(self, target_lat: float, target_lon: float,
>                                 alt_m: float, vel_n: float, vel_e: float,
>                                 wind_n: float = 0.0, wind_e: float = 0.0) -> tuple[float, float]:
>         if alt_m <= 0:
>             return target_lat, target_lon
>             
>         # 1. 计算滞空方程（无阻力）
>         t_fall = math.sqrt((2 * alt_m) / self.G)
>         
>         # 2. 计算北向与东向的贯性滑行米数
>         d_north = (vel_n + wind_n) * t_fall
>         d_east = (vel_e + wind_e) * t_fall
>         
>         # 3. 勾股定理算合成距离，atan2 算真北方位角（Bearing）
>         d_total_meters = math.hypot(d_north, d_east)
>         bearing_deg = math.degrees(math.atan2(d_east, d_north))
>         
>         # 4. 基于目标点逆向推送（距离不变，方位角反转 180°）
>         target_idx = Point(latitude=target_lat, longitude=target_lon)
>         reverse_bearing = (bearing_deg + 180.0) % 360.0
>         
>         # 调用严密 WGS-84 模型获取倒推的理想释放经纬度
>         release_pt = distance(meters=d_total_meters).destination(target_idx, reverse_bearing)
>         
>         return release_pt.latitude, release_pt.longitude
> ```

### 已知答案测试 (KAT) 示例

| 高度(m) | 地速(m/s) | 航向(°) | 风速(m/s) | 风向(°) | 预期提前距离(m) |
|---------|----------|---------|----------|---------|---------------|
| 50 | 20 | 0 (北) | 0 | 0 | ~63.9 |
| 100 | 25 | 90 (东) | 5 | 270 (西风) | ~142.5 (含风偏) |
| 30 | 15 | 45 | 0 | 0 | ~37.1 |

> [!NOTE]
> **物理投弹机构实现 (MAVLink Servo Control)**
> 
> 在通过飞控 PWM 通道释放载荷（触发舵机拔除插销）时，不能仅仅调用发送函数，必须在事件循环中捕获由飞控返回的 `COMMAND_ACK`，确保投弹指令通过无线电链路下达并生效。
> 
> ```python
> async def trigger_servo_release(self, channel: int, pwm_value: int):
>     """发送 DO_SET_SERVO 投弹指令，并严格死等专属 ACK"""
>     self.mav.mav.command_long_send(
>         self.mav.target_system, self.mav.target_component,
>         mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
>         0,          # confirmation
>         channel,    # param 1: Servo channel number
>         pwm_value,  # param 2: PWM value
>         0, 0, 0, 0, 0 # param 3-7 unused
>     )
>     
>     # 循环监听 ACK (因为可能收到无关命令的 ACK)
>     while True:
>         ack = await self.wait_for_message('COMMAND_ACK', timeout=1.5)
>         if not ack:
>             raise ReleaseError("DO_SET_SERVO command timeout (Link loss?)")
>         
>         if ack.command == mavutil.mavlink.MAV_CMD_DO_SET_SERVO:
>             if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
>                 return True
>             raise ReleaseError(f"Servo command rejected by FC: {ack.result}")
> ```

### 验证标准
- 弹道解算: KAT 全部通过 (误差 < 0.1m)
- MavlinkRelease: mock DO_SET_SERVO 命令正确发送
- GpioRelease: mock gpiod 调用正确
- APPROACH → RELEASE 状态转换: 到达释放点 → 触发
- DRY_RUN 模式: 所有释放动作被跳过 + 日志记录
- **强制投弹降级 (v2.2)**: LOITER 超时 3 轮后 → FORCED_STRIKE → 随机点在围栏内 → 飞向该点投弹 → LANDING
- **强制投弹安全性 (v2.2)**: 生成的随机点必须通过 point_in_polygon 校验

### 建议 OpenSpec Change
`payload-ballistics` + `payload-release` + `forced-strike-degradation`

---

## Phase 8: 全任务集成 + CI/CD

### 目标
将所有模块集成到 `app.py` 主循环，实现完整的 SITL 全任务测试 + CI/CD 管线。

### 前置条件
- Phase 0-7 全部完成

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/app.py` | asyncio 主循环编排 (含 field profile 加载+校验) |
| `scripts/preflight_check.py` | 独立预飞检查脚本 |
| `scripts/lint_registry.py` | CI: 公共符号 ↔ REGISTRY.md 同步检查 |
| `scripts/check_pkg_versions.py` | CI: pkg/ 版本一致性检查 |
| `scripts/setup_rpi5.sh` | 树莓派部署脚本 |
| `.github/workflows/ci.yml` | GitHub Actions: lint + test + SITL |
| `tests/integration/test_sitl_full_mission.py` | **完整任务 SITL 测试** (含 SCAN↔LOITER 循环 + 强制投弹) |
| `docs/architecture.md` | 架构文档 |
| `docs/config_reference.md` | 配置参考 (含 field profile JSON 格式) |
| `docs/field_profile.md` | 场地配置编写指南 (v2.2 新增) |
| `docs/states.md` | 状态机文档 (含 v2.2 SCAN/FORCED_STRIKE 状态) |
| `docs/ballistics.md` | 弹道模型文档 |
| `docs/wiring.md` | 接线文档 |

### 主循环架构

```python
# app.py
async def main():
    settings = StrikerSettings()
    log = configure_logging(settings)
    
    # (v2.2) 加载并校验场地配置 — 校验失败则拒绝起飞
    field_profile = load_field_profile(settings.field)
    
    # 初始化各子系统
    conn = MAVLinkConnection(settings)
    safety = SafetyMonitor(conn, settings, field_profile)
    vision = create_vision_receiver(settings)
    tracker = DropPointTracker(settings)
    flight = FlightController(conn, settings)
    release = create_release_controller(settings)
    ballistics = BallisticCalculator(settings)
    recorder = FlightRecorder(settings)
    
    context = MissionContext(
        conn, flight, vision, tracker, 
        release, ballistics, safety, recorder,
        settings, field_profile,             # (v2.2) 场地配置注入上下文
    )
    fsm = MissionStateMachine(context)
    
    # 启动协程
    async with asyncio.TaskGroup() as tg:
        tg.create_task(conn.run())          # MAVLink 收发
        tg.create_task(safety.run())         # 安全监控
        tg.create_task(vision.run())         # 外部解算坐标接收
        tg.create_task(fsm.run())            # 状态机主循环
        tg.create_task(recorder.run())       # 飞行记录
```

### CI/CD 管线

```
  ┌─────────────────────────────────────────────────────┐
  │  GitHub Actions CI Pipeline                          │
  │                                                      │
  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
  │  │ Lint     │  │ Type     │  │ Unit Tests       │  │
  │  │ ruff     │  │ mypy     │  │ pytest (no SITL) │  │
  │  │ check    │  │ --strict │  │                   │  │
  │  └──────────┘  └──────────┘  └──────────────────┘  │
  │       │             │              │                  │
  │       ▼             ▼              ▼                  │
  │  ┌────────────────────────────────────────────────┐  │
  │  │ Registry Lint + Pkg Version Check               │  │
  │  │ lint_registry.py + check_pkg_versions.py       │  │
  │  └────────────────────────────────────────────────┘  │
  │                      │                                │
  │                      ▼                                │
  │  ┌────────────────────────────────────────────────┐  │
  │  │ SITL Integration Tests (heavy, scheduled)       │  │
  │  │ ArduPlane SITL + pytest-integration             │  │
  │  └────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────┘
```

### 验证标准
- SITL 全任务 (正常路径): ARM → TAKEOFF → **SCAN** → LOITER → (模拟坐标) → ENROUTE → APPROACH → RELEASE (dry run) → **LANDING** → COMPLETED
- SITL 全任务 (降级路径 v2.2): ARM → TAKEOFF → SCAN → LOITER(timeout) → SCAN → LOITER(timeout) → SCAN → LOITER(timeout) → **FORCED_STRIKE** → LANDING → COMPLETED
- CI 管线全绿
- Human Override: SITL 中手动切模式 → 程序检测到 → 进入 OVERRIDE
- 场地配置加载: app.py 启动时成功加载 field profile; 变更 --field 参数切换场地 (v2.2)

### 建议 OpenSpec Change
`integration-main-loop` + `ci-cd-pipeline`

---

## 并行度与时间估算

```
  时间线 (估算, 每 Phase 约 1-3 个 OpenSpec change):
  ════════════════════════════════════════════════════════════════════

  Week 1     ┌─────────────────────┐  ┌────────────────────┐
             │ Phase 0: 脚手架     │  │ Phase 1: AI 治理   │
             │ (1 change)          │  │ (2 changes)        │
             └─────────┬───────────┘  └────────┬───────────┘
                       │                        │
  Week 2     ┌─────────▼───────────┐           │
             │ Phase 2: 配置+场地+日志│◄──────────┘
             │ (2 changes)          │
             └─────────┬───────────┘
                       │
  Week 3     ┌─────────▼───────────┐  ┌────────────────────┐
             │ Phase 3: 通信层     │  │ Phase 3b: SITL环境 │ (并行)
             │ (1 change)          │  │ (1 change)          │
             └─────────┬───────────┘  └────────┬───────────┘
                       │                        │
  Week 4     ┌─────────▼───────────────────────▼──────────┐
             │ Phase 4: FSM引擎 + 安全监控 + 遥测         │
             │ (2-3 changes)                               │
             └─────────┬──────────────────────────────────┘
                       │
  Week 5-6   ┌─────────▼───────────┐
             │ Phase 5: 飞行指令   │
             │ + 扫场+业务状态    │
             │ (3 changes)         │
             └─────────┬───────────┘
                       │
  Week 6-7   ┌─────────▼───────────┐  ┌────────────────────┐
             │ Phase 6: 解算链路   │  │ Phase 7: 投弹+强投 │ (可部分并行)
             │ (3 changes)          │  │ (3 changes)         │
             └─────────┬───────────┘  └────────┬───────────┘
                       │                        │
  Week 8     ┌─────────▼───────────────────────▼──────────┐
             │ Phase 8: 全任务集成 + CI/CD                 │
             │ (2 changes)                                  │
             └─────────────────────────────────────────────┘
```

---

## 风险矩阵与缓解策略

| 风险 | 概率 | 影响 | 出现阶段 | 缓解策略 |
|------|------|------|---------|---------|
| ~~pymavlink + Python 3.14 安装失败~~ | — | — | — | ✅ 已改用 3.13，风险消除 |
| pymavlink 阻塞 API 与 asyncio 冲突 | 低 | 高 | Phase 3 | run_in_executor + Queue 模式已验证可行 |
| ArduPlane 自动降落序列复杂度超预期 | 中 | 中 | Phase 5 | 先用 RTL 作为 fallback，降落序列增量完善 |
| 投弹精度严重依赖风速估算 | 高 | 中 | Phase 7 | 先用无阻力模型 + 实飞标定修正系数 |
| SITL 环境与真机行为差异 | 中 | 中 | Phase 8 | SITL 只验证逻辑正确性，精度依赖实飞 |
| RPi5/Orin GPIO API 不一致 | 低 | 低 | Phase 7 | gpiod 统一抽象 (Phase 0 即验证) |
| AI Agent 生成代码不合规 | 中 | 低 | 全局 | Phase 1 的治理体系 + CI lint 双重保障 |
| 场地配置 JSON 格式设计不合理导致中途重构 (v2.2) | 中 | 中 | Phase 2/5 | 初期在 SITL 中充分实战验证，确认格式后再固化 |
| 强制投弹随机点落在危险区域 (v2.2) | 低 | 高 | Phase 6/7 | point_in_polygon 双重校验 + 安全缓冲区排除跑道/围栏边缘 |

---

## OpenSpec Change 推荐列表 (按执行顺序)

| # | Change 名称 | Phase | 优先级 | 估计任务数 |
|---|------------|-------|--------|-----------|
| 1 | `scaffold-phase0-foundation` | 0 | P0 | 8-12 |
| 2 | `governance-tier1-charter` | 1 | P0 | 5-8 |
| 3 | `governance-tier2-skills` | 1 | P0 | 18-24 |
| 4 | `infra-config-logging` | 2 | P0 | 10-15 |
| 4b | `infra-field-profile` | 2 | P0 | 8-12 |
| 5 | `comms-mavlink-adapter` | 3 | P0 | 12-18 |
| 6 | `infra-sitl-environment` | 3b | P1 | 5-8 |
| 7 | `core-fsm-engine` | 4a | P0 | 12-15 |
| 8 | `safety-monitor` | 4b | P0 | 10-12 |
| 9 | `telemetry-recorder` | 4c | P1 | 6-8 |
| 10 | `flight-control-layer` | 5 | P0 | 15-20 |
| 11 | `mission-states-scan-loiter` | 5 | P0 | 15-22 |
| 12 | `mission-upload-protocol` | 5 | P0 | 8-12 |
| 13 | `vision-interface` | 6 | P0 | 12-15 |
| 14 | `utils-geo-converter` | 6 | P1 | 8-10 |
| 15 | `utils-forced-strike` | 6 | P0 | 6-8 |
| 16 | `payload-ballistics` | 7 | P0 | 10-12 |
| 17 | `payload-release` | 7 | P0 | 8-10 |
| 18 | `forced-strike-degradation` | 7 | P0 | 8-12 |
| 19 | `integration-main-loop` | 8 | P0 | 18-25 |
| 20 | `ci-cd-pipeline` | 8 | P1 | 8-12 |

**预计总任务数**: ~205-285 个 tasks (v2.2 新增 ~40-60 tasks)

---

## 关键约束提醒

> [!CAUTION]
> **以下规则贯穿所有 Phase，违反即为灾难性：**
> 
> 1. **不自动 ARM** — ARM 操作必须有人工确认或明确的预飞检查通过
> 2. **不跳过 Safety Monitor** — 安全监控协程永远启动、永不关闭
> 3. **不在 Override 后自动恢复** — 人工接管是终态
> 4. **不让 pymavlink 泄漏** — 只在 `comms/` 内 import pymavlink
> 5. **不信任未校验坐标** — 所有 GPS 坐标必须通过 validate_gps()
> 6. **不硬编码** — 所有可变参数走配置系统
> 7. **先调研后写代码** — 实际代码变更过程中，AI 在每一轮新功能添加之前，必须强制调用代码搜索能力进行调研，给出修改方案确认后方可开发。
> 8. **不在没有有效 field profile 的情况下起飞** — 场地配置起飞前必须通过校验 (v2.2)
> 9. **不跳过场地配置校验** — 围栏/跑道/航点 必须通过 pydantic 校验 (v2.2)
> 10. **不在强制投弹逻辑中生成围栏外的坐标** — 随机点生成后必须经 point_in_polygon 二次校验 (v2.2)
