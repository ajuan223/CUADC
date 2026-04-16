## ADDED Requirements

### Requirement: 扫场完成判定必须基于真实 mission 进度输入
系统 MUST 使用飞控真实 mission 进度信息来判定扫场是否完成，而不得仅依赖本地递减计数器或固定轮询次数来模拟航点完成。

#### Scenario: 最后扫描航点完成
- **WHEN** 飞控 mission 进度表明最后一个扫描航点已完成
- **THEN** 系统才可以认定 SCAN 阶段结束并进入投弹点决策链路

#### Scenario: 本地计数与真实进度冲突
- **WHEN** 本地状态计数认为扫描已结束，但飞控 mission 进度尚未完成最后扫描航点
- **THEN** 系统不得提前结束 SCAN 阶段

### Requirement: 扫场完成观测必须保留可审计的状态输入
系统 SHALL 为”scan 完成”判定保留可观测、可测试的输入来源，例如 `MISSION_ITEM_REACHED`、当前 mission index 或同等级的飞控进度事件，并把该来源纳入日志或状态上下文。

**实现约束**：
- `MISSION_ITEM_REACHED` 常量已在 `src/striker/comms/messages.py:31` 定义。
- `src/striker/comms/connection.py:_rx_loop` 已将原始报文推入 `asyncio.Queue`，因此 `MISSION_ITEM_REACHED` 原始消息**已在队列中可达**，但当前无消费者。
- `MISSION_CURRENT` 常量尚未在 `messages.py` 中定义，需要新增。
- 实现时只需在消费侧（状态机或 context 更新回调）订阅这些消息类型，不需要修改连接层 producer 逻辑。

#### Scenario: mission 进度事件到达
- **WHEN** 通信层收到与 mission 进度相关的飞控输入（如 `MISSION_ITEM_REACHED` 或 `MISSION_CURRENT`）
- **THEN** 系统必须能够将该输入传递给任务状态机或其等价的状态判定层

#### Scenario: 任务回放或测试验证
- **WHEN** 开发者执行单元测试、集成测试或日志回放
- **THEN** 测试或日志必须能够说明系统基于何种 mission 进度输入认定 SCAN 已完成
