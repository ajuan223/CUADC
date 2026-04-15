## Context

当前正在开启 Striker 无人机飞控自动飞行系统的 Phase 0 开发。由于项目将在树莓派5 / NVIDIA Orin 上运行，且需要与 CUAV X7（ArduPlane固件）进行串行 MAVLink 高频通信，项目的包依赖、Python版本、构建与类型检查规范需要在一开始就得到严格的确立和锁定，以此来避免后续 Phase 中的熵增和灾难性依赖冲突问题。

## Goals / Non-Goals

**Goals:**
- 从零建立可构建、可测试、可 lint 的 Python 空骨架。
- 采用目前最优的依赖锁管理工具实现一致性隔离（`uv` 工作区隔离机制）。
- 提供基础的代码质量保障工具链：静态类型检查（`mypy`）、格式化与 Lint（`ruff`）及异步测试框架（`pytest-asyncio`）。
- 奠定项目的系统异常（Exception Hierarchy）结构。

**Non-Goals:**
- 编写任何与飞行控制、任务状态机或 MAVLink 组件相关的实际业务代码。
- 配置真实的物理硬件传感器或串口测试。

## Decisions

- **选择 Python 3.13 作为唯一解释器版本**
  - **Rationale**: pymavlink 的 `fastcrc` 依赖在 Python 3.14 的预编译 wheel 上存在兼容性问题（[GitHub Issue #1138](https://github.com/ardupilot/pymavlink/issues/1138)）。Python 3.13 足够先进（存在 TaskGroup 等协程特性），且生态成熟能满足本项目 10-50ms 级别的延迟容忍度。
  - **Alternatives**: 放弃 pymavlink 转向 MAVSDK-Python（不可选，因为目标飞控是 ArduPlane 而非 PX4）；使用更低版本如 Python 3.11（缺乏高级 async 特性）。

- **依赖包管理器选用 `uv` 并划定 `pkg/` Workspace**
  - **Rationale**: `uv` 使用 Rust 编写，具有极快的解析与虚拟环境创建速度。通过 `[tool.uv.workspace] members = ["pkg/*"]` 配置，能将后续抽象的通用组件（如能力注册表支持）锁定在独立的包中，进而防止源业务代码与底层库产生双向循环依赖。

- **基于 Pydantic-Settings & Structlog 的环境脚手架**
  - **Rationale**: 尽早在 Phase 0 引入 `pydantic-settings` 有利于确立“配置模型”，满足三层优先级配置诉求；`structlog` 确立基于 JSON 和上下文的系统级日志根基。

## Risks / Trade-offs

- [Risk] **Python 3.13 的生态局限性** 
  - **Mitigation**：由于这仍是一个较新的版本，目前已锁定为 3.13。如果有任何外设依赖（例如特殊的串口扩展包或 Orin 的硬件解算接口）尚未支持，将在后续 Phase 回退至 3.12 并在 lock 阶段修复。
- [Risk] **Workspace 环境对 AI agent 及用户的复杂度增加**
  - **Mitigation**：在 `pkg/` 增加专门的 `README.md`，解释该结构是为了避免业务与插件双向耦合，并用规范明确隔离策略。
