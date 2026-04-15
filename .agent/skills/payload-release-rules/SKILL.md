# 载荷投弹模块编码规范

本 Skill 约束 `src/striker/payload/` 目录下的所有代码。载荷模块负责弹道解算、释放控制和强制投弹降级。

## 架构约束

- 载荷投放为**弹道式**（固定翼不能悬停），释放时机由弹道解算决定
- 弹道解算输入: 当前位置(高度/速度/航向)、目标坐标、风场数据、载荷物理参数
- 弹道解算输出: 释放点坐标 (提前量计算)
- 强制投弹是超时降级机制：`scan_cycle_count >= max_scan_cycles` 时触发
- 强制投弹坐标必须在围栏内且通过 `point_in_polygon` 二次校验 (RL-10)
- 强制投弹坐标通过 `generate_random_point_in_polygon()` 生成

### 强制投弹流程 (v2.2)
1. LOITER 超时且 `scan_cycle_count >= max_scan_cycles`
2. 调用 `generate_random_point_in_polygon(field.geofence)` 生成随机目标
3. `point_in_polygon()` 二次校验确认坐标在围栏内
4. 转入 FORCED_STRIKE 状态，飞向该坐标投弹

### 依赖方向
- `payload/` 可依赖: `comms/`(遥测数据), `config/`(弹道参数), `core/events.py`, `safety/geofence.py`, `exceptions.py`
- `payload/` 被依赖: `core/states/`(STRIKE 状态触发投弹)
- `payload/` 禁止依赖: `flight/`, `vision/`, `core/machine.py`

### 数据流
- 输入: 当前位置 + 目标坐标 + 风场 → 弹道解算 → 释放点
- 输入: 围栏多边形 → 随机点生成 → 二次校验 → 强制投弹坐标

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `solve_release_point()` | 弹道解算函数 |
| `generate_random_point_in_polygon()` | 围栏内随机点生成 |
| `execute_payload_release()` | 执行载荷释放 |

## 禁止模式

- **禁止**跳过弹道解算直接在目标正上方释放 — 固定翼有前进速度，必须计算提前量
- **禁止**强制投弹坐标不经 `point_in_polygon` 二次校验 — RL-10 红线
- **禁止**硬编码载荷物理参数（质量、风阻系数等）— 必须从 `config/` 读取
- **禁止**在弹道解算中忽略风场数据 — 风场对弹道影响显著
- **禁止**将弹道解算结果视为精确值 — 必须有误差评估和已知答案测试 (KAT)
