## MODIFIED Requirements

### Requirement: partial_write_mission 降级为可选工具
`partial_write_mission()` SHALL 保留在代码库中作为可选工具函数，但 SHALL NOT 再是主任务流程的必需步骤。主流程打击导航 SHALL 通过 GUIDED 模式 DO_REPOSITION 实现。

#### Scenario: 主流程不调用 partial_write
- **WHEN** 系统执行标准打击流程（guided_strike 状态）
- **THEN** SHALL NOT 调用 `partial_write_mission()`

#### Scenario: 函数保留可用
- **WHEN** 需要在非主流程场景下覆写 mission items
- **THEN** `partial_write_mission()` SHALL 仍可正常调用
