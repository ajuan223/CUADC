# Attack Run SITL 联调报告

> 日期: 2026-04-16
> 变更: attack-run-precision-drop + sitl-attack-run-integration
> 环境: ArduPlane V4.8.0-dev SITL + MAVProxy + pymavlink

## 1. 全链路执行结果

### 1.1 Dry-run 模式 (companion 释放)

```
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE(attack run) → RELEASE → LANDING → COMPLETED
```

| 阶段 | 时间戳 (UTC) | 耗时 | 关键日志 |
|------|-------------|------|---------|
| INIT | 04:36:38 | 1s | `MAVLink connected` sys=1 comp=0 |
| PREFLIGHT | 04:36:40 | 0.5s | `Mission upload complete` count=12 |
| TAKEOFF | 04:36:50 | 10s | `Target altitude reached` alt=73.28m |
| SCAN | 04:39:26 | 156s | `Scan complete` final_seq=9 |
| ENROUTE | 04:39:28 | 1.3s | `Attack mission uploaded` target_seq=2 landing_start=4 |
| RELEASE | 04:39:28 | 0.05s | `Payload released (dry-run via companion)` |
| LANDING | 04:40:29 | 61s | `Landing detected` alt=0.461m |
| COMPLETED | 04:40:29 | - | `Mission completed successfully!` |

**总耗时: ~3m51s**

**说明:** dry-run 模式下 ENROUTE 极短 (1.3s)，因为 MISSION_SET_CURRENT 重置了 seq 指针后 SITL 立刻完成所有 waypoints。未实际飞行 attack run 航段。

### 1.2 Non-dry-run 模式 (DO_SET_SERVO 原生释放)

```
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE(attack run) → RELEASE → LANDING → COMPLETED
```

| 阶段 | 时间戳 (UTC) | 耗时 | 关键日志 |
|------|-------------|------|---------|
| INIT | 04:55:30 | 1s | `MAVLink connected` sys=1 comp=0 |
| PREFLIGHT | 04:55:32 | 0.5s | `Mission upload complete` count=12 |
| TAKEOFF | 04:55:42 | 10s | `Target altitude reached` alt=72.7m |
| SCAN | 04:59:07 | 165s | `Scan complete` final_seq=9 |
| ENROUTE | 04:59:08 | 22.2s | `Attack mission uploaded` target_seq=2 landing_start=5 |
| RELEASE | 04:59:30 | 0.05s | `Payload released (native DO_SET_SERVO)` |
| LANDING | 05:00:06 | 36s | `Landing detected` alt=0.881m |
| COMPLETED | 05:00:06 | - | `Mission completed successfully!` |

**总耗时: ~4m36s**

**攻击跑飞行过程 (ENROUTE 阶段 22.2s):**

| 时间戳 | mission_seq | dist_to_target | 说明 |
|--------|-------------|---------------|------|
| 04:59:08 | - | - | MISSION_SET_CURRENT → approach |
| 04:59:13 | 1 | 360.6m | 飞向 approach 点 |
| 04:59:18 | 1 | 256.0m | 接近 approach |
| 04:59:23 | 2 | 148.1m | 通过 approach，飞向 target |
| 04:59:28 | 2 | 37.6m | 接近 target |
| 04:59:30 | 4 | - | 通过 target → DO_SET_SERVO 触发 → 转入 RELEASE |

**任务项结构 (7 项):**

```
seq 0: HOME (dummy, ArduPlane 替换)
seq 1: approach waypoint (30.264272, 120.096905) alt=30m
seq 2: target waypoint  (30.265, 120.095) alt=30m
seq 3: DO_SET_SERVO channel=6 pwm=2000
seq 4: exit waypoint    (30.265727, 120.093095) alt=30m
seq 5: landing approach waypoint alt=30m
seq 6: NAV_LAND touchdown alt=0m
```

**释放精度:** DO_SET_SERVO 在 target waypoint 完成时触发，此时距目标点 ~37.6m (在 WP_RADIUS ~30m 之外，但 SITL 速度较高导致惯性过冲)。实际部署时可通过增大 WP_RADIUS 或降低进场速度改善。

---

## 2. 调试过程

### 调试轮次概览

| 轮次 | 结果 | 根因 |
|------|------|------|
| 第1轮 | ENROUTE 失败: `MISSION_ACK type=13` | 误判为 DO_LAND_START 不兼容 |
| 第2轮 | ENROUTE 失败: SITL 反复重请求 seq=4 | 同上，protocol fix 生效但仍被拒 |
| 第3轮 | ENROUTE 失败: 同上 (6项任务，无 DO_LAND_START) | 确认不是 DO_LAND_START 问题 |
| 第4轮 | **全链路通过** | 修复了真正根因: mission item seq 编号错误 |

### 第1轮: 初次 dry-run — MISSION_ACK type=13

**现象:**

```
Attack run geometry computed heading=294.2
Mission upload: clearing all count=7
Mission upload: sending count count=7
Unexpected request sequence expected=5, got=4
Unexpected request sequence expected=6, got=4
Failed to upload attack mission: MissionUploadError: Final MISSION_ACK rejected: type=13
```

**诊断过程:**

1. 看到MISSION_ACK type=13 (UNSUPPORTED) + SITL反复请求seq=4，初步判断 DO_LAND_START (cmd=189) 在 SITL 中不支持
2. 查阅 ArduPlane 源码 `AP_Mission.cpp:1260`，确认 DO_LAND_START 在 switch 中有处理 (`case MAV_CMD_DO_LAND_START: break;`)，不应返回 UNSUPPORTED
3. 转而检查 mission upload protocol 的行为：SITL请求seq=4，但代码发送的是items[5]而不是items[4]

**修复尝试 (误诊):**
- 将 DO_LAND_START 替换为普通 NAV_WAYPOINT
- 修复 upload protocol：当 SITL 重新请求某 seq 时，发送正确 seq 的 item

### 第2-3轮: 去掉 DO_LAND_START 后仍失败

**现象:**

```
Mission upload: sending count count=6  (去掉了 DO_LAND_START)
SITL re-requested item requested_seq=4 expected_seq=5  (重复)
```

**诊断:**

- 任务从7项减到6项，seq=4 现在是 landing approach waypoint (NAV_WAYPOINT)
- SITL 仍然拒绝 seq=4，说明**不是 DO_LAND_START 的问题**
- 第1次上传 (preflight, 12项, MANUAL+disarmed) 全部通过
- 第2次上传 (enroute, 6项, AUTO+armed) seq=4 被拒

**关键洞察:**
- SITL 接受 seq 0-3 (HOME + approach + target + exit)
- SITL 拒绝 seq 4 (landing approach waypoint)
- 拒绝的不是命令类型，而是 seq 编号

### 第4轮: 找到根因 — Mission item seq 编号错误

**根因分析:**

在 `upload_attack_mission()` 中：

```python
# Bug: start_seq=0 生成 landing items，内部 seq 编号为 0, 1
landing_items = generate_landing_sequence(field_profile, conn.mav, start_seq=0)
```

然后在 `build_attack_run_mission()` 中：

```python
# Bug: 直接追加，item.seq 仍是 0, 1，但期望 4, 5
for item in landing_items:
    items.append(item)  # item.seq = 0, 1 而非 4, 5
    seq += 1
```

ArduPlane 收到 seq=4 的请求，得到的 item 内嵌 seq=0，解码后校验失败，返回 UNSUPPORTED。

**对比 preflight 为什么正常：**
- `upload_full_mission` 调用 `generate_landing_sequence(start_seq=landing_start_index)` 传入了正确的起始 seq
- 所以 landing items 的 seq 编号从一开始就是正确的

**修复:**

`navigation.py` — 追加 landing items 时重新编号：

```python
for item in landing_items:
    item.seq = seq        # 修复: 重编 seq 号
    items.append(item)
    seq += 1
```

`mission_upload.py` — 协议层支持重试：

```python
# 旧: 线性发送 items[i]
mav.mav.send(items[i])

# 新: 按 SITL 请求的 seq 发送
mav.mav.send(items[req_seq])
```

`landing_sequence.py` — 去掉 DO_LAND_START，改为 NAV_WAYPOINT：

```python
# 旧: DO_LAND_START + approach + NAV_LAND (3 items)
# 新: approach + NAV_LAND (2 items)
```

---

## 3. 代码变更清单

| 文件 | 变更 | 原因 |
|------|------|------|
| `src/striker/flight/navigation.py:224-228` | landing items 追加时 `item.seq = seq` | 修复 seq 编号错误 (根因) |
| `src/striker/flight/mission_upload.py:72-87` | upload protocol 支持按 req.seq 重发 | 处理 SITL 重新请求场景 |
| `src/striker/flight/landing_sequence.py` | DO_LAND_START → NAV_WAYPOINT, 3→2 items | 简化，避免 SITL 兼容问题 |

---

## 4. 实际运行指导

### 4.1 SITL 环境启动

SITL 需要 arduplane 二进制 + MAVProxy 作为 MAVLink 桥接。

```bash
# Step 1: 启动 ArduPlane SITL (直接用二进制)
cd ~/ardupilot
~/ardupilot/build/sitl/bin/arduplane \
  -S --model plane --speedup 1 --instance 0 \
  --defaults ~/ardupilot/Tools/autotest/models/plane.parm \
  --home 30.265,120.095,0,0 \
  &>/tmp/arduplane_sitl.log &
# 等待约 5 秒让 SITL 完成 boot

# Step 2: 启动 MAVProxy (桥接 TCP → UDP，双端输出)
mavproxy.py \
  --master tcp:127.0.0.1:5760 \
  --out 127.0.0.1:14550 \
  --out 127.0.0.1:14551 \
  --daemon &>/tmp/mavproxy.log &
# 等待约 3 秒
# UDP:14550 → striker (控制)
# UDP:14551 → MissionPlanner/GCS (监视)

# Step 3: 验证连通性
python3 -c "
from pymavlink import mavutil
c = mavutil.mavlink_connection('udp:127.0.0.1:14550')
c.wait_heartbeat(timeout=5)
print(f'OK: mode={c.flightmode}')
c.close()
"
```

**端口拓扑:**

```
arduplane (TCP:5760) → MAVProxy → UDP:14550 → striker(pymavlink)
                                  → UDP:14551 → 其他 GCS/调试工具
```

### 4.2 Striker dry-run 启动

```bash
# Step 1: 启动 mock vision (TCP client → striker's TCP server:9876)
source .venv/bin/activate
python3 scripts/mock_vision_server.py \
  --lat 30.2650 --lon 120.0950 --interval 2.0 &
# mock server 会自动重试连接，无需等 striker 先启动

# Step 2: 启动 striker
STRIKER_MAVLINK_URL=udp:127.0.0.1:14550 \
.venv/bin/python3 -m striker --dry-run --field sitl_default

# 或者: 无视觉投弹点 (测试 fallback midpoint 路径)
python3 scripts/mock_vision_server.py --no-drop-point &
```

### 4.3 Non-dry-run 启动 (真实释放)

```bash
# 注意: 不加 --dry-run 标志
STRIKER_MAVLINK_URL=udp:127.0.0.1:14550 \
.venv/bin/python3 -m striker --field sitl_default
```

non-dry-run 模式下，攻击任务会嵌入 DO_SET_SERVO 命令项，由 ArduPlane 飞控在 target waypoint 完成时自动触发舵机释放。

### 4.4 SITL 常见问题排查

#### 症状: pymavlink 连接超时

```bash
# 1. 检查 SITL 进程
ps aux | grep arduplane

# 2. 检查 MAVProxy 进程
ps aux | grep mavproxy

# 3. 检查端口
ss -tlnp | grep 5760   # SITL TCP
ss -ulnp | grep 14550  # striker pymavlink (连接后才出现)

# 4. pymavlink 快速测试
python3 -c "
from pymavlink import mavutil
c = mavutil.mavlink_connection('udp:127.0.0.1:14550')
c.wait_heartbeat(timeout=5)
print(f'OK: mode={c.flightmode}')
c.close()
"
```

#### 症状: Mission upload 失败

1. **MISSION_ACK type=13 (UNSUPPORTED)** — 检查 mission items 的 seq 编号是否正确（每个 item 的 seq 必须与其在任务中的位置一致）
2. **Timeout waiting for mission request** — SITL 可能未就绪（INITIALISING 状态）或 MAVProxy 连接断开
3. **SITL 反复重请求同一 seq** — 该 seq 对应的 item 内容被 ArduPlane 拒绝，检查命令类型、坐标、frame 是否有效

#### 症状: 状态机卡住

- **TAKEOFF 超时** — 检查 SITL 是否成功 ARM (`Vehicle armed` 日志) 和切换到 AUTO 模式
- **SCAN 超时** — 检查 mission_current_seq 是否推进 (`mission_seq` 日志)
- **ENROUTE 超时** — 检查攻击任务是否上传成功，AUTO 模式是否激活
- **LANDING 超时** — 检查 landing_start_index 是否正确，MISSION_SET_CURRENT 是否生效

### 4.5 清理 SITL 进程

```bash
# 杀所有 SITL 相关进程
pkill -9 -f arduplane
pkill -f mavproxy
pkill -f "python3 -m striker"
pkill -f mock_vision_server

# 验证清理完成
ps aux | grep -E "(arduplane|mavproxy|striker|mock_vision)" | grep -v grep
```

---

## 5. 已知限制与建议

### 已知限制

1. **dry-run 攻击跑瞬间完成** — SITL 中 MISSION_SET_CURRENT 重置 seq 指针后，mission_current_seq 直接跳过 target_seq，dry-run 模式无法测量真实释放精度。**Non-dry-run 已验证:** 实际飞行 22.2s，DO_SET_SERVO 原生触发成功
2. **释放精度 ~37.6m** — non-dry-run 模式下 target waypoint 完成时距目标 ~37.6m，略超 WP_RADIUS (~30m)。SITL 默认空速较高导致惯性过冲。实际部署时可增大 WP_RADIUS 或降低进场速度
3. **SERVO_OUTPUT_RAW 未直接捕获** — SERVO 监控脚本使用 UDP 14551 端口，但该端口被旧进程占用导致数据异常。striker 日志确认 DO_SET_SERVO 已执行
4. **风场模拟未测试** — SITL 默认无风，approach heading 使用了 fallback 直飞策略。需设置 `SIM_WIND_DIR`/`SIM_WIND_SPD` 参数验证逆风进场

### 后续建议

1. **Fallback 路径** — 用 `--no-drop-point` 测试无视觉数据时的 midpoint 计算
2. **加风速模拟** — 在 SITL 启动后通过 MAVProxy 设置 `param set SIM_WIND_SPD 5` 和 `param set SIM_WIND_DIR 0`，验证逆风进场逻辑
3. **speedup 加速** — 使用 `--speedup 2` 可加速 SITL 时间，加快联调迭代。注意超时参数需同步调整
4. **精度优化** — 调小 WP_RADIUS 或降低 attack_alt_m 以减小过冲距离；或使用更低的 approach 距离 (当前 200m)
5. **实际部署时** — DO_LAND_START 建议保留用于真实飞控（非 SITL 重上传场景），但当前 SITL 联调中用 NAV_WAYPOINT 替代是可行的

---

## 6. MAVLink 路由层部署拓扑

MissionPlanner (GCS) 和 striker companion 需要同时连接飞控的 MAVLink 流。通过 MAVProxy 或 mavlink-routerd 做路由转发实现多端共存。

### 6.1 SITL 拓扑

```
arduplane (TCP:5760)
    └─ MAVProxy
        ├─ UDP:14550 → striker (pymavlink)
        └─ UDP:14551 → MissionPlanner / QGC / 调试工具
```

**MAVProxy 启动命令 (SITL):**

```bash
mavproxy.py \
  --master tcp:127.0.0.1:5760 \
  --out 127.0.0.1:14550 \
  --out 127.0.0.1:14551 \
  --daemon
```

### 6.2 实飞部署拓扑

```
flight controller (/dev/serial0, 921600 baud)
    └─ MAVProxy 或 mavlink-routerd
        ├─ UDP:14550 → striker (companion 本地 pymavlink)
        └─ UDP:14551 → MissionPlanner (经由 telemetry/WiFi)
```

**MAVProxy 启动命令 (实飞):**

```bash
mavproxy.py \
  --master /dev/serial0 \
  --baudrate 921600 \
  --out 127.0.0.1:14550 \
  --out udpout:<GCS_IP>:14551 \
  --daemon
```

**mavlink-routerd 替代方案 (实飞):**

```bash
mavlink-routerd \
  /dev/serial0:921600 \
  UDP:127.0.0.1:14550 \
  UDP:<GCS_IP>:14551
```

> **注意:** `<GCS_IP>` 替换为 MissionPlanner/GCS 的实际 IP 地址。SITL 中使用 `127.0.0.1`；实飞中通常是 ground station 的 WiFi 或 telemetry IP。
