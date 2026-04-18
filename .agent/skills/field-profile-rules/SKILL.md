# 场地配置编码规范

本 Skill 约束场地配置 (Field Profile) 相关代码，主要涉及 `src/striker/config/field_profile.py` 和 `data/fields/` 目录。

## 架构约束

- 场地配置使用 pydantic `BaseModel`，数据文件固定为 `data/fields/{name}/field.json`
- `FieldProfile` 当前包含：`boundary`、`landing`、`scan`、`attack_run`、`safety_buffer_m`
- 围栏是封闭多边形，首尾点缺失时由加载器自动补闭合
- `landing.touchdown_point` 和导出的落地进近点必须位于围栏内；否则加载直接失败
- `scan` 保存的是程序化生成参数，不是手写航点列表；扫描航点由 `mission_geometry.py` 运行时生成
- `scan.boundary_margin_m` 属于场地数据本身，不能再通过全局 settings 漂移覆盖
- `attack_run.fallback_drop_point` 是可选场地级降级投弹点；无视觉投弹点时才会被 `scan.py` 使用
- `sitl_home_string()` 和 `sitl_params_path()` 为 `scripts/run_sitl.sh` 提供场地相关启动输入

### 依赖方向
- `field_profile.py` 可依赖: `exceptions.py`, `striker.utils.geo`, pydantic
- 被依赖: `flight/mission_geometry.py`, `flight/landing_sequence.py`, `core/context.py`, `core/states/scan.py`, `scripts/run_sitl.sh`
- 禁止依赖: `payload/`, `vision/`, `safety/monitor.py`

### 数据流
- `data/fields/{name}/field.json` → `load_field_profile()` → pydantic 校验 + 地理校验 → `FieldProfile`
- `FieldProfile` → mission geometry / landing sequence / SITL launcher / field editor 导入导出

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `FieldProfile` | 场地配置总模型 |
| `load_field_profile()` | 场地配置加载函数 |
| `point_in_polygon()` | 围栏点内判定 |
| `sitl_home_string()` | 生成 SITL home 字符串 |

## 禁止模式

- **禁止**在场地模型中保留已删除的 `runway`、`scan_waypoints`、`loiter_point` 等旧字段描述
- **禁止**绕过加载阶段的围栏与进近点校验 — 非法场地必须直接失败
- **禁止**硬编码场地坐标或参数到业务代码 — 必须从 `data/fields/{name}/field.json` 读取
- **禁止**把 `scan.boundary_margin_m` 再放回全局 settings 作为主来源
- **禁止**在本模块中混入 payload / release 决策逻辑 — 这里只负责字段模型与地理合法性
