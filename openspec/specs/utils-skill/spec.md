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
All business states (AttackRunState) SHALL use `striker.utils.geo.haversine_distance()` for GPS distance calculations instead of hardcoded degree-to-meter approximations.

#### Scenario: AttackRunState uses haversine for drop point distance check
- **WHEN** `AttackRunState.execute()` calculates distance to drop point
- **THEN** it calls `haversine_distance(pos.lat, pos.lon, dp_lat, dp_lon)` from `striker.utils.geo`

#### Scenario: No hardcoded 111000 coefficients in state files
- **WHEN** a grep for `111.?000` is run on `src/striker/core/states/`
- **THEN** zero matches are found

---



### Requirement: LandingMonitorState uses pre-uploaded landing sequence
`LandingMonitorState` SHALL monitor the pre-uploaded landing sequence from the full mission. The full mission SHALL preserve the landing sequence items (`DO_LAND_START` + approach waypoint + `NAV_LAND`) after the takeoff item and scan waypoints. It SHALL NOT use RTL mode as the landing method.

#### Scenario: LandingMonitorState monitors landing sequence
- **WHEN** `LandingMonitorState.execute()` runs for the first time
- **THEN** it verifies AUTO mode and waits for landing completion

#### Scenario: LandingMonitorState does not use RTL
- **WHEN** `LandingMonitorState.execute()` is inspected
- **THEN** it does NOT reference `ArduPlaneMode.RTL` for triggering the landing
