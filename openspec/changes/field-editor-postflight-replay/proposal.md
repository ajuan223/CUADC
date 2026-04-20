## Why

Field Editor 目前擅长场地规划，但缺少飞后复盘能力。对于另一台设备上的远程查看场景，Mission Planner 能提供通用地面站视角，却不能把航迹、计划投弹语义和场地几何放在同一个前端里统一回看，因此现在需要把 Field Editor 补齐为“飞后分析 / 回放前端”，而不是再做一套实时地面站。

## What Changes

- 在 Field Editor 中新增飞后回放视图，允许加载历史 `flight_log` 并在地图上回放飞机航迹。
- 在回放视图中展示当前回放时刻的飞机位置，并提供播放、暂停、拖动进度、倍速和缩放到轨迹等基础控制。
- 在回放视图中叠加场地边界、跑道、扫场预览、计划投弹点与实际投弹点，支持飞后偏差观察。
- 扩展 `flight_log` 结构与记录行为，使其能在日志中标记 release 触发时刻，并保留与飞后复盘相关的投弹点字段。
- 明确该变更不包含实时飞机位置查看，不尝试替代 Mission Planner 的在线地面站能力。

## Capabilities

### New Capabilities
- `field-editor-postflight-replay`: 提供基于历史飞行日志的地图回放、轨迹展示和投弹结果复盘能力。

### Modified Capabilities
- `flight-recorder`: 调整飞行记录结构，使 release 事件标记与投弹点相关字段能够直接落入 `flight_log`，供飞后回放消费。

## Impact

- Affected code: `src/field_editor/`, `src/striker/telemetry/flight_recorder.py`, `src/striker/core/context.py`, 以及 release / vision 相关状态更新链路。
- Affected artifacts: `runtime_data/flight_logs/` 下的 CSV 结构与解析逻辑。
- Affected UX: Field Editor 从纯规划前端扩展为规划 + 飞后复盘前端。
- Non-goal: 不新增实时 Web 遥测流，不引入 WebSocket 在线飞机位置显示。