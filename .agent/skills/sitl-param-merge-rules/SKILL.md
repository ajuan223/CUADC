# SITL 参数合并规范

将实飞 ArduPlane 参数（`.param` 文件）与 SITL 默认参数合并时，**只注入任务行为/操控逻辑参数**，**禁止**覆盖 SITL 飞行动力学、PID、传感器和硬件映射参数。

## 目标

- 最大化保留真实飞机的任务行为语义：起飞、导航、降落、failsafe、围栏、模式逻辑
- 最大化保留 SITL 默认机体的稳定性：气动模型、PID、舵面混控、传感器配置仍由 `plane.parm` 决定
- 避免“实飞参数直接套进 SITL 导致筒滚/发散/假故障”

## 架构约束

- SITL 必须始终以 `plane.parm` 作为飞行动力学基线启动
- 实飞参数文件是**行为层覆盖源**，不是完整替代源
- 参数合并优先级：`SITL plane.parm` → `筛选后的 merged.param / PARAM_SET 覆盖`
- 合并输出文件统一写入：`data/fields/sitl_default/sitl_merged.param`
- 当前实飞参数源文件：`~/下载/cuavx7_260329.param`
- 若仅为复现实飞任务行为，优先选择 **筛选后通过 MAVLink PARAM_SET 注入**，不要改动 SITL 默认启动文件

### 允许注入（KEEP）

这些参数保留真实飞机的“行为逻辑”，通常不直接破坏 SITL 机体稳定性：

| 类别 | 参数前缀/名称 | 说明 |
|------|---------------|------|
| 降落逻辑 | `LAND_*` | flare、进近、风补偿、下滑逻辑 |
| 航点逻辑 | `WP_*` | 接受半径、任务航点判定 |
| 导航逻辑 | `NAVL1_*` | L1 导航阻尼/周期 |
| 起飞逻辑 | `TKOFF_*` | 起飞加速、爬升行为 |
| 空速目标 | `AIRSPEED_*` | 巡航/目标空速 |
| 滑翔逻辑 | `GLIDE_*` | 滑翔坡度与相关约束 |
| 油门基准 | `TRIM_THROTTLE` | 巡航油门 |
| 缩放基准 | `SCALING_SPEED` | 速度缩放参考 |
| 模式映射 | `FLTMODE*` | 模式开关语义 |
| 解锁逻辑 | `ARMING_*` | ARM 检查行为 |
| 围栏逻辑 | `FENCE_*` | 围栏行为 |
| failsafe | `FS_*` | 失效保护 |
| 电池逻辑 | `BATT_*` | 电池阈值 |
| 返回逻辑 | `RTL_*` | RTL 高度/半径 |
| 任务逻辑 | `MIS_*` | 任务执行相关 |
| Guided 行为 | `GUIDED_*` | Guided 控制参数 |
| 集结点 | `RALLY_*` | rally 行为 |
| Home 行为 | `HOME_*` | home 重置/相关逻辑 |
| 低速约束 | `MIN_GROUNDSPEED` | 最低地速 |
| 稳定模式行为 | `STAB_*` | 稳定模式行为层 |
| 摇杆混控 | `STICK_MIXING` | stick mixing 逻辑 |
| 巡航行为 | `CRUISE_*` | cruise 模式行为 |
| 飞行选项 | `FLIGHT_OPTIONS` | 功能开关位 |
| 方向舵行为 | `RUDD_*` | 行为层方向舵参数 |
| 降落伞 | `CHUTE_*` | chute 行为 |
| 精确降落 | `PLND_*` | precision landing 逻辑 |
| 测距降落 | `RNGFND_LANDING` | 降落辅助 |

### 禁止注入（EXCLUDE）

这些参数与机体模型、舵面、传感器、飞控硬件强相关，直接套入 SITL 高概率导致异常：

| 类别 | 参数前缀/名称 | 原因 |
|------|---------------|------|
| 速率 PID | `PTCH_RATE_*`, `RLL_RATE_*`, `YAW_RATE_*` | 内环 PID 与机体模型强耦合 |
| 舵面控制 | `PTCH2SRV_*`, `RLL2SRV_*`, `YAW2SRV_*`, `STEER2SRV_*` | 舵面/地面转向控制律 |
| 能量控制 | `TECS_*` | 与空速、升阻特性强耦合 |
| 前馈/特技 | `KFF_*`, `ACRO_*` | 飞行动力学相关 |
| 舵机映射 | `SERVO*` | 舵面功能、行程、方向、trim |
| RC 校准 | `RC1`-`RC16`, `RCMAP_*` | 遥控器与通道硬件相关 |
| 传感器姿态 | `AHRS_*`, `INS_*`, `EK3_*` | IMU / EKF / 姿态估计 |
| 磁罗盘 | `COMPASS_*` | 罗盘硬件校准 |
| 气压/GPS/空速硬件 | `BARO*`, `GPS*`, `ARSPD_*` | 传感器硬件配置 |
| 板级/总线/串口 | `BRD_*`, `CAN_*`, `SERIAL*` | 飞控硬件平台相关 |
| 显示/通知 | `OSD*`, `NTF_*` | 外设配置，不影响任务语义 |
| MAVLink 流率 | `SR*` | 链路速率，不用于拟真飞行行为 |
| 机体特殊面 | `DSPOILER*`, `DSPOILR_*`, `FBWB_*`, `MAN_*` | 机体/模式专项控制 |
| 调参与状态 | `AUTOTUNE_*`, `TUNE_*`, `LOG_*`, `STAT_*` | 调试或运行态信息 |

## 合并流程

1. **启动基线 SITL**
   - 使用 `plane.parm` 启动 ArduPlane SITL
   - 验证 SITL 心跳正常后再进行参数覆盖

2. **筛选实飞参数**
   - 从实飞 `.param` 文件读取所有参数
   - 仅保留 KEEP 白名单中的参数
   - 生成 `data/fields/sitl_default/sitl_merged.param`

3. **应用参数**
   - 优先方式：通过 MAVLink `PARAM_SET` 注入已筛选参数
   - 禁止方式：把实飞参数整体替换成 SITL 默认参数文件

4. **验证关键参数**
   - 至少验证：`LAND_FLARE_ALT`, `LAND_FLARE_SEC`, `WP_RADIUS`, `NAVL1_PERIOD`, `TRIM_THROTTLE`
   - 若飞机出现异常姿态（筒滚/发散/无法转弯），第一检查项是是否误注入了 EXCLUDE 类参数

## 数据流

- 输入：实飞参数文件 `~/下载/cuavx7_260329.param`
- 规则：本 Skill 中的 KEEP / EXCLUDE 分类
- 输出：`data/fields/sitl_default/sitl_merged.param`
- 应用：MAVLink `PARAM_SET` → SITL

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `data/fields/sitl_default/sitl_merged.param` | SITL 合并后参数文件 |
| `~/下载/cuavx7_260329.param` | 当前实飞参数源文件 |
| `should_keep(param_name)` | 参数筛选逻辑 |

## 禁止模式

- **禁止**将实飞 `.param` 整体覆盖 SITL 默认参数
- **禁止**把 `PTCH_RATE_*` / `RLL_RATE_*` / `TECS_*` / `SERVO*` 注入 SITL 作为“拟真”
- **禁止**把串口、CAN、罗盘、IMU、GPS 等硬件参数当成“通信设置”带入 SITL
- **禁止**在未重启/未清理旧进程的情况下反复混装不同参数集
- **禁止**看到降落异常就直接全量导入实飞参数；必须先区分“行为参数问题”还是“动力学参数问题”

## 推荐筛选逻辑

```python
KEEP_PREFIXES = [
    "LAND_", "WP_", "NAVL1_", "TKOFF_", "AIRSPEED_",
    "GLIDE_", "FLTMODE", "ARMING_", "FENCE_", "FS_",
    "BATT_", "RTL_", "MIS_", "GUIDED_", "RALLY_", "HOME_",
    "MIN_GROUNDSPEED", "STAB_", "STICK_MIXING", "CRUISE_",
    "FLIGHT_OPTIONS", "RUDD_", "CHUTE_", "PLND_", "RNGFND_LANDING",
]

EXACT_KEEP = {
    "TRIM_THROTTLE",
    "SCALING_SPEED",
    "MIN_GROUNDSPEED",
    "STICK_MIXING",
    "FLIGHT_OPTIONS",
    "RNGFND_LANDING",
}


def should_keep(param_name: str) -> bool:
    if param_name in EXACT_KEEP:
        return True
    return any(param_name.startswith(prefix) for prefix in KEEP_PREFIXES)
```
