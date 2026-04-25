# Striker — 项目愿景

Striker 是一套面向固定翼无人机的自主任务飞控系统，目标是在**固定场地**内完成从起飞、扫场、投放到降落的全自动任务闭环。

当前系统已经从早期的多阶段探索方案，收敛为一条更清晰、更可验证的主链：

```text
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING → COMPLETED
```

---

## 1. 项目使命

Striker 运行在伴飞计算机上，通过 MAVLink 与 ArduPlane 飞控通信，在固定翼平台上完成以下工作：

- 读取场地配置
- 自动生成任务几何
- 上传完整任务到飞控
- 执行扫场搜索
- 根据视觉结果或兜底逻辑确定投放点
- 完成投放动作
- 自动进入降落序列

项目的核心目标不是“让任务流程尽量复杂”，而是：

> 用最少的人工航点配置、最强的几何一致性和最清晰的状态机主链，完成一套稳定、可验证、可复现实飞迁移的固定翼自动任务系统。

---

## 2. 当前架构方向

### 2.1 场地事实驱动，而不是手工航点驱动

系统不再要求用户手工编写：

- 降落进近点
- 扫场 waypoint 列表
- 静态起飞段任务

取而代之的是只配置**场地事实**：

- 围栏 polygon
- 接地点 touchdown_point
- 跑道方向 heading_deg
- 下滑角 glide_slope_deg
- 进近高度 approach_alt_m
- 跑道长度 runway_length_m
- 扫场间距 spacing_m
- 扫场方向 heading_deg

然后由系统自动生成：

- 起飞几何
- 扫场几何
- 降落几何

这意味着：

> 用户描述场地，系统生成任务。

---

## 3. 三类程序化几何

### 3.1 程序化降落几何

降落进近点通过下滑线反推得到：

- 输入：`touchdown_point + heading_deg + approach_alt_m + glide_slope_deg`
- 公式：

```text
distance = delta_alt / tan(glide_slope_deg)
```

对于默认 SITL 场地：

- `approach_alt_m = 30m`
- `glide_slope_deg = 3°`
- 理论距离约 `573m`
- 实测推导值约 `572.4m`

这证明程序化降落点推导是可解释、可验证的。

### 3.2 程序化扫场几何

扫场路径由 boundary polygon 自动生成，不再依赖手工 waypoint 列表。

当前算法采用 Boustrophedon 覆盖路径思路：

1. 按指定 heading 旋转多边形
2. 使用 sweep line 生成覆盖条带
3. 以往返方式排序
4. 逆旋转回原坐标系

结果是：

- 更稳定
- 更容易调整 spacing
- 更适应不同场地边界

### 3.3 程序化起飞几何

起飞任务从跑道事实自动生成：

- 跑道中点
- 起飞起点
- 爬升点

目标是让起飞任务与场地方向天然一致，而不是依赖固定的 NAV_TAKEOFF + 静态 waypoint 组合。

---

## 4. 当前任务链的设计理念

### 4.1 INIT

负责加载配置、建立连接、初始化上下文。

### 4.2 PREFLIGHT

负责生成完整 mission geometry 并上传 full mission。

这是当前系统最关键的结构点之一：

> 在真正起飞前，就把起飞 + 扫场 + 降落几何全部生成并上传。

### 4.3 TAKEOFF

自动起飞并到达扫场高度。

### 4.4 SCAN

执行程序化扫场路径。

SCAN 的意义是让系统先完整飞过场地，获取视觉投放点输入，而不是直接飞向一个静态目标。

### 4.5 ENROUTE

扫场结束后，系统根据投放点生成临时攻击跑任务并上传。

这个阶段的特点是：

- 使用临时 attack mission
- 飞机进入攻击跑
- 任务尾部拼接 landing sequence

### 4.6 RELEASE

释放逻辑独立成状态，便于：

- dry-run
- native DO_SET_SERVO
- GPIO release
- 未来扩展不同投放机构

### 4.7 LANDING

投放完成后立即进入降落序列。

当前系统不再保留早期那些复杂的中间状态规划，而是强调：

> 投放完成后快速、稳定地进入 landing。

---

## 5. 视觉输入语义

当前视觉链路输入的是：

- **投放点坐标**

而不是：

- 原始目标识别结果
- 靶标框
- 弹道求解前的抽象目标点

这使系统边界更清楚：

- 视觉系统负责识别与解算
- Striker 负责飞行控制与任务编排

若扫描结束后没有可用视觉点，则系统按照以下 **优先级（3级兜底策略）** 确定最终投放点：

1. **外部视觉传入**：若视觉系统提供平滑后的投放点，则直接使用。
2. **场地预设兜底点**：若无视觉结果，尝试使用 `field.json` 中的 `attack_run.fallback_drop_point`。
3. **几何质心**：若预设兜底点未配置，则计算当前飞行边界区域的几何质心作为最终兜底。

这样可以保证主链持续推进，而不是停留在等待态。

---

## 6. 对“简化”的理解

Striker 的目标不是把所有可能的状态都塞进主链，而是把真正有价值、真正可验证、真正与飞控闭环相关的环节保留下来。

因此当前方向强调：

- 少状态，但每个状态职责明确
- 少手工航点，但几何自动生成可解释
- 少模糊中间层，但任务主链闭环清晰
- 少“未来也许会用”的复杂设计，多已经能在 SITL 验证通过的现实链路

---

## 7. 当前阶段的成功标准

一个版本是否达标，优先看这些问题：

1. 是否可以只靠 field profile 自动生成 mission geometry？
2. 是否能在 SITL 中完成 full mission upload？
3. 是否能从 TAKEOFF 正常进入 SCAN？
4. 是否能在 SCAN 后切到 ENROUTE 并执行 RELEASE？
5. 是否能在 RELEASE 后进入 LANDING？
6. 降落进近点的距离是否和 glide slope 公式一致？

如果这些都成立，那么系统的核心价值链就是成立的。

---

## 8. 当前成果状态

当前已验证：

- field-driven procedural mission generation 已落地
- 新 field profile schema 已生效
- 降落进近点自动反推正确
- 程序化 Boustrophedon 扫场已生成并在 SITL 中执行
- 程序化起飞几何已生效
- full mission upload 与 attack mission upload 已跑通
- 主链 `INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING` 已在 SITL 中验证

这意味着项目已经从“架构探索期”进入“围绕当前主链持续打磨与稳固”的阶段。
