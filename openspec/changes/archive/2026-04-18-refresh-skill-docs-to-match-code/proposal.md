## Why

经过多轮 SITL 调试、field editor 交互修复和 Agent 规范重构后，仓库中的 `SKILL.md`、`AGENTS.md` 与 OpenSpec 说明已经和当前代码行为明显漂移。现在继续沿用这些旧说明，会把后续实现和调试引向错误入口、错误约束和错误流程。

## What Changes

- 全面审计 `.agent/skills/`、`.agent/SKILL_REGISTRY.md` 与 `AGENTS.md`，删除已经失效的旧逻辑描述，补齐当前代码已经落地但文档未同步的规则。
- 将 Skill 路由入口正式收敛到 `.agent/SKILL_REGISTRY.md`，并更新顶层 AI 宪法对 Skill 装载流程的要求。
- 更新模块级 Skill，使其准确描述当前状态链、payload 释放路径、field editor 坐标/投弹点编辑、测试边界、SITL 启动链路与调试闭环。
- 更新与 Skill 内容强绑定的 OpenSpec 能力规格，确保文档合同反映当前代码，而不是最初规划轮的旧结构。
- **BREAKING**: 删除或改写所有仍指向旧状态、旧字段、旧脚本行为、旧注册表位置的说明；今后的 Agent 行为将以收敛后的 Skill/Spec 为唯一依据。

## Capabilities

### New Capabilities
- `skill-registry-routing`: 定义 `.agent/SKILL_REGISTRY.md` 作为 Skill 路由总表、`AGENTS.md` 只保留转接入口的规范

### Modified Capabilities
- `ai-coding-constitution`: 顶层 AI 约束不再维护静态 Skill 路由表，而是要求先读取 `SKILL_REGISTRY`
- `module-skills`: 模块级 Skill 的结构和内容必须和当前代码一致，补充对已知陈旧项的清理要求
- `field-profile`: 场地配置规格补齐 `scan.boundary_margin_m` 与 `attack_run.fallback_drop_point`
- `field-editor-planning-workflow`: 编辑器规划工作流补齐边界余量、降级投弹点和攻击航线预览
- `sitl-environment`: `run_sitl.sh` 的职责更新为拉起 SITL、MAVProxy、Striker，并产出统一日志路径
- `software-only-flight-tuning-loop`: 软件闭环调试流程更新为以 `zjg2` 和当前 `run_sitl.sh` 产物链路为准

## Impact

- 受影响目录：`.agent/skills/`、`.agent/SKILL_REGISTRY.md`、`AGENTS.md`、`openspec/specs/`
- 受影响系统：Agent 路由与规范装载、field editor 场地导出流程、SITL 自动调试闭环、测试规范说明
- 不涉及新的运行时代码能力；重点是删除陈旧文档合同并建立与现状一致的规范基线
