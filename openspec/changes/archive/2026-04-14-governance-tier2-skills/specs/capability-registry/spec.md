## ADDED Requirements

### Requirement: REGISTRY.md 初始结构
REGISTRY.md SHALL 以 Markdown 表格形式组织，初始包含表头但无数据行。表头列为：函数名、描述、所在模块、签名。

#### Scenario: 初始 REGISTRY.md 格式
- **WHEN** 首次创建 REGISTRY.md
- **THEN** 文件 MUST 包含表头行 `| 函数名 | 描述 | 所在模块 | 签名 |` 以及分隔行，但无数据行

#### Scenario: 后续注册格式
- **WHEN** 某模块实现了一个通用函数并向 REGISTRY.md 注册
- **THEN** MUST 在表格中追加一行，包含函数名、功能描述、`src/striker/{module}/` 路径、函数签名

### Requirement: 能力注册 SKILL.md
`.agent/skills/capability-registry/SKILL.md` SHALL 定义能力注册的操作规范，包含注册时机、注册格式、查询流程。

#### Scenario: 注册时机
- **WHEN** 开发者或 AI Agent 在任一模块中实现了可复用的通用函数
- **THEN** MUST 按照 SKILL.md 中定义的格式向 REGISTRY.md 注册该能力

#### Scenario: 查询流程
- **WHEN** AI Agent 开始实现一个新的函数
- **THEN** MUST 先扫描 REGISTRY.md 中的已有条目，确认无等效能力后再编写新代码
