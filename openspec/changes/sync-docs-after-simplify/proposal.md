## Why

`simplify-mission-flow-drop-point` 变更已通过 SITL 双路径验证并合入主分支，但配套文档、AI Agent Skill 规范和 OpenSpec live spec 仍描述旧的多循环 scan↔loiter→forced_strike 架构。AI Agent 依据过期 Skill 规范写码会导致错误代码；用户手册和项目宪章描述的 OKR / 红线 / 状态流转图与实际代码严重不符。

## What Changes

- **BREAKING** 删除所有对 LOITER、FORCED_STRIKE、APPROACH 状态及其转移的文档描述
- **BREAKING** 将所有 `GpsTarget` / `TargetTracker` / `target_tracker` / `last_target` / `弹道解算主流程` 的文档引用替换为 `GpsDropPoint` / `DropPointTracker` / `drop_point_tracker` / `active_drop_point` / `视觉直给投弹点`
- 更新 `.agent/skills/` 下 6 个 SKILL.md 以反映简化后的架构
- 更新 `docs/user_manual.md` 状态机章节（状态流转图、状态说明表、配置字段表、视觉章节、投放章节）
- 更新 `CHARTER.md` OKR 和红线（删除 KR2.3、KR4.3、RL-10，修正措辞）
- 更新 `AGENTS.md` 常量示例
- 更新 `openspec/specs/` 下 4 个 live spec（config-system、project-framework、utils-skill、sitl-default-field）
- 重写 `meta_development_plan.md` 和 `init愿景.md`，直接用当前架构替换旧内容
- 填充 `REGISTRY.md` 能力注册表

## Capabilities

### New Capabilities

（无新增能力，本 change 纯粹同步文档）

### Modified Capabilities

- `config-system`: 配置字段列表删除 loiter/forced_strike 相关字段，target_tracker→drop_point_tracker
- `project-framework`: 配置字段列表同步
- `utils-skill`: 删除 forced_strike_point 需求，删除 ApproachState 弹道传递需求
- `module-skills`: 更新 6 个 SKILL.md 的架构描述、注册表和禁止模式
- `capability-registry`: 填充新能力注册
- `project-charter`: OKR 和红线修正

## Impact

- 影响: `.agent/skills/`（6 个文件）、`docs/`（user_manual.md）、`CHARTER.md`、`AGENTS.md`、`openspec/specs/`（4+ 个文件）、`meta_development_plan.md`、`init愿景.md`、`REGISTRY.md`
- 无代码变更，纯文档同步
- AI Agent 编码行为将基于正确的 Skill 规范
