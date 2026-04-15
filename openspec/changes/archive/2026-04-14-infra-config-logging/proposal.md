## Why

Phase 0 建立了项目骨架，Phase 1 完成了 AI 治理体系，但 `src/striker/` 目前只有 4 个空壳文件。所有后续业务模块（MAVLink 通信、状态机、飞行控制等）都依赖配置系统和日志框架。没有统一的配置加载机制，各模块将各自硬编码参数；没有 structlog 结构化日志，SITL 仿真和实飞调试将缺乏可追溯性。这是所有业务模块共享的基础设施层，必须在 Phase 3 之前完成。

## What Changes

- 新增 `src/striker/config/` 包：实现 `StrikerSettings(BaseSettings)` 三层配置优先级（代码默认 < config.json < 环境变量），环境变量前缀 `STRIKER_`
- 新增 `src/striker/config/field_profile.py`：实现 `FieldProfile(BaseModel)` 场地配置数据模型，包含围栏多边形、跑道、扫场航点、降落参数的 pydantic 校验
- 新增 `src/striker/config/platform.py`：实现 `detect_platform()` 平台检测（RPi5 / Orin / SITL / Unknown）
- 新增 `src/striker/config/validators.py`：配置校验器（物理量合理范围校验）
- 新增 `src/striker/telemetry/` 包：实现 structlog 全局配置（开发 TTY 用 ConsoleRenderer，生产用 JSONRenderer）
- 充实 `src/striker/exceptions.py`：添加场地配置相关异常类
- 充实 `config.example.json`：补全 Phase 2 新增的配置字段
- 新增单元测试：配置三层优先级测试、场地配置加载与校验测试、平台检测测试

## Capabilities

### New Capabilities
- `config-system`: 三层配置系统 — pydantic-settings BaseSettings 实现，包含配置加载、优先级覆盖、平台检测和物理量校验
- `field-profile`: 场地配置系统 — FieldProfile 数据模型、地理围栏校验、航点在围栏内校验、跑道在围栏内校验、场地 JSON 文件加载
- `logging-framework`: structlog 结构化日志 — 全局配置函数、TTY 环境检测、ConsoleRenderer/JSONRenderer 切换、contextvars 支持

### Modified Capabilities
- `project-framework`: 充实 exceptions.py 异常层次（新增场地配置相关异常），更新 config.example.json 模板

## Impact

- **代码**: `src/striker/config/`（全新）、`src/striker/telemetry/`（全新）、`src/striker/exceptions.py`（扩展）、`config.example.json`（扩展）
- **依赖**: pydantic-settings（已在 Phase 0 安装）、structlog（已在 Phase 0 安装）、pydantic（传递依赖）
- **测试**: 新增 `tests/unit/test_config.py`、`tests/unit/test_field_profile.py`、`tests/unit/test_platform.py`
- **数据**: 现有 `data/fields/sitl_default/field.json` 将被 FieldProfile 加载器消费
- **下游影响**: Phase 3（MAVLink 通信层）将依赖 `StrikerSettings` 获取串口参数，依赖 structlog 记录通信日志
