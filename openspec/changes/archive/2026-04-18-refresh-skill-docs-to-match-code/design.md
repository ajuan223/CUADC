## Context

当前仓库已经经历了多轮运行时和工具链演化，但 `.agent/skills/`、`AGENTS.md` 和 OpenSpec 的部分描述仍停留在更早的规划形态。已确认的漂移包括：

- Skill 路由表已从 `AGENTS.md` 正文迁出，但顶层规范与命名仍未完全收敛
- `run_sitl.sh` 已从“只起 SITL + MAVProxy”演化为“起完整链路并产生日志目标”，相关 Skill 仍按旧启动顺序描述
- `field_profile` 和 field editor 已支持 `scan.boundary_margin_m`、`attack_run.fallback_drop_point`，但规格和部分 Skill 未同步
- `testing-rules`、`sitl-param-merge-rules` 等仍保留与当前代码/流程不一致的旧约束

这不是单点文案修补，而是横跨 Agent 入口、模块级 Skill、SITL 流程和 field editor 的文档收敛问题。

## Goals / Non-Goals

**Goals:**
- 建立单一 Skill 路由入口，避免与能力注册表 `REGISTRY.md` 混名
- 让 `.agent/skills/*.md` 的约束与当前代码结构、字段、脚本职责一致
- 让 OpenSpec 对 Skill 体系、field editor 规划输出、SITL 调试链路和场地字段模型的要求回到当前事实
- 为后续“文本收敛轮”提供稳定基线，减少 Agent 被旧文档误导

**Non-Goals:**
- 不在本次变更中引入新的运行时功能
- 不修改飞行控制、安全约束或场地运行参数本身
- 不尝试在本次变更中重新设计 Skill 体系，只做与现状对齐的收敛

## Decisions

### 1. Skill 路由与能力注册分离命名
采用 `.agent/SKILL_REGISTRY.md` 作为 Skill 路由总表，保留 `.agent/skills/capability-registry/REGISTRY.md` 作为能力注册表。

原因：
- 两者语义不同，一个负责“加载哪个 Skill”，一个负责“复用哪个能力”
- 继续共用 `REGISTRY.md` 名称会造成持续误读

备选方案：
- 继续使用 `.agent/REGISTRY.md`
  - 放弃，原因是和 capability-registry 的 `REGISTRY.md` 冲突太强

### 2. 以“代码事实优先”审计所有 Skill
所有模块级 Skill 以当前代码、字段和脚本职责为准，不保留为了兼容旧规划而存在的说明。

原因：
- 文档系统的价值在于约束后续实现，而不是保存已经失效的历史路线
- 本轮的目标就是文本收敛，不是保留旧提法

备选方案：
- 在 Skill 中同时保留“历史做法”和“当前做法”
  - 放弃，原因是会继续污染 Agent 装载时的第一上下文

### 3. 将文档漂移拆回已有能力规格，而不是新增一个“大杂烩”规格
本次只新增 `skill-registry-routing`，其余变化回写到已有能力：`ai-coding-constitution`、`module-skills`、`field-profile`、`field-editor-planning-workflow`、`sitl-environment`、`software-only-flight-tuning-loop`。

原因：
- 漂移点分别落在不同系统边界，拆回原能力更容易长期维护
- OpenSpec delta spec 应该描述“哪个能力变了”，而不是“我们修了一批文档”

备选方案：
- 新增一个 `skill-doc-convergence` 总规格
  - 放弃，原因是无法清晰绑定到已有运行/工具能力

### 4. 把已确认的陈旧项直接上升为规范约束
本次规格中会显式约束以下失真项必须被删除或更新：

- `AGENTS.md` 不再维护静态 Skill 路由表正文
- `testing-rules` 不再把弹道/KAT 当成通用强约束
- `sitl-param-merge-rules` 不再把输出固定写到 `data/fields/sitl_default/sitl_merged.param`
- `sitl-autodebug-loop` 必须反映当前 `run_sitl.sh` 的实际职责和日志产物
- field editor / field profile 必须覆盖 `boundary_margin_m` 与 `fallback_drop_point`

原因：
- 这些问题已经通过代码和现状核对被证实，不再是推测

## Risks / Trade-offs

- [规范覆盖面大] → 用少量新增要求覆盖高风险漂移点，不在一轮里重写无争议的 Skill 内容
- [历史 OpenSpec 仍保留旧表述] → 本轮只修改当前生效 specs，不批量清理 archive 内容
- [文档先于代码继续演化] → 通过把“与现状一致”写进 module-skills 和 ai-coding-constitution 约束，降低再次漂移概率
- [SITL 工作流仍可能继续变化] → 在 sitl-environment / tuning-loop 中描述职责和产物，而不是绑定临时命令细节
