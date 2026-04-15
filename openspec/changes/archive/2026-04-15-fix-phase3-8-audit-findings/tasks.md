## 1. P0 阻塞性修复 — FSM 转换表

- [x] 1.1 `core/machine.py`: 在 `to_landing` 声明中添加 `forced_strike.to(landing)` (F-01)
- [x] 1.2 `core/machine.py`: 在 `to_override` 声明中添加 `forced_strike.to(override)` (F-01, F-12)
- [x] 1.3 `core/machine.py`: 在 `to_emergency` 声明中添加 `forced_strike.to(emergency)` (F-01, F-12)
- [x] 1.4 验证: python-statemachine 在 forced_strike 状态下调用 `to_landing()` 不抛 `TransitionNotAllowed`

## 2. P0 阻塞性修复 — app.py 集成

- [x] 2.1 `app.py`: 在 TaskGroup 前添加 `await vision_receiver.start()` (F-02)
- [x] 2.2 `app.py`: 实现 `_vision_dispatch()` 协程，100ms 轮询 `vision_receiver.get_latest()` 并推送到 `target_tracker.push()` (F-02)
- [x] 2.3 `app.py`: 在 TaskGroup 中添加 `tg.create_task(_vision_dispatch(...))` (F-02)
- [x] 2.4 `app.py`: 调用 `safety_monitor.set_event_callback(lambda e: fsm.process_event(e))` (F-03)
- [x] 2.5 验证: 手动测试 safety check 失败时 FSM 进入 EMERGENCY

## 3. P1 — pymavlink 隔离 (RL-04)

- [x] 3.1 `comms/messages.py`: 添加 MAVLink 命令 ID 常量 (MAV_CMD_COMPONENT_ARM_DISARM=400 等 15 个值) (F-04)
- [x] 3.2 `comms/messages.py`: 添加 `build_heartbeat_msg(target_system, target_component)` 函数返回可 send 的心跳消息 (F-08)
- [x] 3.3 `flight/controller.py`: 移除所有 `from pymavlink import mavutil`，改用 comms 常量 (F-04)
- [x] 3.4 `payload/mavlink_release.py`: 移除 `from pymavlink import mavutil`，改用 comms 常量 (F-04)
- [x] 3.5 `comms/telemetry.py`: 保留 pymavlink 导入（在 comms/ 内，合规）
- [x] 3.6 验证: `grep -r "from pymavlink" src/striker/ --exclude-dir=comms` 返回零结果

## 4. P1 — HeartbeatMonitor 类型修正

- [x] 4.1 `comms/heartbeat.py`: 将 `conn` 参数类型从 `mavutil.mavfile` 改为 `MAVLinkConnection` (F-08)
- [x] 4.2 `comms/heartbeat.py`: `_heartbeat_sender()` 改用 `conn.send(build_heartbeat_msg(...))` 发送心跳 (F-08)
- [x] 4.3 `comms/heartbeat.py`: 移除 pymavlink 导入（心跳消息构建改用 comms 常量）(F-08)
- [x] 4.4 验证: `app.py` 中 `HeartbeatMonitor(conn=connection)` 类型检查通过

## 5. P1 — 配置优先级修正

- [x] 5.1 `config/settings.py`: 修改 `settings_customise_sources` 返回顺序为 `(init, Json, env, secrets)` (F-05)
- [x] 5.2 `config/settings.py`: 更新注释为 `init defaults < JSON < env`
- [x] 5.3 验证: 单元测试 — 设置 config.json + STRIKER_ 环境变量，确认 env 覆盖 json

## 6. P1 — LandingState 降落序列修正

- [x] 6.1 `core/states/landing.py`: 移除 `__import__()` 动态导入和 RTL 模式 (F-06)
- [x] 6.2 `core/states/landing.py`: 改用 AUTO 模式 + `MAV_CMD_MISSION_SET_CURRENT` 跳转到降落序列起始索引 (F-06)
- [x] 6.3 `comms/messages.py`: 添加 `MAV_CMD_MISSION_SET_CURRENT = 224` 常量
- [x] 6.4 验证: 代码中无 `__import__` 调用

## 7. P1 — 弹道解算参数补全

- [x] 7.1 `core/states/approach.py`: 从 context 提取速度/风速数据传入 `calculate_release_point()` (F-07)
- [x] 7.2 `core/context.py`: 添加 `current_speed` 和 `current_wind` 属性存储遥测数据 (F-07)
- [x] 7.3 验证: ApproachState 在有速度数据时传递非零 velocity 参数

## 8. P2 — 距离计算统一

- [x] 8.1 `core/states/enroute.py`: 替换 `111_000` 硬编码为 `haversine_distance()` (F-09)
- [x] 8.2 `core/states/approach.py`: 替换 `111_000` 硬编码为 `haversine_distance()` (F-09)
- [x] 8.3 `core/states/forced_strike.py`: 替换 `111_000` 硬编码为 `haversine_distance()` (F-09)
- [x] 8.4 验证: `grep -r "111.?000" src/striker/core/states/` 返回零结果

## 9. P2 — forced_strike_point 安全缓冲增强

- [x] 9.1 `utils/geo.py`: 将 `safety/geofence._point_to_segment_distance` 提取为公共函数 `point_to_segment_distance()` (F-13)
- [x] 9.2 `utils/forced_strike_point.py`: 导入 `point_to_segment_distance` 和 haversine (F-13)
- [x] 9.3 `utils/forced_strike_point.py`: 候选点经 `point_in_polygon` 后，额外计算到最近边距离，< buffer_m 则拒绝 (F-13)
- [x] 9.4 验证: 生成 1000 个随机点，全部 >= buffer_m 距离到最近边界

## 10. P2 — 依赖与缺失产出物

- [x] 10.1 `pyproject.toml`: 添加 `[project.optional-dependencies]` gpio = ["gpiod"] (F-10)
- [x] 10.2 创建 `src/striker/py.typed` 空文件 (F-11)
- [x] 10.3 创建 `.env.example` 含所有 STRIKER_* 环境变量 (F-11)
- [x] 10.4 创建 `data/fields/sitl_default/field.json` SITL 默认场地配置 (F-11)
- [x] 10.5 创建 `pkg/README.md` + `pkg/.gitkeep` workspace 骨架 (F-11)
- [x] 10.6 验证: `load_field_profile("sitl_default")` 成功返回 FieldProfile

## 11. 回归验证

- [x] 11.1 `uv run ruff check .` 通过
- [x] 11.2 `uv run mypy src/ --strict` 通过
- [x] 11.3 `uv run pytest tests/unit/` 通过
- [x] 11.4 `uv run python -m striker` 可执行（打印版本号后退出）
