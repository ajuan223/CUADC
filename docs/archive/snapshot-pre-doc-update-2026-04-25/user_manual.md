# Striker 用户手册

Striker 是一套固定翼无人机自主搜查打击飞控系统。当前版本与 Mission Planner 紧密结合：飞控端预烧录全量航点任务，Striker 负责下载任务并在指定时刻通过 GUIDED 模式接管飞行执行高精度投弹打击。

---

## 1. 系统概览

### 1.1 当前任务主链

```text
INIT → STANDBY → SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR → COMPLETED
```

含义：

- **INIT**：加载配置、建立连接
- **STANDBY**：从飞控下载并解析预烧录的全量任务
- **SCAN_MONITOR**：监控飞机执行预烧录的起飞和扫场流程，等待到达盘旋点(Loiter)
- **GUIDED_STRIKE**：进入 GUIDED 模式，接管控制权飞向目标投弹点执行攻击跑
- **RELEASE_MONITOR**：执行并确认载荷释放动作
- **LANDING_MONITOR**：切回 AUTO 模式，恢复飞控预烧录的自动降落序列
- **COMPLETED**：任务完成

### 1.2 核心设计变化

当前系统经历了核心架构变更：

1. **预烧录任务架构**  
   放弃了以前的动态航点生成（Procedural Generation）。起飞、扫场、降落等完整航线由操作员通过 Mission Planner 预先规划并烧录至飞控。
2. **GUIDED 接管**  
   不再飞行中动态覆写或上传子任务，而是在扫场结束后直接使用 GUIDED 模式（DO_REPOSITION）接管飞机进行投弹，然后切回 AUTO 降落。
3. **极简系统边界**  
   Striker 仅负责“何时接管”与“朝哪投弹”，不干预固定翼起降等高风险基础飞行控制。

---

## 2. 安装

### 2.1 环境要求

| 项目 | 要求 |
|---|---|
| Python | 3.13 |
| 系统 | Linux / Ubuntu / Raspberry Pi OS |
| 包管理 | `uv` |
| 飞控 | ArduPlane |
| 通信 | 串口或 UDP MAVLink |

### 2.2 安装项目

```bash
git clone <repo-url> /opt/striker
cd /opt/striker
uv sync
```

GPIO 投放支持：

```bash
uv sync --extra gpio
```

---

## 3. 运行配置

Striker 的常用配置来源有：

- 代码默认值
- `config.json`
- `STRIKER_*` 环境变量
- CLI 启动参数（如 `--field`、`--dry-run`）

### 3.1 常用配置项

| 字段 | 默认值 | 说明 |
|---|---|---|
| `transport` | `serial` | `serial` 或 `udp` |
| `serial_port` | `/dev/serial0` | 串口设备 |
| `serial_baud` | `921600` | 串口波特率 |
| `mavlink_url` | `""` | MAVLink URL，适合 SITL |
| `field` | `sitl_default` | 场地配置名称 |
| `dry_run` | `false` | 干跑模式 |
| `cruise_speed_mps` | `12.0` | 巡航速度 (m/s) |
| `arm_force_bypass` | `false` | 起飞前 ARM 强制旁路 |
| `release_method` | `mavlink` | `mavlink` 或 `gpio` |
| `release_channel` | `6` | DO_SET_SERVO 通道 |
| `release_pwm_open` | `2000` | 释放 PWM |
| `vision_receiver_type` | `tcp` | `tcp` 或 `udp` |
| `vision_host` | `0.0.0.0` | 视觉监听地址 |
| `vision_port` | `9876` | 视觉监听端口 |
| `log_level` | `INFO` | 日志级别 |

### 3.2 常见启动方式

标准启动：

```bash
uv run python -m striker
```

干跑模式：

```bash
uv run python -m striker --dry-run
```

指定场地：

```bash
uv run python -m striker --field sitl_default
```

使用 UDP 连接 SITL：

```bash
STRIKER_TRANSPORT=udp uv run python -m striker --field sitl_default
```

---

## 4. 场地配置（Field Profile）

每个场地位于：

```text
data/fields/<field-name>/field.json
```

### 4.1 当前 schema

```json
{
  "name": "SITL Default",
  "description": "Default field profile for SITL testing at Zijingang",
  "coordinate_system": "WGS84",
  "boundary": {
    "description": "Test flight area",
    "polygon": [
      {"lat": 30.2700, "lon": 120.0900},
      {"lat": 30.2700, "lon": 120.1000},
      {"lat": 30.2600, "lon": 120.1000},
      {"lat": 30.2600, "lon": 120.0900},
      {"lat": 30.2700, "lon": 120.0900}
    ]
  },
  "landing": {
    "description": "North-south runway approach",
    "touchdown_point": {
      "lat": 30.2610,
      "lon": 120.0950,
      "alt_m": 0.0
    },
    "heading_deg": 180.0,
    "glide_slope_deg": 3.0,
    "approach_alt_m": 30.0,
    "runway_length_m": 200.0,
    "use_do_land_start": true
  },
  "scan": {
    "description": "Lawnmower scan pattern",
    "altitude_m": 80.0,
    "spacing_m": 200.0,
    "heading_deg": 0.0,
    "boundary_margin_m": 100.0
  },
  "attack_run": {
    "approach_distance_m": 200,
    "exit_distance_m": 200,
    "release_acceptance_radius_m": 0,
    "fallback_drop_point": {
      "lat": 30.2650,
      "lon": 120.0950,
      "alt_m": 0.0
    }
  },
  "safety_buffer_m": 50.0
}
```

### 4.2 兜底与边界作用

当前 `field.json` 不再用于自动生成航点，主要提供：

- `fallback_drop_point`：当无视觉输入时使用的默认投弹点
- `boundary`：结合 `safety_buffer_m` 进行飞行安全越界监控
- `attack_run`：进场、退场等攻击跑参数

### 4.3 校验规则

加载场地配置时，系统会校验：

- 围栏闭合
- 配置参数格式合法

预检命令：

```bash
STRIKER_FIELD=sitl_default uv run python scripts/preflight_check.py
```

---

## 5. 视觉与投放点

Striker 接收的是**投放点坐标**，不是原始识别目标。

### 5.1 视觉输入

视觉系统通过 TCP/UDP 将投放点发送给 Striker，Striker 内部使用 `DropPointTracker` 做平滑。

### 5.2 扫场结束后的投放点决策

扫场完成后，系统按照以下 **优先级（3级兜底策略）** 确定最终投放点：

1. **外部视觉传入**：若视觉系统提供平滑后的投放点，则直接使用。
2. **场地预设兜底点**：若无视觉结果，尝试使用 `field.json` 中的 `attack_run.fallback_drop_point`。
3. **几何质心**：若预设兜底点未配置，则计算当前飞行边界区域的几何质心作为最终兜底。

随后进入：

```text
SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR
```

---

## 6. 投放系统

### 6.1 MAVLink 投放

默认使用 `DO_SET_SERVO`：

```json
{
  "release_method": "mavlink",
  "release_channel": 6,
  "release_pwm_open": 2000,
  "release_pwm_close": 1000
}
```

### 6.2 GPIO 投放

树莓派可使用 GPIO：

```json
{
  "release_method": "gpio",
  "release_gpio_pin": 17,
  "release_gpio_active_high": true
}
```

### 6.3 干跑模式

`dry_run=true` 时不执行真实释放，仅记录流程日志。

---

## 7. SITL 使用说明

### 7.1 推荐启动顺序

优先使用仓库内置脚本：

```bash
./scripts/run_sitl.sh <field>
```

该脚本会：

- 从 field profile 推导 `--home`
- 加载 `data/fields/<field>/sitl_merged.param`
- 加载 `~/ardupilot/Tools/autotest/models/plane.parm`
- 从仓库 `.venv` 启动 MAVProxy
- 自动拉起 Striker dry-run
- 将 SITL / MAVProxy / Striker 日志保存在 `runtime_data/manual_sitl/<field>/<timestamp>/`

#### 1）启动 ArduPlane SITL

```bash
/home/xbp/ardupilot/build/sitl/bin/arduplane \
  -w --model plane --speedup 1 -I 0 \
  --home <derived-from-field-profile> \
  --defaults /home/xbp/dev-zju/cuax-autodriv/data/fields/<field>/sitl_merged.param \
  --defaults /home/xbp/ardupilot/Tools/autotest/models/plane.parm \
  --sim-address=127.0.0.1
```

#### 2）启动 MAVProxy

```bash
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/mavproxy.py \
  --master tcp:127.0.0.1:5760 \
  --out 127.0.0.1:14550 \
  --out 127.0.0.1:14551
```

#### 3）启动 Striker

```bash
STRIKER_TRANSPORT=udp \
STRIKER_ARM_FORCE_BYPASS=1 \
uv run python -m striker --field sitl_default
```

### 7.2 已验证的 SITL 结果

已完成以下验证：

- 正确 home 位置：`30.2610, 120.0950`
- 完整主链：
  ```text
  INIT → STANDBY → SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR
  ```
- Mission Download 与解析正常
- GUIDED 模式接管攻击跑正常执行

---

## 8. 故障排查

### 8.1 启动后连接 `/dev/serial0` 失败

现象：

```text
No such file or directory: '/dev/serial0'
```

原因：默认 `transport=serial`，而 SITL 需要 UDP。

解决：

```bash
STRIKER_TRANSPORT=udp uv run python -m striker --field sitl_default
```

### 8.2 `plane.parm` 找不到

不要使用不存在的：

```text
Tools/autotest/default_params/plane.parm
```

应使用：

```text
Tools/autotest/models/plane.parm
```

### 8.3 视觉端口 9876 被占用

现象：

```text
OSError: [Errno 98] address already in use
```

解决：

```bash
pkill -9 -f 'python.*striker'
```

### 8.4 任务上传卡在 landing items

若日志中出现反复 `SITL re-requested item`，检查 `src/striker/flight/navigation.py` 是否对 landing items 做了正确的 seq 重编号。

### 8.5 飞机初始位置不对

若 SITL home 仍在 Canberra（`-35.363262, 149.165237`），说明未设置正确 `--home` 参数。应显式传入场地接地点附近坐标。

---

## 9. 常用命令

```bash
# 运行单元测试
uv run pytest tests/unit/

# 运行场地预检
STRIKER_FIELD=sitl_default uv run python scripts/preflight_check.py

# 启动 Striker（SITL）
STRIKER_TRANSPORT=udp STRIKER_ARM_FORCE_BYPASS=1 uv run python -m striker --field sitl_default

# 查看日志
tail -f /tmp/striker.log

# 杀掉旧进程
pkill -9 -f 'python.*striker'
pkill -9 -f mavproxy
pkill -9 -f arduplane
```
