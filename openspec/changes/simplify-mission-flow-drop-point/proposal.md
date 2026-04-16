## Why

当前 Striker 的任务链路仍然建立在“扫场后盘旋等待目标、超时后重扫、最终随机强制打击、接近阶段再做弹道释放点解算”的假设上，这与当前业务已经确认的简化流程不一致：任务应收敛为“起飞 → 扫场 → 收到投弹点则直飞投弹点投放并降落；未收到投弹点则取扫场结束点与降落参考点的中点投放并降落”。继续保留旧链路会让状态机、配置项、测试和真机行为持续偏离任务定义。

同时，当前代码虽然已经具备 ArduPlane/CUAV 友好的 mission takeoff、GUIDED goto、servo 投放和 landing jump 基础能力，但仍缺少两类关键收敛：一是把“投弹点已由视觉侧解算完成”的前提真正落实到业务链路中，移除本侧多余的弹道解算与随机打击退化；二是把“人工遥控接管立即退让”作为唯一必要的自动控制兜底真正打通，而不是继续扩展未接实的复杂安全检查。

## What Changes

- 将任务主流程重构为固定的单次链路：PREFLIGHT 上传完整任务后，执行 TAKEOFF → SCAN；扫场结束时直接进入“投弹点决策”，不再进入 LOITER，也不再进行多轮重扫。
- 删除盘旋等待、重扫循环与随机强制打击语义，移除 `loiter`、`forced_strike` 及其相关配置、测试、文档中的主流程职责。**BREAKING**
- 将视觉输入从“靶标点”语义收敛为“投弹点”语义：收到视觉投弹点后直接作为飞行与投放目标，不再在 APPROACH 阶段基于风场、速度和落体时间重新解算释放点。**BREAKING**
- 新增“无视觉投弹点”兜底策略：以扫场结束点与降落参考点计算中点作为兜底投弹点，并沿同一投放→降落链路执行。
- 保留并强化飞控原生能力边界：起飞与降落继续依赖预上传 mission + AUTO；收到投弹点后的转场继续依赖 GUIDED/global target；投放继续依赖 MAVLink servo/GPIO 触发。
- 将安全兜底收敛为“人工接管立即退让”：打通 HEARTBEAT/模式遥测 → OverrideDetector → OverrideEvent → OverrideState 这条链路；不在本次变更中新增复杂安全检查项。
- 为扫场完成判定补充真实 mission 进度观测要求，避免继续依赖本地假计数器；该要求以可观测性和状态迁移契约的形式落入 spec 与任务。

## Capabilities

### New Capabilities
- `simplified-mission-flow`: 定义删减后的主任务状态链、状态迁移约束与旧状态移除规则。
- `drop-point-routing`: 定义视觉投弹点直飞、无投弹点中点兜底、投放后进入降落的业务契约。
- `override-handover`: 定义基于飞控模式变化的人工接管退让契约。
- `mission-progress-observation`: 定义扫场完成与 mission 进度观测要求，替代本地倒计数式伪完成判断。

### Modified Capabilities
<!-- 无 -->

## Impact

- Affected code: `src/striker/core/machine.py`, `src/striker/app.py`, `src/striker/core/states/scan.py`, `src/striker/core/states/loiter.py`, `src/striker/core/states/forced_strike.py`, `src/striker/core/states/enroute.py`, `src/striker/core/states/approach.py`, `src/striker/core/states/release.py`, `src/striker/core/states/landing.py`, `src/striker/core/context.py`, `src/striker/vision/models.py`, `src/striker/vision/tracker.py`, `src/striker/safety/monitor.py`, `src/striker/safety/override_detector.py`, `src/striker/comms/telemetry.py`, `src/striker/comms/connection.py`, `src/striker/payload/ballistics.py`, 相关测试与文档。
- Runtime behavior: 扫场后不再盘旋或随机打击；视觉投弹点直接驱动转场与投放；无视觉点时执行中点兜底投放；人工模式切换立即终止自动控制。
- Config/API/contract impact: 视觉输入语义从 target 收敛为 drop point；部分 loiter / forced strike 配置项、状态与测试将被删除或失效； mission 进度观测将成为状态迁移输入的一部分。
- External dependencies/behavior: 继续依赖 ArduPlane AUTO mission 语义、GUIDED 全局坐标导航、MAVLink HEARTBEAT 模式信息与 DO_SET_SERVO/GPIO 投放能力。