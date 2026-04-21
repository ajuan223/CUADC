# 外部解算接口编码规范

本 Skill 约束 `src/striker/vision/` 目录下的所有代码。本模块负责接收外部视觉系统发送的投弹点坐标。

## 架构约束

- 视觉解算程序与 Striker 运行在同一 Python 进程内（或通过共享内存/RPC写入，当前为同进程全局变量）
- `global_var.py` 提供线程安全的单例状态容器，用于存放和获取视觉解算得到的投弹点坐标
- 接收到的坐标数据必须通过 `validate_gps()` 验证
- 投弹点语义: 视觉系统设置的是**投弹点坐标**（payload 应该释放的精确地面位置），不需要弹道二次解算

### 依赖方向
- `vision/` 可依赖: `exceptions.py`
- `vision/` 被依赖: `core/states/loiter_hold.py` (在 FSM 中获取当前投弹点)
- `vision/` 禁止依赖: `comms/`, `flight/`, `safety/`, `core/machine.py`

### 数据流
- 外部视觉系统调用 `set_vision_drop_point()` → 更新 `global_var.VISION_DROP_POINT` → `loiter_hold.py` 调用 `get_vision_drop_point()` 获取

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `get_vision_drop_point()` | 线程安全地获取当前全局视觉投弹点 |
| `set_vision_drop_point()` | 线程安全地设置当前全局视觉投弹点并执行地理边界验证 |
| `GpsDropPoint` | 投弹点坐标数据类 |
| `validate_gps()` | GPS坐标验证 |

## 禁止模式

- **禁止**重新引入 `TcpReceiver` / `UdpReceiver` 或基于网络的 receiver 接口 — 架构已简化为全局变量读写
- **禁止**在本模块中实现图像处理或视觉算法 — 图像处理和解算由外部程序独立完成
- **禁止**信任外部程序设置的坐标未经校验 — `set_vision_drop_point` 必须调用 `validate_gps()` 验证
