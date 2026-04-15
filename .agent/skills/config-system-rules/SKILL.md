# 配置系统编码规范

本 Skill 约束 `src/striker/config/` 目录下的所有代码。配置系统是 Striker 所有模块的共享基础设施。

## 架构约束

- 配置采用三层优先级: **代码默认 < config.json < 环境变量**（后者覆盖前者）
- 所有配置模型必须继承 `pydantic-settings` 的 `BaseSettings`
- 三层优先级通过 `settings_customise_sources()` 显式保证加载顺序
- 环境变量前缀: `STRIKER_`（如 `STRIKER_SERIAL_PORT`, `STRIKER_DRY_RUN`）
- 敏感信息（密钥、密码）**必须**通过环境变量注入，禁止硬编码或写入 config.json
- `detect_platform()` 返回枚举值: `RPi5` / `Orin` / `SITL` / `Unknown`
- 配置校验器使用 pydantic validator，确保物理量在合理范围内（如 baud rate > 0）

### pydantic-settings 集成要点
```python
class StrikerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STRIKER_",
        json_file="config.json",
        json_file_encoding="utf-8",
    )
    # 所有字段都有代码内默认值
    serial_port: str = "/dev/serial0"
    ...
```

### 依赖方向
- `config/` 可依赖: `exceptions.py`, pydantic-settings, pydantic
- `config/` 被依赖: **所有模块** — config 是最底层的共享基础设施
- `config/` 禁止依赖: 任何 `src/striker/` 下的其他业务模块

### 数据流
- config.json + 环境变量 → `StrikerSettings` 单例 → 各模块通过依赖注入获取

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `StrikerSettings` | 全局配置模型 |
| `detect_platform()` | 平台检测函数 |

## 禁止模式

- **禁止**在 config.json 中存储敏感信息 — 密钥必须走环境变量
- **禁止**跳过 pydantic 校验直接读取 JSON — 所有配置必须经过 BaseSettings 校验
- **禁止**业务模块直接读取环境变量 — 必须通过 `StrikerSettings` 统一管理
- **禁止**修改 `settings_customise_sources()` 的优先级顺序 — 三层顺序是架构约束
- **禁止**在配置模型中硬编码连接参数默认值以外的可变参数 — 所有可变参数必须可配置
