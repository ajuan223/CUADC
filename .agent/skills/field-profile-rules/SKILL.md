# 场地配置编码规范

本 Skill 约束场地配置 (Field Profile) 相关代码，主要涉及 `src/striker/config/field_profile.py` 和 `data/fields/` 目录。

> v2.2 新增: 场地配置从 config 模块独立为专门规范，因其涉及复杂的地理数据模型和校验逻辑。

## 架构约束

- 场地配置使用 pydantic `BaseModel`（非 BaseSettings），数据文件存放在 `data/fields/{name}.json`
- `FieldProfile` 包含: 围栏多边形 (geofence)、跑道参数 (runway)、扫场航点 (scan_waypoints)、降落序列参数 (landing)、安全区域
- 围栏是**封闭多边形**，首尾坐标必须相同（或由加载器自动闭合）
- 航点必须在围栏内（加载时校验，`PointOutsideGeofenceError`）
- 跑道必须完全在围栏内（加载时校验）
- 场地配置文件通过 `field` 配置项选择（如 `STRIKER_FIELD=zijingang`）
- 无有效场地配置不得起飞 (RL-08)
- 围栏/跑道/航点必须通过 pydantic 校验 (RL-09)

### 数据模型结构
```python
class FieldProfile(BaseModel):
    name: str
    geofence: list[GeoPoint]       # 封闭多边形
    runway: RunwayConfig           # 跑道参数
    scan_waypoints: list[GeoPoint] # 扫场航点序列
    landing: LandingConfig         # 降落序列参数
    safe_altitude_m: float         # 安全高度
```

### 依赖方向
- `field_profile.py` 可依赖: `config/settings.py`(场地名), `exceptions.py`, pydantic
- 被依赖: `flight/navigation.py`(扫场航点), `flight/landing_sequence.py`(降落参数), `safety/geofence.py`(围栏), `payload/`(强制投弹)

### 数据流
- `data/fields/{name}.json` → `FieldProfile.load()` → pydantic 校验 → 注入到 `MissionContext`

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `FieldProfile` | 场地配置数据模型 |
| `load_field_profile()` | 场地配置加载函数 |
| `validate_waypoints_in_geofence()` | 航点围栏校验函数 |

## 禁止模式

- **禁止**加载未通过 pydantic 校验的场地配置 — RL-09 红线
- **禁止**允许航点在围栏外的配置通过加载 — 必须抛出 `PointOutsideGeofenceError`
- **禁止**允许跑道不在围栏内的配置通过加载
- **禁止**硬编码场地坐标 — 所有场地数据必须从 `data/fields/*.json` 读取
- **禁止**在无有效场地配置时允许起飞 — RL-08 红线
- **禁止**跳过围栏封闭性校验 — 多边形必须闭合
