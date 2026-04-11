# 🛩️ Striker 项目开发顺序元规划 (Meta Development Plan)

> **创建日期**: 2026-04-12 · **基于**: init愿景.md v2.1
> **目的**: 为 AI Agent 实现提供有序的开发路线图，避免熵增和灾难性依赖冲突

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
    ├──▶ Phase 2: 配置系统 + 异常层次 + 日志框架
    │        │
    │        ├──▶ Phase 3: 通信层 (MAVLink Adapter)
    │        │        │
    │        │        ├──▶ Phase 4: 状态机引擎 + 安全监控
    │        │        │        │
    │        │        │        ├──▶ Phase 5: 飞行指令层 + 降落序列
    │        │        │        │        │
    │        │        │        │        ├──▶ Phase 6: 视觉链路 + 坐标工具库
    │        │        │        │        │        │
    │        │        │        │        │        └──▶ Phase 7: 投弹系统 (弹道 + 释放)
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
| `.python-version` | `3.14` |
| `src/striker/__init__.py` | 版本号 `__version__` |
| `src/striker/__main__.py` | `python -m striker` 入口 (空壳) |
| `src/striker/py.typed` | PEP 561 类型标记 |
| `src/striker/exceptions.py` | 完整异常层次 (StrikerError → 子类) |
| `tests/conftest.py` | pytest fixtures 骨架 |
| `tests/__init__.py` | |
| `config.example.json` | 配置模板 |
| `.env.example` | 环境变量模板 |
| `.gitignore` | Python + uv + data/ + config.json |
| `README.md` | 项目说明 |
| `pkg/` 目录 | 空，含 README.md 说明用途 |
| `data/` 目录 | 空，含 .gitkeep |
| `scripts/` 目录 | 空骨架 |
| `docs/` 目录 | 空骨架 |

### 关键决策与技术验证

> [!IMPORTANT]
> **pymavlink + Python 3.14 兼容性风险**
> 
> 根据调研 ([GitHub Issue #1138](https://github.com/ardupilot/pymavlink/issues/1138))：
> - pymavlink 的 `fastcrc` 依赖在 Python 3.14 上存在预编译 wheel 问题 (主要影响 Windows)
> - Linux 上编译安装通常可行，树莓派/Orin ARM 平台可能需要注意
> - pymavlink 社区正在讨论将 `fastcrc` 改为可选依赖
> 
> **建议**: Phase 0 中必须在 Linux (x86_64 + aarch64) 上验证 `uv add pymavlink` 成功安装。
> 如果 3.14 出问题，退守 3.13 作为保底方案。

### 具体步骤

```bash
# 1. 初始化项目 (src layout)
uv init --package ./
uv python pin 3.14

# 2. 安装核心依赖
uv add pymavlink pydantic-settings structlog

# 3. 安装开发工具
uv add --dev ruff mypy pytest pytest-asyncio

# 4. 验证工具链
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
建立三层治理架构，让后续所有 Phase 的 AI 实现都有规范可循。

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
| `.agent/skills/testing-rules/SKILL.md` | 测试规范 |
| `.agent/skills/capability-registry/SKILL.md` | 能力注册规范 |
| `.agent/skills/capability-registry/REGISTRY.md` | 能力清单 (初始为空表) |

### 分组策略

**1a. 宪法级 (必须先完成)**
- CHARTER.md
- AGENTS.md
- AGENTS.local.md

**1b. 模块 Skills (可并行编写)**
- 8 个模块 Skill 可同时创建，它们之间无依赖

### 验证标准
- AGENTS.md < 100 行有效指令
- 每个 SKILL.md 含：Architecture Constraints, Registration Pattern, Forbidden Patterns
- Skill 路由表覆盖所有 `src/striker/*/` 目录

### 建议 OpenSpec Change
`governance-tier1-charter` + `governance-tier2-skills`

---

## Phase 2: 配置系统 + 日志框架

### 目标
实现三层配置优先级 + structlog 结构化日志 + 平台检测。
这是所有业务模块的共享基础设施。

### 前置条件
- Phase 0 完成 (依赖已安装)
- Phase 1 的 `config-system-rules` SKILL 已创建

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/config/__init__.py` | |
| `src/striker/config/settings.py` | `StrikerSettings(BaseSettings)` — 三层配置 |
| `src/striker/config/platform.py` | `detect_platform()` → RPi5 / Orin / SITL / Unknown |
| `src/striker/config/validators.py` | 配置校验器 (物理量合理范围) |
| `src/striker/telemetry/__init__.py` | |
| `src/striker/telemetry/logger.py` | structlog 全局配置 |
| `src/striker/exceptions.py` | 完整异常层次 (Phase 0 已创建，这里充实) |
| `tests/unit/test_config.py` | 配置三层优先级测试 |
| `tests/unit/test_platform.py` | 平台检测测试 |
| `config.example.json` | 完整配置模板 (Phase 0 已创建，这里充实) |

### 关键设计要点

```python
# pydantic-settings 三层优先级实现
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
    # ... 
```

> [!NOTE]
> pydantic-settings 的优先级链：`init defaults → json_file → env_vars` 
> 天然满足愿景中的三层设计，无需额外实现。

### 验证标准
- 三层优先级：default 被 json 覆盖，json 被 env 覆盖
- `STRIKER_DRY_RUN=true` 环境变量生效
- `detect_platform()` 在 SITL 环境下返回 `Platform.SITL`
- structlog 输出 JSON 格式日志

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
> **pymavlink 的阻塞 API 与 asyncio 的矛盾**
> 
> pymavlink 是同步 API。在 asyncio 中需要：
> - 用 `loop.run_in_executor()` 将阻塞 `recv_match()` 放到线程池
> - 或者用单独的消息接收协程 + `asyncio.Queue` 分发
> - **禁止** 在协程中直接调用阻塞函数

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
> 业务状态 (PREFLIGHT → TAKEOFF → LOITER → ...) 在后续 Phase 5-7 中逐步添加。
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

### 验证标准
- FSM: INIT → (event) → INIT (无转换); INIT → OverrideEvent → OVERRIDE
- SafetyMonitor: 模拟电池低 → 触发 EmergencyEvent
- Override 检测: 模拟飞控模式切换 → 触发 OverrideEvent
- CSV 飞行记录器: 写入/读回数据一致

### 建议 OpenSpec Change
`core-fsm-engine` + `safety-monitor` + `telemetry-recorder`

---

## Phase 5: 飞行指令层 + 降落序列

### 目标
实现高级飞行指令 (arm/takeoff/goto/set_mode) 和降落序列管理，
并填充业务状态 (PREFLIGHT → TAKEOFF → LOITER → ENROUTE → RETURN → LANDING → COMPLETED)。

### 前置条件
- Phase 4 完成 (FSM 引擎、安全监控)
- Phase 3 完成 (MAVLink 通信层)

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/flight/__init__.py` | |
| `src/striker/flight/controller.py` | `FlightController` — arm/takeoff/goto/set_mode/set_speed |
| `src/striker/flight/modes.py` | ArduPlane 模式枚举 (MANUAL, FBWA, AUTO, GUIDED, LOITER, RTL...) |
| `src/striker/flight/navigation.py` | 航线/航点管理 |
| `src/striker/flight/landing_sequence.py` | 降落序列生成 + 上传到飞控 |
| `src/striker/core/states/preflight.py` | PreflightState |
| `src/striker/core/states/takeoff.py` | TakeoffState |
| `src/striker/core/states/loiter.py` | LoiterState |
| `src/striker/core/states/enroute.py` | EnrouteState |
| `src/striker/core/states/return_base.py` | ReturnState |
| `src/striker/core/states/landing.py` | LandingState |
| `src/striker/core/states/completed.py` | CompletedState |
| `tests/unit/test_flight_controller.py` | |
| `tests/integration/test_sitl_takeoff.py` | SITL 起飞测试 |

### 关键固定翼注意事项

```
  ┌───────────────────────────────────────────────────────┐
  │  固定翼降落序列 (必须在起飞前上传到飞控!)              │
  │                                                       │
  │  Mission Item 序列:                                   │
  │  [n]   DO_LAND_START  → 标记降落序列开始              │
  │  [n+1] NAV_WAYPOINT   → 进近航点 (跑道延长线上)       │
  │  [n+2] NAV_LAND       → 着陆点 + 下滑道参数           │
  │                                                       │
  │  或 ArduPlane 4.5+:                                   │
  │  AUTOLAND 模式 (简化, 但需验证 CUAV X7 固件版本)      │
  └───────────────────────────────────────────────────────┘
```

### 验证标准
- SITL: ARM → AUTO (NAV_TAKEOFF) → 爬升到指定高度 → LOITER 盘旋
- SITL: GUIDED goto → 飞到目标点
- 降落序列: Mission items 正确上传到飞控
- 状态转换链: INIT → PREFLIGHT → TAKEOFF → LOITER → ENROUTE → RETURN → LANDING → COMPLETED 全链路通过

### 建议 OpenSpec Change
`flight-control-layer` + `mission-states-basic`

---

## Phase 6: 视觉链路 + 坐标工具库

### 目标
实现视觉坐标接收、目标跟踪 (自适应频率)、坐标转换工具库。

### 前置条件
- Phase 4 完成 (FSM 引擎 — 视觉坐标触发 LOITER→ENROUTE 转换)
- Phase 2 完成 (配置、日志)

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/vision/__init__.py` | 接收器注册表 |
| `src/striker/vision/protocol.py` | `VisionReceiver` Protocol |
| `src/striker/vision/models.py` | `GpsTarget` 数据类 + 校验 |
| `src/striker/vision/tcp_receiver.py` | TCP 实现 |
| `src/striker/vision/udp_receiver.py` | UDP 实现 |
| `src/striker/vision/tracker.py` | `TargetTracker` (滑动窗口 + 自适应频率) |
| `src/striker/utils/__init__.py` | |
| `src/striker/utils/geo.py` | GPS/坐标计算 |
| `src/striker/utils/converter.py` | `CoordConverter` (公共坐标转换) |
| `src/striker/utils/units.py` | 单位转换 |
| `src/striker/utils/timing.py` | 精确计时 |
| `tests/unit/test_tracker.py` | |
| `tests/unit/test_geo.py` | |
| `tests/unit/test_converter.py` | 坐标转换已知答案测试 |

### 自适应频率策略

```
  ┌────────────────────────────────────────────────────┐
  │  TargetTracker                                     │
  │                                                    │
  │  0 Hz (无数据)  → 维持 LOITER, last_target = None   │
  │  单次            → 立即采纳, 切 ENROUTE             │
  │  低频 (<1Hz)    → 每次更新目标, 修正航线             │
  │  高频 (>1Hz)    → 滑动窗口 N 帧加权平均              │
  │                                                    │
  │  过期检测: last_update + stale_timeout → 标记stale  │
  └────────────────────────────────────────────────────┘
```

### 验证标准
- TCP/UDP 接收器：用 mock 发送 GPS 坐标 → 正确解析
- 自适应频率：高频输入 → 输出平滑，低频 → 每条都采纳
- CoordConverter: NED(100m N, 50m E) → GPS 偏移量正确 (已知答案)
- GPS 校验：非法坐标 (lat=200) → 拒绝 + WARNING 日志

### 建议 OpenSpec Change
`vision-interface` + `utils-geo-converter`

---

## Phase 7: 投弹系统 (弹道解算 + 释放机构)

### 目标
实现弹道解算引擎和双通道释放机构抽象 (MAVLink Servo / GPIO)。

### 前置条件
- Phase 5 完成 (飞行指令层 — 需要遥测数据: 地速、航向、高度、风速)
- Phase 6 完成 (视觉链路 — 需要目标坐标)

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
| `tests/unit/test_ballistics.py` | **弹道已知答案测试** (最关键!) |
| `tests/unit/test_release.py` | 释放机构测试 |

### 弹道模型

```
  基础公式 (无空阻):
  ━━━━━━━━━━━━━━━━━
  t_fall = √(2h / g)     其中 g = 9.81 m/s²
  d_forward = v_ground × t_fall
  
  含风补偿:
  ━━━━━━━━━━
  d_x = (v_ground_x + W_x) × t_fall
  d_y = (v_ground_y + W_y) × t_fall
  
  释放坐标:
  ━━━━━━━━━
  release_lat = target_lat - (d_north / R_earth) × (180/π)
  release_lon = target_lon - (d_east / R_earth / cos(lat)) × (180/π)
```

### 已知答案测试 (KAT) 示例

| 高度(m) | 地速(m/s) | 航向(°) | 风速(m/s) | 风向(°) | 预期提前距离(m) |
|---------|----------|---------|----------|---------|---------------|
| 50 | 20 | 0 (北) | 0 | 0 | ~63.9 |
| 100 | 25 | 90 (东) | 5 | 270 (西风) | ~142.5 (含风偏) |
| 30 | 15 | 45 | 0 | 0 | ~37.1 |

### 验证标准
- 弹道解算: KAT 全部通过 (误差 < 0.1m)
- MavlinkRelease: mock DO_SET_SERVO 命令正确发送
- GpioRelease: mock gpiod 调用正确
- APPROACH → RELEASE 状态转换: 到达释放点 → 触发
- DRY_RUN 模式: 所有释放动作被跳过 + 日志记录

### 建议 OpenSpec Change
`payload-ballistics` + `payload-release`

---

## Phase 8: 全任务集成 + CI/CD

### 目标
将所有模块集成到 `app.py` 主循环，实现完整的 SITL 全任务测试 + CI/CD 管线。

### 前置条件
- Phase 0-7 全部完成

### 产出物

| 文件 | 说明 |
|------|------|
| `src/striker/app.py` | asyncio 主循环编排 (启动所有协程) |
| `scripts/preflight_check.py` | 独立预飞检查脚本 |
| `scripts/lint_registry.py` | CI: 公共符号 ↔ REGISTRY.md 同步检查 |
| `scripts/check_pkg_versions.py` | CI: pkg/ 版本一致性检查 |
| `scripts/setup_rpi5.sh` | 树莓派部署脚本 |
| `.github/workflows/ci.yml` | GitHub Actions: lint + test + SITL |
| `tests/integration/test_sitl_full_mission.py` | **完整任务 SITL 测试** |
| `docs/architecture.md` | 架构文档 |
| `docs/config_reference.md` | 配置参考 |
| `docs/states.md` | 状态机文档 |
| `docs/ballistics.md` | 弹道模型文档 |
| `docs/wiring.md` | 接线文档 |

### 主循环架构

```python
# app.py
async def main():
    settings = StrikerSettings()
    log = configure_logging(settings)
    
    # 初始化各子系统
    conn = MAVLinkConnection(settings)
    safety = SafetyMonitor(conn, settings)
    vision = create_vision_receiver(settings)
    tracker = TargetTracker(settings)
    flight = FlightController(conn, settings)
    release = create_release_controller(settings)
    ballistics = BallisticCalculator(settings)
    recorder = FlightRecorder(settings)
    
    context = MissionContext(conn, flight, vision, tracker, 
                            release, ballistics, safety, recorder, settings)
    fsm = MissionStateMachine(context)
    
    # 启动协程
    async with asyncio.TaskGroup() as tg:
        tg.create_task(conn.run())          # MAVLink 收发
        tg.create_task(safety.run())         # 安全监控
        tg.create_task(vision.run())         # 视觉接收
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
- SITL 全任务: ARM → TAKEOFF → LOITER → (模拟坐标) → ENROUTE → APPROACH → RELEASE (dry run) → RETURN → LANDING → COMPLETED
- CI 管线全绿
- Human Override: SITL 中手动切模式 → 程序检测到 → 进入 OVERRIDE

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
             │ Phase 2: 配置+日志  │◄──────────┘
             │ (1 change)          │
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
             │ + 业务状态          │
             │ (2 changes)         │
             └─────────┬───────────┘
                       │
  Week 6-7   ┌─────────▼───────────┐  ┌────────────────────┐
             │ Phase 6: 视觉链路   │  │ Phase 7: 投弹系统  │ (可部分并行)
             │ (2 changes)          │  │ (2 changes)         │
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
| pymavlink + Python 3.14 安装失败 | 中 | 高 | Phase 0 | 退守 3.13；在 Linux aarch64 上提前验证 |
| pymavlink 阻塞 API 与 asyncio 冲突 | 低 | 高 | Phase 3 | run_in_executor + Queue 模式已验证可行 |
| ArduPlane 自动降落序列复杂度超预期 | 中 | 中 | Phase 5 | 先用 RTL 作为 fallback，降落序列增量完善 |
| 投弹精度严重依赖风速估算 | 高 | 中 | Phase 7 | 先用无阻力模型 + 实飞标定修正系数 |
| SITL 环境与真机行为差异 | 中 | 中 | Phase 8 | SITL 只验证逻辑正确性，精度依赖实飞 |
| RPi5/Orin GPIO API 不一致 | 低 | 低 | Phase 7 | gpiod 统一抽象 (Phase 0 即验证) |
| AI Agent 生成代码不合规 | 中 | 低 | 全局 | Phase 1 的治理体系 + CI lint 双重保障 |

---

## OpenSpec Change 推荐列表 (按执行顺序)

| # | Change 名称 | Phase | 优先级 | 估计任务数 |
|---|------------|-------|--------|-----------|
| 1 | `scaffold-phase0-foundation` | 0 | P0 | 8-12 |
| 2 | `governance-tier1-charter` | 1 | P0 | 5-8 |
| 3 | `governance-tier2-skills` | 1 | P0 | 15-20 |
| 4 | `infra-config-logging` | 2 | P0 | 10-15 |
| 5 | `comms-mavlink-adapter` | 3 | P0 | 12-18 |
| 6 | `infra-sitl-environment` | 3b | P1 | 5-8 |
| 7 | `core-fsm-engine` | 4a | P0 | 12-15 |
| 8 | `safety-monitor` | 4b | P0 | 10-12 |
| 9 | `telemetry-recorder` | 4c | P1 | 6-8 |
| 10 | `flight-control-layer` | 5 | P0 | 15-20 |
| 11 | `mission-states-basic` | 5 | P0 | 12-18 |
| 12 | `vision-interface` | 6 | P0 | 12-15 |
| 13 | `utils-geo-converter` | 6 | P1 | 8-10 |
| 14 | `payload-ballistics` | 7 | P0 | 10-12 |
| 15 | `payload-release` | 7 | P0 | 8-10 |
| 16 | `integration-main-loop` | 8 | P0 | 15-20 |
| 17 | `ci-cd-pipeline` | 8 | P1 | 8-12 |

**预计总任务数**: ~165-225 个 tasks

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
