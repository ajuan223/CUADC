## Why

根据《Striker 项目开发顺序元规划》(meta_development_plan.md) 的 Phase 0 要求，我们需要从零建立一个可构建、可测试、可 lint 的空项目骨架。作为整个无人机搜查打击飞控系统的根基，在编写业务逻辑之前建立规范的工具链、包治理结构与基础设施，是避免代码熵增和依赖冲突的关键。选择 Python 3.13 能够规避低版本或 3.14 版本中的各种兼容性问题。

## What Changes

- 初始化基于 `uv` 工具链的 Python 3.13 项目，并配置 `pyproject.toml`。
- 引入基础核心依赖：`pymavlink`, `pydantic-settings`, `structlog`。
- 安装并配置开发工具依赖：`ruff`, `mypy`, `pytest`, `pytest-asyncio`。
- 构建整体目录结构，包括 `src/striker/` 源代码、全局异常层次结构 (`exceptions.py`)。
- 建立基于 `uv workspace` 的 `pkg/` 冻结包隔离目录以及配套的 `runtime_data/`, `docs/`, `scripts/` 骨架。
- 建立 `data/fields/sitl_default/` 的场地配置模板框架及项目的 `.gitignore`, `README.md` 等工程化必需文件。

## Capabilities

### New Capabilities
- `project-framework`: 项目基础框架能力，提供标准入口点、全局异常基类定义以及代码风格与静态类型检查标准。
- `development-toolchain`: 提供可执行的开发与测试工具链（配置好了环境的 pytest, ruff, mypy）。
- `workspace-isolation`: 提供 `uv` 工作区管理能力，确保内部库拆分时的严格隔离性。

### Modified Capabilities


## Impact

- 这是一次“从 0 到 1”的构建，将奠定核心系统的架构根基。所有的代码、CI/CD 构建流水线以及测试套件，此后均运行于本次提交确立的框架中。
- 定义了后续 Phase 1 到 Phase 8 所依赖的核心基础环境，包括全局环境变量模板以及初始配置示范。
