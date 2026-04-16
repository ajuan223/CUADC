## Why

`simplify-mission-flow-drop-point` 变更将状态机从 `scan → loiter → forced_strike` 旧流程重构为 `scan → drop-point-routing → release → landing` 新流程。在代码修改完成后，必须在本地 SITL 环境中进行一次全链路 dry-run 联调，验证从起飞、扫场、投弹点决策、转场投放、降落到完成的完整任务链路。当前 SITL 环境存在路径错误（plane.parm 缺失）、MAVProxy 未安装、视觉和航点数据需要 mock 等问题，需要一套明确的联调策略和 SITL/MAVProxy debug 指南，使 Claude Code 在后续 dry-run 中能自主诊断和修复 SITL 连接、飞控模式切换、mission upload、航点执行等环节的常见故障。

## What Changes

- **修复 SITL 环境基础**：修正 plane.parm 路径引用（实际位于 `~/ardupilot/Tools/autotest/models/plane.parm`），确认 arduplane 二进制可用，安装 MAVProxy（`pip install MAVProxy`），确保 `sim_vehicle.py` 或直接启动 arduplane SITL 可正常监听 `udp:127.0.0.1:14550`。
- **建立 Mock 数据策略**：为视觉投弹点（TCP/UDP mock server 发送 WGS84 坐标）、扫场航点（已有 `data/fields/sitl_default/field.json`）、地图/边界（已有 field.json boundary）定义确定的 mock 方案，使 dry-run 不依赖外部硬件或真实视觉系统。
- **定义全量 Dry-Run 策略**：分阶段验证 init → preflight → takeoff → scan → drop-point-routing → release(dry) → landing → completed 的完整链路，每个阶段定义通过/失败判定标准、可观测日志断言、超时容忍度。
- **编写 SITL/MAVProxy Debug Spec**：针对 Ubuntu 上 ArduPlane SITL + pymavlink 连接的常见故障模式（无心跳、模式切换失败、mission upload 超时、MISSION_ITEM_REACHED 不触发、GUIDED goto 无效等），定义结构化 debug 方法论，使 Claude Code 能按步骤定位和修复。

## Capabilities

### New Capabilities
- `sitl-environment-setup`: SITL 环境修复与验证，包括二进制、参数文件、MAVProxy 安装、UDP 端口连通性检查
- `mock-data-strategy`: 视觉投弹点 mock server、航点 mock、地图/边界 mock 的实现方案与使用方法
- `dryrun-validation-strategy`: 全链路 dry-run 分阶段策略，定义每个状态迁移的通过标准和可观测断言
- `sitl-debug-guide`: SITL/MAVProxy 故障 debug spec，覆盖连接、心跳、模式、mission upload、航点执行等常见故障模式的结构化排查流程

### Modified Capabilities
<!-- 无现有 spec 需要修改 -->

## Impact

- **测试基础设施**：`tests/integration/conftest.py` 需修正 plane.parm 路径；可能需新增 SITL 启动/停止 fixture
- **开发依赖**：需确认 `MAVProxy` 包安装到正确 venv（`ardupilot-venv` 或项目 `.venv`）
- **配置**：`data/fields/sitl_default/field.json` 可能需微调航点坐标以适配 SITL 模拟环境
- **运行时环境**：需要 `~/ardupilot/build/sitl/bin/arduplane` 二进制可执行；SITL 监听 `udp:127.0.0.1:14550`；striker 通过 `STRIKER_TRANSPORT=udp STRIKER_MAVLINK_URL=udp:127.0.0.1:14550` 连接
- **CI/本地测试**：集成测试将从 skip 状态变为可执行
