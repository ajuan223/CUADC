---
name: sitl-autodebug-loop
description: Automatically iterate SITL flight debugging for Striker fixed-wing missions. Use when the task is to repeatedly launch `scripts/run_sitl.sh zjg2`, then launch Striker against `udp:127.0.0.1:14550`, wait until Striker stops, inspect the run's MAVProxy log, flight log CSV, and artifact directory outputs, compare the actual behavior against the required same-runway takeoff -> strict scan path -> payload release -> landing flow, diagnose mismatches, patch code, and rerun. Never use this skill to modify field JSON, merged params, safety constraints, or to disable existing checks.
---

# SITL 自动调试闭环

本 Skill 用于 `zjg2` 的固定翼全链路自动调试。目标不是“飞起来就算成功”，而是逼近以下唯一正确行为：

- 同一跑道起飞
- 严格按 scan 航点扫场
- 进入投弹阶段并完成释放
- 按进近逻辑回同一跑道降落

## 红线

- **禁止**修改 `data/fields/**`
- **禁止**修改 `*.param`、`sitl_merged.param`、ArduPilot 默认参数
- **禁止**通过关闭/绕过现有安全约束来让任务“看起来通过”
- **禁止**删除或放松 geofence、airspeed、landing corridor、mission gating 等已有保护
- **禁止**把问题归因于 SITL 随机性而不查日志证据

允许修改的范围：

- `src/striker/flight/` 中的路径规划、航迹生成、进近/降落几何
- `src/striker/core/states/` 中的任务切换、scan/release/landing 状态推进条件
- `src/striker/telemetry/`、`src/striker/safety/` 中与日志、观测、判定时序相关但**不降低约束**的逻辑
- 测试与调试辅助代码

## 固定启动顺序

每一轮都必须先清残留端口，再按下面顺序启动：

1. 检查并清理残留 `5760`、`14550`、`14551`
2. 启动 `~/dev-zju/cuax-autodriv/scripts/run_sitl.sh zjg2`
3. 读取其输出里的以下路径：
   - `MAVProxy log: ...`
   - `Flight log target: ...`
   - `Artifact dir: ...`
   忽略 `SITL log`
4. 再启动 Striker：

```bash
cd ~/dev-zju/cuax-autodriv
STRIKER_TRANSPORT=udp \
STRIKER_MAVLINK_URL=udp:127.0.0.1:14550 \
STRIKER_ARM_FORCE_BYPASS=1 \
STRIKER_DRY_RUN=true \
python -m striker --field zjg2
```

5. 持续监听 Striker 输出，直到出现 `stopped`、进程退出，或明确卡死/失败
6. 读取并对比本轮日志，再决定下一轮代码修改

## 端口与残留清理

每轮开始前先确认端口状态：

```bash
ss -ltnup | grep -E ':5760|:14550|:14551'
```

若有残留，先定位：

```bash
lsof -iTCP:5760 -sTCP:LISTEN -n -P
lsof -iUDP:14550 -n -P
lsof -iUDP:14551 -n -P
```

再按进程清理，而不是盲目重启机器：

```bash
pkill -f "python -m striker" || true
pkill -f mavproxy.py || true
pkill -f arduplane || true
```

## 每轮必须收集的证据

至少检查这三个对象：

- `MAVProxy log`
- `Flight log target` 对应的 CSV
- `Artifact dir`

在 `Artifact dir` 中优先找：

- `striker.log`
- 其他本轮派生诊断文件

如果 `Flight log target` 不存在，或 `Artifact dir` 里没有任何 Striker 日志，这本身就是故障信号，必须记录为：

- Striker 未正常启动
- Striker 未连上 MAVLink
- Flight recorder 未启动
- 进程提前退出

## 预期行为对照表

每轮都要把实际行为和下面的目标链路逐项对比：

1. `takeoff`
   起飞航迹应从设定跑道开始，不能先偏航出场
2. `scan`
   必须严格按 scan 航点顺序执行，不能跳扫、不能越界扫
3. `release`
   扫场结束后必须出现进入攻击/投弹任务的证据，不能直接从 scan 跳 landing
4. `landing`
   必须先进入进近，再进入最终着陆；不能在空中“速度 0”式异常坠地，不能在跑道外落地

## 判因优先级

看到异常时，按这个顺序排查，避免误判：

1. 应用层状态机有没有真的跑起来
2. Mission 上传了什么，是否中途被替换
3. 几何生成是否把场外点、错误进近点、错误落点直接塞给飞控
4. 安全约束是否正当地阻止了后续阶段
5. 飞控执行是否和上传任务一致

不要先猜“飞控发散”。

## 日志判读要点

### MAVProxy log

重点看：

- `AP: Flight plan received`
- `AP: Mission: N ...`
- `Reached waypoint`
- `Passed waypoint`
- `LandStart`
- `DO_SET_SERVO`
- `Distance from LAND point`
- `SIM Hit ground`

结论规则：

- 只有一次 `Flight plan received`，且 scan 后直接 `LandStart`，通常说明**没有进入 release 任务链**
- 早期 scan 航点就越界，优先怀疑**扫描几何生成**
- `Land` 前没有合理的进近/下滑证据，优先怀疑**landing activation / approach geometry**

### Flight log CSV

重点比对：

- 飞机位置是否出 boundary
- 当前任务序号是否与 scan/release/landing 预期匹配
- 空速、高度、地速在起飞/进近/着陆阶段是否合理
- 是否出现“高度还在空中但速度归零”的不合理状态

### Striker 输出 / striker.log

重点看：

- `FSM transition`
- `State entered/exited`
- `mission uploaded`
- `scan`
- `enroute`
- `release`
- `landing`
- `stopped`
- `warning` / `emergency`

如果应用层从未进入 `scan -> enroute -> release`，那就不要把问题归咎于投弹器。

## 调试策略

一轮只改一类原因，避免把多个变量混在一起：

- 几何错误：只改 mission geometry / navigation / landing sequence
- 状态推进错误：只改 state gating / mission progress interpretation
- 观测错误：只改 telemetry / recorder / event detection

每次修改后必须：

1. 补单元测试或回归测试
2. 重新跑一轮完整 SITL
3. 用新日志验证症状是否消失，且没有引入新的行为退化
4. 在 `./route_changelog/roundx.log` 记录本轮变更与结果

## 每轮变更记录

每轮代码修改后都必须留下 changelog，目录固定为：

```text
./route_changelog/
```

文件名固定为：

```text
round1.log
round2.log
round3.log
...
```

如果目录不存在，先创建目录再写文件。

每个 `roundx.log` 至少包含：

1. 本轮时间
2. 使用的产物目录和日志路径
3. 观察到的实际行为
4. 与预期链路的差异
5. 本轮代码改动点
6. 为什么这样改
7. 修改后的验证结果
8. 下一轮仍待解决的问题

记录目标是让后续轮次无需重新通读所有旧日志，也能知道：

- 之前改过什么
- 哪个假设已经被证伪
- 哪个症状已经解决
- 剩余问题在哪一段链路

## 停止条件

满足以下条件才算完成：

- 起飞后不越界
- scan 按路径完整执行
- scan 后进入 release，而不是直接 landing
- 降落前出现合理进近链路
- 落点在跑道逻辑允许范围内
- 本轮日志和代码修改能自洽解释

若未满足，就继续下一轮，不要停在“分析完了”。
