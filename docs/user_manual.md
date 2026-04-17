# Striker 用户手册

Striker 是一套固定翼无人机自主搜查打击飞控系统。当前版本采用**场地事实驱动的程序化任务生成**：用户不再手写起飞、扫场、降落航点，而是配置围栏、跑道、接地点和扫场约束，由系统自动生成完整任务几何。

---

## 1. 系统概览

### 1.1 当前任务主链

```text
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING → COMPLETED
```

含义：

- **INIT**：加载配置、建立连接
- **PREFLIGHT**：生成并上传完整任务
- **TAKEOFF**：自动起飞并爬升到扫场高度
- **SCAN**：执行程序化 Boustrophedon 扫场路径
- **ENROUTE**：上传攻击跑任务并飞向投放点
- **RELEASE**：执行释放动作
- **LANDING**：执行自动降落序列
- **COMPLETED**：任务完成

### 1.2 核心设计变化

当前系统与早期版本相比有三点关键变化：

1. **降落进近点自动反推**  
   由 `touchdown_point + heading_deg + approach_alt_m + glide_slope_deg` 自动计算进近点。
2. **扫场路径自动生成**  
   由 `boundary + scan.spacing_m + scan.heading_deg` 自动生成 Boustrophedon 覆盖路径。
3. **起飞几何自动生成**  
   由 `touchdown_point + takeoff_heading_deg + runway_length_m` 自动生成跑道对正起飞路径。

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
    "heading_deg": 0.0
  },
  "attack_run": {
    "approach_distance_m": 200,
    "exit_distance_m": 200,
    "release_acceptance_radius_m": 0
  },
  "safety_buffer_m": 50.0
}
```

### 4.2 程序化生成规则

#### 降落几何

系统自动根据：

- `landing.touchdown_point`
- `landing.heading_deg`
- `landing.approach_alt_m`
- `landing.glide_slope_deg`

反推出降落进近点。

公式：

```text
distance = delta_alt / tan(glide_slope_deg)
```

SITL 默认场地中：

- `approach_alt_m = 30m`
- `glide_slope_deg = 3°`
- 推导距离约 `572.4m`，与理论 `573m` 一致

#### 扫场几何

系统自动根据：

- `boundary.polygon`
- `scan.altitude_m`
- `scan.spacing_m`
- `scan.heading_deg`

生成 Boustrophedon 扫场路径。

#### 起飞几何

系统自动根据：

- `landing.touchdown_point`
- `landing.heading_deg`
- `landing.runway_length_m`

生成跑道对正的起飞起点和爬升点。

### 4.3 校验规则

加载场地配置时，系统会校验：

- 围栏闭合
- 接地点在围栏内
- 跑道长度为正数
- 降落参数组合合法
- 程序化推导出的进近点不越界

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

扫场完成后：

1. 若视觉系统提供平滑后的投放点，则直接使用
2. 若没有视觉结果，则使用**兜底中点**：
   - 扫场最后一个航点
   - 降落接地点
   的地理中点

随后进入：

```text
SCAN → ENROUTE → RELEASE → LANDING
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
./scripts/run_sitl.sh sitl_default
```

该脚本会：

- 使用验证过的 `--home 30.2610,120.0950,0,180`
- 加载 `data/fields/sitl_default/sitl_merged.param`
- 加载 `~/ardupilot/Tools/autotest/models/plane.parm`
- 从仓库 `.venv` 启动 MAVProxy
- 将 SITL / MAVProxy 日志保存在 `runtime_data/manual_sitl/<timestamp>/`

#### 1）启动 ArduPlane SITL

```bash
/home/xbp/ardupilot/build/sitl/bin/arduplane \
  -w --model plane --speedup 1 -I 0 \
  --home 30.2610,120.0950,0,180 \
  --defaults /home/xbp/dev-zju/cuax-autodriv/data/fields/sitl_default/sitl_merged.param \
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
  INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING
  ```
- Landing approach 自动反推距离：`572.4m`
- Full mission upload：`16 items`
- Attack mission upload：`8 items`
- Scan path：`10 waypoints / 5 sweeps`

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
