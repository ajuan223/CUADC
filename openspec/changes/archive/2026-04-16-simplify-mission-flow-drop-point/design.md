## Context

当前代码中的任务状态机仍然按照 `init → preflight → takeoff → scan ↔ loiter → enroute → approach → release → landing → completed` 组织，且保留了 `forced_strike` 退化分支。该设计源自更早的“视觉输出靶标点、本侧继续做释放点解算、多轮盘旋重扫、最终随机兜底打击”的假设，但最新任务定义已经切换为更窄、更直接的业务链：视觉侧在扫场结束后给出投弹点；若有点则直飞并投放，若无点则本侧计算中点兜底投放；随后统一进入降落。

这次变更是一次跨 `core/`、`flight/`、`vision/`、`safety/`、`payload/`、`comms/` 的收敛性重构，而不是局部 bugfix。它既要删除旧流程中的无效状态和配置，也要重新定义状态迁移输入、视觉数据语义、兜底投放点计算来源，以及人工接管的最小安全闭环。代码检索表明：

- `src/striker/core/machine.py` 和 `src/striker/app.py` 明确注册并连通了 `loiter` / `forced_strike` 分支；
- `src/striker/core/states/scan.py` 仍以本地 `_waypoints_remaining` 倒计数模拟扫场完成，而不消费真实 mission 进度；
- `src/striker/core/states/approach.py` 与 `src/striker/payload/ballistics.py` 仍把视觉输入当作靶标点处理；
- `src/striker/safety/override_detector.py`、`src/striker/core/machine.py` 已有 override 架构，但 `src/striker/safety/monitor.py` 尚未真正以遥测模式触发 override；
- `src/striker/comms/telemetry.py` 当前仅将 `custom_mode` 以字符串数字保存，但代码注释（telemetry.py:156）已指出 pymavlink 的 `mavfile` 连接对象提供了 `.flightmode` 属性，会自动将 `custom_mode` 映射为 ArduPlane 模式名。实现时应利用该已有属性，而非自行解析原始 `custom_mode`。

## Goals / Non-Goals

**Goals:**
- 将主状态链严格收敛到“起飞 → 扫场 → 投弹点决策 → 转场投放 → 降落 → 完成”。
- 删除 LOITER、重扫、随机强制打击、弹道释放点解算这些已脱离业务定义的主流程职责。
- 明确“视觉输入 = 投弹点”这一系统契约，并以统一数据模型贯穿 `vision`、`context`、`states`。
- 为“无视觉投弹点”提供确定性的中点兜底规则，且明确该计算依赖的数据来源。
- 将人工接管退让实现为唯一必要的安全兜底，并打通从 HEARTBEAT 到 OverrideState 的事件链。
- 为扫场完成提供真实 mission 进度输入接口，避免继续依赖伪状态推进。

**Non-Goals:**
- 不在本次变更中引入新的传感器安全检查、地理围栏策略或飞控参数调优流程。
- 不在本次变更中重新设计投放硬件协议；MAVLink servo / GPIO 保持现有能力边界。
- 不在本次变更中为 NED 建立全局任务坐标体系；任务层仍以 WGS84/GPS 为主。
- 不在本次变更中实现复杂弹道命中优化；若未来重新恢复“靶标点 → 释放点”模式，再单独设计。

## Decisions

### 1. 用“投弹点决策”取代 `loiter` 与 `forced_strike`
状态机将不再把 SCAN 完成后的下一步定义为盘旋等待，而是进入一个直接决策点：如果视觉系统已经提供投弹点，则直接进入转场；如果没有提供投弹点，则立即计算中点兜底投弹点并进入同一转场链路。

这样做的原因是，当前业务不再要求盘旋或多轮重扫，而 `forced_strike` 的随机点语义与“降落参考点和扫场结束点之间的中点”完全不同。保留这些旧状态只会让实现、配置与测试继续分叉。

**Alternatives considered**
- **保留 `loiter` 但把超时设为 0**：拒绝。状态名和业务意图仍然错误，且会残留重扫/最大轮数等配置噪音。
- **保留 `forced_strike`，仅把随机点改成中点**：拒绝。该状态名和失败语义仍暗示“随机退化打击”，不符合现在的标准流程。
- **把所有决策全部塞进 `ScanState`**：可行但不优先。为了保持状态职责清晰，建议以显式的“扫场完成判定 + 投弹点决策”组织实现，即便未来不一定独立成单独状态类。

### 2. 视觉输入统一定义为“投弹点”，删除本侧释放点二次解算
`vision/models.py`、`vision/tracker.py`、`MissionContext` 以及后续状态逻辑都应把视觉侧输入视为“已经可用于投放转场的 GPS 点”，而不是待本侧重新做弹道计算的靶标点。

这样做的原因是当前业务已经明确“收到的是投弹点而非靶标点”。继续保留 `ApproachState + BallisticCalculator` 会导致飞行器先飞向本侧重新解算出的 release point，从而违背外部接口契约，并制造额外误差源。

**Alternatives considered**
- **保留 ballistic solver 作为可选开关**：本次拒绝。会让代码同时维护两套相互冲突的输入语义。
- **仅在文档中说明‘当前默认不解算’，代码暂不删**：拒绝。状态迁移和数据命名仍会误导后续实现。

### 3. 无视觉投弹点时，中点兜底必须由 companion software 明确计算
兜底投放点不会交给飞控推导，而是由本侧根据“扫场结束点 + 降落参考点”计算得到。任务层继续使用 WGS84，经纬度中点或基于地理距离的中点求解都在本侧完成，然后再以全局坐标命令驱动 GUIDED 转场。

这样做的原因是 ArduPlane/CUAV 能执行 mission、能飞向给定 GPS 点、能触发投放和 landing，但不会理解“若视觉未给点，则按这两个业务参考点生成兜底投弹点”的规则。

**Alternatives considered**
- **由飞控执行随机或固定默认投放点**：拒绝，不符合任务定义。
- **用 LOCAL_NED 作为兜底点主表示**：拒绝。外部接口、场地配置、降落点和 scan waypoints 当前全部基于 WGS84，全链路切 NED 会放大重构范围。

### 4. 任务层保持 WGS84，局部数学可保留 NED
本次变更不会把任务主坐标系统改为 NED。状态机、场地配置、视觉输入、mission/goto 输出继续以 GPS 点为主；如果局部几何计算需要 NED（例如未来恢复弹道或做相对位移推导），则只在解算层内部使用，不改变任务接口。

**Alternatives considered**
- **全系统切换为 NED 主坐标**：拒绝。需要引入原点管理、全链路坐标转换、配置格式迁移，与当前需求不匹配。

### 5. 人工接管退让通过“模式变化 → OverrideEvent”实现，而不是继续扩展复杂安全检查
安全系统本次只收敛到一个最小闭环：解析 HEARTBEAT 对应的 ArduPlane 模式名；识别 `MANUAL`、`STABILIZE`、`FBWA` 等人工接管模式；一旦模式切换进入这些集合，立即发出 `OverrideEvent`，FSM 进入 `override` 终态，不再恢复自动控制。

这样做的原因是代码中 override 架构已经存在，但没真正接实；而更复杂的电池、GPS、地理围栏等逻辑并不是本次需求的核心，继续扩展会稀释主变更目标。

**Alternatives considered**
- **继续保留现有 SafetyMonitor 全量扩展路线**：拒绝。当前实现尚未把最基本的人工接管闭环打通。
- **通过遥控摇杆量检测而非模式切换判定接管**：本次不采用。现有代码和飞控交互层已经具备 HEARTBEAT 模式信息这一更直接的切入点。

### 6. 扫场完成必须以真实 mission 进度为输入，而不是本地伪计数
`ScanState` 当前用 `_waypoints_remaining -= 1` 模拟航点完成，这在 demo 阶段可接受，但在“扫场结束后做投弹点分支决策”的新链路中不再可靠。设计上必须引入真实 mission progress 观测点，例如 `MISSION_ITEM_REACHED`、当前 mission index、或同等级的飞控进度信息，并把它们收敛为状态迁移输入。

**Alternatives considered**
- **继续沿用本地倒计数并把计数初始化为 waypoint 数**：拒绝。这样得到的“扫场完成”不代表飞控真实完成最后扫描点。
- **直接用位置接近最后航点阈值代替 mission 进度**：可作为降级手段，但不应成为主契约。

## Risks / Trade-offs

- **[删除旧状态后，FSM 迁移路径大幅变化]** → 先用 spec 明确新状态链与删除项，再逐层更新注册、转换和单元测试，避免边改边猜。
- **[视觉输入语义切换会影响命名、测试和文档的一致性]** → 统一把 `target` 语义收敛为 `drop point`，同步修改模型名、上下文字段、日志与测试断言。
- **[中点兜底依赖“降落参考点”定义不清]** → 在实现前先固定 reference 的来源（例如 `landing.approach_waypoint` 或 `touchdown_point`），并写入 spec；若业务仍未决，先在 design 中标记为开放问题。
- **[真实 mission 进度接入可能受现有 comms 队列设计影响]** → 经代码验证，`connection.py:_rx_loop` 已将所有原始报文（包括 `MISSION_ITEM_REACHED`）推入队列，只需在消费侧订阅即可；需要新增 `MISSION_CURRENT` 常量并决定是否将其纳入 `TelemetryParser`。
- **[简化安全逻辑后，旧的复杂检查测试将不再适配]** → 在任务中显式包含测试清理与重建，确保测试集与新任务定义一致。

## Migration Plan

1. 先写入 proposal/specs/design，冻结新任务链、视觉输入语义和 override 契约。
2. 在实现阶段优先完成状态图瘦身与数据模型收敛，再处理中点兜底和 mission 进度观测。
3. 删除或废弃 loiter / forced strike / ballistics 相关配置与测试时，保持每次提交都能通过受影响单元测试。
4. 最后补齐集成测试与用户文档，确保新流程从启动说明、场地配置、视觉接口到状态机日志描述完全一致。

## Open Questions

- “降落航点”在兜底中点规则里究竟指 `landing.approach_waypoint` 还是 `landing.touchdown_point`？如果两者不同，哪个更符合投放后转入 landing 的飞行几何？
- mission 进度观测在当前架构中优先消费哪一种输入：`MISSION_ITEM_REACHED`、mission current index，还是位置接近阈值 + 原始报文辅助？
- 是否需要在本次变更里同步重命名 `ApproachState`，还是直接移除该状态并把“到点投放”归并入 `EnrouteState/ReleaseState`？