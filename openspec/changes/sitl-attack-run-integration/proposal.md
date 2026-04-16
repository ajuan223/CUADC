## Why

`attack-run-precision-drop` 变更已完成 enroute 状态重写（GUIDED → AUTO 攻击跑）、DO_SET_SERVO 原生释放、mission seq 监控等核心代码修改。任务 4.5 和 7.x 标记为未完成，需要在 SITL 中验证新的攻击跑全链路：init → preflight → takeoff → scan → enroute(attack run AUTO) → release → landing → completed。现有的 `sitl-dryrun-debug-spec` 定义了旧 GUIDED 流程的联调策略，需要更新以适配攻击跑的新行为（AUTO 任务上传、mission_current_seq 监控、DO_SET_SERVO 时机验证）。

## What Changes

- **更新 dry-run 联调策略**：将 Phase 4 (drop-point routing) 从 GUIDED goto 验证改为攻击跑 AUTO 任务验证，包括 approach/target/exit 航点上传、MISSION_SET_CURRENT 触发、mission_current_seq 推进监控
- **新增攻击跑 SITL 验证 spec**：定义 attack run 特有的验证点——approach heading 计算、approach/exit 坐标正确性、target waypoint 通过时 DO_SET_SERVO 执行时机、mission seq 推进时序
- **更新 mock 数据策略**：mock_vision_server 需发送位于 field boundary 内的投弹点，且坐标需使攻击跑 approach/exit 点不出界
- **更新 SITL debug guide**：新增攻击跑相关故障模式——AUTO 模式切换失败、attack mission upload 失败、MISSION_SET_CURRENT 无效、mission_current_seq 不推进、DO_SET_SERVO 未执行
- **更新日志断言**：enroute 阶段日志从 "GUIDED" / "goto" 改为 "attack run mission uploaded"、"approach heading"、"mission_current_seq" 等攻击跑特有日志

## Capabilities

### New Capabilities
- `attack-run-sitl-validation`: SITL 中攻击跑全链路验证策略——覆盖 approach 几何解算、AUTO 任务上传与执行、mission seq 推进、DO_SET_SERVO 时机、precision 评估

### Modified Capabilities
- `sitl-default-field`: field.json attack_run 配置节已在 attack-run-precision-drop 中添加，SITL 联调需验证配置值在模拟环境中的合理性（approach/exit 点在 boundary 内）

## Impact

- **SITL 联调流程**：dry-run Phase 4 验证逻辑从 GUIDED 改为 attack run；新增 mission seq 监控断言
- **Mock 数据**：mock_vision_server 需确保发送的投弹点坐标使 approach/exit 点在合理范围内
- **Debug 指南**：新增 M-06 (MISSION_SET_CURRENT 无效)、M-07 (mission_current_seq 不推进)、B-05 (attack mission 空间约束冲突) 等故障模式
- **日志格式**：enroute 阶段的日志输出需包含 attack run 特有信息（approach heading、mission seq、target distance）
