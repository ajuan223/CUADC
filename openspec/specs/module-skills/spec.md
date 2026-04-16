## ADDED Requirements

### Requirement: SKILL.md 标准三段结构
每个模块级 SKILL.md 文件 SHALL 包含三个标准段落：架构约束 (Architecture Constraints)、注册模式 (Registration Pattern)、禁止模式 (Forbidden Patterns)。

#### Scenario: SKILL.md 结构完整性检查
- **WHEN** 审查任意 `.agent/skills/{module}-rules/SKILL.md`
- **THEN** 文件 MUST 包含"架构约束"、"注册模式"、"禁止模式"三个段落标题

### Requirement: 架构约束段内容
架构约束段 SHALL 定义该模块在 Striker 整体架构中的定位、职责边界、允许的依赖方向和数据流向。

#### Scenario: 架构约束段要素
- **WHEN** 审查 SKILL.md 的架构约束段
- **THEN** 该段 MUST 包含职责定义、可依赖的模块列表（或"无"）、数据流入/流出方向说明

### Requirement: 注册模式段内容
注册模式段 SHALL 定义该模块需要向 REGISTRY.md 注册的能力条目及其格式。

#### Scenario: 注册模式格式示例
- **WHEN** 审查 SKILL.md 的注册模式段
- **THEN** 该段 MUST 包含至少一个注册条目示例，包含函数签名、描述、所在模块路径

### Requirement: 禁止模式段内容
禁止模式段 SHALL 列出该模块中明确不允许的编码行为和常见反模式。

#### Scenario: 禁止模式要素
- **WHEN** 审查 SKILL.md 的禁止模式段
- **THEN** 该段 MUST 包含至少 3 条禁止项，每条有明确说明

### Requirement: 模块 SKILL 覆盖完整性
SHALL 创建覆盖以下模块的 SKILL.md 文件：core-fsm-rules, comms-mavlink-rules, flight-control-rules, safety-monitor-rules, vision-interface-rules, payload-release-rules, config-system-rules, field-profile-rules, telemetry-rules, testing-rules，共计 10 个模块级 Skill。

#### Scenario: Skill 文件存在性
- **WHEN** 检查 `.agent/skills/` 目录
- **THEN** 上述 10 个子目录下 MUST 各存在一个 `SKILL.md` 文件

### Requirement: SKILL.md 使用中文编写
所有模块级 SKILL.md 的正文内容 SHALL 使用中文编写。

#### Scenario: 中文内容验证
- **WHEN** 审查任意 SKILL.md 文件
- **THEN** 正文内容（架构约束、注册模式、禁止模式段落）MUST 以中文撰写

### Requirement: core-fsm-rules 架构约束
core-fsm-rules SHALL 定义：状态机是 Striker 的业务编排核心；FSM 引擎通过事件驱动状态转换；所有状态 MUST 继承 BaseState ABC 并实现 on_enter/execute/on_exit；MissionContext 为状态间共享数据的唯一容器。

#### Scenario: core 模块职责边界
- **WHEN** AI Agent 触及 `src/striker/core/`
- **THEN** 其行为 MUST 符合 SKILL.md 中定义的 FSM 引擎规范，不得绕过事件系统直接转换状态

### Requirement: comms-mavlink-rules 架构约束
comms-mavlink-rules SHALL 定义：pymavlink 是 MAVLink 通信的唯一入口，封装在 `src/striker/comms/` 内；上层模块通过消息收发接口通信，MUST NOT 直接 import pymavlink；连接管理支持串口 (921600 baud) 和 UDP (SITL)。

#### Scenario: comms 模块封装边界
- **WHEN** AI Agent 在 `src/striker/comms/` 以外的代码中需要发送 MAVLink 消息
- **THEN** MUST 通过 comms 模块提供的公共接口调用，MUST NOT 直接 `import pymavlink`

### Requirement: safety-monitor-rules 架构约束
safety-monitor-rules SHALL 定义：Safety Monitor 是独立协程，从 ARM 到任务结束始终运行；它 MUST NOT 被暂停或关闭 (RL-02)；Override 触发后系统进入终态，MUST NOT 自动恢复 (RL-03)；围栏校验使用 point_in_polygon 算法。

#### Scenario: safety monitor 存活保证
- **WHEN** 系统处于飞行状态
- **THEN** Safety Monitor 协程 MUST 持续运行，任何异常 MUST 通过降级而非停止来处理

### Requirement: config-system-rules 架构约束
config-system-rules SHALL 定义：配置采用三层优先级（代码默认 < config.json < 环境变量）；所有配置模型 MUST 继承 pydantic-settings 的 BaseSettings；敏感信息 MUST 通过环境变量注入，MUST NOT 硬编码或写入 config.json。

#### Scenario: 配置优先级
- **WHEN** 同一配置项在代码默认值、config.json、环境变量中均有定义
- **THEN** 环境变量的值 MUST 优先生效

### Requirement: capability-registry 规范
capability-registry SHALL 定义能力注册中心的使用规范，包括如何向 REGISTRY.md 注册新能力和如何查询已有能力。

#### Scenario: 能力查询流程
- **WHEN** AI Agent 需要实现一个通用函数
- **THEN** MUST 先查询 REGISTRY.md，确认不存在已注册的等效能力后再创建新实现

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
