## Context

Phase 0 创建了 `src/striker/` 骨架（`__init__.py`, `__main__.py`, `py.typed`, `exceptions.py`）和 `config.example.json`。Phase 1 建立了 AI 治理体系（CHARTER.md, AGENTS.md, 11 个模块 SKILL）。当前 `config/` 和 `telemetry/` 目录不存在。

所有后续业务模块（MAVLink 通信、状态机、飞行控制）都需要：
- 统一的配置获取方式（串口参数、场地名称、超时等）
- 结构化日志输出（开发友好 + 生产 JSON）
- 完整的异常类型（场地校验失败等）

已有约束：
- `config-system-rules` SKILL: 三层优先级、`STRIKER_` 前缀、`settings_customise_sources()` 顺序不可修改
- `field-profile-rules` SKILL: FieldProfile 用 `BaseModel`（非 BaseSettings）、围栏封闭校验、航点/跑道在围栏内校验
- `telemetry-rules` SKILL: structlog 是唯一日志框架、处理器链固定、禁 `print()` 和 stdlib `logging`
- `data/fields/sitl_default/field.json` 已有初始场地数据

## Goals / Non-Goals

**Goals:**
- 实现 `StrikerSettings(BaseSettings)` 三层配置：代码默认 < config.json < 环境变量
- 实现 `FieldProfile(BaseModel)` 场地配置数据模型 + 地理校验
- 实现 `detect_platform()` 平台检测
- 实现 structlog 全局配置（TTY 检测自动切换渲染器）
- 充实异常层次（场地配置相关异常）
- 完整单元测试覆盖

**Non-Goals:**
- FlightRecorder（CSV 飞行数据记录）— 属于 Phase 4b
- GCS Reporter（状态上报）— 属于 Phase 4b
- 配置热重载 / 文件监听 — 无此需求
- 多场地同时加载 — 单次任务只用一个场地
- 运行时配置变更 — 配置在启动时一次性加载

## Decisions

### D1: pydantic-settings JsonConfigSettingsSource 内置支持

**选择**: 使用 `pydantic-settings` 内置的 `JsonConfigSettingsSource`，通过 `settings_customise_sources()` 控制优先级。

**替代方案**: 自定义 `PydanticBaseSettingsSource` 子类手动读取 JSON — 更灵活但不必要，内置源已满足需求且经过充分测试。

**优先级顺序**: `init_settings` → `env_settings` → `JsonConfigSettingsSource` → `file_secret_settings`。Sources returned earlier in the tuple take higher priority（pydantic-settings 文档确认）。

### D2: FieldProfile 使用 pydantic BaseModel + 自定义加载器

**选择**: `FieldProfile` 继承 `BaseModel`（非 `BaseSettings`），通过独立函数 `load_field_profile(name: str, base_dir: Path)` 从 `data/fields/{name}/field.json` 加载。

**理由**: 场地配置不从环境变量加载，是纯数据模型 + 文件加载。使用 BaseModel 避免 BaseSettings 的环境变量扫描开销。加载器负责文件读取，FieldProfile 负责数据校验——职责分离。

### D3: 地理校验使用射线法 (Ray Casting)

**选择**: 使用射线法判断点是否在多边形内（Point-in-Polygon）。这是一个经典算法，实现简单、无需额外依赖。

**替代方案**: 引入 `shapely` 库 — 功能强大但对当前需求过重（仅需要点在多边形内判断）。Phase 6 如果需要复杂地理计算再引入。

### D4: 平台检测通过文件系统特征

**选择**: `detect_platform()` 通过检查 `/proc/device-tree/model`（RPi）、`/etc/nv_tegra_release`（Orin）和 `MAVLINK_SITL` 环境变量来判断平台。

**替代方案**: `platform.machine()` 检测架构 — RPi5 和 Orin 都是 aarch64，无法区分。

### D5: structlog 使用 native 配置（非 stdlib 集成）

**选择**: 直接使用 structlog 原生 API（`structlog.configure()`），不集成 stdlib `logging`。

**理由**: 项目完全不使用 stdlib logging（AGENTS.md R04），避免双重日志系统的复杂性。使用 `make_filtering_bound_logger` 提供级别过滤。

### D6: FieldProfile 数据模型结构映射现有 field.json

**选择**: FieldProfile 模型字段直接映射 `data/fields/sitl_default/field.json` 的结构，包括嵌套模型：`BoundaryConfig`、`LandingConfig`（含 `ApproachWaypoint`、`TouchdownPoint`）、`ScanWaypointsConfig`、`LoiterPointConfig`。

**理由**: 已有 field.json 结构经过 Phase 0 设计，直接映射避免数据转换层。

## Risks / Trade-offs

**[Risk] pydantic-settings 版本升级可能改变 `settings_customise_sources` 签名** → 锁定 pydantic-settings 主版本，测试覆盖三层优先级行为

**[Risk] 射线法在高纬度地区精度下降** → 当前场地都在中纬度，影响可忽略；如需高精度可在后续 Phase 引入投影坐标系

**[Risk] 平台检测结果在 Docker 容器中可能不准确** → 添加 `STRIKER_PLATFORM` 环境变量覆盖，使容器化部署可手动指定

**[Risk] structlog `cache_logger_on_first_use=True` 导致测试中无法重新配置** → 测试中使用 `structlog.reset_defaults()` + 重新配置
