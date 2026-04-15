## Context

Phase 1 分组 1a 已交付 CHARTER.md（L0 宪章）和 AGENTS.md（L1 宪法，34 有效行）。AGENTS.md 中 R08 定义了 Skill 路由表，将 9 个 `src/striker/` 子目录映射到对应的 `.agent/skills/` SKILL.md 文件，但这些 L2 Skill 文件尚不存在。

当前 `.agent/skills/` 目录仅包含 OpenSpec 工作流技能（openspec-apply-change 等），没有任何业务模块治理技能。

### 约束

- 所有 SKILL.md 内容**必须用中文编写**（用户明确要求）
- 每个 SKILL.md 必须包含三段：架构约束、注册模式、禁止模式
- SKILL.md 无行数限制（与 AGENTS.md 不同），但应保持聚焦
- 9 个模块 Skill 可并行创建，相互无依赖
- REGISTRY.md 初始为空表（各模块实现时自行注册）

### 源码目录与 Skill 映射（来自 AGENTS.md R08）

| 源码目录 | Skill 名称 | Phase 来源 |
|----------|-----------|-----------|
| `src/striker/core/` | `core-fsm-rules` | Phase 4 |
| `src/striker/comms/` | `comms-mavlink-rules` | Phase 3 |
| `src/striker/flight/` | `flight-control-rules` | Phase 5 |
| `src/striker/safety/` | `safety-monitor-rules` | Phase 4 |
| `src/striker/vision/` | `vision-interface-rules` | Phase 6 |
| `src/striker/payload/` | `payload-release-rules` | Phase 7 |
| `src/striker/config/` | `config-system-rules` | Phase 2 |
| `src/striker/telemetry/` | `telemetry-rules` | Phase 4b |
| `src/striker/utils/` | `utils-rules` | 跨 Phase |

额外：
- `.agent/skills/field-profile-rules/` — 场地配置（Phase 2，v2.2 新增独立模块）
- `.agent/skills/testing-rules/` — 测试规范（跨 Phase）
- `.agent/skills/capability-registry/` — 能力注册（含 REGISTRY.md）

## Goals / Non-Goals

**Goals:**
- 创建 9 个模块 SKILL.md + testing-rules + capability-registry（共 11 个 SKILL.md）
- 创建 REGISTRY.md 初始空表
- 每个 SKILL.md 包含：架构约束、注册模式、禁止模式
- 所有内容用中文编写

**Non-Goals:**
- 不修改 AGENTS.md（路由表已在 1a 中完成）
- 不修改任何 Python 源码
- 不创建实际的 Python 模块实现
- 不定义具体的 pydantic schema / dataclass 结构（那是各 Phase 实现时的职责）

## Decisions

### D1: SKILL.md 标准结构

**选择**: 每个 SKILL.md 采用统一三段结构：

```
# {模块名} 编码规范

## 架构约束
- 本模块在整体架构中的定位和职责边界
- 依赖关系（可依赖谁，被谁依赖）
- 数据流向

## 注册模式
- 模块需要向 REGISTRY.md 注册的能力
- 注册格式示例

## 禁止模式
- 明确不允许的编码行为
- 常见陷阱和反模式
```

**理由**: 三段结构确保每个 Skill 既有正面指导（架构约束、注册模式），又有负面约束（禁止模式），形成完整的编码护栏。

### D2: telemetry-rules 与 config-system-rules 分离

**选择**: telemetry-rules 独立于 config-system-rules

**理由**: meta_development_plan.md 中 telemetry（Phase 4b）与 config（Phase 2）属于不同 Phase，职责边界清晰。telemetry 聚焦 structlog 配置和 GCS 报告格式，config 聚焦三层配置和 pydantic-settings。

### D3: field-profile-rules 独立 SKILL

**选择**: 单独创建 field-profile-rules SKILL（meta_development_plan v2.2 新增）

**理由**: 场地配置（围栏、跑道、安全区域）是固定翼无人机特有的关键数据模型，涉及复杂校验逻辑（point_in_polygon、跑道方向、安全高度），值得独立规范。它由 config 模块引用但逻辑自洽。

### D4: capability-registry 同时包含 SKILL.md 和 REGISTRY.md

**选择**: 在 `.agent/skills/capability-registry/` 下同时放置 SKILL.md（注册规范）和 REGISTRY.md（能力清单）

**理由**: AGENTS.md R06 要求实现通用函数前必查 REGISTRY.md。将注册规范和清单放在同一目录下，保持内聚性。REGISTRY.md 初始为空表（含表头），各模块实现时按 SKILL.md 中的注册模式填充。

### D5: testing-rules 覆盖全项目

**选择**: testing-rules 不绑定到特定 `src/striker/` 子目录，而是作为跨模块的测试规范

**理由**: 测试规范适用于所有模块（asyncio 测试模式、mock 边界、SITL 集成测试策略），不局限于某一个业务目录。它通过 Skill 路由表之外的通用引用机制被加载。

## Risks / Trade-offs

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| SKILL.md 内容与后续 Phase 实际实现不一致 | 中 | 低 | 各 Phase 实现时可更新对应 SKILL；SKILL 是指导而非不可变约束 |
| 11 个 SKILL 维护成本高 | 低 | 低 | SKILL 是 Markdown 文件，更新成本低；且每个聚焦单一模块 |
| testing-rules 中的 asyncio 模式可能随 Python 版本变化 | 低 | 低 | 项目锁定 Python 3.13；重大变化时更新 SKILL |
| REGISTRY.md 初始为空可能导致早期开发忽略注册 | 中 | 低 | 各模块 SKILL.md 的"注册模式"段会提醒开发者注册 |
