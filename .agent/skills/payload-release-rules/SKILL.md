# 载荷投弹模块编码规范

本 Skill 约束 `src/striker/payload/` 目录下的所有代码。载荷模块负责释放机构控制和弹道解算工具。

## 架构约束

- 释放机构有双通道实现：MAVLink `DO_SET_SERVO` 和 GPIO 直控
- 释放时机由上层状态机决定（ENROUTE 到达投弹点后触发 RELEASE 状态）
- 投弹点坐标来自两个来源：视觉系统直接提供的投弹点，或兜底中点计算
- `BallisticCalculator` 保留为独立工具类，不在主任务流程中调用
- `ReleaseConfig` 封装释放参数（方法、通道、PWM 值、GPIO 引脚等）

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
| `MavlinkRelease` | MAVLink 释放控制器 |
| `GpioRelease` | GPIO 释放控制器 |
| `ReleaseConfig` | 释放配置数据类 |
| `BallisticCalculator` | 弹道解算工具类（非主流程） |

## 禁止模式

- **禁止**硬编码载荷释放参数（通道号、PWM 值等）— 必须从 `config/` 读取
- **禁止**在释放控制中忽略连接状态 — 必须确认 MAVLink 连接正常
- **禁止**将 `BallisticCalculator` 引入主任务流程 — 主流程使用视觉直给投弹点或兜底中点
