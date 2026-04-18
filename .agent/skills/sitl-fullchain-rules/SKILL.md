# SITL 全链路测试规范

本 Skill 约束 SITL 全链路集成测试的启动、端口映射、服务编排和故障排查。

## 启动顺序与命令

启动顺序严格为：**SITL → MAVProxy → Striker**，每一步必须等待上一步就绪。

`scripts/run_sitl.sh` 是当前仓库提供的脚本化全链路入口；本 Skill 下方列出的命令是它所展开的手动顺序，用于排障或局部替换。

### 1. SITL (ArduPlane)

```bash
~/ardupilot/build/sitl/bin/arduplane \
  -w --model plane --speedup 1 -I 0 \
  --home "<HOME_STRING>" \
  --defaults data/fields/<field>/sitl_merged.param \
  --defaults ~/ardupilot/Tools/autotest/models/plane.parm \
  --sim-address=127.0.0.1
```

- `-w`: EEPROM 冷启动（首次或切换场地时必须）
- `--defaults` 顺序：先 `sitl_merged.param`，后 `plane.parm`（plane.parm 覆盖底层动力学）
- `--speedup`: 1=实时，2-3=加速（先 speedup 1 跑通再加速）
- 就绪标志：stdout 输出 `bind port 5760 for SERIAL0`，TCP 5760 可连接

### 2. MAVProxy

```bash
.venv/bin/mavproxy.py \
  --master tcp:127.0.0.1:5760 \
  --sitl 127.0.0.1:5501 \
  --out udp:127.0.0.1:14550 \
  --out udp:127.0.0.1:14551 \
  --daemon
```

**关键约束：**
- `--sitl 127.0.0.1:5501` **不可省略** — 这是 FG protocol 仿真数据桥，缺少则 SITL 卡死在 "Smoothing reset"
- `--out` 必须带 `udp:` 前缀 — 裸 `127.0.0.1:14550` 会开 TCP 监听，导致 Striker UDP 连接失败
- `--daemon`: 无头模式运行
- 就绪标志：SITL 日志输出 `validate_structures`，MAVProxy 收到心跳

### 3. Striker

```bash
STRIKER_TRANSPORT=udp \
STRIKER_MAVLINK_URL=udp:127.0.0.1:14550 \
STRIKER_ARM_FORCE_BYPASS=1 \
STRIKER_DRY_RUN=true \
.venv/bin/python -m striker --field <field>
```

环境变量说明：
- `STRIKER_TRANSPORT=udp`: UDP 连接模式
- `STRIKER_MAVLINK_URL=udp:127.0.0.1:14550`: 对应 MAVProxy `--out udp:127.0.0.1:14550`
- `STRIKER_ARM_FORCE_BYPASS=1`: SITL 跳过 arm 检查
- `STRIKER_DRY_RUN=true`: 不触发实际舵机释放；移除此变量可测试真实释放

## 端口映射

| 端口  | 协议 | 方向                   | 服务              | 说明                    |
|-------|------|------------------------|-------------------|-------------------------|
| 5760  | TCP  | SITL ← MAVProxy       | SITL SERIAL0      | MAVLink 指令与遥测      |
| 5501  | UDP  | SITL ↔ MAVProxy       | FG protocol       | 仿真数据桥（**关键**）  |
| 14550 | UDP  | MAVProxy → Striker    | UDP output        | Striker MAVLink 通道    |
| 14551 | UDP  | MAVProxy → GCS/备用   | UDP output        | QGroundControl 等       |

## 清理

```bash
pkill -f "python -m striker"; pkill -f mavproxy; pkill -f arduplane
```

启动前必须确认三个端口全部释放：`ss -tlnup | grep -E '5760|5501|14550|14551'`

## 故障排查表

| 症状 | 原因 | 修复 |
|------|------|------|
| SITL 卡在 "Smoothing reset" | MAVProxy 缺少 `--sitl` | 加 `--sitl 127.0.0.1:5501` |
| "bind failed on port 5760" | 残留 arduplane 进程 | `pkill -9 -f arduplane` |
| Striker 连不上 | `--out` 缺少 `udp:` 前缀 | 用 `--out udp:127.0.0.1:14550` |
| 起飞后急转坠机 | TKOFF_ALT > scan 高度 | 降低 TKOFF_ALT 到 scan altitude |
| SITL 加载参数后退出 | MIS_TOTAL > 0 但无航点 | 设 `MIS_TOTAL=0` |
| MAVProxy 立即退出 | SITL 尚未就绪 | 等 `bind port 5760` 后再启动 MAVProxy |

## 参数调整约束

调参时遵守 `sitl-param-merge-rules` skill 的 KEEP/EXCLUDE 清单：
- **只调**行为层参数：TKOFF_*, LAND_*, WP_*, NAVL1_*, AIRSPEED_*, FENCE_* 等
- **禁止调**动力学参数：PTCH_RATE_*, RLL2SRV_*, TECS_*, SERVO*, AHRS_* 等
- 小场地关键参数：TKOFF_ALT=scan高度, TKOFF_DIST=场地对角线一半, MIS_TOTAL=0

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `/sitl-test` | .claude/commands 中的 slash command |
| `conftest.py::SITLStack` | pytest 集成测试 fixture |
| `scripts/run_sitl.sh` | 手动全链路启动脚本 |

## 禁止模式

- **禁止** MAVProxy 不带 `--sitl 127.0.0.1:5501` 启动
- **禁止** `--out` 不带 `udp:` 前缀
- **禁止** 在残留进程未清理时重新启动栈
- **禁止** 在未确认 TCP 5760 就绪时启动 MAVProxy
- **禁止** 调整 SITL 动力学参数来"修复"任务行为问题
