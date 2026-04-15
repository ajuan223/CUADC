## 1. 目录结构创建

- [x] 1.1 创建 `.agent/skills/` 下 11 个子目录：core-fsm-rules, comms-mavlink-rules, flight-control-rules, safety-monitor-rules, vision-interface-rules, payload-release-rules, config-system-rules, field-profile-rules, telemetry-rules, testing-rules, capability-registry

## 2. 能力注册中心

- [x] 2.1 创建 `.agent/skills/capability-registry/SKILL.md`，定义能力注册/查询规范（中文）
- [x] 2.2 创建 `.agent/skills/capability-registry/REGISTRY.md`，含表头 `| 函数名 | 描述 | 所在模块 | 签名 |` 的空表格

## 3. 核心模块 SKILL

- [x] 3.1 创建 `.agent/skills/core-fsm-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）
- [x] 3.2 创建 `.agent/skills/comms-mavlink-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）
- [x] 3.3 创建 `.agent/skills/safety-monitor-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）

## 4. 飞行与载荷 SKILL

- [x] 4.1 创建 `.agent/skills/flight-control-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）
- [x] 4.2 创建 `.agent/skills/payload-release-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）
- [x] 4.3 创建 `.agent/skills/vision-interface-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）

## 5. 基础设施 SKILL

- [x] 5.1 创建 `.agent/skills/config-system-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）
- [x] 5.2 创建 `.agent/skills/field-profile-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）
- [x] 5.3 创建 `.agent/skills/telemetry-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）
- [x] 5.4 创建 `.agent/skills/testing-rules/SKILL.md`（架构约束 + 注册模式 + 禁止模式，中文）

## 6. 集成验证

- [x] 6.1 确认 11 个 SKILL.md 文件均存在
- [x] 6.2 验证每个 SKILL.md 均包含"架构约束"、"注册模式"、"禁止模式"三个段落标题
- [x] 6.3 验证 REGISTRY.md 表头格式正确
- [x] 6.4 验证所有 SKILL.md 正文为中文内容
