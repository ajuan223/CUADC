# 状态机模块编码规范

本 Skill 约束 `src/striker/core/` 目录下的所有代码。核心模块是 Striker 的业务编排骨架，负责状态机引擎、事件系统和状态注册。

## 架构约束

- 状态机基于 `python-statemachine` 库实现，类继承 `StateMachine`
- 状态链: `init→preflight→takeoff→scan→enroute→release→landing→completed`，加两个终端态 `override` 和 `emergency`，共 10 态
- 每个业务状态对应一个 `State` 声明和一个 `states/{name}.py` 文件
- 所有状态类必须继承 `BaseState` ABC，实现 `on_enter()` / `execute()` / `on_exit()` 生命周期
- `MissionContext` 是状态间共享数据的**唯一**容器，禁止通过全局变量或模块级状态传递数据
- FSM 引擎具有两个全局拦截：`OverrideEvent` 和 `EmergencyEvent`，任意非终端状态均可触发
- 状态转换通过事件驱动或 `execute()` 返回 `Transition`，禁止绕过事件系统直接修改 `current_state`
- SCAN 完成后执行投弹点决策：有视觉投弹点 → ENROUTE；无视觉投弹点 → 计算兜底中点 → ENROUTE
- 异步模式下 `rtc=False`（禁用 run-to-completion）

### 依赖方向
- `core/` 可依赖: `config/`, `comms/`(通过接口), `exceptions.py`
- `core/` 被依赖: `app.py`, `safety/`, `vision/` 通过上下文、事件和状态推进与 FSM 交互
- `core/states/` 中的业务状态可依赖 `flight/`, `safety/` 的公共接口

### 数据流
- 事件 (`Event`) → FSM 引擎 → 当前状态 `handle()` → 返回 `Transition` 或 `None`
- `MissionContext` 双向: 状态写入 / 安全监控与视觉链路读取

## 注册模式

FSM 引擎和状态注册完成后，应注册以下能力：

| 注册项 | 说明 |
|--------|------|
| `MissionStateMachine` | 状态机引擎类 |
| `BaseState` | 状态基类 ABC |
| `MissionContext` | 共享状态容器 |
| `Event` 子类 | 各类事件（OverrideEvent, EmergencyEvent 等） |

## 禁止模式

- **禁止**绕过事件系统直接修改当前状态 — 必须通过 `process_event()` 触发转换
- **禁止**在 `MissionContext` 外使用全局变量传递飞行状态 — 共享数据必须收敛到 context
- **禁止**在状态类的 `execute()` 中执行阻塞 I/O — 所有操作必须是 async
- **禁止**业务状态直接 import pymavlink — 必须通过 `comms/` 模块的公共接口
- **禁止**继续引用 `loiter`、`approach`、`forced_strike` 等已删除状态或旧状态链
- **禁止**把 payload 决策留在 `payload/` 模块中实现 — 当前投弹点决策发生在 `scan.py`，释放动作发生在 `release.py`
