# 场地配置编码规范

本 Skill 约束场地配置 (Field Profile) 相关代码，主要涉及 `src/striker/config/field_profile.py` 和 `data/fields/` 目录。

## 架构约束

- 场地配置使用 pydantic `BaseModel`，数据文件固定为 `data/fields/{name}/field.json`
- 支持 JSONC 格式：文件内**必须**使用 `// runtime` 或 `// shared` 对字段进行消费阶段标注。Python 侧加载器会自动通过正则剥离注释。
- `FieldProfile` 仅包含纯运行时与共享所需字段：`boundary`、`landing`（仅含航向与落点）、`scan`（仅含基准高度）、`attack_run`、`safety_buffer_m`。
- **纯规划字段被彻底隔离**：如 `scan.spacing_m` 或 `landing.glide_slope_deg` 属于 Web Editor 生成 `.waypoints` 的临时上下文，**严禁**出现在 `field.json` 或后端 Pydantic 模型中。
- 围栏是封闭多边形，首尾点缺失时由加载器自动补闭合
- `landing.touchdown_point` 必须位于围栏内；否则加载直接失败（注：进近点计算与校验已移交至前端规划阶段）
- `attack_run.fallback_drop_point` 是可选场地级降级投弹点；无视觉投弹点时才会被 `guided_strike.py` 兜底使用
- `sitl_home_string()` 和 `sitl_params_path()` 为 `scripts/run_sitl.sh` 提供场地相关启动输入

### 依赖方向
- `field_profile.py` 可依赖: `exceptions.py`, `striker.utils.geo`, pydantic
- 被依赖: `flight/attack_geometry.py`, `core/context.py`, `core/states/loiter_hold.py`, `scripts/run_sitl.sh`
- 禁止依赖: `payload/`, `vision/`, `safety/monitor.py`

### 数据流
- `data/fields/{name}/field.json` → `load_field_profile()` → pydantic 校验 + 地理校验 → `FieldProfile`
- `FieldProfile` → attack geometry / SITL launcher / field editor 导入导出

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `FieldProfile` | 场地配置总模型 |
| `load_field_profile()` | 场地配置加载函数 |
| `point_in_polygon()` | 围栏点内判定 |
| `sitl_home_string()` | 生成 SITL home 字符串 |

## 禁止模式

- **禁止**在场地模型中保留任何用于生成 `.waypoints` 的**纯规划阶段“幽灵”字段**（如 `scan.spacing_m`，`landing.glide_slope_deg` 等）。
- **禁止**绕过加载阶段的围栏（`boundary`）与落点（`touchdown_point`）校验 — 非法场地必须直接失败。
- **禁止**硬编码场地坐标或参数到业务代码 — 必须从 `data/fields/{name}/field.json` 读取。
- **禁止**在本模块中混入 payload / release 决策逻辑 — 这里只负责字段模型与地理合法性。
- **禁止**在 Pydantic 模型中忽略写 `description="runtime"` 或 `description="shared"` 的注释。
