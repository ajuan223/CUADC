## Why

Phase 0 已交付可构建、可测试的项目骨架，但目前项目层面**没有任何 AI 编码约束**——既没有宪法级规范 (`AGENTS.md`) 约束 AI Agent 的行为边界，也没有项目宪章 (`CHARTER.md`) 定义 OKR 与 Red Lines。
在 Phase 2+ 开始写业务代码之前，必须**先注入刚性治理体系**，否则 AI 生成的代码将面临：命名不一致、类型标注缺失、日志格式混乱、循环依赖蔓延、pymavlink 泄漏到上层等灾难性熵增。

本 Change 聚焦 Phase 1 的 **Tier-1 宪法级治理** (分组 1a)，为后续 Tier-2 模块 Skills 提供顶层框架。

## What Changes

- **新增** `CHARTER.md` — 项目宪章，定义 OKR、使命、Red Lines、关键约束
- **新增** `AGENTS.md` — AI 宪法级规范 (<100 行有效指令)，包含：
  - 命名约定 (snake_case modules, PascalCase classes, UPPER_SNAKE constants)
  - 类型标注强制 (`--strict` mypy)
  - Import 顺序 (stdlib → third-party → local)
  - 日志规范 (structlog only, no print)
  - Skill 路由表 (哪些目录触发哪个 SKILL.md)
  - 严禁盲目落码规则 / 能力发现优先规则
  - 包治理与防腐墙 (pkg/ 规则)
- **新增** `AGENTS.local.md` — 个人覆盖模板 (gitignored)，允许开发者覆盖部分规范
- **新增** `.gitignore` 条目 — 确保 `AGENTS.local.md` 被忽略

## Capabilities

### New Capabilities
- `project-charter`: 项目宪章 — 定义 Striker 项目的 OKR、使命声明、Red Lines、关键安全约束 (10 条不可违反规则)
- `ai-coding-constitution`: AI 宪法级编码规范 — 命名、类型、日志、Import、Skill 路由表、严禁盲目落码、能力发现优先、包治理防腐墙，<100 行有效指令约束

### Modified Capabilities
_(无 — 这是项目第一批治理文件，不修改已有 spec)_

## Impact

- **代码影响**: 无代码变更，纯文档/规范文件
- **后续 Phase 依赖**: 所有后续 Phase (2-8) 的 AI 编码行为将受 `AGENTS.md` 约束
- **Tier-2 前置**: `governance-tier2-skills` Change 将基于 `AGENTS.md` 中的 Skill 路由表，创建 9 个模块级 SKILL.md
- **CI 影响**: 未来 Phase 8 的 CI 管线将包含 `AGENTS.md` 合规检查
- **`.gitignore`**: 需追加 `AGENTS.local.md` 条目
