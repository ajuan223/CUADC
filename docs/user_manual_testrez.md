# Striker 用户手册功能测试报告

**日期**: 2026-04-16  
**测试环境**: Linux dev workstation + unit tests + SITL end-to-end validation

---

## 测试摘要

| 类别 | 结果 | 说明 |
|------|------|------|
| 包入口 & 导入 | PASS | `python -m striker` 正常 |
| 配置系统 | PASS | `STRIKER_*` 配置生效 |
| 场地配置 schema | PASS | 新 `scan` / `landing` schema 正常 |
| 程序化降落几何 | PASS | approach distance ≈ 572.4m |
| 程序化扫场几何 | PASS | 10 waypoints / 5 sweeps |
| 程序化起飞几何 | PASS | runway-aligned takeoff |
| 任务上传 | PASS | full mission 16 items |
| 状态机主链 | PASS | INIT→PREFLIGHT→TAKEOFF→SCAN→ENROUTE→RELEASE→LANDING |
| 单元测试 | PASS | 当前相关测试通过 |

---

## 1. 本轮测试重点

本轮重点不再是早期弹道链路或 LOITER/FORCED_STRIKE 方案，而是：

- 新 field profile schema 是否正确
- 是否能从场地事实自动生成 mission geometry
- SITL 中是否能跑通新的主链

---

## 2. Schema 迁移验证

已验证的新配置结构：

### landing

- 删除 `approach_waypoint`
- 新增：
  - `touchdown_point`
  - `heading_deg`
  - `glide_slope_deg`
  - `approach_alt_m`
  - `runway_length_m`

### scan

- 删除 `scan_waypoints.waypoints`
- 改为：
  - `altitude_m`
  - `spacing_m`
  - `heading_deg`

结论：

- 新 schema 可加载
- 单元测试覆盖正常
- 无需再手工维护扫场/降落进近航点

---

## 3. 程序化几何结果

### 3.1 降落几何

SITL 默认场地参数：

- glide slope: `3°`
- approach altitude: `30m`

系统推导结果：

- approach distance: `572.4m`

这与理论值 `30 / tan(3°)` 一致。

### 3.2 扫场几何

系统生成：

- `10` 个扫场航点
- `5` 条 sweep
- spacing=`200m`

### 3.3 起飞几何

系统根据 runway facts 自动生成：

- 起飞起点
- 爬升点
- 与跑道方向对齐

---

## 4. SITL 全链路结果

已完成链路：

```text
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING
```

验证点：

- 程序化 full mission 上传成功：`16 items`
- attack mission 上传成功：`8 items`
- 飞机成功从 TAKEOFF 进入 SCAN
- scan 完成后切入 ENROUTE
- DO_SET_SERVO 原生释放触发
- RELEASE 后切入 LANDING

---

## 5. 本轮修复的问题

### 5.1 Landing items seq bug

问题：

- landing items 在 full mission 中未重新编号
- SITL 重复请求 item 13
- upload 超时

修复：

- 在 `build_waypoint_sequence()` 中对 landing items 重写 seq

结果：

- upload 成功
- 16 items 全部被 SITL 接受

### 5.2 SITL home 错误

问题：

- 默认落在 Canberra

修复：

- 显式设置 `--home 30.2610,120.0950,0,180`

### 5.3 plane.parm 路径错误

修复为：

```text
Tools/autotest/models/plane.parm
```

---

## 6. 结论

当前用户手册所描述的主流程、配置方式与 SITL 行为是一致的。

项目已从：

- 手工航点配置
- 旧的 scan_waypoints / approach_waypoint 模式
- 早期复杂降级设想

迁移为：

- 场地事实驱动
- 程序化几何生成
- 简化主链
- 可在 SITL 中闭环验证
