# Striker 用户手册功能测试报告

**日期**: 2026-04-15
**测试环境**: Linux dev workstation (非 SITL / 非嵌入式)
**Python**: 3.13 | **uv**: latest | **ruff**: clean

---

## 测试摘要

| 类别 | 测试数 | 通过 | 失败 | 发现缺陷 |
|------|--------|------|------|---------|
| 包入口 & 导入 | 3 | 3 | 0 | 0 |
| 配置系统 | 3 | 3 | 0 | 0 |
| 场地配置 | 3 | 3 | 0 | 0 |
| 异常体系 | 3 | 3 | 0 | 0 |
| 平台检测 | 3 | 3 | 0 | 0 |
| 状态机 | 17 | 17 | 0 | 0 |
| 安全监控 | 4 | 4 | 0 | 0 |
| 地理工具 | 5 | 5 | 0 | 0 |
| 弹道计算器 | 4 | 4 | 0 | 0 |
| 强制打击点 | 2 | 2 | 0 | 0 |
| 电子围栏 | 2 | 2 | 0 | 0 |
| 预检脚本 | 1 | 1 | 0 | 0 |
| 单元测试套件 | 187 | 187 | 0 | 0 |
| **总计** | **237** | **237** | **0** | **3 (已修复)** |

**最终结果: PASS** (187/187 pytest + 50 手动功能测试全部通过)

---

## 1. 包入口 & 导入

### 1.1 `python -m striker` 入口点

**状态**: PASS (修复后)

启动程序成功执行以下步骤后因无串口而退出（开发环境预期行为）：
- 加载 StrikerSettings 配置
- 加载 sitl_default 场地配置
- 初始化 13 状态 FSM
- 尝试连接 MAVLink → 失败 (无 serial 模块 / 无硬件)

**发现缺陷**: `app.py:108` 使用 `stall_speed_m=` 参数名，但 `SafetyMonitor.__init__` 定义为 `stall_speed_mps=`。已修复。

### 1.2 `import striker; striker.__version__`

**状态**: PASS

```
striker.__version__ → "0.1.0" (非空字符串，符合 semver)
```

### 1.3 `py.typed` 标记文件

**状态**: PASS

```
src/striker/py.typed 存在
```

---

## 2. 配置系统

### 2.1 三层优先级: 代码默认值 < config.json < 环境变量

**状态**: PASS

| 测试 | 结果 |
|------|------|
| 代码默认值: `serial_port="/dev/serial0"`, `dry_run=False` | PASS |
| 环境变量 `STRIKER_SERIAL_PORT=/dev/ttyTEST` 覆盖默认值 | PASS |
| 环境变量 `STRIKER_DRY_RUN=true` 覆盖默认值 | PASS |
| `STRIKER_LOG_LEVEL=DEBUG` 前缀工作正常 | PASS |

### 2.2 配置字段完整性

**状态**: PASS

全部 24 个配置字段均有代码默认值，无 env/config 时可正常实例化。

---

## 3. 场地配置 (Field Profile)

### 3.1 sitl_default 加载

**状态**: PASS

```
name = "SITL Default"
scan_waypoints = 8 个航点
boundary vertices = 5 (含闭合点)
safety_buffer_m = 50.0
```

### 3.2 不存在的场地名

**状态**: PASS

`load_field_profile("nonexistent")` 正确抛出 `ConfigError`。

### 3.3 多边形自动闭合

**状态**: PASS

首尾顶点自动补齐，`polygon[0] == polygon[-1]` 成立。

---

## 4. 预检脚本

### 4.1 `scripts/preflight_check.py`

**状态**: PASS

```
Field: sitl_default
Dry run: False
Transport: serial
Release method: mavlink

Validating field profile 'sitl_default'...
  Name: SITL Default
  Scan waypoints: 8
  Boundary vertices: 5
  Safety buffer: 50.0m
  OK

All checks passed.
```

---

## 5. 异常体系

### 5.1 继承关系

**状态**: PASS

全部 6 个子异常均可通过 `except StrikerError` 捕获：`ConfigError`, `CommsError`, `FlightError`, `SafetyError`, `PayloadError`, `FieldValidationError`。

### 5.2 FieldValidationError 字段上下文

**状态**: PASS

`FieldValidationError("scan_waypoints[0]", "outside geofence")` 的 str 输出包含字段名和原因。

---

## 6. 平台检测

### 6.1 `STRIKER_PLATFORM=sitl` 强制覆盖

**状态**: PASS → `Platform.SITL`

### 6.2 `MAVLINK_SITL` 环境变量检测

**状态**: PASS → `Platform.SITL`

### 6.3 无覆盖时的回退

**状态**: PASS → `Platform.Unknown` (开发工作站预期)

---

## 7. 状态机

### 7.1 基本状态流转 (11 步)

**状态**: PASS

```
init → preflight → takeoff → scan → loiter → scan → loiter → enroute → approach → release → landing → completed
```

### 7.2 forced_strike 路径

**状态**: PASS

```
... → loiter → forced_strike → landing
```

### 7.3 全局拦截器

**状态**: PASS

```
forced_strike → override  (OverrideEvent)
scan → emergency → landing (EmergencyEvent)
```

### 7.4 全部 13 状态声明

**状态**: PASS

`init`, `preflight`, `takeoff`, `scan`, `loiter`, `enroute`, `approach`, `release`, `landing`, `forced_strike`, `completed`, `override`, `emergency`

---

## 8. 安全监控

### 8.1 构造 & 接口

**状态**: PASS

- `SafetyMonitor(geofence, check_interval_s=1.0, battery_min_v=11.1, stall_speed_mps=10.0)` 构造成功
- `set_heartbeat_check(lambda: True)` 注册正常
- `set_event_callback(lambda e: ...)` 注册正常
- `stop()` 方法可用

---

## 9. 地理工具

### 9.1 haversine_distance

**状态**: PASS

`haversine_distance(30.0, 120.0, 30.0, 120.001) = 96.30m` (1/1000 经度约 96m，合理)

### 9.2 point_to_segment_distance

**状态**: PASS

- 线段上的点距离 = 0.0000 (正确)
- 线段外 0.001° 的点距离 = 111.32m (合理)

### 9.3 nearest_boundary_distance

**状态**: PASS (修复后)

**发现缺陷**: `nearest_boundary_distance` 使用 `polygon[i][0]` 下标访问，不兼容 `GeoPoint` 对象。已修复为 `hasattr` 双模式访问。

`sitl_default` 多边形中心到最近边界 = 264.42m (合理)

---

## 10. 弹道计算器

### 10.1 基本投放点计算

**状态**: PASS

| 输入 | 投放点 |
|------|--------|
| target (30.265, 120.095), alt=80m, Vn=15m/s | (30.264454, 120.095000) — 向上游偏移 ~60m |
| target, alt=80m, V=0 | (30.265, 120.095) — 无偏移 |
| target, alt=80m, wind NE=5m/s | (30.264818, 120.094790) — 风补偿 |

---

## 11. 强制打击点生成

### 11.1 随机点生成 (buffer=50m)

**状态**: PASS (修复后)

连续生成 10 个点，全部在 `sitl_default` 多边形边界框内。

**发现缺陷**: `generate_forced_strike_point` 使用 `p[0]` 下标访问，不兼容 `GeoPoint` 对象。已修复为 `hasattr` 双模式访问。

---

## 12. 电子围栏

### 12.1 is_inside 检测

**状态**: PASS

- 多边形中心点 → `True`
- 远处点 (31.0, 121.0) → `False`

---

## 13. 单元测试套件

### 13.1 pytest 全量

**状态**: PASS

```
187 passed, 7 skipped, 0 failed
```

7 个跳过的是 SITL 集成测试 (需要 `--integration` 标记和 ArduPlane 运行)。

---

## 发现并修复的缺陷

### BUG-01: app.py 参数名错误

| 项目 | 详情 |
|------|------|
| **文件** | `src/striker/app.py:108` |
| **问题** | `stall_speed_m=settings.stall_speed_mps` 参数名与 `SafetyMonitor.__init__` 签名不匹配 |
| **影响** | 程序启动即崩溃 (TypeError) |
| **修复** | `stall_speed_m` → `stall_speed_mps` |

### BUG-02: nearest_boundary_distance 不兼容 GeoPoint

| 项目 | 详情 |
|------|------|
| **文件** | `src/striker/utils/geo.py:97` |
| **问题** | `polygon[i][0]` 下标访问不兼容 `GeoPoint` 对象（无 `__getitem__`） |
| **影响** | 运行时调用 `nearest_boundary_distance` 时传入 GeoPoint 多边形会 TypeError |
| **修复** | 改为 `hasattr(p, "lat")` 双模式访问，同时兼容 tuple 和 GeoPoint |

### BUG-03: forced_strike_point 不兼容 GeoPoint

| 项目 | 详情 |
|------|------|
| **文件** | `src/striker/utils/forced_strike_point.py:45` |
| **问题** | `p.lat` 属性访问不兼容 tuple，`p[0]` 下标访问不兼容 GeoPoint |
| **影响** | 传入 GeoPoint 多边形时 AttributeError / 传入 tuple 多边形时 AttributeError |
| **修复** | 改为 `hasattr(p, "lat")` 双模式访问 |

### BUG-04: point_in_polygon 不兼容 GeoPoint (关联 BUG-02)

| 项目 | 详情 |
|------|------|
| **文件** | `src/striker/utils/point_in_polygon.py:28` |
| **问题** | `polygon[i]` 解包为 `(yi, xi)` 不兼容 GeoPoint |
| **影响** | 从 forced_strike_point 调用时传入 GeoPoint 多边形会 TypeError |
| **修复** | 改为 `hasattr(p, "lat")` 双模式访问 |

---

## 未测试项 (需要硬件/SITL)

以下功能需要 ArduPlane SITL 或真实飞控硬件，在纯开发环境无法测试：

- MAVLink 串口/UDP 连接建立
- 任务航线上传 (mission_upload)
- 实际起飞/扫描/降落指令
- 视觉接收器 TCP/UDP 数据接收
- GPIO 投放 (需要 gpiod 硬件)
- 心跳收发实际时序
- 飞行记录器 CSV 输出

这些项可通过 `pytest -m integration` 在 SITL 环境中测试。
