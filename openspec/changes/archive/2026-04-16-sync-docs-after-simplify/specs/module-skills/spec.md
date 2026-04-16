## ADDED Requirements

### Requirement: Skill 规范与实际代码架构一致
所有 `.agent/skills/*/SKILL.md` 文件 SHALL 准确反映当前代码架构，不得包含对已删除状态、模块或功能的引用。

#### Scenario: vision-interface-rules 不引用 GpsTarget 或 loiter
- **WHEN** `vision-interface-rules/SKILL.md` 被读取
- **THEN** 不包含 `GpsTarget`、`TargetTracker`、`loiter.py`、`forced_strike_point` 的引用
- **AND** 包含 `GpsDropPoint`、`DropPointTracker`、`scan.py` 的描述

#### Scenario: payload-release-rules 不引用弹道解算主流程
- **WHEN** `payload-release-rules/SKILL.md` 被读取
- **THEN** 不包含"弹道解算决定释放时机"、"强制投弹"、"FORCED_STRIKE"的引用
- **AND** 描述释放控制器（MAVLink DO_SET_SERVO / GPIO）作为唯一投弹机制

#### Scenario: core-fsm-rules 描述 10 态简化链
- **WHEN** `core-fsm-rules/SKILL.md` 被读取
- **THEN** 状态链描述为 `init→preflight→takeoff→scan→enroute→release→landing→completed + override + emergency`
- **AND** 不包含 `loiter`、`approach`、`forced_strike` 状态

#### Scenario: safety-monitor-rules 包含 FBWA 模式
- **WHEN** `safety-monitor-rules/SKILL.md` 被读取
- **THEN** OverrideDetector 默认接管模式集合包含 `MANUAL`、`STABILIZE`、`FBWA`
- **AND** 说明模式检测使用 `connection.flightmode` 属性

#### Scenario: field-profile-rules 不引用 payload 强制投弹依赖
- **WHEN** `field-profile-rules/SKILL.md` 被读取
- **THEN** "被依赖"列表中不包含 `payload/`(强制投弹) 的引用

#### Scenario: testing-rules 不强制要求弹道 KAT
- **WHEN** `testing-rules/SKILL.md` 被读取
- **THEN** 不包含 "弹道解算禁止 mock" 的禁止模式
- **AND** 不将弹道解算作为测试分层策略的示例
