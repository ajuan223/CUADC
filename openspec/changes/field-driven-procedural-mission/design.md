## Context

当前 `FieldProfile` 同时承担“场地事实描述”和“人工 mission 细节配置”两类职责。`landing.approach_waypoint`、`scan_waypoints.waypoints` 这些字段允许用户直接把 Mission Planner 风格的点位写进配置，但这会让配置文件绕过任务几何算法本身。最近的 SITL 现象已经证明：当接近点、跑道方向、下滑角和真实机体行为不一致时，系统虽然能执行 mission，但会表现出不真实的末段几何和不稳定的降落状态。

这次设计要把系统改成“用户只给场地事实和任务目标，程序负责生成可飞序列”。这属于跨模块重构：会影响 `field_profile` 数据模型、起飞/扫场/降落任务几何生成、mission upload 索引、默认场地 JSON 以及相关测试。

约束如下：
- 外部输入仍然是 `data/fields/*/field.json`。
- 固定翼降落接近点必须从 `touchdown_point`、`heading_deg`、`approach_alt_m`、`glide_slope_deg` 自动反推，不能再依赖用户手写经纬度。
- 后续算法应允许持续迭代，因此配置契约必须尽量表达“目标/约束”，而不是表达“中间航点”。
- 当前系统已经有 `destination_point()`、`haversine_distance()` 等几何工具，可作为程序化生成基础。

## Goals / Non-Goals

**Goals:**
- 将场地配置收敛为场地事实输入与任务约束输入。
- 为固定翼任务新增统一的程序化几何生成层，输出起飞、扫场、降落所需 mission 点列与关键序列索引。
- 用 touchdown/runway heading/glide slope/approach altitude 自动计算降落接近点，消除人工写点导致的几何失配。
- 让扫场与起飞也从“人工点列”转为“程序生成结果”，为后续算法优化预留接口。
- 保持 mission upload 与状态机对外行为稳定：上传的仍是标准 MAVLink mission，只是来源从手写点改为计算结果。

**Non-Goals:**
- 本次不引入外部在线地图或第三方规划服务。
- 本次不求解全局最优航迹，也不做复杂避障、风场优化或地形感知。
- 本次不改变主任务状态机的整体业务流程（仍是 TAKEOFF → SCAN → ENROUTE/RELEASE → LANDING）。
- 本次不把所有算法一次做到最终形态；优先建立可迭代的生成框架与最小可用几何规则。

## Decisions

### Decision: 引入独立的程序化任务几何层
新增独立的 mission geometry 生成模块，由它接收 `FieldProfile` 中的场地事实和任务约束，产出：
- 起飞序列几何
- 扫场路径几何
- 降落序列几何
- 与 mission upload 对接所需的序列索引元数据

**Why:**
如果继续把几何计算散落在 `takeoff.py`、`landing_sequence.py`、`navigation.py` 内，会让场地 schema 迁移和算法演进互相耦合。独立层可以把“配置是什么”和“如何算路径”解耦。

**Alternatives considered:**
- 直接在现有 `landing_sequence.py` 上就地补丁：能修 landing，但无法为 takeoff/scan 提供统一演进面。
- 继续让 field.json 手写所有关键点：实施最省事，但根本不符合用户只传场地信息的目标。

### Decision: 场地模型从“航点输入”改为“跑道/约束输入”
`LandingConfig` 不再要求用户提供 `approach_waypoint`。改为要求用户提供 touchdown/runway/approach 约束，例如：
- `touchdown_point`
- `heading_deg`
- `glide_slope_deg`
- `approach_alt_m`
- 跑道长度/可用起降方向等事实信息

扫场也从直接给 waypoint 列表改为给扫描区域、期望条带方向、条带间距/覆盖要求、飞行高度、速度要求等约束。

**Why:**
用户配置的应该是“事实”和“目标”，而不是算法输出。只有这样，后续替换更优算法时才能不反复改场地文件。

**Alternatives considered:**
- 保留旧字段并新增自动模式开关：兼容性更强，但会长期保留两套行为，增加歧义。
- 仅对 landing 去人工化：无法满足“起飞/扫场也一样”的目标。

### Decision: 降落接近点按几何公式从 touchdown 反推
降落接近点由以下步骤计算：
1. 计算高度差 `delta_alt = approach_alt_m - touchdown_alt_m`。
2. 根据 `glide_slope_deg` 计算所需水平距离 `distance = delta_alt / tan(glide_slope_deg)`。
3. 依据跑道 `heading_deg` 的反向方位，从 touchdown 点沿反向延伸 `distance` 得到 approach 点。
4. 若计算结果超出 geofence 或明显短于最小稳定进近距离，则进入约束校验失败或应用保守修正策略。

**Why:**
这满足“approach 点是派生量”的要求，也使 glide slope 真正进入任务几何，而不是只作为未使用的配置项。

**Alternatives considered:**
- 让用户仍填写 approach alt + approach lat/lon：仍然把核心几何责任留给人工。
- 固定一个经验进近距离：无法与 glide slope 和 touchdown 高度保持一致。

### Decision: 起飞与扫场先采用可解释的确定性算法
- 起飞：根据跑道中心线/起飞方向/跑道长度生成起飞起始点与离场方向，确保首段航迹与跑道一致。
- 扫场：先生成规则化 lawnmower/boustrophedon 路径，输入为边界、多边形、条带方向、飞行高度、速度和间距约束。

**Why:**
当前更需要稳定、可验证、可测试的几何生成，而不是过早追求黑盒“最优”。确定性算法最适合建立第一版规范。

**Alternatives considered:**
- 直接接入网络搜索到的高级航迹算法：可能更优，但引入过多外部依赖和验证成本。
- 使用 AI/优化器在线规划：不可控且难以做规范测试。

### Decision: mission upload 消费统一生成结果对象
mission 生成层输出统一的几何结果对象，包含 mission item 原料和关键 index（如 takeoff start、scan span、landing start）。mission upload 不再直接读 field profile 的人工 waypoint 字段，而是消费该结果对象。

**Why:**
mission upload 应该是协议发送层，而不是配置解释层。这样字段迁移后，上传逻辑保持职责单一。

**Alternatives considered:**
- 在 upload 层里直接读取新旧配置并混合生成：短期省事，但会把协议层与算法层耦合。

## Risks / Trade-offs

- [旧场地文件不兼容] → 提供明确迁移路径，更新默认 `field.json`，并在加载时对遗留字段报出可操作错误。
- [自动生成的 approach 点落在围栏外或地理上不可用] → 在生成阶段加入 geofence 校验和最小稳定进近距离校验，失败时拒绝生成而不是静默使用错误几何。
- [扫场算法第一版不够优] → 先定义稳定输入/输出契约，后续可替换算法实现而不改 schema。
- [起飞与降落都从跑道事实推导后，mission 索引更复杂] → 由统一结果对象显式返回关键索引，避免状态机靠硬编码 seq 猜测。
- [Breaking change 影响现有调试脚本] → 同步更新示例场地、测试和技能文档，让默认路径尽快迁移到新模型。

## Migration Plan

1. 在 OpenSpec 中先定义新的 `field-profile`、`procedural-mission-geometry`、`fixed-wing-takeoff-sequence`、`mission-upload` 契约。
2. 调整 `FieldProfile` schema 与默认 `field.json`，移除人工 landing approach 点与人工 scan waypoint 列表依赖。
3. 实现程序化几何生成模块，并先接管 landing approach 反推；随后接管 takeoff/scan。
4. 修改 mission upload/状态机衔接逻辑，改用生成器输出的 mission 序列和 index。
5. 更新单元测试与 SITL 验证用例，确认 landing 几何与状态推进正常。
6. 若回滚，需要恢复旧 field schema 与旧 mission 生成路径；在新结构稳定前不删除相关迁移提示。

## Open Questions

- 跑道事实在 field.json 中的最小必要表达是什么：两个端点、中心点+长度+heading，还是 touchdown + heading + runway_length？
- 扫场第一版约束集合要收敛到哪些字段：条带间距、条带方向、速度、高度、重叠率，还是更少？
- 当反推出来的 approach 点超出 geofence 时，是直接报错，还是沿 geofence 做裁剪/退化？
- 起飞方向是否总与 landing heading 共享跑道轴线，还是需要分别支持双向跑道偏好？
