## 1. Archiving Obsolete Vision

- [x] 1.1 Move `init愿景.md` to `docs/archive/procedural_generation_vision.md`
- [x] 1.2 Add a historical note to the top of `procedural_generation_vision.md` explaining it was superseded by the `preburned-mission-refactor`

## 2. user_manual.md Rewrite

- [x] 2.1 Update Section 1.1 (当前任务主链) to exactly match the new sequence: `INIT → STANDBY → SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR → COMPLETED`
- [x] 2.2 Delete the obsolete programmatic generation claims in Section 1.2 (核心设计变化)
- [x] 2.3 Update Section 4 (场地配置), removing all mathematical formulas for programmatic geometry derivation (landing, scan, takeoff)
- [x] 2.4 Update Section 7 (SITL 使用说明) to reflect that the system downloads a preburned mission and executes a GUIDED takeover for the attack run

## 3. sitl_setup.md Rewrite

- [x] 3.1 Update the "Validated Mission Chains" to match the new state machine
- [x] 3.2 Remove the "Procedural landing geometry", "Procedural scan geometry", and "Procedural takeoff geometry" subsections from "What Gets Validated"
- [x] 3.3 Update the "Expected Log Milestones" to remove logs that no longer exist (e.g., `Boustrophedon scan generated`) and include current logs

## 4. data/fields/README.md Cleanup

- [x] 4.1 Remove constraints mentioning programmatic derivation (e.g., "程序化推导出的降落进近点必须位于围栏内") from the Notice section
