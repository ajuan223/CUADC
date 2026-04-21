## MODIFIED Requirements

### Requirement: ScanMonitorState shall monitor mission progress while the aircraft executes the uploaded scan segment in AUTO
ScanMonitorState SHALL 监控飞控在 Auto 模式下执行预烧录扫描航段的进度。触发条件保持不变：当 `mission_current_seq >= preburned_info.loiter_seq` 时触发转换。

#### Scenario: scan 完成到达 loiter
- **WHEN** `context.mission_current_seq >= context.preburned_info.loiter_seq`
- **THEN** ScanMonitorState SHALL 返回 `Transition("guided_strike", "Reached loiter seq")`

### Requirement: ScanMonitorState shall transition directly to GUIDED_STRIKE when scan completion is observed
ScanMonitorState SHALL 在检测到扫描完成后直接转换到 `guided_strike` 状态（而非旧的 `loiter_hold`）。

#### Scenario: 转换目标状态
- **WHEN** scan 完成条件满足
- **THEN** transition target SHALL 为 `"guided_strike"`（非 `"loiter_hold"`）

## REMOVED Requirements

### Requirement: LoiterHoldState shall resolve the drop point from vision first, then field fallback point
**Reason**: LoiterHoldState 被 GuidedStrikeState 替代。投弹点解析逻辑迁移到 guided_strike 状态。
**Migration**: 使用 `guided_strike.py` 中的 on_enter 投弹点解析。
