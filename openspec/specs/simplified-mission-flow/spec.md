### Requirement: 主任务链必须收敛为单次投放流程
系统 SHALL 将自动任务主链定义为 `PREFLIGHT → TAKEOFF → SCAN → 投弹点决策 → 转场投放 → LANDING → COMPLETED`，并且在 SCAN 完成后不得再进入盘旋等待、多轮重扫或随机强制打击分支。

#### Scenario: 扫场后收到视觉投弹点
- **WHEN** 飞控真实完成扫场且视觉侧已经提供有效投弹点
- **THEN** 系统进入转场投放链路而不是进入 `loiter` 或重扫链路

#### Scenario: 扫场后未收到视觉投弹点
- **WHEN** 飞控真实完成扫场且视觉侧未提供有效投弹点
- **THEN** 系统必须进入兜底投放点计算链路而不是进入 `loiter`、重扫或随机强制打击链路

### Requirement: 旧的盘旋与随机强制打击主流程必须被移除
系统 MUST 移除 `loiter`、多轮重扫、`forced_strike` 随机点打击在主任务流程中的职责，并且相关状态、配置和文档不得再被描述为标准任务路径的一部分。

#### Scenario: 状态机注册
- **WHEN** 系统初始化任务状态机
- **THEN** 主任务路径中不得要求 `loiter` 或 `forced_strike` 作为扫场后的必经状态

#### Scenario: 配置收敛
- **WHEN** 系统加载任务行为配置
- **THEN** 不得再依赖 `loiter_timeout_s`、`max_scan_cycles` 或 `forced_strike_enabled` 才能完成标准任务链
