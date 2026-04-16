## 1. SITL 环境就绪确认

- [x] 1.1 验证 `~/ardupilot/build/sitl/bin/arduplane` 二进制存在且可执行
- [x] 1.2 验证 `$HOME/.config/ardupilot/locations.txt` 包含 `Zijingang=30.265,120.095,0,0`
- [x] 1.3 验证 MAVProxy 已安装（`mavproxy.py --version`）
- [x] 1.4 启动 SITL：`sim_vehicle.py -v ArduPlane -L Zijingang --no-console --no-map`，确认 UDP 14550 可达（`ss -ulnp | grep 14550`），pymavlink `wait_heartbeat()` 成功

## 2. Mock 数据准备

- [x] 2.1 验证 `scripts/mock_vision_server.py` 存在且可用，默认投弹点坐标位于场区中心附近（30.2650, 120.0950），确保 approach/exit 200m offset 在 boundary 内
- [x] 2.2 验证 `data/fields/sitl_default/field.json` 包含 `attack_run` 配置节（approach_distance_m=200, exit_distance_m=200, release_acceptance_radius_m=0）
- [x] 2.3 启动 mock_vision_server 后确认 striker 的 TcpReceiver 能接收 mock 投弹点数据

## 3. 攻击跑几何验证

- [x] 3.1 在 SITL 中完成 init → preflight → takeoff → scan 阶段，确认 scan 完成后 striker correctly enters enroute state
- [x] 3.2 验证 enroute on_enter 日志输出 attack run 几何信息：approach heading、approach/target/exit 坐标、attack mission waypoint count
- [x] 3.3 验证 approach/exit 坐标在 field boundary 内（mock 投弹点在中心附近时）
- [ ] 3.4 （可选）设置 SITL 风场参数 `SIM_WIND_DIR` / `SIM_WIND_SPD`，验证逆风进场逻辑

## 4. Attack Mission 上传与执行验证

- [x] 4.1 验证 attack mission upload 成功：日志显示 "attack run mission uploaded"，确认 MISSION_ACK result=0
- [x] 4.2 验证 AUTO 模式切换成功：HEARTBEAT custom_mode=10（ArduPlane AUTO）
- [x] 4.3 验证 MISSION_SET_CURRENT 到 approach seq 成功：MISSION_CURRENT seq 跳到 approach
- [x] 4.4 监控 mission_current_seq 推进：approach → target → exit，记录每个 seq 变化时刻和 GLOBAL_POSITION_INT
- [x] 4.5 验证 target waypoint 完成触发 enroute → release 状态转换

## 5. Release 验证

- [x] 5.1 Dry-run 模式：验证 release 状态调用 `context.release_controller.release()` 并打日志后转换到 LANDING
- [x] 5.2 Non-dry-run 模式：验证 DO_SET_SERVO 在 target waypoint 完成时由 ArduPlane 执行，SERVO_OUTPUT_RAW 显示 PWM 变化
- [x] 5.3 记录 target waypoint 完成时刻的 GLOBAL_POSITION_INT 与目标坐标的 haversine 距离（release_distance_m），确认 <= WP_RADIUS (~30m)

## 6. Landing 验证

- [x] 6.1 验证 landing 状态发送 MISSION_SET_CURRENT 到 landing_start_index（不重新上传 mission）
- [x] 6.2 验证 SITL 执行 landing approach → NAV_LAND 序列
- [x] 6.3 验证 touchdown 检测：relative_alt_m < 1.0，FSM transition to=completed

## 7. Fallback 路径验证（无视觉数据）

- [ ] 7.1 运行 mock_vision_server `--no-drop-point` 模式，验证 fallback midpoint 计算和 attack run 执行
- [ ] 7.2 验证 fallback 路径完整链路：scan → enroute(attack run to midpoint) → release → landing → completed

## 8. 日志断言与 Debug Guide 更新

- [ ] 8.1 更新 `scripts/dryrun.sh` 日志断言模式，Phase 4 改为 attack run 特有日志（"attack run mission uploaded", "mission_current_seq", "approach heading" 等）
- [ ] 8.2 更新 enroute 超时为 90s（attack run 400m@20m/s + margin）
- [ ] 8.3 更新 `docs/sitl_debug_guide.md` 新增故障模式：M-06 (MISSION_SET_CURRENT 无效)、M-07 (mission_current_seq 不推进)、M-08 (DO_SET_SERVO 未执行)、B-05 (approach/exit 出界)

## 9. 联调报告

- [x] 9.1 记录 dry-run 全链路日志到 `docs/attack_run_dryrun_report.md`
- [x] 9.2 记录各阶段耗时、mission seq 推进时序、实际释放精度
- [x] 9.3 记录发现的问题和 debug 过程（引用故障模式 ID）
