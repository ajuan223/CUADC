# 测试编码规范

本 Skill 约束 `tests/` 目录下的所有测试代码。适用于全项目所有模块的测试编写。

## 架构约束

- 测试框架: `pytest` + `pytest-asyncio`
- 异步测试使用 `async def test_()` + `@pytest.mark.asyncio` 装饰器
- 测试目录结构: `tests/unit/` (单元测试), `tests/integration/` (SITL 集成测试)
- 单元测试可使用 mock，集成测试必须连接真实 SITL 环境
- SITL fixture 在 `tests/integration/conftest.py` 中管理自动启停
- `conftest.py` 提供共享 fixture（如 mock MAVLink 连接、测试用 FieldProfile）
- 测试覆盖目标: 业务逻辑模块 ≥ 80% (KR3.2)

### 测试分层策略

| 层级 | 位置 | 运行条件 | 示例 |
|------|------|---------|------|
| 单元测试 | `tests/unit/` | 始终运行 | FSM 状态转换、配置加载、弹道解算 |
| 集成测试 | `tests/integration/` | 需要 SITL | 连接飞控、起飞、扫场循环 |
| KAT 测试 | `tests/unit/` | 始终运行 | 已知答案的弹道解算、坐标转换 |

### 异步测试模式
```python
@pytest.mark.asyncio
async def test_state_transition():
    fsm = MissionStateMachine(context)
    await fsm.activate_initial_state()
    await fsm.process_event(OverrideEvent())
    assert fsm.current_state_id == "override"
```

### Mock 边界
- `comms/` 层可 mock — 用 `AsyncMock` 替代真实 MAVLink 连接
- `config/` 层可 mock — 注入测试配置
- `safety/` 层可 mock — 注入模拟遥测数据
- `payload/` 弹道解算**禁止 mock** — 必须使用真实算法 + KAT 验证

## 注册模式

测试规范不向 REGISTRY.md 注册能力，但以下测试工具函数可注册：

| 注册项 | 说明 |
|--------|------|
| `make_mock_connection()` | 创建 mock MAVLink 连接 fixture |
| `make_test_field_profile()` | 创建测试用 FieldProfile fixture |

## 禁止模式

- **禁止**在单元测试中连接真实飞控或 SITL — 单元测试必须完全隔离
- **禁止**mock 弹道解算算法 — 必须使用真实算法 + 已知答案测试
- **禁止**跳过 `@pytest.mark.asyncio` — 异步测试必须正确标记
- **禁止**在测试中硬编码魔数 — 使用命名常量或 pytest.parametrize
- **禁止**忽略 `conftest.py` 中的共享 fixture — 重复的 fixture 设置应提取到 conftest
- **禁止**在集成测试中 mock 核心业务逻辑 — 集成测试验证真实交互
