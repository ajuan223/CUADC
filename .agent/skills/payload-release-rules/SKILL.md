# 载荷投弹模块编码规范

本 Skill 约束 `src/striker/payload/` 目录下的所有代码。载荷模块负责释放机构控制，并保留少量与释放相关的辅助模型/工具。

## 架构约束

- 释放机构当前有两类实现：MAVLink `DO_SET_SERVO` 和 GPIO 直控
- 释放时机由上层状态机决定；`release.py` 进入 RELEASE 状态后仅调用 payload 控制器执行释放，并由 `MissionContext` 记录首次成功 release 时间
- 投弹点来源由 `scan.py` / `MissionContext` 决定，payload 模块不负责投弹点选择
- `ReleaseConfig` 封装释放参数（方法、通道、PWM 值、GPIO 引脚等）
- `BallisticCalculator` 与 `BallisticParams` 仍存在于代码中，但不是当前主任务流程的依赖，不得把它重新写回主链路说明
- `SequencedRelease` 目前是保留 stub，不是已启用能力

### 依赖方向
- `payload/` 可依赖: `comms/`(MAVLink 发送), `config/`(释放参数), `core/events.py`, `exceptions.py`
- `payload/` 被依赖: `core/states/release.py`(RELEASE 状态触发投弹)
- `payload/` 禁止依赖: `flight/`, `vision/`, `core/machine.py`, `safety/`

### 数据流
- 输入: `ReleaseController.execute_release()` — 收到释放指令即执行
- 输出: MAVLink DO_SET_SERVO 命令 / GPIO 电平切换

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `ReleaseController` | 释放控制器 Protocol |
| `MavlinkRelease` | MAVLink 释放控制器 |
| `GpioRelease` | GPIO 释放控制器 |
| `ReleaseConfig` | 释放配置数据类 |
| `SequencedRelease` | 多次释放 stub（未接入主流程） |

## 禁止模式

- **禁止**硬编码载荷释放参数（通道号、PWM 值等）— 必须从 `config/` 读取
- **禁止**在释放控制中忽略连接状态 — 必须确认 MAVLink 连接正常
- **禁止**把 payload 模块描述成“决定投弹点”或“决定释放时机”的业务层
- **禁止**将 `BallisticCalculator` 重新引入当前主任务流程说明 — 当前主链路依赖视觉投弹点或 field/midpoint fallback
- **禁止**把 `SequencedRelease` 写成已启用多投能力 — 它目前只是 stub
