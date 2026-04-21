## Context

Striker 当前全权管理飞控航点生命周期：从 field_profile 解算 boustrophedon scan path、takeoff geometry、landing approach，全量上传后在飞行中多次重建并重新上传（attack mission、landing-only mission）。这在比赛场景下风险过大——Mission Planner 已经能通过 GUI 精确规划航点并直接烧录飞控，Striker 重复造轮子的航点解算是脆弱的。

重构后的架构：航点序列通过 Mission Planner 预烧录在飞控 EEPROM 中，Striker 仅在扫场结束后的 `NAV_LOITER_UNLIM` 阶段介入，通过 `MISSION_WRITE_PARTIAL_LIST` 覆写 5 个预留航点槽位（投弹 approach → target → servo → exit → spare），然后 `MISSION_SET_CURRENT` 跳过 LOITER 解除阻塞，飞控自动执行后续 landing 序列。

### 当前模块依赖

```
app.py
  └─ MissionStateMachine
       ├─ PreflightState → generate_mission_geometry() + upload_full_mission()
       ├─ TakeoffState   → arm() + takeoff() + set_mode(AUTO)
       ├─ ScanState      → 监听 mission_current_seq
       ├─ EnrouteState   → generate_mission_geometry() + upload_attack_mission()
       ├─ ReleaseState   → release + upload_landing_mission()
       └─ LandingState   → set_mode(AUTO) + MISSION_SET_CURRENT
```

## Goals / Non-Goals

**Goals:**
- 将航点规划职责从 Striker 移交给 Mission Planner（预烧录）
- Striker 仅管理扫场结束 → 降落之间的投弹决策和动态航点注入
- 实现 `MISSION_WRITE_PARTIAL_LIST` 局部覆写和 Mission Download Protocol
- 视觉投弹点改为 Python 进程内全局变量
- 降低系统复杂度，删除不再需要的解算/上传代码

**Non-Goals:**
- 不修改 Field Editor（只涉及 Striker）
- 不修改 comms/、safety/、telemetry/、utils/ 底层模块
- 不改变投弹释放机构（payload/）的硬件接口
- 不修改 SITL 仿真环境本身（但测试用例需要适配预烧录任务）
- 不设计多目标多次投弹（本次只处理单投弹点）

## Decisions

### D1: 阻塞机制选择 — NAV_LOITER_UNLIM

**选定**: 预烧录任务中在 scan 结束后放置 `NAV_LOITER_UNLIM`，飞机到达后自动盘旋等待。

**备选 A**: 切 GUIDED 模式 + DO_REPOSITION
- 否决理由: GUIDED 模式下 fence/failsafe 行为与 AUTO 不同，增加模式切换风险

**备选 B**: MISSION_SET_CURRENT 反复锁定
- 否决理由: 固定翼无法悬停，到达后继续向前飞，锁定无效

**理由**: LOITER_UNLIM 是 ArduPlane AUTO 模式原生支持的盘旋等待指令，fence 和 failsafe 全程生效，用 `MISSION_SET_CURRENT` 跳到下一个 seq 即可解除。

### D2: 航点插入机制 — MISSION_WRITE_PARTIAL_LIST

**选定**: 用 `MISSION_WRITE_PARTIAL_LIST(start_seq, end_seq)` 覆写预留的 5 个槽位。

**备选**: MISSION_CLEAR_ALL + 全量重写
- 否决理由: 会丢失预烧录的 takeoff/scan/landing 航点

**理由**: ArduPilot 确认支持在 AUTO 飞行中使用 partial write 修改航点。不改变任务总数，只替换内容。飞控完成当前航点后执行新内容。

### D3: 预留槽位数量 — 5 个

```
slot_0 (N+2): NAV_WAYPOINT  → approach 航点
slot_1 (N+3): NAV_WAYPOINT  → 投弹点航点
slot_2 (N+4): DO_SET_SERVO  → 投弹舵机释放
slot_3 (N+5): NAV_WAYPOINT  → exit 航点
slot_4 (N+6): NAV_WAYPOINT  → spare（预留扩展）
```

占位槽初始坐标设为 LOITER 点坐标（安全默认值）。spare 槽留给未来多目标扩展。

### D4: 视觉接口 — 进程内全局变量

**选定**: `VISION_DROP_POINT: tuple[float, float] | None = None`

**备选 A**: 保留 TCP receiver
- 否决理由: 视觉程序和 Striker 将在同一 Python 进程中运行

**备选 B**: multiprocessing.Value
- 否决理由: 同进程不需要跨进程共享

**实现**: 在 `striker/vision/` 下新建 `global_var.py`，定义全局变量和线程安全的读写函数。视觉程序直接 import 并写入。

### D5: 任务下载与 seq 解析 — STANDBY 状态

启动时新增 STANDBY 状态，使用 MAVLink Mission Download Protocol 从飞控读取预烧录任务：
1. `MISSION_REQUEST_LIST` → 获取总 item 数
2. 逐条 `MISSION_REQUEST_INT` → 读取所有 mission item
3. 扫描找到 `NAV_LOITER_UNLIM` → 记为 `loiter_seq`
4. `loiter_seq + 1` ~ `loiter_seq + 5` → 预留槽位范围
5. 找到 `DO_LAND_START` 或 `NAV_LAND` → 记为 `landing_start_seq`
6. 校验槽位存在且结构正确

### D6: 降级投弹点来源

从 `field_profile.attack_run.fallback_drop_point` 读取。已有数据结构 `GeoPoint(lat, lon)` 支持，无需新增配置。

### D7: Striker 启动时机

起飞前启动，等待心跳建立连接后进入 STANDBY 下载并校验任务。飞机在人工/AUTO 模式下起飞执行 scan，Striker 全程监听 `MISSION_CURRENT` 等待 loiter_seq 触发。

## Risks / Trade-offs

**[R1] Partial write 在飞行中原子性不保证** → 
使用 LOITER_UNLIM 期间执行覆写，飞机盘旋中不会推进到槽位航点，覆写完成后再 MISSION_SET_CURRENT 跳转，消除竞态。

**[R2] 预烧录任务结构错误（缺少 LOITER 或槽位数不足）** → 
STANDBY 状态执行严格校验：检查 LOITER_UNLIM 存在、槽位数 >= 5、landing 序列存在。校验失败拒绝启动并报错。

**[R3] 视觉全局变量线程安全** →
使用 `threading.Lock` 保护读写，提供 `set_drop_point()` / `get_drop_point()` 封装函数。

**[R4] 5 个槽位可能不够（未来多目标）** →
当前设计只支持单投弹点。slot_4 为 spare 预留。多目标需要重新设计预烧录结构。

**[R5] SITL 测试需要预烧录任务文件** →
需要为 SITL 准备 `.waypoints` 文件，通过 MAVProxy `wp load` 加载。现有 SITL 脚本需要适配。

## Open Questions

- Q1: SITL 测试中预烧录任务文件放在哪个目录？`data/missions/` ？
- Q2: spare 槽位（slot_4）默认航点坐标：与 LOITER 相同还是与 exit 相同？
