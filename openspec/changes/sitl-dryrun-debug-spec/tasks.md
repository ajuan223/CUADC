## 1. SITL 环境修复与验证

- [ ] 1.1 创建 `$HOME/.config/ardupilot/locations.txt`，添加 `Zijingang=30.265,120.095,0,0`，使 sim_vehicle.py 可通过 `-L Zijingang` 加载紫金港测试场区位置。
- [ ] 1.2 在项目 `.venv` 中安装 MAVProxy：`pip install MAVProxy`，验证 `mavproxy.py --version` 可执行。
- [ ] 1.3 验证 sim_vehicle.py 启动：运行 `sim_vehicle.py -v ArduPlane -L Zijingang -w --no-console --no-map`，确认 MAVProxy 创建 UDP 输出到 14550，pymavlink 可通过 `udp:127.0.0.1:14550` 连接并收到 heartbeat。
- [ ] 1.4 修正 `tests/integration/conftest.py`：将 SITL 启动方式改为 sim_vehicle.py 或修正 raw binary 的参数路径和端口检查（raw binary 默认 TCP 5760，不是 UDP 14550）。

## 2. Mock 数据基础设施

- [ ] 2.1 创建 `scripts/mock_vision_server.py`，支持以下 CLI 参数：`--host`（默认 0.0.0.0）、`--port`（默认 9876）、`--interval`（默认 2.0s）、`--lat`/`--lon`（固定坐标）、`--random`（随机坐标）、`--no-drop-point`（不发数据）。
- [ ] 2.2 Mock server 发送格式为 JSON `{"lat": <float>, "lon": <float>}` + 换行符，使用 structlog 记录每条发送的消息。
- [ ] 2.3 验证 `--random` 模式生成的坐标在 field.json boundary 范围内（lat 30.2600-30.2700, lon 120.0900-120.1000）。
- [ ] 2.4 确认 `data/fields/sitl_default/field.json` 已有 8 个 scan waypoints + landing 配置 + boundary 多边形，可直接作为 dry-run 的航点和地图 mock。

## 3. Dry-Run 执行脚本

- [ ] 3.1 创建 `scripts/dryrun.sh`，按顺序执行：(1) 杀残留进程 → (2) `sim_vehicle.py -v ArduPlane -L Zijingang -w --no-console --no-map` → (3) 等待 UDP 14550 就绪 → (4) 启动 mock_vision_server.py（后台）→ (5) 启动 striker `STRIKER_MAVLINK_URL=udp:127.0.0.1:14550 --dry-run --field sitl_default` → (6) 捕获日志 → (7) cleanup。
- [ ] 3.2 Dry-run 脚本支持 `--with-vision`（启动 mock server 发送投弹点）和 `--no-vision`（不发投弹点，测试兜底中点路径）。
- [ ] 3.3 Dry-run 脚本在退出时（正常或异常）必须 cleanup 所有子进程。

## 4. 日志断言与通过标准

- [ ] 4.1 定义各阶段的日志断言模式：
  - INIT→PREFLIGHT: "FSM transition to=preflight"
  - PREFLIGHT: "Mission upload complete"
  - TAKEOFF: "Target altitude reached"
  - SCAN: "Scan complete"
  - DROP-ROUTING: "GUIDED" 或 "goto" 日志
  - RELEASE: "Payload released"
  - LANDING: "Landing detected"
  - COMPLETED: "FSM transition to=completed"
- [ ] 4.2 定义各阶段超时：TAKEOFF=60s, SCAN=120s, ENROUTE=60s, RELEASE=10s, LANDING=60s，总链路 5 分钟。
- [ ] 4.3 创建日志分析脚本 `scripts/dryrun_analyze.py`，输出各阶段耗时、通过/失败状态、失败阶段的 debug 建议（引用故障模式 ID）。

## 5. SITL Debug Guide 文档化

- [ ] 5.1 创建 `docs/sitl_debug_guide.md`，按四层模型组织故障模式。注意：sim_vehicle.py 启动时 SITL 本身监听 TCP 5760，MAVProxy 将数据转发到 UDP 14550/14551。striker 连的是 MAVProxy 的 UDP 输出（14550），不是 SITL 直接端口。
- [ ] 5.2 Physical Layer：SITL 未启动（`ps aux | grep arduplane`）、SITL 崩溃、端口冲突（`ss -tlnp | grep 5760` 和 `ss -ulnp | grep 14550`）。
- [ ] 5.3 Transport Layer：无心跳（先查 MAVProxy 是否运行 `ps aux | grep mavproxy`、再查 UDP 14550）、连接丢失、MAVProxy 未创建 UDP 输出。
- [ ] 5.4 Protocol Layer：COMMAND_ACK 拒绝、Mission upload 超时、MISSION_ITEM_REACHED 未触发、GUIDED goto 无效、模式切换失败。
- [ ] 5.5 Business Logic Layer：状态机卡住、视觉数据未到达 tracker、降落序列未执行、Override 未检测到。
- [ ] 5.6 Quick-Reference：SITL 健康检查命令集（区分 SITL 进程和 MAVProxy 进程）。
- [ ] 5.7 Claude Code 结构化 Debug 工作流：Capture → Layer Classify → Pattern Match → Diagnose → Repair → Verify → Document。

## 6. SITL 集成测试修复

- [ ] 6.1 修正 `tests/integration/conftest.py`：确保 fixture 可启动 SITL 并等待正确端口（sim_vehicle.py → UDP 14550；raw binary → TCP 5760）。
- [ ] 6.2 更新 `tests/integration/test_sitl_full_mission.py` 状态链为新流程。
- [ ] 6.3 编写可执行的 `test_normal_path`（有视觉投弹点）。
- [ ] 6.4 重写 `test_degradation_path` 为 `test_fallback_midpoint_path`（兜底中点）。
- [ ] 6.5 编写可执行的 `test_human_override`（模式切换触发 OverrideEvent）。

## 7. Dry-Run 执行与验证

- [ ] 7.1 运行 `scripts/dryrun.sh --with-vision`，验证有视觉投弹点全链路通过。
- [ ] 7.2 运行 `scripts/dryrun.sh --no-vision`，验证兜底中点路径通过。
- [ ] 7.3 在 dry-run 中通过 MAVProxy 终端执行 `mode MANUAL`，验证 OverrideEvent 触发。
- [ ] 7.4 记录所有问题到 `docs/dryrun_report.md`，含 debug guide 引用和修复建议。
