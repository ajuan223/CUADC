## ADDED Requirements

### Requirement: AGENTS.md R01 命名约定补充正反示例
AGENTS.md R01 段 SHALL 为每个命名类别（模块/文件、类、常量、函数/变量）提供至少一个正面示例和一个反面示例。

#### Scenario: 命名约定示例完整性
- **WHEN** 审查 AGENTS.md R01 段
- **THEN** 每个命名类别 MUST 包含至少一个 ✓ 正面示例和一个 ✗ 反面示例

#### Scenario: 行数预算
- **WHEN** R01 段补充示例后
- **THEN** AGENTS.md 总有效指令行数 MUST 仍 < 100

### Requirement: utils-rules SKILL.md 存在
`.agent/skills/utils-rules/SKILL.md` SHALL 存在，包含架构约束、注册模式、禁止模式三个标准段落，正文使用中文。

#### Scenario: 文件存在性
- **WHEN** 检查 `.agent/skills/utils-rules/` 目录
- **THEN** MUST 存在 `SKILL.md` 文件

#### Scenario: 三段结构
- **WHEN** 审查 `utils-rules/SKILL.md`
- **THEN** MUST 包含"架构约束"、"注册模式"、"禁止模式"三个段落标题

### Requirement: utils-rules 架构约束
utils-rules SHALL 定义：`utils/` 模块容纳无副作用的纯工具函数，被所有业务模块共享；每个函数必须向 REGISTRY.md 注册；函数必须是无状态的纯函数（输入 → 输出，无 I/O 副作用）。

#### Scenario: utils 函数纯度
- **WHEN** AI Agent 在 `src/striker/utils/` 中实现函数
- **THEN** 函数 MUST NOT 包含 I/O 操作（网络、文件、日志除外）、MUST NOT 修改全局状态

### Requirement: 路由表与 SKILL.md 对齐
AGENTS.md R08 路由表中列出的每个 Skill MUST 在 `.agent/skills/` 下存在对应的 SKILL.md 文件。

#### Scenario: 路由表完整性
- **WHEN** 检查 R08 路由表的 9 个条目
- **THEN** 每个条目指向的 Skill 名称 MUST 在 `.agent/skills/{name}/SKILL.md` 存在

---

### Requirement: Business states use haversine_distance for GPS distance
All business states (EnrouteState, ApproachState, ForcedStrikeState) SHALL use `striker.utils.geo.haversine_distance()` for GPS distance calculations instead of hardcoded degree-to-meter approximations.

#### Scenario: EnrouteState uses haversine for approach distance check
- **WHEN** `EnrouteState.execute()` calculates distance to target
- **THEN** it calls `haversine_distance(pos.lat, pos.lon, tgt.lat, tgt.lon)` from `striker.utils.geo`

#### Scenario: ApproachState uses haversine for release point arrival check
- **WHEN** `ApproachState.execute()` calculates distance to release point
- **THEN** it calls `haversine_distance()` from `striker.utils.geo`

#### Scenario: No hardcoded 111000 coefficients in state files
- **WHEN** a grep for `111.?000` is run on `src/striker/core/states/`
- **THEN** zero matches are found

---

### Requirement: forced_strike_point validates safety buffer via boundary distance
`generate_forced_strike_point()` SHALL reject candidate points whose distance to the nearest polygon edge is less than `buffer_m`. The point-to-segment distance function SHALL be a shared utility in `striker.utils.geo`.

#### Scenario: Generated point is at least buffer_m from boundary
- **WHEN** `generate_forced_strike_point(polygon, buffer_m=50)` returns a point
- **THEN** the point's distance to the nearest polygon edge is >= 50 meters

#### Scenario: Point too close to boundary is rejected
- **WHEN** a candidate random point has boundary distance < buffer_m
- **THEN** the point is rejected and the algorithm tries another candidate

#### Scenario: point_to_segment_distance is in utils.geo
- **WHEN** `from striker.utils.geo import point_to_segment_distance` is executed
- **THEN** the import succeeds and returns a callable

---

### Requirement: LandingState uses pre-uploaded landing sequence
`LandingState` SHALL trigger the pre-uploaded landing sequence (uploaded during PREFLIGHT via DO_LAND_START + approach waypoint + NAV_LAND) by setting AUTO mode and sending `MAV_CMD_MISSION_SET_CURRENT` to jump to the landing sequence start index. It SHALL NOT use RTL mode as the landing method.

#### Scenario: LandingState triggers landing sequence
- **WHEN** `LandingState.execute()` runs for the first time
- **THEN** it sends a `MAV_CMD_MISSION_SET_CURRENT` command pointing to the landing sequence start index and sets AUTO mode

#### Scenario: LandingState does not use RTL
- **WHEN** `LandingState.execute()` is inspected
- **THEN** it does NOT reference `ArduPlaneMode.RTL` for triggering the landing

---

### Requirement: ApproachState passes velocity and wind to ballistic calculator
`ApproachState` SHALL extract current airspeed/groundspeed and wind data from the mission context (via telemetry) and pass them as `velocity_n_mps`, `velocity_e_mps`, `wind_n_mps`, `wind_e_mps` to `ballistic_calculator.calculate_release_point()`.

#### Scenario: Ballistic calculator receives non-zero velocity when available
- **WHEN** the aircraft is flying at 20 m/s groundspeed heading north
- **THEN** `calculate_release_point()` is called with `velocity_n_mps > 0` (not default 0)

#### Scenario: Ballistic calculator receives wind data when available
- **WHEN** wind data is available in telemetry
- **THEN** `calculate_release_point()` is called with `wind_n_mps` and `wind_e_mps` populated
