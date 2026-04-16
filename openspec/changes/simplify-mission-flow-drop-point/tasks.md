## 1. 需求冻结与代码现状复核

- [x] 1.1 重新检索 `src/striker/core/machine.py`、`src/striker/app.py`，确认当前状态注册与状态转移图中所有 `loiter`、`forced_strike`、`approach` 的入口与出口。
- [x] 1.2 重新检索 `src/striker/core/states/scan.py`、`src/striker/core/states/loiter.py`、`src/striker/core/states/forced_strike.py`，逐条标记哪些行为与本 change 的新主流程冲突。
- [x] 1.3 重新检索 `src/striker/core/states/enroute.py`、`src/striker/core/states/approach.py`、`src/striker/core/states/release.py`、`src/striker/core/states/landing.py`，确认哪些状态职责保留、合并或删除最合适。
- [x] 1.4 重新检索 `src/striker/vision/models.py`、`src/striker/vision/tracker.py`、`src/striker/core/context.py`，列出所有仍使用 `target` 语义而非 `drop point` 语义的类型名、字段名、日志文案与测试断言。
- [x] 1.5 重新检索 `src/striker/payload/ballistics.py` 与所有调用点，确认弹道解算在新流程中的所有残留依赖。
- [x] 1.6 重新检索 `src/striker/config/settings.py`、`docs/user_manual.md`、相关测试，列出 `loiter_timeout_s`、`max_scan_cycles`、`forced_strike_enabled` 等旧配置的使用点与清理范围。
- [x] 1.7 重新检索 `src/striker/safety/monitor.py`、`src/striker/safety/override_detector.py`、`src/striker/comms/telemetry.py`，确认 override 事件链当前真实缺口。
- [x] 1.8 重新检索 `src/striker/comms/connection.py`、`src/striker/comms/messages.py`、`src/striker/comms/telemetry.py`，确认 mission 进度相关 MAVLink 报文目前是否已进入队列或需要新增解析。
- [x] 1.9 重新检索 `tests/unit/test_states.py`、`tests/unit/test_state_machine.py`、`tests/integration/test_sitl_full_mission.py`，标出哪些测试反映旧流程，需要删除、重写或新增。
- [x] 1.10 根据 `data/fields/*/field.json` 与 `docs/user_manual.md`，确认"降落航点"在业务里更适合映射到 `landing.approach_waypoint` 还是 `landing.touchdown_point`，并将结论回填实现说明。

## 2. 状态机主链瘦身

- [x] 2.1 修改 `src/striker/core/machine.py`，删除 `scan ↔ loiter` 和 `loiter → forced_strike` 主路径，定义新的扫场完成后分支。
- [x] 2.2 修改 `src/striker/app.py`，取消或替换 `LoiterState` 与 `ForcedStrikeState` 的注册，确保应用启动时只注册新主流程所需状态。
- [x] 2.3 修改 `src/striker/core/states/scan.py`，将"扫场完成后进入 loiter"改为"扫场完成后进入投弹点决策/转场链路"。
- [x] 2.4 决定 `ApproachState` 的命运：若保留则改成纯直飞到投弹点的接近状态；若删除则将其职责并入 `EnrouteState` 或 `ReleaseState`。
- [x] 2.5 修改 `src/striker/core/states/enroute.py`，使其围绕"投弹点坐标"而不是泛化目标点工作。
- [x] 2.6 修改 `src/striker/core/states/release.py`，确保视觉点链路与兜底中点链路在投放完成后统一进入 `landing`。
- [x] 2.7 修改 `src/striker/core/states/landing.py`，验证其仍与预上传 landing mission 跳转契约兼容，不引入旧流程分支依赖。
- [x] 2.8 删除或停用 `src/striker/core/states/loiter.py` 与 `src/striker/core/states/forced_strike.py` 的运行时入口，并清理引用。
- [x] 2.9 如有必要，新增一个显式的"投弹点决策"状态或等价逻辑单元，使代码职责与 spec 对齐。
- [x] 2.10 更新所有状态迁移相关日志，确保不再出现"loiter""rescan""forced strike"作为标准流程描述。

## 3. 投弹点语义收敛与兜底中点实现

- [x] 3.1 修改 `src/striker/vision/models.py`，将输入模型命名和文档从 target 语义收敛到 drop point 语义。
- [x] 3.2 修改 `src/striker/vision/tracker.py`，将内部命名、返回值语义和日志从 target 收敛到 drop point。
- [x] 3.3 修改 `src/striker/core/context.py`，将 `last_target` 等字段收敛为投弹点语义字段，并补充兜底投弹点所需的上下文保存位。
- [x] 3.4 修改 `src/striker/app.py` 的视觉分发逻辑，确保视觉输入进入上下文时按投弹点契约落地。
- [x] 3.5 修改 `src/striker/core/states/enroute.py`，使转场命令直接使用视觉投弹点坐标。
- [x] 3.6 删除 `src/striker/payload/ballistics.py` 在主流程中的调用，确保"视觉已给投弹点"链路不再触发释放点二次解算。
- [x] 3.7 评估 `src/striker/payload/ballistics.py` 是否应完全删除、保留为未使用模块，或在后续 change 中再下线，并据此处理引用与测试。（决定：保留为未使用模块）
- [x] 3.8 在适当模块中实现"扫场结束点 + 降落参考点 → 兜底中点"的计算函数，输入输出都是 WGS84 坐标。项目已依赖 `geopy`（`geodesic` 已在 `ballistics.py` 中使用），中点可由 `geodesic(kilometers=d/2).destination(point, bearing)` 直接算出，无需引入新依赖。
- [x] 3.9 明确兜底中点所用的"降落参考点"来源，并把实现与 spec 保持一致。（使用 `landing.approach_waypoint`）
- [x] 3.10 将兜底中点接入转场与投放状态链，确保后续行为与视觉投弹点路径完全一致。
- [x] 3.11 更新相关日志与事件文案，区分"视觉投弹点"与"兜底中点投弹点"两类来源。

## 4. 飞控接管退让闭环

- [x] 4.1 修改 `src/striker/comms/telemetry.py`，利用 pymavlink `mavfile.flightmode` 属性（已在连接对象上自动维护，参见 telemetry.py:156 注释）将模式信息暴露为可判定的 ArduPlane 模式名，而不是仅保存 `str(msg.custom_mode)` 数字字符串。
- [x] 4.2 如有必要，在 `src/striker/comms/connection.py` 上新增属性或回调，使 `.flightmode` 可被 `SafetyMonitor` 等上层消费者读取；不需要自行实现 `custom_mode → 模式名` 映射。
- [x] 4.3 修改 `src/striker/core/context.py` 与消息更新路径，确保最新模式信息始终可被安全监控读取。
- [x] 4.4 修改 `src/striker/safety/monitor.py`，在周期检查中调用 `OverrideDetector.check_mode(...)`。
- [x] 4.5 修改 `src/striker/safety/override_detector.py`，确认人工接管模式集合符合当前固定翼任务需求，并可按配置或常量维护。
- [x] 4.6 验证 `src/striker/core/machine.py` 中 `OverrideEvent → override` 的全局拦截仍适用于新主流程。
- [x] 4.7 更新 `src/striker/core/states/override.py` 日志与说明，确保其表达"人工接管后自动控制永久退让"。
- [x] 4.8 清理或降级当前 `SafetyMonitor` 中与本次需求无关且未接实的复杂安全检查描述，避免误导。

## 5. 扫场完成的真实 mission 进度观测

- [x] 5.1 确认 `MISSION_ITEM_REACHED`（常量已在 `messages.py:31` 定义）和 `MISSION_CURRENT`（需新增常量）在当前 pymavlink 接入中的可获得性。
- [x] 5.2 修改 `src/striker/comms/messages.py`，补充 `MISSION_CURRENT = "MISSION_CURRENT"` 常量。
- [x] 5.3 确认 `src/striker/comms/connection.py:_rx_loop` 已将原始报文推入队列，`MISSION_ITEM_REACHED` 和 `MISSION_CURRENT` 的原始消息已在队列中可达，不需要修改连接层 producer 逻辑。
- [x] 5.4 设计并实现 mission 进度在上层的承载方式：直接原始消息消费、typed dataclass，或 `MissionContext` 字段。（使用 MissionContext.mission_current_seq）
- [x] 5.5 修改 `src/striker/core/context.py`，增加扫场 mission 进度所需上下文字段。
- [x] 5.6 修改 `src/striker/core/states/scan.py`，用真实 mission 进度替代 `_waypoints_remaining` 伪倒计数。
- [x] 5.7 为"本地计数与真实 mission 进度冲突时不得提前结束 SCAN"补充保护逻辑或断言。
- [x] 5.8 为 mission 进度输入补充日志，确保后续排查能明确说明系统为何认定扫场结束。
- [x] 5.9 如需要，为 `README.md` 或运行文档补充"scan 完成依赖真实 mission 进度"的说明。

## 6. 配置、文档与命名清理

- [x] 6.1 修改 `src/striker/config/settings.py`，删除或废弃 `loiter_timeout_s`、`max_scan_cycles`、`forced_strike_enabled` 等旧流程配置。
- [x] 6.2 检查 `config.example.json`、`.env.example`、`docs/user_manual.md`，删除与 loiter/rescan/forced strike 相关的公开配置说明。
- [x] 6.3 更新 `README.md` 与其他文档中对任务流程的文字描述，使其与新主链一致。
- [x] 6.4 更新 `docs/user_manual.md` 中关于视觉系统输入的说明，明确收到的是投弹点而不是靶标点。
- [x] 6.5 更新文档中关于安全监控的描述，明确当前唯一必要兜底是人工接管退让。
- [x] 6.6 检查全仓库日志、注释、测试名、文档标题，消除 `target acquired`、`forced strike`、`loiter timeout` 等过时业务术语。

## 7. 单元测试与集成测试重建

- [x] 7.1 修改 `tests/unit/test_states.py`，删除或重写 `LoiterState`、`ForcedStrikeState`、旧 scan→loiter 迁移测试。
- [x] 7.2 为新主链补充单元测试：扫场完成 + 有视觉投弹点、扫场完成 + 无视觉投弹点、投放后进入降落。
- [x] 7.3 为投弹点语义补充测试：视觉点进入上下文后不得触发 ballistic release point 解算。
- [x] 7.4 为兜底中点逻辑补充测试：输入扫场结束点和降落参考点时生成确定性中点。
- [x] 7.5 为 override 闭环补充测试：`AUTO → MANUAL` 触发 `OverrideEvent`，`AUTO → GUIDED` 不触发。
- [x] 7.6 为 HEARTBEAT 模式解析补充单元测试，验证 pymavlink `mavfile.flightmode` 属性到模式名（如 `"MANUAL"`, `"AUTO"`, `"GUIDED"`, `"FBWA"`）的映射结果。
- [x] 7.7 为真实 mission 进度驱动 scan 完成补充测试，覆盖"最后扫描航点完成后才能结束 SCAN"。
- [x] 7.8 修改 `tests/unit/test_flight_controller.py` 与其他相关测试，确保不再依赖旧流程的状态或配置。
- [x] 7.9 修改 `tests/integration/test_sitl_full_mission.py` 的场景描述，使其从"scan→loiter→..."更新为"scan→投弹点决策→投放→landing"。
- [x] 7.10 如环境允许，补充或细化 SITL 集成测试输入，模拟视觉给点与不给点两条任务路径。

## 8. 质量验证与实现前检查

- [x] 8.1 对本 change 涉及的所有文件再次做关键字检索，确认 `loiter`、`forced_strike`、`ballistic` 等旧流程关键词只保留在必要的历史/兼容位置。
- [x] 8.2 运行受影响单元测试集合，确认新状态链、投弹点语义和 override 闭环通过。
- [x] 8.3 运行静态检查（至少 ruff/mypy 对受影响模块），确认重命名和删除状态后无悬空引用。
- [x] 8.4 若可用，执行最小化 dry-run 或 SITL 验证，确认主链日志顺序符合"takeoff → scan → drop routing → release → landing"。
- [x] 8.5 人工复读 proposal/design/specs，确认实现结果没有偏离本 change 设定的主流程与边界。
