## 1. AI Agent Skill 规范更新

- [x] 1.1 重写 `.agent/skills/vision-interface-rules/SKILL.md`：`GpsTarget` → `GpsDropPoint`，`TargetTracker` → `DropPointTracker`，删除 `forced_strike_point` 引用，更新依赖关系（`loiter.py` → `scan.py`），更新数据流描述
- [x] 1.2 重写 `.agent/skills/payload-release-rules/SKILL.md`：删除弹道解算主流程描述，删除强制投弹流程，删除 `generate_random_point_in_polygon` 注册，更新禁止模式为仅保留释放控制相关约束
- [x] 1.3 更新 `.agent/skills/core-fsm-rules/SKILL.md`：将架构描述从 13 态改为 10 态简化链，确保状态链描述为 `init→preflight→takeoff→scan→enroute→release→landing→completed + override + emergency`
- [x] 1.4 更新 `.agent/skills/safety-monitor-rules/SKILL.md`：OverrideDetector 默认模式集合补充 `FBWA`，说明模式检测使用 `connection.flightmode` 属性，标注实际已接通的检查项（heartbeat + override）
- [x] 1.5 更新 `.agent/skills/field-profile-rules/SKILL.md`：从"被依赖"列表中删除 `payload/`(强制投弹) 引用
- [x] 1.6 更新 `.agent/skills/testing-rules/SKILL.md`：删除"弹道解算禁止 mock"禁止模式，更新测试分层策略示例（删除弹道解算示例），删除"围栏内随机点生成测试"

## 2. 用户手册更新

- [x] 2.1 更新 `docs/user_manual.md` 第 3.4 节配置字段表：删除 `loiter_radius_m`、`loiter_timeout_s`、`max_scan_cycles`、`forced_strike_enabled` 四行
- [x] 2.2 重写 `docs/user_manual.md` 第 6 节任务状态机：将 13 态改为 10 态，更新状态流转图（删除 LOITER↔SCAN 循环、FORCED_STRIKE、APPROACH），更新状态说明表（删除 LOITER/APPROACH/FORCED_STRIKE 行），新增 scan 完成后投弹点决策分支描述
- [x] 2.3 更新 `docs/user_manual.md` 第 7 节安全监控：飞控模式行补充 FBWA，说明使用 `connection.flightmode`
- [x] 2.4 更新 `docs/user_manual.md` 第 8 节视觉系统：`TargetTracker` → `DropPointTracker`，删除"LOITER 状态消费目标"，改为"scan 状态完成投弹点决策"
- [x] 2.5 重写 `docs/user_manual.md` 第 9.4 节弹道计算：删除弹道解算描述，替换为"视觉投弹点直给 + 兜底中点"说明
- [x] 2.6 更新 `docs/user_manual.md` 第 13 节故障排查：删除"LOITER 等待目标"相关排查提示，更新状态机不推进的排查说明

## 3. 项目宪章与编码规范更新

- [x] 3.1 更新 `CHARTER.md` 使命描述："目标锁定与载荷投放" → "投弹点决策与载荷投放"
- [x] 3.2 删除 `CHARTER.md` KR2.3（SCAN↔LOITER 超时重扫循环正确执行率）
- [x] 3.3 删除 `CHARTER.md` KR4.3（强制投弹随机点 100% 落在围栏内）
- [x] 3.4 删除 `CHARTER.md` RL-10（Forced-strike 围栏内校验）
- [x] 3.5 更新 `AGENTS.md` 第 R01 节常量示例：`MAX_SCAN_CYCLES` → 其他现存常量（如 `HEARTBEAT`、`MISSION_ITEM_REACHED`）

## 4. OpenSpec Live Specs 更新

- [x] 4.1 更新 `openspec/specs/config-system/spec.md`：配置字段列表删除 `loiter_radius_m`、`loiter_timeout_s`、`max_scan_cycles`、`forced_strike_enabled`；`target_tracker.push()` → `drop_point_tracker.push()`；`GpsTarget` → `GpsDropPoint`；删除 forced_strike 源状态场景
- [x] 4.2 更新 `openspec/specs/project-framework/spec.md`：配置字段列表删除已移除字段
- [x] 4.3 更新 `openspec/specs/utils-skill/spec.md`：删除 `forced_strike_point` 需求及其场景；删除 `ApproachState` 弹道传递需求；新增 `compute_fallback_drop_point` 需求
- [x] 4.4 检查 `openspec/specs/field-profile/spec.md` 和 `openspec/specs/sitl-default-field/spec.md`：确认 `loiter_point` 相关描述与场地配置保留决策一致

## 5. 开发计划与愿景文档重写

- [x] 5.1 重写 `meta_development_plan.md`：删除所有 scan↔loiter 循环、弹道解算主流程、强制投弹降级、FORCED_STRIKE 状态、ApproachState、TargetTracker、GpsTarget 的描述；用当前 10 态单程投弹流架构替换；更新配置字段列表；更新文件目录树
- [x] 5.2 重写 `init愿景.md`：删除旧的多循环流程图和弹道模型描述；用当前架构替换状态流转图、配置示例、数据流图；更新所有代码示例中的类名和字段名

## 6. 能力注册表填充

- [x] 6.1 在 `.agent/skills/capability-registry/REGISTRY.md` 中注册：`compute_fallback_drop_point()`、`DropPointTracker`、`GpsDropPoint`、`MAVLinkConnection.flightmode`、`MissionContext.set_drop_point()`、`MissionContext.update_mission_seq()`
- [x] 6.2 确认 `REGISTRY.md` 中不包含已删除能力的条目

## 7. 验证

- [x] 7.1 全仓库 grep 检索：确认 `GpsTarget`、`TargetTracker`、`target_tracker`、`last_target`、`forced_strike_point`、`FORCED_STRIKE`、`ApproachState`、`Approach`（作为状态名）在文档和 spec 中不再出现
- [x] 7.2 验证 `meta_development_plan.md` 和 `init愿景.md` 不再包含旧流程描述
- [x] 7.3 验证所有 Skill 规范的"禁止模式"列表不包含对已删除功能的约束
