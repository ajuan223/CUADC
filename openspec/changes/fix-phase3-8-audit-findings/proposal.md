## Why

Phase 3-8 代码已批量生成，但系统性审查发现 13 处设计偏离和运行时缺陷。其中 3 项为阻塞性问题（FSM 转换缺失导致降级路径不可用、vision receiver 未启动、安全回调未连接），会导致核心功能无法运行。其余问题涉及约束违反（pymavlink 泄漏）、逻辑错误（配置优先级反转、降落序列误用 RTL）和缺失产出物。必须在 SITL 集成测试之前全部修复。

## What Changes

### P0 — 阻塞性缺陷（运行时必崩）

- **F-01**: FSM 声明式转换表缺少 `forced_strike` 作为源状态的所有转换（`forced_strike → landing`、`forced_strike → override`、`forced_strike → emergency`）。LOITER 超时进入 FORCED_STRIKE 后，`_perform_transition("landing")` 调用 `to_landing()` 时 python-statemachine 抛 `TransitionNotAllowed`。同理 override/emergency 全局拦截在 forced_strike 状态下失效。
- **F-02**: `app.py` TaskGroup 未启动 `vision_receiver.start()`，外部解算坐标永远不会被接收，LOITER 永远等不到 TARGET_ACQUIRED。
- **F-03**: `app.py` 未调用 `safety_monitor.set_event_callback()` 将安全事件桥接到 FSM 的 `process_event()`，导致电池/GPS/心跳/围栏检查失败时不会触发 EmergencyEvent，安全监控形同虚设。

### P1 — 约束违反与逻辑错误

- **F-04 (RL-04 违反)**: `flight/controller.py` 内 4 处 `from pymavlink import mavutil`、`payload/mavlink_release.py` 内 1 处，pymavlink 导入泄漏到 comms/ 包以外。设计文档要求所有 pymavlink 调用封装在 comms/ 内。修复方案：将 pymavlink 常量引用（`MAV_CMD_*`, `MAV_MODE_FLAG_*` 等）迁移到 `comms/messages.py` 作为纯整数常量导出，flight/ 和 payload/ 改为引用 comms 的常量。
- **F-05 (配置优先级反转)**: `settings.py:settings_customise_sources` 返回 `(init, env, Json, secrets)`，pydantic-settings 后出现的优先级更高，实际效果为 `init < env < json`。设计文档要求 `init < json < env`（env 可覆盖一切）。修复：将元组顺序改为 `(init_settings, JsonConfigSettingsSource(settings_cls), env_settings, file_secret_settings)`。
- **F-06 (降落序列误用)**: `landing.py` 使用 `set_mode(RTL)` 并通过 `__import__()` 动态导入，而设计文档要求使用 PREFLIGHT 阶段已上传到飞控的 DO_LAND_START 降落序列。修复：LandingState 应设置 AUTO 模式并跳转到已上传降落序列的起始航点索引，移除 `__import__()`。
- **F-07 (弹道解算缺参)**: `approach.py` 调用 `ballistic_calculator.calculate_release_point()` 时只传了 `target_lat, target_lon, altitude_m`，未传 `velocity_n_mps, velocity_e_mps, wind_n_mps, wind_e_mps`，全部使用默认值 0，导致投弹释放点等于目标点（无提前量）。修复：ApproachState 从 context 中提取当前速度和风速数据传入。
- **F-08 (HeartbeatMonitor 类型不匹配)**: `heartbeat.py` 构造函数参数 `conn` 标注为 `mavutil.mavfile`，但 TYPE_CHECKING 块内为空（`pass`），且 `app.py` 传入的是 `MAVLinkConnection` 实例。修复：将类型标注改为 `MAVLinkConnection`，内部通过 `conn.mav` 访问 pymavlink 对象，`_heartbeat_sender` 通过 `conn.send()` 发送心跳。

### P2 — 设计不一致与缺失

- **F-09 (距离计算硬编码)**: `enroute.py:52` 和 `approach.py:68` 使用 `111_000` 系数的简化距离公式，但 `utils/geo.py` 已有 `haversine_distance()`。违反 RL-06（不硬编码）。修复：替换为 `haversine_distance()` 调用。
- **F-10 (gpiod 依赖缺失)**: `gpio_release.py` 中 `import gpiod`，但 `pyproject.toml` 的 dependencies 中没有 `gpiod`。修复：添加为可选依赖 `[optional-dependencies]` 中 `gpio = ["gpiod"]`。
- **F-11 (Phase 0 缺失产出物)**: 设计文档 Phase 0 要求的以下文件未创建：`src/striker/py.typed`、`.env.example`、`data/fields/sitl_default/field.json`（SITL 默认场地配置）、`pkg/` workspace 骨架目录。其中 `field.json` 是系统启动的必要条件（`load_field_profile("sitl_default")` 会因文件不存在而失败）。
- **F-12 (FSM to_override/to_emergency 源状态不完整)**: `machine.py` 中 `to_override` 和 `to_emergency` 的声明缺少 `forced_strike` 和 `completed` 作为源状态。虽然 completed 是终态不太需要转换，但 forced_strike 在降级路径中必须能被全局拦截。
- **F-13 (forced_strike_point 安全缓冲排除简化)**: `forced_strike_point.py` 通过缩小 bounding box 近似 buffer 排除，但未排除多边形内部边界附近的点。meta 文档 RL-10 要求"随机点生成后必须经 point_in_polygon 二次校验"（已做），但安全缓冲区排除应更严格。增强方案：生成后额外计算到最近边的距离，小于 buffer_m 则拒绝。

## Capabilities

### New Capabilities

- `pymavlink-isolation`: 将 pymavlink 的 MAVLink 常量（命令 ID、模式标志等）提取到 comms 层作为纯 Python 常量导出，使 flight/ 和 payload/ 不再直接 import pymavlink，满足 RL-04 约束
- `sitl-default-field`: SITL 默认场地配置文件 `data/fields/sitl_default/field.json`，含围栏、降落序列、扫场航点等，使系统能以 `--field sitl_default` 启动

### Modified Capabilities

- `config-system`: 修正 `settings_customise_sources` 返回顺序为 `init < json < env`；HeartbeatMonitor 类型标注修正为 MAVLinkConnection；gpiod 添加为可选依赖
- `project-framework`: 补充 Phase 0 缺失产出物（py.typed、.env.example、pkg/ 骨架）
- `utils-skill`: forced_strike_point 增加 distance_to_boundary 校验；enroute/approach 距离计算替换为 haversine_distance

## Impact

- **源文件修改** (~15 个文件):
  - `src/striker/core/machine.py` — FSM 转换表补充 forced_strike 源状态
  - `src/striker/app.py` — 启动 vision_receiver、连接 SafetyMonitor 回调
  - `src/striker/config/settings.py` — 配置优先级顺序修正
  - `src/striker/comms/heartbeat.py` — 类型标注修正为 MAVLinkConnection
  - `src/striker/comms/messages.py` — 新增 MAVLink 常量导出
  - `src/striker/flight/controller.py` — 移除 pymavlink 直接导入，改用 comms 常量
  - `src/striker/core/states/landing.py` — 改用 DO_LAND_START 降落序列
  - `src/striker/core/states/approach.py` — 传入速度/风速参数 + 距离计算改用 haversine
  - `src/striker/core/states/enroute.py` — 距离计算改用 haversine
  - `src/striker/payload/mavlink_release.py` — 移除 pymavlink 直接导入
  - `src/striker/utils/forced_strike_point.py` — 增加 boundary distance 校验
  - `pyproject.toml` — gpiod 可选依赖

- **新文件** (~4 个文件):
  - `src/striker/py.typed`
  - `.env.example`
  - `data/fields/sitl_default/field.json`
  - `pkg/README.md` + `pkg/.gitkeep`

- **无 API 变更**: 所有修改为内部实现修正，不改变外部接口
- **无依赖新增** (gpiod 为可选依赖，不影响核心安装)
