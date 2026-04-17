## MODIFIED Requirements

### Requirement: 旧的盘旋与随机强制打击主流程必须被移除
系统 MUST 移除 `loiter`、多轮重扫、`forced_strike` 随机点打击在主任务流程中的职责，并且相关状态、配置、场地输入模型、编辑器和文档不得再被描述为标准任务路径的一部分。

#### Scenario: 状态机注册
- **WHEN** 系统初始化任务状态机
- **THEN** 主任务路径中不得要求 `loiter` 或 `forced_strike` 作为扫场后的必经状态

#### Scenario: 配置收敛
- **WHEN** 系统加载任务行为配置
- **THEN** 不得再依赖 `loiter_timeout_s`、`max_scan_cycles` 或 `forced_strike_enabled` 才能完成标准任务链

#### Scenario: 场地输入收敛
- **WHEN** 系统加载当前标准任务使用的场地配置
- **THEN** 不得再要求提供 `loiter_point` 或其他盘旋等待点字段才能完成标准任务链

#### Scenario: 文档与编辑器收敛
- **WHEN** 操作员查看当前任务文档或使用 field editor 编辑场地
- **THEN** 标准任务界面与说明中不得再把 loiter 盘旋点描述为必填或现役任务要素
