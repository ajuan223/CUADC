## 1. 基础设施准备

- [x] 1.1 在 `utils/geo.py` 中新增 `haversine_distance(lat1, lon1, lat2, lon2) -> float` 函数，返回两点间距离（米）
- [x] 1.2 为 `haversine_distance` 编写单元测试（已知坐标对验证精度）

## 2. 预烧录任务结构简化

- [x] 2.1 修改 `flight/preburned_mission.py`：`PreburnedMissionInfo` 删除 `slot_start_seq` / `slot_end_seq` 字段
- [x] 2.2 修改 `parse_preburned_mission()`：移除 5 slot 校验逻辑，仅解析 `loiter_seq` 和 `landing_start_seq`，校验 `landing_start_seq > loiter_seq + 1`
- [x] 2.3 更新 `preburned_mission.py` 单元测试

## 3. 攻击几何简化

- [x] 3.1 修改 `flight/attack_geometry.py`：将 `compute_attack_slots()` 重构为 `compute_attack_geometry()`，返回 `(approach, target, exit)` 三个 `(lat, lon)` 元组，不再生成 mission items
- [x] 3.2 删除 `compute_attack_slots()` 中的 mav / release_channel / release_pwm 参数
- [x] 3.3 更新 `attack_geometry.py` 单元测试

## 4. 核心：新建 GuidedStrikeState

- [x] 4.1 创建 `core/states/guided_strike.py`，实现 `GuidedStrikeState(BaseState)` 含内部 phase 枚举 (INIT/APPROACH/STRIKE/EXIT)
- [x] 4.2 实现 `on_enter()`：读取投弹点（vision 优先 → fallback 降级）、调用 `compute_attack_geometry()` 计算三个坐标、`set_mode(GUIDED)` + `goto()` 导航到 approach
- [x] 4.3 实现 `execute()` APPROACH 阶段：`resend_position_target` keepalive + `haversine_distance` 到达判定 → 切换 STRIKE
- [x] 4.4 实现 `execute()` STRIKE 阶段：keepalive + 距离判定 → `send_command(DO_SET_SERVO)` 投弹（dry_run 跳过）+ `mark_release_triggered()`
- [x] 4.5 实现 `execute()` EXIT 阶段：导航到 exit 点 + 到达判定 → `Transition("release_monitor")`
- [ ] 4.6 调用 `register_state("guided_strike", GuidedStrikeState)`

## 5. 状态机转换链更新

- [x] 5.1 修改 `core/machine.py`：删除 `loiter_hold` / `attack_run` State 声明，新增 `guided_strike` State
- [x] 5.2 更新转换定义：`to_guided_strike = scan_monitor.to(guided_strike)`，`to_release_monitor = guided_strike.to(release_monitor)`
- [x] 5.3 更新 `to_override` 和 `to_emergency` 包含 `guided_strike` 源状态

## 6. 关联状态更新

- [x] 6.1 修改 `core/states/scan_monitor.py`：transition target 从 `"loiter_hold"` 改为 `"guided_strike"`
- [x] 6.2 修改 `core/states/release_monitor.py`：不再依赖 `preburned_info.slot_start_seq`，改为检查 `context.release_triggered` 标志
- [x] 6.3 修改 `core/states/landing_monitor.py`：`on_enter()` 新增 `MISSION_SET_CURRENT(landing_start_seq)` + `set_mode(AUTO)` 切换

## 7. 清理与注册

- [x] 7.1 删除 `core/states/loiter_hold.py`
- [x] 7.2 删除 `core/states/attack_run.py`
- [x] 7.3 更新 `core/states/__init__.py`：移除 loiter_hold / attack_run 注册
- [x] 7.4 更新 `app.py`：import 和注册 `GuidedStrikeState` 替代 `LoiterHoldState` + `AttackRunState`

## 8. 验证

- [x] 8.1 运行 `ruff check` + `mypy --strict` 确保零错误
- [x] 8.2 运行全量单元测试 `pytest tests/`
- [x] 8.3 SITL 全链路验证：更新预烧录任务文件（删除空白 slot）后执行 `scripts/run_sitl.sh`
