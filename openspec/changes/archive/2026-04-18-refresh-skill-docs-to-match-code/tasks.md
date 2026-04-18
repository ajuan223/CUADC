## 1. 收敛 Skill 路由入口

- [x] 1.1 统一 `AGENTS.md` 与 `.agent/SKILL_REGISTRY.md` 的入口关系，删除残留的旧路由表或旧文件名引用
- [x] 1.2 校对 `.agent/SKILL_REGISTRY.md` 中列出的 Skill 目录与当前 `.agent/skills/` 实际目录一致

## 2. 更新模块级 Skill 内容

- [x] 2.1 审计并更新 `core-fsm-rules`、`payload-release-rules`、`field-editor-rules`，删除与当前状态链、投弹流程、field editor 功能不一致的旧描述
- [x] 2.2 审计并更新 `testing-rules`、`sitl-param-merge-rules`、`sitl-autodebug-loop`，移除弹道/KAT 泛化约束、`sitl_default` 写死路径和过时的 SITL 启动顺序
- [x] 2.3 审计其余 `.agent/skills/*/SKILL.md`，删除已失效字段、脚本职责或模块引用，确保内容与当前代码一致

## 3. 校验规格与文档收敛

- [x] 3.1 更新受影响的 OpenSpec 规格与实际 Skill/代码状态一致，包括 Skill 路由、field profile、field editor 与 SITL 工作流
- [x] 3.2 通过全文搜索校验仓库中不再残留已删除的旧入口、旧字段名和旧流程描述
- [x] 3.3 运行相关文档/规范校验命令并复核变更结果，确认该 change 已达到可实施状态
