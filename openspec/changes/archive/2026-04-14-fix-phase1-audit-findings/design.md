## Context

AGENTS.md 当前 34 非空行（远低于 100 行上限），有充足的预算补充 R01 示例。R08 路由表已正确列出 `utils-rules` 条目，只缺对应的 SKILL.md 文件。

### 缺陷详情

1. **FAIL-1**: `AGENTS.md` R01 段仅列出抽象类别映射（如"模块/文件: `snake_case`"），但 spec (`ai-coding-constitution/spec.md` line 19) 要求 "concrete examples"，task 2.2 要求 "含正反示例"。
2. **FAIL-2**: R08 路由表第 9 行 `src/striker/utils/` → `utils-rules`，但 `.agent/skills/utils-rules/SKILL.md` 不存在。

## Goals / Non-Goals

**Goals:**
- 为 R01 的 4 个命名类别各补充 ≥1 个正面示例和 ≥1 个反面示例
- 创建 `utils-rules` SKILL.md（三段结构，中文）
- AGENTS.md 总有效行数仍 < 100

**Non-Goals:**
- 不修改其他规则 (R02-R08)
- 不修改 CHARTER.md
- 不修改已有的其他 SKILL.md

## Decisions

### D1: R01 示例采用紧凑内联格式

**选择**: 每个类别用单行 `✓ good_name / ✗ badName` 格式内联示例

**理由**: 行数预算有限（当前 34 行，上限 100），不能为每个类别开辟独立代码块。内联格式每个类别仅需 1 行。

### D2: utils-rules SKILL.md 聚焦工具函数规范

**选择**: utils SKILL 聚焦纯函数工具库的注册、测试和组织标准

**理由**: `src/striker/utils/` 将容纳坐标转换、数据校验、格式化等无副作用的纯工具函数。它不涉及特定业务逻辑，而是被所有模块共享。规范重点在 REGISTRY 注册、无副作用、可测试性。

## Risks / Trade-offs

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| R01 示例导致行数膨胀 | 低 | 低 | 紧凑内联格式，预计增加 4 行 |
| utils-rules 内容在后续 Phase 需更新 | 中 | 低 | SKILL 是可演进的 Markdown 文件 |
