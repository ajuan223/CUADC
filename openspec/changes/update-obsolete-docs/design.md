## Context

Striker 项目刚刚经历了从多阶段过渡态向"场地事实驱动程序化任务生成" (field-driven procedural mission generation) 的重构。随后，v0.0.3 在此基础上增加了多个场地/运行时参数（如 `boundary_margin_m`、`fallback_drop_point` 和 `cruise_speed_mps`），并细化了投弹点兜底优先级策略。然而，核心文档和规范（`docs/user_manual.md`, `init愿景.md`, `data/fields/README.md`）并没有跟随代码更新，而某些早期愿景文档（如 `HIL愿景.md`）仍占据在根目录，造成了理解干扰。在此之前需要把它们整理好，防止关键概念和使用方法缺失。

## Goals / Non-Goals

**Goals:**
- 提供最新的 `field.json` schema 配置文档和机制说明。
- 在用户手册和架构愿景中正确反映当前系统中使用的“三级投弹点优先级”策略。
- 归档干扰性质的历史记录。

**Non-Goals:**
- 不涉及核心代码或组件架构的重构。
- 不对 `AGENTS.md` (AI 宪法) 或 `CHARTER.md` (项目宪章) 的顶层原则进行结构性破坏。

## Decisions

- **建立历史隔离区 (Docs Archive):** 鉴于过往文档包含宝贵的决策上下文（如为何不用 HIL），不应直接删除，而是移入 `docs/archive/`。
- **使用单一信息源原则:** 更新文档时，直接反映 `v0.0.3` 所添加的 `boundary_margin_m` 等字段在 `field.json` 及其对任务程序化生成的直接影响，并在 `user_manual.md` 中做主要维护，`init愿景.md` 则简要提纲挈领。

## Risks / Trade-offs

- **Risk**: 移动文档可能导致现有外部链接失效。
  - **Mitigation**: 本项目为相对私有封闭工程，且受众为核心开发或同平台工具，移动时直接在 Git 中进行 rename/move 即可，副作用较小。
