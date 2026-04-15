# 能力注册中心规范

本 Skill 定义 Striker 项目能力注册中心的使用规范。所有模块实现可复用通用函数后，必须向 `REGISTRY.md` 注册。

## 架构约束

- 能力注册中心位于 `.agent/skills/capability-registry/REGISTRY.md`
- 它是项目范围内**唯一**的能力清单，用于防止重复造轮子 (AGENTS.md R06)
- 注册中心由各模块在实现时主动填充，**非**自动生成
- AI Agent 实现新函数前，必须先扫描 REGISTRY.md 确认无等效能力

## 注册模式

### 何时注册
- 实现了可被其他模块复用的通用函数（如坐标转换、数据校验、格式化工具）
- 实现了某个 Protocol/ABC 的具体实现（如 VisionReceiver 的 TCP/UDP 实现）

### 注册格式
在 REGISTRY.md 表格中追加一行：

```markdown
| validate_gps | 校验 GPS 坐标是否在合理范围内 | src/striker/safety/ | validate_gps(lat: float, lon: float) -> bool |
```

### 字段说明
- **函数名**: Python 函数名或类名
- **描述**: 一句话功能描述
- **所在模块**: 相对路径，格式 `src/striker/{module}/`
- **签名**: 完整函数/方法签名

## 禁止模式

- **禁止**实现新通用函数前不查 REGISTRY.md — 先检索，后编码 (AGENTS.md R06)
- **禁止**在 REGISTRY.md 中注册模块内部私有函数（`_` 前缀的函数）
- **禁止**注册信息与实际代码不一致 — 函数签名变更时必须同步更新 REGISTRY.md
- **禁止**将 REGISTRY.md 用作模块间通信机制 — 它只是发现工具，不是调用入口
