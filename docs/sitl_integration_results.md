# SITL + Striker 集成联调报告

**日期**: 2026-04-17  
**环境**: Linux dev workstation + ArduPlane V4.8.0-dev SITL + repo `.venv` MAVProxy + Striker

---

## 测试摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| Repo launcher / integration fixture 对齐 | PASS | 统一使用 raw `arduplane`、显式 `--home`、`sitl_merged.param`、`Tools/autotest/models/plane.parm` |
| MAVProxy 路由 | PASS | `tcp:127.0.0.1:5760 -> udp:14550 / udp:14551` |
| Striker 建链 | PASS | 项目 `.venv` 启动，`STRIKER_TRANSPORT=udp` |
| 正常视觉链路 | PASS | 起飞 → 扫场 → 视觉投弹点 → 投弹 → 降落 → 完成 |
| fallback 链路 | PASS | 起飞 → 扫场 → fallback midpoint → 投弹 → 降落 → 完成 |
| override 链路 | PASS | 起飞 → 扫场 → MANUAL 接管 → OVERRIDE，且不再继续发控制指令 |
| 每轮 artifact 保留 | PASS | 每个测试独立目录保留 `sitl.log` / `mavproxy.log` / `striker.log` / `flight_log.csv` |
| 短 override recorder 可见性 | PASS | `flight_log.csv` 在短接管路径中仍然可读 |

---

## 1. 本次复验命令

```bash
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/pytest \
  tests/integration/test_sitl_full_mission.py \
  -k "test_normal_path_vision or test_normal_path_fallback or test_human_override" \
  -vv
```

结果：

```text
3 passed, 1 deselected in 882.58s (0:14:42)
```

这轮复验表明当前 R4 三条关键闭环链路已经能够在项目环境中重复跑通。

---

## 2. 统一后的启动拓扑

### 2.1 ArduPlane SITL

```bash
/home/xbp/ardupilot/build/sitl/bin/arduplane \
  -w --model plane --speedup 1 -I 0 \
  --home 30.2610,120.0950,0,180 \
  --defaults /home/xbp/dev-zju/cuax-autodriv/data/fields/sitl_default/sitl_merged.param \
  --defaults /home/xbp/ardupilot/Tools/autotest/models/plane.parm \
  --sim-address=127.0.0.1
```

### 2.2 MAVProxy

```bash
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/mavproxy.py \
  --master tcp:127.0.0.1:5760 \
  --out 127.0.0.1:14550 \
  --out 127.0.0.1:14551
```

### 2.3 Striker

```bash
STRIKER_TRANSPORT=udp \
STRIKER_ARM_FORCE_BYPASS=1 \
STRIKER_RECORDER_OUTPUT_PATH=<artifact-dir>/flight_log.csv \
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/python -m striker --field sitl_default
```

### 2.4 当前固定不变量

- `--home 30.2610,120.0950,0,180`
- `data/fields/sitl_default/sitl_merged.param`
- `~/ardupilot/Tools/autotest/models/plane.parm`
- SITL 上游 TCP `5760`
- MAVProxy 下游 UDP `14550` / `14551`
- `STRIKER_TRANSPORT=udp`
- 集成 harness 为每次运行分配独立 vision TCP 端口

---

## 3. 三条验证链路

### 3.1 正常视觉链路

验证主链：

```text
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING → COMPLETED
```

本轮 artifact：

- `runtime_data/integration_runs/tests-integration-test_sitl_full_mission.py-TestSITLFullMission-test_normal_path_vision-1776388288336/`

关键日志里程碑：

- `Preflight: mission uploaded`
- `Target altitude reached`
- `Scan complete`
- `Using vision drop point`
- `Attack mission uploaded`
- `Attack run initiated`
- `Payload released (native DO_SET_SERVO)`
- `Landing detected`
- `Mission completed successfully!`

### 3.2 fallback 链路

验证主链：

```text
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE(fallback midpoint) → RELEASE → LANDING → COMPLETED
```

本轮 artifact：

- `runtime_data/integration_runs/tests-integration-test_sitl_full_mission.py-TestSITLFullMission-test_normal_path_fallback-1776388706112/`

关键日志里程碑：

- `Preflight: mission uploaded`
- `Target altitude reached`
- `Scan complete`
- `Using fallback midpoint drop point`
- `Attack mission uploaded`
- `Attack run initiated`
- `Payload released (native DO_SET_SERVO)`
- `Landing detected`
- `Mission completed successfully!`

### 3.3 override 链路

验证主链：

```text
INIT → PREFLIGHT → TAKEOFF → SCAN → OVERRIDE
```

本轮 artifact：

- `runtime_data/integration_runs/tests-integration-test_sitl_full_mission.py-TestSITLFullMission-test_human_override-1776389124835/`

关键日志里程碑：

- `Preflight: mission uploaded`
- `Target altitude reached`
- `Autonomy relinquished`
- `Human override — autonomous control permanently relinquished`

并明确验证：

- **不会**出现 `Payload released (native DO_SET_SERVO)`
- **不会**出现 `Mission completed successfully!`
- override 短路径仍会保留 `flight_log.csv`

---

## 4. 当前已验证的关键能力

### 4.1 程序化降落几何

日志持续给出：

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

说明降落进近点反推仍与理论值一致。

### 4.2 程序化扫场几何

日志持续给出：

```text
Boustrophedon scan generated ... waypoints=10 sweeps=5 spacing_m=200.0
```

说明 boundary polygon → 扫场覆盖路径生成保持正确。

### 4.3 程序化起飞几何

日志持续给出：

```text
Takeoff geometry generated ... heading=0.0
```

说明起飞起点/爬升点由跑道事实推导仍然有效。

### 4.4 任务进度可观测性

Striker 在建链后显式请求：

- `MISSION_CURRENT`
- `MISSION_ITEM_REACHED`

因此 scan/enroute/attack-run 进度不再依赖 MAVProxy 默认流配置。

### 4.5 短接管 recorder 保留

`src/striker/telemetry/flight_recorder.py` 现在每次写样本都 `flush()`，因此 override 这种短流程不会再出现 CSV 已生成但测试窗口内不可见的问题。

---

## 5. 本轮 artifact 保留情况

每个测试独立保存在：

```text
runtime_data/integration_runs/<test-nodeid>-<timestamp>/
```

本轮三条 full-chain 路径可见的文件：

- `sitl.log`
- `mavproxy.log`
- `striker.log`
- `flight_log.csv`
- `vision.log`（vision / fallback 路径）

这意味着失败时可以直接对照同一轮的 SITL、路由、Striker、vision、flight recorder 证据，而不是依赖 `/tmp` 被覆盖后的残余信息。

---

## 6. 这轮复验中仍能观察到的现象

### 6.1 vision / fallback 在 preflight 可能出现一次上传重试

在最近一轮 vision 与 fallback artifact 中都能看到：

```text
Preflight mission upload failed
...
Mission upload complete
Preflight: mission uploaded
```

本轮表现为：

- 首次 full mission upload 等待 `MISSION_REQUEST` 超时
- 随后立即重试成功
- 三条链路整体仍然 PASS

当前结论：

- 这不再阻塞 R4 闭环复现
- 但它仍是后续可继续优化的启动稳定性观察点
- 相关证据已经保留在最新 artifact 中，可作为后续 R5 或专项稳定性工作的输入

---

## 7. 已完成的关键修复收口

### 7.1 启动栈对齐

- 修正旧的 `default_params/plane.parm` 路径为 `Tools/autotest/models/plane.parm`
- 补齐显式 `--home`
- 统一 repo `.venv` 中的 MAVProxy / Python
- 启动前增加缺失前置条件的 fail-fast 检查

### 7.2 正常链路打通

- 替换跳过的 placeholder 测试
- 调整 mission-progress 订阅
- 修正 stale mission progress 的攻击跑判定
- 保留攻击跑 exit leg，不再粗暴跳 `DO_LAND_START`
- 重校正常链路 runtime budget

### 7.3 fallback 链路收口

- 每轮独立 vision socket，隔离陈旧 publisher 污染
- no-wind fallback attack geometry 对齐 landing-approach gate
- 为目标航点编码 acceptance radius，避免 fixed-wing 过点不算 reached

### 7.4 override 链路收口

- 集成测试验证 MANUAL 接管后进入 `OVERRIDE`
- 使用稳定日志子串断言接管结果
- recorder 改为逐样本 flush，确保短路径 artifact 可读

---

## 8. 结论

当前可以确认：

1. **R4 所需的三条关键全量闭环链路已经能在项目 `.venv` 环境下复现通过**
2. **脚本、fixture、文档、artifact 路径已经对齐到同一套验证拓扑**
3. **正常路径、fallback 路径、override 路径均有独立 artifact 可回溯**
4. **override 的“立即让出自主权且不继续完成任务”验证已经具备自动化覆盖**
5. **后续若进入 R5，可直接在保留 artifact 的基础上做 flight_log 分析与飞行逻辑微调**
