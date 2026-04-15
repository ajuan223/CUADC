## Why

Phase 1 合规审计发现 2 个缺陷：(1) AGENTS.md R01 命名约定缺少 spec 和 tasks 要求的正反示例；(2) AGENTS.md R08 路由表将 `src/striker/utils/` 映射到 `utils-rules`，但该 SKILL.md 文件不存在。这些缺陷导致 AI Agent 在触及 `utils/` 目录时无规范可循，且命名规则缺乏可操作性。

## What Changes

- **修改** `AGENTS.md` R01 — 为每个命名类别补充具体的正/反示例
- **新增** `.agent/skills/utils-rules/SKILL.md` — 工具函数模块编码规范（架构约束 + 注册模式 + 禁止模式，中文）

## Capabilities

### New Capabilities

- `utils-skill`: `utils/` 模块编码规范 — 工具函数的注册、组织、测试标准

### Modified Capabilities

_(无新 capability 修改。AGENTS.md 的变更是对已有 R01 规则的补充示例，不改变 spec 级行为定义。)_

## Impact

- **AGENTS.md**: R01 段落行数增加，但总有效行数仍需 < 100
- **`.agent/skills/utils-rules/`**: 新增 1 个 SKILL.md 文件
- **路由表**: 无需变更（已有 `utils-rules` 条目，只是缺文件）
- **无代码变更**: 纯文档修改
