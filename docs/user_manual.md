# Striker 用户手册

Striker 是一套固定翼无人机自主搜查打击飞控系统。本手册描述如何安装、配置、运行和维护该系统。

---

## 目录

1. [系统要求](#1-系统要求)
2. [安装](#2-安装)
3. [配置系统](#3-配置系统)
4. [场地配置 (Field Profile)](#4-场地配置-field-profile)
5. [启动程序](#5-启动程序)
6. [任务状态机](#6-任务状态机)
7. [安全监控](#7-安全监控)
8. [视觉系统](#8-视觉系统)
9. [投放系统](#9-投放系统)
10. [SITL 仿真测试](#10-sitl-仿真测试)
11. [树莓派部署](#11-树莓派部署)
12. [日志与调试](#12-日志与调试)
13. [故障排查](#13-故障排查)
14. [命令速查](#14-命令速查)

---

## 1. 系统要求

| 项目 | 最低要求 |
|------|---------|
| Python | >= 3.13 |
| 操作系统 | Raspberry Pi OS (RPi5) / Ubuntu (Orin) / 任意 Linux (SITL) |
| 包管理器 | [uv](https://docs.astral.sh/uv/) |
| 飞控硬件 | 运行 ArduPlane 固件的 Pixhawk 系列 |
| 通信链路 | 串口 / UDP MAVLink 连接 |

---

## 2. 安装

### 2.1 安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2.2 克隆并安装项目

```bash
git clone <repo-url> /opt/striker
cd /opt/striker
uv sync
```

如需 GPIO 投放支持（树莓派）：

```bash
uv sync --extra gpio
```

### 2.3 验证安装

```bash
uv run python -m striker
# 输出: 0.1.0
```

---

## 3. 配置系统

Striker 使用 **三层优先级** 配置系统：

```
代码默认值 (最低) < config.json < 环境变量 STRIKER_* (最高)
```

### 3.1 方式一：config.json

复制模板并按需修改：

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "serial_port": "/dev/serial0",
  "serial_baud": 921600,
  "transport": "serial",
  "field": "zijingang",
  "dry_run": false,
  "log_level": "INFO"
}
```

### 3.2 方式二：环境变量

复制模板并取消注释所需项：

```bash
cp .env.example .env
```

环境变量前缀为 `STRIKER_`，字段名全部大写。示例：

```bash
export STRIKER_SERIAL_PORT=/dev/ttyUSB0
export STRIKER_FIELD=zijingang
export STRIKER_DRY_RUN=true
export STRIKER_LOG_LEVEL=DEBUG
```

### 3.3 方式三：命令行参数

启动时直接覆盖：

```bash
uv run python -m striker --field zijingang --dry-run
```

CLI 参数优先级最高（覆盖环境变量）。

### 3.4 配置字段一览

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `serial_port` | str | `/dev/serial0` | MAVLink 串口设备 |
| `serial_baud` | int | `921600` | 串口波特率 |
| `transport` | str | `serial` | 传输方式: `serial` 或 `udp` |
| `mavlink_url` | str | `""` | MAVLink 连接 URL（覆盖 transport，如 `udp:127.0.0.1:14550`）|
| `battery_min_v` | float | `11.1` | 最低电池电压 (V) |
| `stall_speed_mps` | float | `10.0` | 最低空速 (m/s) |
| `heartbeat_timeout_s` | float | `3.0` | 心跳超时 (s) |
| `safety_check_interval_s` | float | `1.0` | 安全检查间隔 (s) |
| `field` | str | `sitl_default` | 场地配置名称 |
| `dry_run` | bool | `false` | 干跑模式（不实际投放） |
| `release_method` | str | `mavlink` | 投放方式: `mavlink` 或 `gpio` |
| `release_channel` | int | `6` | MAVLink 投放通道号 |
| `release_pwm_open` | int | `2000` | 投放开 PWM 值 |
| `release_pwm_close` | int | `1000` | 投放关 PWM 值 |
| `release_gpio_pin` | int | `17` | GPIO 投放引脚号 |
| `release_gpio_active_high` | bool | `true` | GPIO 高电平触发 |
| `vision_receiver_type` | str | `tcp` | 视觉接收类型: `tcp` 或 `udp` |
| `vision_host` | str | `0.0.0.0` | 视觉监听地址 |
| `vision_port` | int | `9876` | 视觉监听端口 |
| `recorder_output_path` | str | `flight_log.csv` | 飞行日志路径 |
| `recorder_sample_rate_hz` | float | `1.0` | 日志采样率 (Hz) |
| `log_level` | str | `INFO` | 日志级别: DEBUG/INFO/WARNING/ERROR |

---

## 4. 场地配置 (Field Profile)

每个飞行场地对应 `data/fields/` 下的一个子目录，包含 `field.json`。

### 4.1 目录结构

```
data/fields/
  sitl_default/
    field.json
  zijingang/
    field.json
```

### 4.2 field.json 结构

```json
{
  "name": "场地名称",
  "description": "场地描述",
  "coordinate_system": "WGS84",
  "boundary": {
    "description": "围栏描述",
    "polygon": [
      {"lat": 30.2700, "lon": 120.0900},
      {"lat": 30.2700, "lon": 120.1000},
      {"lat": 30.2600, "lon": 120.1000},
      {"lat": 30.2600, "lon": 120.0900},
      {"lat": 30.2700, "lon": 120.0900}
    ]
  },
  "landing": {
    "description": "降落航线描述",
    "approach_waypoint": {
      "lat": 30.2615,
      "lon": 120.0945,
      "alt_m": 30.0
    },
    "touchdown_point": {
      "lat": 30.2610,
      "lon": 120.0950,
      "alt_m": 0.0
    },
    "glide_slope_deg": 3.0,
    "heading_deg": 180.0
  },
  "scan_waypoints": {
    "description": "扫描航线描述",
    "altitude_m": 80.0,
    "waypoints": [
      {"lat": 30.2690, "lon": 120.0910},
      {"lat": 30.2690, "lon": 120.0990}
    ]
  },
  "loiter_point": {
    "description": "盘旋点描述",
    "lat": 30.2650,
    "lon": 120.0950,
    "alt_m": 80.0,
    "radius_m": 80.0
  },
  "safety_buffer_m": 50.0
}
```

### 4.3 地理校验规则

系统加载场地配置时会自动校验：

- 围栏多边形自动闭合（首尾点相同）
- 所有扫描航点必须在围栏多边形内部
- 降落进近点必须在围栏内部
- 接地点必须在围栏内部
- 盘旋点必须在围栏内部
- `safety_buffer_m` 必须为正数

如果校验失败，程序启动时将报错退出。

### 4.4 创建新场地配置

1. 在 `data/fields/` 下创建以场地名命名的目录
2. 编写 `field.json`，按上述结构填写各坐标
3. 运行预检验证：

```bash
uv run python scripts/preflight_check.py -- --field <场地名>
```

或直接：

```bash
STRIKER_FIELD=<场地名> uv run python scripts/preflight_check.py
```

---

## 5. 启动程序

### 5.1 标准启动

```bash
uv run python -m striker
```

程序将：
1. 读取 `config.json` + 环境变量 + CLI 参数，合并配置
2. 加载并校验场地配置
3. 建立 MAVLink 连接
4. 启动视觉接收器
5. 启动异步任务组（MAVLink 连接、心跳、安全监控、飞行记录、状态机、视觉派发）
6. 状态机从 INIT 状态开始运行

### 5.2 干跑模式

用于调试，不执行实际投放动作：

```bash
uv run python -m striker --dry-run
# 或
STRIKER_DRY_RUN=true uv run python -m striker
```

### 5.3 指定场地

```bash
uv run python -m striker --field zijingang
# 或
STRIKER_FIELD=zijingang uv run python -m striker
```

### 5.4 列出可用场地

```bash
uv run python -m striker --list-fields
```

查看 `data/fields/` 下的目录名即可。

### 5.5 停止程序

按 `Ctrl+C` 或发送 SIGTERM 信号。程序会执行优雅关闭：
- 停止状态机运行循环
- 停止飞行记录器
- 断开 MAVLink 连接

---

## 6. 任务状态机

Striker 的核心是一个 10 状态异步有限状态机。

### 6.1 状态流转图

```
INIT ──→ PREFLIGHT ──→ TAKEOFF ──→ SCAN ──→ ENROUTE ──→ RELEASE ──→ LANDING ──→ COMPLETED
                    │                                          ↑
                    │      ┌──── 投弹点决策 ────┐              │
                    │      │                    │              │
                    │   视觉投弹点          兜底中点计算       │
                    │   (直接使用)    (扫场终点+降落参考中点)  │
                    │      │                    │              │
                    └──────┴────────────────────┴──────────────┘
                                              (任意状态)
                                         ┌────────────┐
                                         │  OVERRIDE  │ (终端)
                                         │  EMERGENCY │ → LANDING
                                         └────────────┘
```

### 6.2 各状态说明

| 状态 | 说明 | 触发条件 |
|------|------|---------|
| **INIT** | 初始化，加载配置 | 系统启动 |
| **PREFLIGHT** | 飞前检查，上传任务航线 | 初始化完成 |
| **TAKEOFF** | 自动起飞 | 任务上传成功 |
| **SCAN** | 沿预设航点执行扫描航线 | 起飞到达高度 |
| **ENROUTE** | 飞向投弹点（GUIDED 模式） | 扫场完成，投弹点已确定 |
| **RELEASE** | 执行投放 | 到达投弹点附近 |
| **LANDING** | 执行预设降落航线 | 投放完成 |
| **COMPLETED** | 任务完成（终端） | 降落成功 |
| **OVERRIDE** | 飞手接管（终端） | 飞控切换到 MANUAL/STABILIZE/FBWA |
| **EMERGENCY** | 紧急状态 | 安全检查失败（心跳丢失等） |

### 6.3 投弹点决策

扫场完成后执行投弹点决策：

1. **视觉投弹点**：如果视觉系统在扫描期间发送了投弹点坐标，直接使用该坐标飞向投弹点
2. **兜底中点**：如果未收到视觉投弹点，计算扫场结束点与降落参考点的地理中点作为投弹点

两条路径后续行为完全一致：ENROUTE → RELEASE → LANDING。

### 6.3 全局拦截器

以下事件可从任意状态（除终端状态外）触发：

- **OverrideEvent**: 飞手切换飞控模式 → 进入 OVERRIDE
- **EmergencyEvent**: 安全监控检测到异常 → 进入 EMERGENCY → 可转入 LANDING

---

## 7. 安全监控

安全监控器以协程形式持续运行，周期性检查以下项目：

| 检查项 | 默认阈值 | 说明 |
|--------|---------|------|
| 电池电压 | >= 11.1V | 低于阈值触发紧急 |
| 心跳 | 超时 3.0s | MAVLink 心跳丢失触发紧急 |
| 空速 | >= 10.0 m/s | 低于失速速度触发紧急 |
| GPS | - | GPS 锁定检查 |
| 电子围栏 | 场地边界 | 飞出围栏触发紧急 |
| 飞控模式 | - | 切换到 MANUAL/STABILIZE/FBWA 触发 OverrideEvent（使用 `connection.flightmode` 属性检测） |

安全检查间隔由 `safety_check_interval_s` 控制（默认 1 秒）。

---

## 8. 视觉系统

Striker 通过 TCP/UDP 接收外部视觉系统发送的投弹点坐标。

### 8.1 配置

```json
{
  "vision_receiver_type": "tcp",
  "vision_host": "0.0.0.0",
  "vision_port": 9876
}
```

### 8.2 投弹点接收流程

1. 程序启动时先启动视觉接收器（在任务组之前）
2. `_vision_dispatch` 协程以 100ms 间隔轮询接收器
3. 收到新投弹点后推入 `DropPointTracker`
4. `DropPointTracker` 使用滑动窗口中值滤波消除抖动
5. 扫场完成时由 SCAN 状态执行投弹点决策：有平滑投弹点则使用视觉点，否则计算兜底中点

### 8.3 外部视觉系统对接

外部视觉系统需向配置的地址发送投弹点坐标（非靶标坐标）。视觉系统应预先完成目标识别和投弹点解算，Striker 直接使用该坐标飞向投弹。协议格式请参考 `src/striker/vision/` 下的接收器实现。

---

## 9. 投放系统

### 9.1 MAVLink 投放（默认）

通过 MAVLink `DO_SET_SERVO` 命令控制舵机：

```json
{
  "release_method": "mavlink",
  "release_channel": 6,
  "release_pwm_open": 2000,
  "release_pwm_close": 1000
}
```

### 9.2 GPIO 投放

通过树莓派 GPIO 直接控制：

```json
{
  "release_method": "gpio",
  "release_gpio_pin": 17,
  "release_gpio_active_high": true
}
```

需要安装 GPIO 依赖：

```bash
uv sync --extra gpio
```

### 9.3 干跑模式

`dry_run = true` 时投放器仅记录日志，不执行物理动作。

### 9.4 投弹点来源

投弹点由以下两种方式之一确定（不使用弹道解算）：

1. **视觉投弹点**：外部视觉系统直接发送投弹点 GPS 坐标，Striker 飞向该点执行投放
2. **兜底中点**：扫场结束时未收到视觉投弹点，系统计算扫场最后一个航点与降落参考点之间的地理中点（geopy geodesic）作为投弹点

`BallisticCalculator` 作为独立工具类保留在代码库中，但不在主任务流程中调用。

---

## 10. SITL 仿真测试

### 10.1 搭建 SITL 环境

```bash
./scripts/setup_sitl.sh
```

该脚本会：
- 克隆 ArduPilot 到 `~/ardupilot`
- 更新子模块
- 编译 ArduPlane SITL 二进制

可通过环境变量自定义路径：

```bash
ARDUPILOT_DIR=/path/to/ardupilot ./scripts/setup_sitl.sh
```

### 10.2 启动 SITL

```bash
./scripts/run_sitl.sh [场地名]
# 默认场地: sitl_default
```

SITL 启动后 MAVLink 在 `udp:127.0.0.1:14550` 可用。

### 10.3 运行 Striker 连接 SITL

```bash
# 设置环境标识
export MAVLINK_SITL=1

# 使用 UDP 连接
uv run python -m striker --field sitl_default --dry-run
```

或者配置 `config.json`：

```json
{
  "transport": "udp",
  "mavlink_url": "udp:127.0.0.1:14550",
  "field": "sitl_default",
  "dry_run": true
}
```

### 10.4 平台检测

系统自动检测运行平台：

| 条件 | 平台 |
|------|------|
| 环境变量 `MAVLINK_SITL` 已设置 | SITL |
| `/proc/device-tree/model` 含 "Raspberry Pi 5" | RPi5 |
| `/etc/nv_tegra_release` 存在 | Orin |
| 其他 | Unknown |

可强制覆盖：

```bash
export STRIKER_PLATFORM=sitl
```

---

## 11. 树莓派部署

### 11.1 一键部署

```bash
./scripts/setup_rpi5.sh
```

该脚本会：
- 安装 Python 3.13 和系统依赖
- 安装 uv
- 安装 Striker 到 `/opt/striker`
- 配置 systemd 服务

### 11.2 手动部署

```bash
# 安装依赖
sudo apt-get install python3.13 python3.13-venv

# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目
cd /opt/striker
uv sync

# 配置
cp config.example.json config.json
# 编辑 config.json 设置 serial_port 等
```

### 11.3 systemd 管理

```bash
# 启动
sudo systemctl start striker

# 查看状态
sudo systemctl status striker

# 查看日志
journalctl -u striker -f

# 停止
sudo systemctl stop striker

# 开机自启
sudo systemctl enable striker
```

---

## 12. 日志与调试

### 12.1 日志级别

通过配置控制：

```bash
STRIKER_LOG_LEVEL=DEBUG uv run python -m striker
```

| 级别 | 用途 |
|------|------|
| DEBUG | 开发调试，输出所有状态机循环细节 |
| INFO | 正常运行，记录状态转换和关键事件 |
| WARNING | 安全检查失败、异常情况 |
| ERROR | 严重错误 |

### 12.2 日志格式

- **开发环境**: 控制台彩色输出 (structlog ConsoleRenderer)
- **生产环境**: JSON 格式 (便于日志聚合)

### 12.3 飞行记录

飞行记录器以 CSV 格式持续记录遥测数据：

```json
{
  "recorder_output_path": "flight_log.csv",
  "recorder_sample_rate_hz": 1.0
}
```

---

## 13. 故障排查

### 程序启动即退出："Field profile validation failed"

**原因**: 场地配置坐标有误（航点在围栏外、多边形未闭合等）

**排查**:
```bash
uv run python scripts/preflight_check.py
```
查看具体校验失败信息，修正 `data/fields/<name>/field.json`。

### 无法连接 MAVLink

**排查步骤**:
1. 检查串口设备是否存在: `ls /dev/serial0` 或 `ls /dev/ttyUSB0`
2. 检查波特率是否匹配飞控设置
3. 如使用 UDP，确认 SITL 或 MAVProxy 已启动且端口正确
4. 检查 `transport` 和 `mavlink_url` 配置

### 心跳超时

**现象**: 安全监控持续报 "Safety check failed: heartbeat"

**排查**:
1. 确认飞控已上电并运行
2. 检查串口/UDP 连接是否正常
3. 增大超时: `STRIKER_HEARTBEAT_TIMEOUT_S=5.0`

### 状态机不推进

**排查**:
1. 将日志级别设为 DEBUG 查看状态机循环输出
2. 检查当前状态是否在等待某个条件（如 SCAN 等待任务进度、ENROUTE 等待到达投弹点）
3. 确认视觉系统是否正常发送投弹点坐标

### 安全监控误报

**排查**:
1. 调整阈值: `STRIKER_BATTERY_MIN_V`, `STRIKER_STALL_SPEED_MPS`
2. 增大检查间隔: `STRIKER_SAFETY_CHECK_INTERVAL_S=2.0`
3. 检查遥测数据是否正常上报

---

## 14. 命令速查

```bash
# 安装
uv sync                          # 安装核心依赖
uv sync --extra gpio             # 安装 GPIO 支持

# 启动
uv run python -m striker                           # 默认配置启动
uv run python -m striker --field zijingang         # 指定场地
uv run python -m striker --dry-run                 # 干跑模式
uv run python -m striker --field sitl_default --dry-run  # SITL 测试

# SITL
./scripts/setup_sitl.sh          # 搭建 SITL 环境
./scripts/run_sitl.sh            # 启动 ArduPlane SITL
MAVLINK_SITL=1 uv run python -m striker --dry-run  # 连接 SITL

# 预检
uv run python scripts/preflight_check.py           # 验证配置和场地
STRIKER_FIELD=zijingang uv run python scripts/preflight_check.py  # 验证指定场地

# 测试
uv run pytest                    # 运行全部测试
uv run pytest tests/unit/        # 仅单元测试
uv run pytest tests/integration/ # 仅集成测试

# 代码质量
uv run ruff check .              # Lint 检查
uv run ruff check --fix .        # 自动修复
uv run mypy                      # 类型检查

# 树莓派
sudo systemctl start striker     # 启动服务
sudo systemctl status striker    # 查看状态
journalctl -u striker -f         # 实时日志
```
