## 1. Field Profile: AttackRunConfig 数据模型

- [x] 1.1 在 `src/striker/config/field_profile.py` 中新增 `AttackRunConfig(BaseModel)` 数据模型，包含 `approach_distance_m` (float, default 200), `exit_distance_m` (float, default 200), `release_acceptance_radius_m` (float, default 0)
- [x] 1.2 在 `FieldProfile` 中新增 `attack_run: AttackRunConfig` 字段（带默认值工厂以保证向后兼容）
- [x] 1.3 更新 `data/fields/sitl_default/field.json` 添加 `attack_run` 配置节
- [x] 1.4 验证：运行现有 field_profile 单元测试，确认无 `attack_run` 的旧 field JSON 仍能正常加载

## 2. Navigation: 攻击跑任务生成

- [x] 2.1 在 `src/striker/flight/navigation.py` 中新增 `make_do_set_servo(seq, channel, pwm, mav)` 函数，生成 `MAV_CMD_DO_SET_SERVO` MISSION_ITEM_INT 消息
- [x] 2.2 在 `src/striker/flight/navigation.py` 中新增 `build_attack_run_mission()` 函数，生成完整攻击跑+降落任务序列：[dummy HOME, approach, target, DO_SET_SERVO?(dry), exit, DO_LAND_START, landing approach, NAV_LAND]
- [x] 2.3 在 `src/striker/comms/messages.py` 中确认 `MAV_CMD_DO_SET_SERVO = 183` 常量存在（已存在则跳过）
- [x] 2.4 验证：编写单元测试确认生成的 mission items 序列、seq 编号、DO_SET_SERVO 参数正确

## 3. Mission Upload: 攻击跑任务上传

- [x] 3.1 在 `src/striker/flight/mission_upload.py` 中新增 `upload_attack_mission()` 函数：调用 `build_attack_run_mission()` + `upload_mission()`，设置 `context.landing_sequence_start_index`，返回 target waypoint seq
- [x] 3.2 验证：确认 `upload_attack_mission()` 与现有 `upload_mission()` 协议兼容（MISSION_CLEAR_ALL → MISSION_COUNT → MISSION_ITEM_INT × N → MISSION_ACK）

## 4. Enroute State: 重写为攻击跑策略

- [x] 4.1 重写 `src/striker/core/states/enroute.py` 的 `on_enter()`：计算 approach heading（逆风优先→直飞→landing heading fallback），计算 approach/exit 坐标，调用 `upload_attack_mission()`，切换 AUTO 模式，`MISSION_SET_CURRENT(approach_seq)`
- [x] 4.2 重写 `execute()`：监控 `context.mission_current_seq`，当 seq >= target_seq + 1 时返回 `Transition("release")`
- [x] 4.3 保留调试日志（每 5s 输出当前 mission seq、距目标距离）
- [x] 4.4 删除旧的 GUIDED 相关代码（`_send_position_target` 调用、`_heading_to_drop` 标志、1Hz resend 逻辑、100m 距离阈值）
- [ ] 4.5 验证：在 SITL 中运行 striker `--dry-run --field sitl_default`，确认 enroute 进入 AUTO 模式、mission seq 正确推进

## 5. Release State: 适配原生释放

- [x] 5.1 修改 `src/striker/core/states/release.py`：当 `dry_run=False` 时，记录 "Payload released (native DO_SET_SERVO)" 并立即转换到 LANDING；当 `dry_run=True` 时，调用 `context.release_controller.release()` 走现有 dry_run 逻辑
- [x] 5.2 验证：确认 dry_run 模式下 RELEASE 仍只打日志不触发物理舵机

## 6. Landing State: 简化（使用预上传降落任务）

- [x] 6.1 修改 `src/striker/core/states/landing.py`：如果已在 AUTO 模式且 `landing_sequence_start_index` 已设置，直接 `mission_set_current` 到 landing start seq；否则走原有完整流程（兼容非攻击跑入口）
- [x] 6.2 验证：确认攻击跑后的降落流程正常触发 DO_LAND_START → landing approach → NAV_LAND

## 7. SITL 全链路联调

- [ ] 7.1 启动 ArduPlane SITL，运行 striker `--dry-run --field sitl_default` + mock_vision_server，完成 init→preflight→takeoff→scan→enroute(attack run)→release→landing→completed 全链路
- [ ] 7.2 记录攻击跑日志：approach/exit 坐标、飞行航向、到达 target 时的实际距离、mission seq 推进时序
- [ ] 7.3 运行 fallback midpoint 路径（无视觉数据），确认兜底投放链路正常
- [ ] 7.4 运行 vision TCP 路径，确认视觉投弹点攻击跑正常
- [ ] 7.5 验证非 dry_run 模式：确认 DO_SET_SERVO 在任务中的执行时机和 WP_RADIUS 精度
