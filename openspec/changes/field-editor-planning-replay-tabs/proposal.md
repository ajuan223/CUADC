## Why

Field Editor 现在把规划编辑与飞后回放堆在同一页面流里，虽然功能可用，但会把“创建/编辑场地”和“飞后复盘”两种不同工作流混在一起。用户已经明确要求回放不要继续做成规划页里的对齐小卡片，而应保持一致布局语言的同时，进入独立的 replay tab。

## What Changes

- 在 Field Editor 中引入最小化的顶层 tab 切换，将页面拆分为“规划”与“回放”两个并列入口。
- 保持现有双栏总体布局与地图承载方式不变，仅把规划表单与回放控件按 tab 分流显示，减少一次性重构成本。
- 让规划 tab 继续承载现有 field profile 编辑、预览和导出能力。
- 让回放 tab 承载历史 `flight_log` 导入、播放控制、轨迹/投放结果叠加与状态摘要。
- 明确 tab 切换不应破坏地图实例与共享 overlay 体系，优先复用已有地图初始化与渲染机制。

## Capabilities

### New Capabilities
- `field-editor-replay-tab-navigation`: 定义 Field Editor 在规划与回放之间的顶层 tab 导航与模式切换行为。

### Modified Capabilities
- `field-editor-planning-workflow`: 规划工作流从单页独占布局调整为规划 tab 内承载，但其既有规划能力保持不变。
- `field-editor-postflight-replay`: 飞后回放从规划页内联控件调整为独立回放 tab 中承载。

## Impact

- Affected code: `src/field_editor/index.html`, `src/field_editor/app.js`, `src/field_editor/styles.css`，必要时少量调整 `logic.mjs` 的 UI 模式辅助函数。
- Affected UX: Field Editor 从“单页混合规划+回放”改为“规划 tab / 回放 tab”双入口。
- Affected specs: `field-editor-planning-workflow`、`field-editor-postflight-replay`，并新增 tab 导航能力 spec。
- Non-goal: 不在这次改造中重新设计地图渲染架构，不扩展新的回放数据源，也不新增实时遥测能力。
