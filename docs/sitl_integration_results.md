# SITL + Striker 集成联调报告

**日期**: 2026-04-15
**环境**: Linux dev workstation (headless, 无 X11/display server)

---

## 测试摘要

| 阶段 | 状态 | 说明 |
|------|------|------|
| ArduPilot 编译 | PASS | arduplane SITL 二进制编译成功 (5.6MB) |
| SITL TCP 连接 | PASS | pymavlink 通过 TCP:5760 成功连接并收到 HEARTBEAT |
| SITL 仿真循环 | **BLOCKED** | SITL 需要 sim 后端持续连接才能推进物理模拟 |
| Striker + SITL 集成 | **BLOCKED** | 依赖 SITL 仿真循环正常推进 |
| 全任务联调 | **BLOCKED** | 依赖以上 |

---

## 1. ArduPilot SITL 编译

**状态**: PASS

```
二进制: ~/ardupilot/build/sitl/bin/arduplane (5.6MB)
版本: ArduPlane latest (main branch, shallow clone)
编译时间: ~1m35s
```

编译过程中的问题及解决：

| 问题 | 解决 |
|------|------|
| `plane.parm` 默认参数文件不存在 | 使用 `Tools/autotest/models/plane.parm` 替代 |
| waf 子模块空目录 | 手动 `git clone` ArduPilot/waf |
| mavlink 子模块空目录 | 手动 `git clone` ArduPilot/mavlink + 子模块 |
| DroneCAN/libcanard 空目录 | 手动 `git clone` DroneCAN/libcanard |
| DroneCAN/pydronecan 空目录 | 手动 `git clone` DroneCAN/pydronecan |
| 缺少 empy 包 | `uv pip install --target=/tmp/empy_pkg empy==3.3.4` |
| 缺少 dronecan 包 | `uv pip install --target=/tmp/empy_pkg dronecan` |

---

## 2. SITL TCP 连接验证

**状态**: PASS (有限)

SITL 从 `~/ardupilot` 目录启动后，可通过 TCP 5760 连接：

```
cd ~/ardupilot
~/ardupilot/build/sitl/bin/arduplane --model plane -I 0 \
    --defaults Tools/autotest/models/plane.parm --sim-address=127.0.0.1
```

pymavlink 连接测试：

```python
conn = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255, source_component=1)
conn.wait_heartbeat(timeout=15)
# 结果: sys=0, comp=0, mode=UNKNOWN, armed=False
```

**限制**:
- `sys=0` 表示 SITL 尚未完成完整初始化
- `mode=UNKNOWN` 因为 sim 循环未推进
- 连接后约 30 秒 SITL 因 sim 超时而终止

---

## 3. SITL 仿真循环问题

**状态**: BLOCKED

### 根因分析

ArduPilot SITL 的架构是**双进程模型**：

```
┌─────────────────┐     sim port      ┌─────────────────┐
│   ArduPlane      │◄──── UDP:5501 ───│   Simulator     │
│   (飞控逻辑)     │                   │   (物理引擎)    │
│                  │──── TCP:5760 ───►│                  │
│                  │     MAVLink      │  (MAVProxy 或   │
└─────────────────┘                   │   sim_vehicle)  │
                                      └─────────────────┘
```

SITL 进程本身只运行飞控代码，**物理模拟**由外部 sim 后端提供。在当前 headless 环境：

1. **sim_vehicle.py** 需要交互式终端来维持 MAVProxy 运行
2. **MAVProxy** 的 `--non-interactive` 模式启动后立即退出（在无 TTY 的环境下）
3. 没有 sim 后端 → SITL 在 "Smoothing reset" 后挂起

SITL 日志：
```
Starting sketch 'ArduPlane'
SERIAL0 on TCP port 5760
Waiting for connection ....
Connection on serial port 5760
Loaded defaults from Tools/autotest/models/plane.parm
Home: -35.363262 149.165237 alt=584.000000m hdg=353.000000
Smoothing reset at 0.001     ← 卡在这里，等待 sim 数据
```

### 解决方案

要让 SITL 在 headless 环境完整运行，需要以下任一方案：

| 方案 | 难度 | 说明 |
|------|------|------|
| A. 在有桌面环境的机器上运行 | 低 | 直接用 sim_vehicle.py 启动 |
| B. 使用 xvfb 虚拟显示 | 中 | `xvfb-run sim_vehicle.py` 可能解决问题 |
| C. 编写自定义 sim 后端 | 高 | 直接向 UDP:5501 发送 SITL 模拟数据帧 |
| D. 使用 ArduPilot 的 Docker 镜像 | 中 | 官方提供 sitl Docker 镜像 |

---

## 4. Striker 端验证 (无 SITL)

在 SITL 无法推进 sim 循环的情况下，Striker 端仍验证了以下能力：

| 验证项 | 结果 | 说明 |
|--------|------|------|
| MAVLinkConnection TCP 连接 | PASS | 能连到 SITL 的 TCP 端口 |
| 心跳接收 | PASS | 收到 HEARTBEAT 消息 |
| TelemetryParser 解析 | PASS | 解析 HEARTBEAT 类型正确 |
| 配置加载 + 场地配置 | PASS | sitl_default 完整加载 |
| 状态机 13 状态 + 转换 | PASS | 含 forced_strike 路径 |
| 弹道计算 | PASS | 三种输入场景验证 |
| 安全监控构建 | PASS | 所有 check 注册正常 |
| 187 单元测试 | PASS | 0 失败 |

---

## 5. 集成测试断点

以下测试项因 SITL sim 循环未运行而无法完成：

- `test_connect_and_receive_heartbeat` — 部分通过 (收到初始 HB，但 sim 未推进)
- `test_telemetry_parsing_with_real_sitl` — BLOCKED (无 GLOBAL_POSITION_INT 数据)
- `test_normal_path` (ARM→TAKEOFF→SCAN→...→COMPLETED) — BLOCKED
- `test_degradation_path` (LOITER timeout→FORCED_STRIKE) — BLOCKED
- `test_human_override` (手动模式切换→OVERRIDE) — BLOCKED
- 任务航线上传/下载验证 — BLOCKED
- 飞行记录器 CSV 输出验证 — BLOCKED

---

## 6. 修复 `run_sitl.sh` 脚本

当前 `scripts/run_sitl.sh` 有两个问题：

### 6.1 默认参数文件路径错误

脚本中使用：
```bash
--defaults "${ARDUPILOT_DIR}/Tools/autotest/default_params/plane.parm"
```

但该文件不存在。应改为：
```bash
--defaults "Tools/autotest/models/plane.parm"
```
并要求 CWD 为 `$ARDUPILOT_DIR`。

### 6.2 缺少 sim 后端

脚本仅启动 arduplane，未启动 sim 后端。建议更新为使用 `sim_vehicle.py` 或添加 MAVProxy 启动。

---

## 7. 结论与下一步

### 已完成

- ArduPilot SITL 编译成功
- Striker 代码质量验证 (187 测试 + 50 手动测试全部通过)
- 4 个运行时缺陷已修复
- MAVLink TCP 连接层验证通过
- 用户手册 + 测试报告已编写

### 需要下一步完成

1. **在有桌面环境或 Docker 中运行完整 SITL 集成测试**
   ```bash
   # 推荐方式 (需要 X11/桌面):
   cd ~/ardupilot
   python3 Tools/autotest/sim_vehicle.py -v ArduPlane -I 0 --no-rebuild
   
   # 或 Docker 方式:
   docker run -it --rm ardupilot/arduplane-sitl
   ```

2. **修复 `scripts/run_sitl.sh`** 使其正确启动完整 SITL 环境

3. **编写 SITL conftest.py fixture** 自动管理 sim_vehicle.py 进程生命周期

4. **执行全任务集成测试** 验证 ARM→TAKEOFF→SCAN→LOITER→ENROUTE→APPROACH→RELEASE→LANDING→COMPLETED 完整流程
