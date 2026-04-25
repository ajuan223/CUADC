## Why

随着系统功能向“场地事实驱动程序化任务生成”和 SITL 验证不断演进，尤其在 v0.0.3 引入诸多配置项（`cruise_speed_mps`、`boundary_margin_m`、`fallback_drop_point` 优先级降级策略）后，当前的核心使用手册、架构说明文档已严重滞后。此外，部分早期联调日志与探索文档（如 HIL 方案评估）留在文档根目录下导致信息冗余，不利于后续开发与维护。本次更改致力于清理与归档历史文档，并对齐现存核心文档与最新代码架构，从而在保持现有 AI 宪法 (`AGENTS.md`) 框架和项目宪章 (`CHARTER.md`) 的前提下，防止架构细节丢失，并保证资料的准确指导性。

## What Changes

- **文档归档机制**: 新建 `docs/archive/` 目录，将历史特定时点的测试报告和探索期愿景文档移入其中。
- **更新 `docs/user_manual.md`**: 补齐 `cruise_speed_mps`、`boundary_margin_m`、`fallback_drop_point` 配置项，并同步全新的三级降级投弹点优先级决策（外部视觉传入 → field.json 降级点 → 几何质心）。
- **更新 `init愿景.md`**: 同步架构愿景中关于投弹点降级的策略。
- **更新 `data/fields/README.md`**: 将最新的场地 schema (含 `fallback_drop_point` 和 `boundary_margin_m`) 补充到文档中。
- **删除/归档历史文档**: 将 `HIL愿景.md`、`docs/user_manual_testrez.md`、`docs/sitl_integration_results.md` 移入 `docs/archive/`。

## Capabilities

### New Capabilities
- `docs-archiving`: 历史与过时文档安全隔离机制，避免影响现有开发。
- `docs-alignment`: 文档同步对齐机制，确保用户手册与代码配置行为一致。

### Modified Capabilities

## Impact

- **Documents**: `docs/user_manual.md`, `init愿景.md`, `data/fields/README.md`。
- **File Structure**: 新增 `docs/archive/` 目录，原根目录的 `HIL愿景.md` 及其它测试日志移除并归档。
- **开发者体验**: 消除过时文档带来的歧义，维持 AI Agent Prompt 背景文档（如宪法）的纯洁性与时效性。
