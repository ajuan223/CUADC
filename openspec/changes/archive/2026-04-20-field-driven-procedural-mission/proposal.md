## Why

当前场地配置把固定翼任务关键几何点直接暴露给用户手填，例如降落 `approach_waypoint` 与扫场 `scan_waypoints`。这会把原本应该由程序保证的飞行几何一致性转嫁给人工配置，导致 glide slope、跑道方向、跑道长度与任务航点之间容易失配，SITL 中已出现降落接近点过近、末段不真实和错误触地判定等问题。

我们需要把场地文件收敛为“场地事实输入”，由程序自动反推出可飞的起飞、扫场、转场和降落序列。这样用户配置的是边界、跑道位置/方向/长度、扫描意图和速度约束，而不是 Mission Planner 式的手工航点；后续也能持续迭代算法而不反复改场地数据格式。

## What Changes

- 将任务几何生成改为“场地驱动、程序反推”模式：降落接近点必须由 `touchdown_point`、`heading`、`approach_alt`、`glide_slope_deg` 自动计算，不再依赖用户手写接近点坐标。
- 将固定翼场地模型扩展为更高层输入：保留场地边界与跑道事实信息，并为扫描任务增加期望路径/速度等目标性输入，减少手工航点配置。
- 新增统一的程序化任务几何能力，用于从场地文件推导起飞序列、扫场路径和降落序列，并允许后续持续替换优化算法而不破坏外部配置契约。
- 修改任务上传与任务生成链路，使其消费程序化生成结果，而不是直接消费人工配置的降落接近点和扫场航点。
- **BREAKING**：场地文件不再把用户手写的降落接近点视为权威输入；相关字段将被移除或降级为内部派生结果。
- **BREAKING**：扫场路径将从“直接提供 waypoint 列表”收敛为“提供场地与扫描约束，由系统自动生成路径”。

## Capabilities

### New Capabilities
- `procedural-mission-geometry`: 根据场地边界、跑道事实、扫描约束和飞行约束自动生成起飞、扫场与降落几何序列。

### Modified Capabilities
- `field-profile`: 场地配置从手工 mission 点位输入收敛为场地事实与任务约束输入，并定义程序化生成所需字段。
- `fixed-wing-takeoff-sequence`: 固定翼起飞序列改为由跑道/场地信息自动推导，而不是依赖静态预写 mission 点。
- `mission-upload`: 任务上传链路改为上传程序化生成的 mission 序列，并记录由生成器给出的序列索引信息。

## Impact

- 受影响代码：`src/striker/config/field_profile.py`、`src/striker/flight/landing_sequence.py`、起飞与扫场 mission 生成逻辑、mission upload/状态机衔接代码、默认场地 JSON。
- 受影响数据：`data/fields/*/field.json` 的 schema 与默认示例需要更新。
- 受影响测试：field profile 校验、landing/takeoff mission 生成、mission upload 索引、SITL 集成验证。
- 受影响系统：SITL 任务行为将更接近真实固定翼几何；后续真实部署也可以在不手工编辑航点的前提下演进算法。
