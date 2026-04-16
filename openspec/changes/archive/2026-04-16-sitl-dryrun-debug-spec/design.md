## Context

`simplify-mission-flow-drop-point` 变更完成后，striker 的状态机将从旧的 `scan → loiter ↔ rescan → forced_strike` 链路切换为新的 `scan → drop-point-routing → release → landing` 链路。这套新的任务流程涉及状态注册、迁移路径、视觉数据语义、mission 进度观测、override 闭环等多个模块的协同，必须在真实 MAVLink 通信环境中验证。

当前本地 SITL 环境：
- `~/ardupilot/build/sitl/bin/arduplane` 二进制已编译可用（ELF 64-bit x86-64）
- `~/ardupilot/Tools/autotest/models/plane.parm` 存在，但 `tests/integration/conftest.py` 引用了错误路径 `default_params/plane.parm`
- `~/ardupilot-venv` 虚拟环境已创建但 MAVProxy 未安装
- 项目 `.venv` 已有 pymavlink 依赖
- `data/fields/sitl_default/field.json` 提供了基于紫金港校区的 mock 航点和降落参数

SITL + MAVProxy 在 Ubuntu 上的运行原理（经 ArduPilot 官方文档纠偏）：
1. **arduplane SITL** 是一个用户态进程，模拟飞控固件。**默认通过 TCP 端口 5760 通信**（不是 UDP 14550）。`--instance N` 会将端口偏移 `10*N`
2. **sim_vehicle.py** 是 ArduPilot 官方推荐的 SITL 启动方式，它会自动：编译二进制、加载参数、启动 SITL、启动 MAVProxy。MAVProxy 创建 UDP 输出到 `127.0.0.1:14550` 和 `14551`
3. **通信拓扑**：`SITL(TCP 5760) → MAVProxy → UDP 14550/14551`。pymavlink 连接 `udp:127.0.0.1:14550` 实际连接的是 MAVProxy 的输出，不是 SITL 本身
4. **直接启动 arduplane 二进制**（不用 sim_vehicle.py）时，serial0 默认是 TCP 服务器在 5760。pymavlink 应使用 `tcp:127.0.0.1:5760` 连接。也可通过 `--serial0 udpin:0.0.0.0:14550` 让 SITL 监听 UDP
5. SITL 启动后需要收到的第一个 HEARTBEAT 来完成 `wait_heartbeat()` 握手，这会设定 `target_system` / `target_component`
6. ArduPlane SITL 的 `custom_mode` 字段是整数，映射到 ArduPlaneMode 枚举（0=MANUAL, 10=AUTO, 15=GUIDED 等）
7. **SITL 初始位置**默认在 CMAC（Canberra: -35.363261, 149.165230, alt 584m）。设置方式：(a) raw binary 用 `--home lat,lng,alt,yaw`；(b) sim_vehicle.py 用 `-L <name>` 从 `locations.txt` 加载；(c) 自定义位置添加到 `$HOME/.config/ardupilot/locations.txt`（格式：`NAME=lat,lng,alt,heading`）

## Goals / Non-Goals

**Goals:**
- 修复 SITL 环境使其可正常启动，且 striker 能通过 MAVProxy UDP 输出（14550）成功连接
- 提供 mock 视觉投弹点数据的方案（TCP mock server），使 dry-run 不依赖真实视觉系统
- 定义分阶段全链路 dry-run 策略，从 init 到 completed 的每个状态迁移都有可观测的通过/失败标准
- 编写 SITL/MAVProxy 故障 debug spec，覆盖最常见故障模式，使 Claude Code 能结构化排查

**Non-Goals:**
- 不在本次变更中修改 striker 的业务代码（那是 `simplify-mission-flow-drop-point` 的职责）
- 不搭建 CI 环境，只做本地 dry-run
- 不做性能测试或压力测试
- 不引入 QGroundControl 或其他 GUI GCS

## Decisions

### 1. SITL 启动方式：sim_vehicle.py + MAVProxy
使用 `sim_vehicle.py -v ArduPlane -L Zijingang -w` 启动 SITL。这是 ArduPilot 官方推荐方式，自动处理编译、参数加载和 MAVProxy 启动。MAVProxy 创建 UDP 输出到 `127.0.0.1:14550` 和 `14551`，striker 的 pymavlink 连接 `udp:127.0.0.1:14550`。

**端口拓扑**：`SITL(TCP 5760) → MAVProxy → UDP 14550/14551`。striker 连的是 MAVProxy 的 UDP 输出，不是 SITL 直接端口。这个拓扑知识写入 debug guide，用于排查连接故障。

**MAVProxy 调试**：sim_vehicle.py 方式下 MAVProxy 已在运行，可通过 MAVProxy 终端执行 `mode MANUAL`、`wp list` 等调试命令。

### 2. Mock 视觉数据：独立的 TCP mock server 脚本
创建一个独立的 Python 脚本 `scripts/mock_vision_server.py`，在配置的 TCP 端口（默认 9876）上监听，按一定频率发送 mock 投弹点坐标。这样 striker 的 `TcpReceiver` 可以原样接收，无需修改 striker 代码。

**替代方案**：在测试中直接 mock `VisionReceiver` 接口 → 可行但不测试真实 TCP 通信链路。dry-run 应尽量使用真实通信路径。

### 3. SITL 初始位置配置：通过 --home 参数或 locations.txt
arduplane 二进制支持 `--home lat,lng,alt,yaw` 直接设置初始位置。sim_vehicle.py 支持 `-L <name>` 从 `~/ardupilot/Tools/autotest/locations.txt` 或 `$HOME/.config/ardupilot/locations.txt` 加载命名位置。

**策略**：创建 `$HOME/.config/ardupilot/locations.txt` 并添加 `Zijingang=30.265,120.095,0,0`，然后使用 `sim_vehicle.py -v ArduPlane -L Zijingang`。

**替代方案**：通过 SIM_LAT/SIM_LNG 参数文件 → 可行但 `--home` / `-L` 是官方文档推荐的方式，更简洁。

### 4. Debug 方法论：分层故障模式 + 逐步排查
按"物理层 → 传输层 → MAVLink 协议层 → 业务逻辑层"四层模型组织 debug spec。每层定义症状、可能原因、排查命令和修复动作。

### 5. Dry-Run 执行方式：bash 脚本 + 日志断言
创建 `scripts/dryrun.sh` 脚本自动启动 SITL → 启动 mock vision → 启动 striker（dry-run 模式）→ 捕获日志 → 断言关键日志行出现。Claude Code 可逐步运行或全量运行。

**替代方案**：纯 pytest 集成测试 → 更规范但对 SITL 环境依赖更重，且不适合"联调"场景。dry-run 的目标是"看到全链路跑通"而非"测试通过"。

## Risks / Trade-offs

- **[SITL GPS 初始位置与 field.json 不匹配]** → 通过 `$HOME/.config/ardupilot/locations.txt` 添加 `Zijingang=30.265,120.095,0,0`，使用 `sim_vehicle.py -L Zijingang` 设定初始位置
- **[SITL 无真实风场数据]** → SITL 的 WIND 消息可能为零或模拟值。可通过 `SIM_WIND_DIR` 和 `SIM_WIND_SPD` 参数模拟风场。新流程已删除弹道，风场数据影响较小
- **[端口模型理解偏差]** → SITL 默认 TCP 5760，不是 UDP 14550。使用 sim_vehicle.py 时 MAVProxy 创建 UDP 14550/14551 输出。若不使用 sim_vehicle.py，pymavlink 连接 URL 必须是 `tcp:127.0.0.1:5760`
- **[mission upload 协议在 SITL 中行为差异]** → SITL 支持 MISSION_COUNT / MISSION_REQUEST_INT / MISSION_ACK 完整协议，但响应时间可能比真实飞控快。增加超时容忍度
- **[MISSIOn_ITEM_REACHED 在 SITL 中触发频率]** → SITL 会为每个航点触发 MISSION_ITEM_REACHED，但需要 AUTO 模式且有有效 mission。scan 完成观测依赖此消息
- **[SITL 速度加速]** → 可用 `--speedup 2` 加速 SITL 时间，但这会改变所有时间相关逻辑的超时行为。初次 dry-run 建议用 `--speedup 1`

## Open Questions

- 是否需要为 SITL 环境创建 Docker 容器以便复用？→ 暂不需要，本地 `~/ardupilot` 已足够
- `scripts/mock_vision_server.py` 是否应加入项目依赖管理？→ 暂不加入，作为独立脚本存在
- dry-run 完成后是否应清理 SITL 进程？→ 是，`dryrun.sh` 脚本应包含 cleanup 逻辑
