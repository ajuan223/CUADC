## REMOVED Requirements

### Requirement: KR2.3 SCAN↔LOITER 超时重扫循环正确执行率
**Reason**: LOITER 状态和 SCAN↔LOITER 循环已在 `simplify-mission-flow-drop-point` 变更中删除。
**Migration**: 不再适用。

### Requirement: KR4.3 强制投弹随机点 100% 落在围栏内
**Reason**: 强制投弹功能已在 `simplify-mission-flow-drop-point` 变更中删除。
**Migration**: 不再适用。

### Requirement: RL-10 Forced-strike 围栏内校验
**Reason**: 强制投弹功能已删除，RL-10 红线不再有执行对象。
**Migration**: 删除 RL-10 条目。

## MODIFIED Requirements

### Requirement: CHARTER 使命描述准确
CHARTER.md 使命描述 SHALL 反映"投弹点决策与载荷投放"而非"目标锁定"。

#### Scenario: 使命措辞不包含"目标锁定"
- **WHEN** CHARTER.md 使命段落被读取
- **THEN** 不包含"目标锁定"措辞
- **AND** 包含"投弹点决策"或等效表述
