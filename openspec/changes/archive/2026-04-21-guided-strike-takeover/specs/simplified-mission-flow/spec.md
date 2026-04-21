## MODIFIED Requirements

### Requirement: 主任务链必须收敛为单次投放流程
系统 SHALL 将自动任务主链定义为 `STANDBY → SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR → COMPLETED`。GUIDED_STRIKE 阶段 SHALL 切换飞控至 GUIDED 模式实现程序化导航打击，完成后切回 AUTO 执行预烧录降落段。

#### Scenario: 扫场后收到视觉投弹点
- **WHEN** 飞控真实完成扫场且视觉侧已经提供有效投弹点
- **THEN** 系统进入 `guided_strike` 状态，切 GUIDED 模式执行程序化打击

#### Scenario: 扫场后未收到视觉投弹点
- **WHEN** 飞控真实完成扫场且视觉侧未提供有效投弹点
- **THEN** 系统 SHALL 使用 field profile 中的 fallback_drop_point 进入 `guided_strike`

### Requirement: 预烧录任务结构不含空白 slot
预烧录任务 SHALL 仅包含：takeoff、scan 航点、LOITER_UNLIM（安全锚）、DO_LAND_START、降落航点。LOITER_UNLIM 与 DO_LAND_START 之间 SHALL NOT 有任何空白 slot。

#### Scenario: 预烧录任务解析
- **WHEN** `parse_preburned_mission()` 解析预烧录任务
- **THEN** SHALL 不再要求 slot_start_seq / slot_end_seq，仅解析 loiter_seq 和 landing_start_seq

#### Scenario: 安全锚行为
- **WHEN** Striker 进程崩溃且飞控到达 LOITER_UNLIM
- **THEN** 飞控 SHALL 在 LOITER_UNLIM 处无限盘旋，不会飞向虚空
