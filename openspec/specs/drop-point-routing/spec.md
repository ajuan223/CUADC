### Requirement: 视觉输入必须被解释为投弹点而非靶标点
系统 SHALL 将视觉链路输入统一定义为“投弹点 GPS 坐标”，并且下游状态机、上下文和日志必须按投弹点语义处理该数据，而不是把它当作待本侧再次解算释放点的靶标点。

#### Scenario: 视觉点进入任务上下文
- **WHEN** 视觉接收器收到合法的经纬度点
- **THEN** 系统必须把该点保存为投弹点语义的数据，而不是保存为等待弹道解算的靶标点语义数据

#### Scenario: 投弹点驱动转场
- **WHEN** 扫场完成后存在有效视觉投弹点
- **THEN** 系统必须直接以该投弹点作为转场目标坐标

### Requirement: 收到视觉投弹点时不得再做本侧弹道释放点解算
系统 MUST 在“视觉已给投弹点”的链路中绕过或删除本侧 `ballistics` 释放点解算，并且不得为了接近投放而额外生成新的 release point 坐标。

#### Scenario: 视觉点存在时进入接近阶段
- **WHEN** 任务链路已收到有效视觉投弹点
- **THEN** 系统不得调用基于风场、速度和落体时间的释放点解算来替代该视觉点

#### Scenario: 投放目标坐标一致性
- **WHEN** 系统记录转场目标与投放决策日志
- **THEN** 日志中的目标坐标必须与视觉提供的投弹点一致

### Requirement: 无视觉投弹点时必须计算确定性的中点兜底投弹点
系统 SHALL 在视觉侧未提供投弹点时，以”扫场结束点 + 降落参考点”为输入计算一个确定性的兜底投弹点，并使用该点执行后续转场与投放。

**实现约束**：
- 项目已依赖 `geopy`（`pyproject.toml`），且 `geopy.distance.geodesic` 已在 `src/striker/payload/ballistics.py` 中使用。
- 中点可通过 `geodesic(kilometers=d/2).destination(point, bearing)` 从两点间等距处获得，无需引入新依赖。
- 扫场结束点可从 `field_profile.scan_waypoints.waypoints[-1]` 获取；降落参考点来源需在实现前与业务确认（`landing.approach_waypoint` 或 `landing.touchdown_point`）。

#### Scenario: 视觉点缺失时生成兜底点
- **WHEN** 扫场完成后视觉投弹点不存在或已失效
- **THEN** 系统必须使用扫场结束点和预定义降落参考点生成一个兜底投弹点

#### Scenario: 兜底点参与后续飞行
- **WHEN** 兜底投弹点生成完成
- **THEN** 系统必须将该点作为后续 GUIDED 转场与投放的统一目标坐标

### Requirement: 投放后必须统一进入降落链路
系统 MUST 在视觉投弹点链路和兜底中点链路中都复用同一条“投放完成 → LANDING”状态迁移，并继续依赖预上传 mission 的 landing 序列执行降落。

#### Scenario: 视觉点投放完成后降落
- **WHEN** 系统在视觉投弹点链路中完成投放触发
- **THEN** 系统必须进入 LANDING 并跳转到预上传 landing 序列

#### Scenario: 兜底点投放完成后降落
- **WHEN** 系统在兜底中点链路中完成投放触发
- **THEN** 系统必须进入与视觉点链路相同的 LANDING 执行路径
