# SITL + Striker 集成联调报告

**日期**: 2026-04-16  
**环境**: Linux dev workstation + ArduPlane V4.8.0-dev SITL + MAVProxy + Striker

---

## 测试摘要

| 阶段 | 状态 | 说明 |
|------|------|------|
| ArduPlane SITL 启动 | PASS | 使用正确 `--home` 和 `plane.parm` 路径 |
| MAVProxy 路由 | PASS | TCP 5760 → UDP 14550 / 14551 |
| Striker 连接 SITL | PASS | UDP 14550 建链成功 |
| 程序化全任务上传 | PASS | Full mission 16 items |
| 自动起飞 | PASS | 起飞后进入 AUTO 并到达扫场高度 |
| 程序化扫场 | PASS | 10 航点 / 5 sweeps |
| 攻击跑上传 | PASS | Attack mission 8 items |
| 原生释放 | PASS | DO_SET_SERVO 触发成功 |
| 自动降落切换 | PASS | RELEASE 后进入 LANDING |

---

## 1. 本次验证的目标

本次验证针对 **field-driven procedural mission generation**：

- 降落进近点由场地事实自动反推
- 扫场路径由 boundary 自动生成
- 起飞路径由跑道事实自动生成
- 任务链从固定航点模式迁移为程序化几何模式

验证主链：

```text
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING
```

---

## 2. 启动方式

### 2.1 ArduPlane SITL

```bash
/home/xbp/ardupilot/build/sitl/bin/arduplane \
  -w --model plane --speedup 1 -I 0 \
  --home 30.2610,120.0950,0,180 \
  --defaults /home/xbp/dev-zju/cuax-autodriv/data/fields/sitl_default/sitl_merged.param \
  --defaults /home/xbp/ardupilot/Tools/autotest/models/plane.parm \
  --sim-address=127.0.0.1
```

关键修正：

- 使用 `Tools/autotest/models/plane.parm`
- 显式设置 `--home 30.2610,120.0950,0,180`
- 使用 `sitl_merged.param`

### 2.2 MAVProxy

```bash
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/mavproxy.py \
  --master tcp:127.0.0.1:5760 \
  --out 127.0.0.1:14550 \
  --out 127.0.0.1:14551 \
  --daemon
```

### 2.3 Striker

```bash
STRIKER_TRANSPORT=udp \
STRIKER_ARM_FORCE_BYPASS=1 \
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/python -m striker
```

---

## 3. 关键验证结果

### 3.1 降落进近点自动反推

日志结果：

```text
Landing approach derived ... distance_m=572.4341006318463
```

配置条件：

- `approach_alt_m = 30m`
- `glide_slope_deg = 3°`

理论值：

```text
30 / tan(3°) ≈ 572.9m
```

实际值与理论值一致，说明 glide slope reverse projection 正常。

### 3.2 Boustrophedon 扫场路径生成

日志结果：

```text
Boustrophedon scan generated ... waypoints=10 sweeps=5 spacing_m=200.0
```

说明：

- boundary polygon 被成功转换为程序化覆盖路径
- 不再依赖手写 `scan_waypoints.waypoints`

### 3.3 起飞几何自动生成

日志结果：

```text
Takeoff geometry generated ... heading=0.0
```

说明起飞点与爬升点由跑道事实自动生成。

### 3.4 Full mission 上传成功

日志结果：

```text
Mission upload complete ... count=16
Preflight: mission uploaded ... landing_start_index=13
```

说明：

- 起飞段 + 扫场段 + 降落段完整上传成功
- landing start seq 计算正确

### 3.5 攻击跑上传成功

日志结果：

```text
Attack mission uploaded ... target_seq=2 landing_start_seq=5
Attack run initiated
Payload released (native DO_SET_SERVO)
```

说明：

- 临时攻击跑 mission 正常上传
- 原生释放动作触发成功
- 释放后正确切入 LANDING

---

## 4. 状态机主链结果

从实际日志提取：

```text
INIT
→ PREFLIGHT
→ TAKEOFF
→ SCAN
→ ENROUTE
→ RELEASE
→ LANDING
```

关键里程碑：

| 状态 | 结果 |
|------|------|
| PREFLIGHT | 程序化任务生成 + 上传完成 |
| TAKEOFF | 车辆 ARM 成功，切 AUTO |
| SCAN | 进入扫场，scan_end_seq=12 |
| ENROUTE | 扫场结束后切换攻击跑 |
| RELEASE | DO_SET_SERVO 触发 |
| LANDING | 降落序列触发 |

---

## 5. 本次发现并修复的问题

### 5.1 landing items seq 未重编号

**现象**：

SITL 重复请求 item 13，full mission upload 超时。

**根因**：

`src/striker/flight/navigation.py` 的 `build_waypoint_sequence()` 在拼接 landing items 时没有重写 `item.seq`。

**修复**：

对 landing items 追加前执行 seq 重编号。

**结果**：

- 修复前：`Timeout waiting for mission request (sent=14/16)`
- 修复后：`Mission upload complete ... count=16`

### 5.2 SITL 初始位置错误

**现象**：

SITL 默认 home 在 Canberra：

```text
-35.363262 149.165237
```

**影响**：

飞机在错误地图运行，无法验证本地场地几何。

**修复**：

增加：

```bash
--home 30.2610,120.0950,0,180
```

### 5.3 错误的 plane.parm 路径

**现象**：

使用不存在的：

```text
Tools/autotest/default_params/plane.parm
```

导致 defaults 加载失败。

**修复**：

改为：

```text
Tools/autotest/models/plane.parm
```

### 5.4 Striker 默认走串口

**现象**：

未设置 UDP 时，Striker 尝试连接 `/dev/serial0`。

**修复**：

```bash
STRIKER_TRANSPORT=udp
```

---

## 6. 结论

本次 SITL 联调表明：

1. **程序化 mission geometry 已经落地并正常工作**
2. **降落进近点自动反推数值正确**
3. **扫场路径自动生成正常**
4. **起飞几何自动生成正常**
5. **主任务链已在 SITL 中完成闭环验证**
6. **mission upload 的 landing seq 问题已定位并修复**

当前可认为：

> field-driven procedural mission generation 已完成核心实现与 SITL 验证。
