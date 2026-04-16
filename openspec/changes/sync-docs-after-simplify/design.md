## Context

`simplify-mission-flow-drop-point` 变更将任务主链从 13 态多循环流简化为 10 态单程流。代码层面已完成并通过 SITL 验证，但配套文档系统存在严重滞后：

- 6 个 AI Agent Skill 规范（`.agent/skills/`）仍描述旧架构，直接影响 Agent 编码行为
- 用户手册（`docs/user_manual.md`）的状态流转图和配置表仍反映旧流程
- 项目宪章（`CHARTER.md`）的 OKR 和红线引用已删除的功能
- OpenSpec live specs 引用已删除的配置字段和语义
- 开发计划文档（`meta_development_plan.md`）和愿景文档（`init愿景.md`）大量描述旧架构

本 change 是纯文档同步，不涉及代码变更。

## Goals / Non-Goals

**Goals:**
- 所有 Skill 规范与实际代码架构一致，AI Agent 不会因过期文档写出错误代码
- 用户手册准确反映 10 态单程流和投弹点语义
- 宪章 OKR 和红线与实际能力匹配
- OpenSpec live specs 不再引用已删除的字段和功能
- 能力注册表填充当前可用能力

**Non-Goals:**
- 不重构文档体系或格式
- 不修改任何代码
- 不修改 `openspec/changes/archive/` 中的已归档 change（历史记录）
- 不修改 `batch-phase3-through-8/` 等已完成但未归档的 change 文档

## Decisions

### D1: Skill 规范采用"重写而非修补"策略

**决定**: `vision-interface-rules` 和 `payload-release-rules` 整篇重写，其他 4 个 Skill 局部修改。

**理由**: 这两个 Skill 的核心语义已完全改变——vision 从"接收靶标坐标"变为"接收投弹点"，payload 从"弹道解算+强制投弹"变为"仅保留释放控制"。局部修补会导致行文不连贯，不如重写。

**备选**: 全部局部修补 → 放弃，因为 payload-rules 整篇围绕已删除功能展开。

### D2: 历史文档直接更新而非标注 deprecated

**决定**: `meta_development_plan.md` 和 `init愿景.md` 中过时内容直接删除/替换为当前架构描述。

**理由**: 用户明确要求。这两份文档是开发参考而非 git 历史记录，保留旧流程描述只会造成混淆。

### D3: `loiter_point` 保留在场地配置 spec 中

**决定**: 场地配置数据模型中的 `loiter_point` 字段保留不动，因为它仍在 `field_profile.py` 中定义且可能用于未来任务规划。但文档中不再将其描述为"SCAN 完成后进入盘旋"的依据。

**理由**: 删除 `LoiterPointConfig` 会破坏现有 JSON 配置文件的兼容性，而场地配置的 cleanup 是独立 concern。

### D4: CHARTER.md 红线调整

**决定**: 删除 RL-10（Forced-strike 围栏内校验），因为强制投弹功能已不存在。保留其余 9 条红线，措辞不变。

**备选**: 重新编号 RL-11→RL-10 → 放弃，避免与已有引用冲突，直接删除 RL-10 并留空即可。

### D5: 能力注册表注册范围

**决定**: 只注册新创建或重命名的公共能力（`compute_fallback_drop_point`、`DropPointTracker`、`GpsDropPoint`、`MAVLinkConnection.flightmode`、`MissionContext.set_drop_point`、`MissionContext.update_mission_seq`），不重新注册所有已有能力。

**理由**: 注册表当前为空，一次性注册所有能力工作量过大且非本 change 目标。

## Risks / Trade-offs

- **[遗漏]** 文档量大，可能遗漏个别过期引用 → 最终实施后全仓库 grep 验证
- **[Skill 行为变更]** AI Agent 依据更新后的 Skill 写码时可能产生与旧代码风格的差异 → 这是期望行为，旧风格正是被简化的对象
- **[Red Line 编号]** 删除 RL-10 后编号不连续 → 可接受，重新编号风险更大
