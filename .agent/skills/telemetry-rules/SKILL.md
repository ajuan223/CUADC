# 遥测日志模块编码规范

本 Skill 约束 `src/striker/telemetry/` 目录下的所有代码。遥测模块负责 structlog 全局配置、飞行数据记录和 GCS 状态上报。

## 架构约束

- structlog 是**唯一**的日志框架 (AGENTS.md R04)，禁止使用 stdlib `logging` 或 `print()`
- 日志配置在 `telemetry/logger.py` 中完成，其他模块通过 `structlog.get_logger()` 获取 logger
- 开发环境 (TTY) 使用 `ConsoleRenderer`，生产环境/SITL 使用 `JSONRenderer`
- 日志处理器链: `merge_contextvars` → `add_log_level` → `TimeStamper(iso, utc)` → `format_exc_info` → `dict_tracebacks` → Renderer
- 支持异步上下文变量 (`contextvars`)，可附加 mission_id、state_name 等上下文
- `FlightRecorder` 将飞行数据以 CSV 格式记录到 `runtime_data/`
- GCS 状态上报通过 `Reporter` 预留接口（实际协议待定义）

### structlog 配置模式
```python
shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.format_exc_info,
    structlog.processors.dict_tracebacks,
]
```

### 依赖方向
- `telemetry/` 可依赖: `config/`(日志级别), `exceptions.py`
- `telemetry/` 被依赖: **所有模块** — 通过 structlog logger 使用
- `telemetry/` 禁止依赖: `comms/`, `core/`, `flight/`, `safety/`

### 数据流
- 各模块 → `structlog.get_logger()` → 共享处理器链 → Console/JSON 输出
- `comms/` 遥测数据 → `FlightRecorder` → CSV 文件

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `configure_logging()` | structlog 全局配置函数 |
| `FlightRecorder` | 飞行数据 CSV 记录器 |

## 禁止模式

- **禁止**在 `src/striker/` 中使用 `print()` — 使用 structlog (R04)
- **禁止**在 `src/striker/` 中直接 `import logging` — 统一使用 structlog
- **禁止**在日志中泄露敏感信息（密钥、完整配置）
- **禁止**使用阻塞式文件 I/O 记录飞行数据 — CSV 写入必须是异步或缓冲批量写入
- **禁止**跳过 `TimeStamper` — 所有日志条目必须有 ISO 8601 UTC 时间戳
- **禁止**在日志处理器链中使用自定义 Renderer — 使用标准 ConsoleRenderer 或 JSONRenderer
