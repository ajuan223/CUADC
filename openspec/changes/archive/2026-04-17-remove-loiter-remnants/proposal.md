## Why

Striker 的运行态主流程已经收敛到 `起飞 -> 扫场 -> 投弹 -> 降落`，但仓库中仍残留 `loiter` 盘旋相关的数据模型、编辑器输入、公开配置和文档描述。继续保留这些旧契约会让场地配置、工具链和软件逻辑长期失配，并误导后续实现与测试。

## What Changes

- 删除 `FieldProfile` 中已不再参与任务主链的 `loiter_point` 配置和对应校验。 **BREAKING**
- 收敛 field editor 的导入、导出、默认值与样例数据，不再要求编辑或保存 `loiter_point`。
- 删除公开配置样例和用户文档中 `loiter_timeout_s`、`max_scan_cycles`、`forced_strike_enabled` 等旧主流程参数描述。
- 对齐相关 specs、测试和场地样例，确保标准任务路径只描述 `起飞 -> 扫场 -> 投弹 -> 降落`。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `simplified-mission-flow`: 旧的 loiter 相关职责不仅从状态机移除，也必须从配置、文档和标准任务输入面移除。
- `field-profile`: 场地配置模型不再包含 `loiter_point`，加载与校验规则同步收敛。
- `field-editor-planning-workflow`: 规划编辑器不再展示或编辑 loiter 相关要素，只保留任务仍使用的边界、跑道、起飞、扫场与降落预览。
- `config-system`: 标准配置接口不再暴露 loiter/rescan/forced-strike 旧参数作为有效任务配置。

## Impact

- Affected code: `src/striker/config/field_profile.py`, `src/field_editor/logic.mjs`, `data/fields/*/field.json`, `config.example.json`, `.env.example`, related tests and docs.
- Affected systems: field profile schema, field editor import/export contract, user-facing configuration examples, mission-flow documentation.
