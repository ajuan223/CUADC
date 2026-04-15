## Why

Phase 1 分组 1a 已交付 L0 宪章 (`CHARTER.md`) 和 L1 宪法 (`AGENTS.md`)，但 AGENTS.md 受 <100 行预算限制，仅包含高层规则编号和 Skill 路由表。AI Agent 触及具体模块目录时（如 `src/striker/comms/`、`src/striker/core/`）缺乏架构约束、注册模式和禁止模式等模块级编码指导，无法产出符合 Striker 架构设计的代码。

本 Change 补齐 Phase 1 分组 1b —— 创建 9 个模块级 SKILL.md + 能力注册中心（REGISTRY.md），完成三层渐进式治理架构的最后一级。

## What Changes

- **新增** `.agent/skills/core-fsm-rules/SKILL.md` — 状态机模块编码规范（FSM 引擎、事件系统、状态注册）
- **新增** `.agent/skills/comms-mavlink-rules/SKILL.md` — MAVLink 通信层编码规范（连接管理、心跳、消息封装、遥测解析）
- **新增** `.agent/skills/flight-control-rules/SKILL.md` — 飞行指令模块编码规范（航点、扫描、起降序列）
- **新增** `.agent/skills/safety-monitor-rules/SKILL.md` — 安全监控模块编码规范（围栏校验、心跳监控、Override 处理）
- **新增** `.agent/skills/vision-interface-rules/SKILL.md` — 视觉接口模块编码规范（外部求解器链接、坐标转换）
- **新增** `.agent/skills/payload-release-rules/SKILL.md` — 载荷投弹模块编码规范（弹道解算、释放控制、强制投弹）
- **新增** `.agent/skills/config-system-rules/SKILL.md` — 配置系统编码规范（三层配置、pydantic-settings、场地配置）
- **新增** `.agent/skills/field-profile-rules/SKILL.md` — 场地配置编码规范（围栏、跑道、安全区域数据模型与校验）
- **新增** `.agent/skills/testing-rules/SKILL.md` — 测试编码规范（asyncio 测试、SITL 集成、KAT 测试）
- **新增** `.agent/skills/capability-registry/SKILL.md` — 能力注册规范（注册/查询流程）
- **新增** `.agent/skills/capability-registry/REGISTRY.md` — 能力清单（初始为空表，后续各模块注册时填充）

## Capabilities

### New Capabilities

- `module-skills`: 9 个模块级 SKILL.md，每个包含架构约束 (Architecture Constraints)、注册模式 (Registration Pattern)、禁止模式 (Forbidden Patterns)，为 AI Agent 提供按需加载的模块编码指导
- `capability-registry`: 能力注册中心 — REGISTRY.md 清单文件 + SKILL.md 注册规范，防止重复造轮子

### Modified Capabilities

_(无 — 这是纯新增的 L2 治理文件，不修改已有 spec)_

## Impact

- **代码影响**: 无 Python 源码变更，纯 `.agent/skills/` 目录下的 Markdown 文件
- **AGENTS.md 依赖**: R05 (严禁盲目落码) 和 R06 (能力发现优先) 的落地机制
- **后续 Phase 依赖**: Phase 2-8 的 AI 编码行为将按需加载对应模块 SKILL
- **验证标准**: 每个 SKILL.md 必含 Architecture Constraints、Registration Pattern、Forbidden Patterns 三段
