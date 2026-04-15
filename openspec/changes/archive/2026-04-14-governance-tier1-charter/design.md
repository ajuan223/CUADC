## Context

Phase 0 交付了完整的项目骨架 (`src/striker/`, `tests/`, `pkg/`, `data/fields/` 等)，工具链 (ruff/mypy/pytest) 已就绪。
当前缺失的是 **AI Agent 行为约束层**：没有任何文件告诉 AI "什么能做、什么不能做、怎么写代码"。

项目采用 **三层渐进式治理架构 (Progressive Disclosure)**：

| 层级 | 文件 | 加载时机 | 指令预算 |
|------|------|---------|---------|
| L0 宪章 | `CHARTER.md` | 始终 (项目根目录) | ~50 行 |
| L1 宪法 | `AGENTS.md` | 始终 (项目根目录) | **<100 行** |
| L2 模块技能 | `.agent/skills/{module}-rules/SKILL.md` | 仅触及对应 `src/striker/{module}/` 时 | 无限制 |

本 Change 仅产出 **L0 + L1**，L2 由后续 `governance-tier2-skills` 覆盖。

### 现有约束

- `.gitignore` **已包含** `AGENTS.local.md` 条目 (Phase 0 已配置)
- `src/striker/` 下当前模块：`__init__.py`, `__main__.py`, `exceptions.py`, `py.typed` — 后续将扩展到 `config/`, `comms/`, `core/`, `flight/`, `safety/`, `vision/`, `payload/`, `telemetry/`, `utils/`

## Goals / Non-Goals

**Goals:**
- 产出 `CHARTER.md`：定义项目使命、OKR、10 条 Red Lines（不可违反的安全/工程约束）
- 产出 `AGENTS.md`：<100 行有效指令的 AI 宪法，覆盖命名、类型、日志、Import、Skill 路由表、严禁盲目落码、能力发现优先、包治理防腐墙
- 产出 `AGENTS.local.md`：gitignored 个人覆盖模板，提供覆盖机制但不含实际内容
- 验证 AGENTS.md 有效指令行数 < 100

**Non-Goals:**
- 不创建 L2 模块 Skills (`.agent/skills/{module}-rules/`) — 由 `governance-tier2-skills` 处理
- 不修改任何 Python 源码
- 不修改 CI 配置 — Phase 8 再引入合规检查
- 不定义信号通信协议 / 状态机规范的模块级细节 — 那是各模块 Skill 的职责

## Decisions

### D1: CHARTER.md 结构 — OKR + Red Lines 合一 vs 分离

**选择**: 合一到单文件 `CHARTER.md`

**理由**: 项目宪章是高层文档，OKR 与 Red Lines 天然紧密耦合。分离为两个文件会增加 AI 需要加载的文件数量，背离"最小指令预算"原则。

**替代方案**: 将 Red Lines 放入 AGENTS.md — 否决，因为 AGENTS.md 已有 <100 行预算压力，且 Red Lines 的受众不只是 AI（人类开发者也需要查阅）。

### D2: AGENTS.md 行数上限策略

**选择**: 严格 <100 行有效指令（空行、注释不计），使用紧凑的规则编号格式

**理由**: meta_development_plan.md 明确要求 <100 行。这是防止 AI 指令预算溢出导致行为降智的核心机制。所有模块级细节必须下沉到 L2 Skill。

**格式约定**:
- 使用 `R01`, `R02` 等编号标识每条规则，便于 Skill 中引用
- 每条规则不超过 2 行描述
- Skill 路由表使用紧凑表格格式

### D3: Skill 路由表设计 — 静态表 vs 动态发现

**选择**: 静态路由表，硬编码在 AGENTS.md 中

**理由**: Skill 路由关系在项目生命周期内相对稳定 (模块目录结构很少变化)。动态发现增加复杂度但收益极低。路由表格式：

```
| 目录模式 | Skill |
|---------|-------|
| src/striker/core/ | core-fsm-rules |
| src/striker/comms/ | comms-mavlink-rules |
| ... | ... |
```

**替代方案**: 用 glob 匹配自动发现 — 否决，AI 工具目前不支持 Skill 自动路由。

### D4: AGENTS.local.md 覆盖机制

**选择**: 提供空模板文件，头部注释说明覆盖语义 (后出现的规则覆盖先出现的规则)。内容由开发者自行填写。

**理由**: 不同开发者可能对缩进宽度、编辑器插件等有个人偏好。但核心安全规则 (Red Lines) 不可被本地覆盖。

### D5: 文件放置位置

**选择**:
- `CHARTER.md` → 项目根目录 (`/`)
- `AGENTS.md` → 项目根目录 (`/`)
- `AGENTS.local.md` → 项目根目录 (`/`)

**理由**: 根目录放置确保 AI Agent 启动时即刻发现这些治理文件，无需额外配置路径。这遵循 Gemini/Cursor/Copilot 等主流 AI Agent 的约定。

## Risks / Trade-offs

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| AGENTS.md <100 行限制导致规则遗漏 | 中 | 低 | L2 Skill 兜底补充模块级细节；优先收录最高频生效的规则 |
| AI Agent 不遵守 AGENTS.md 规则 | 中 | 中 | CI lint + mypy --strict 双重兜底；Phase 8 添加自动合规检查脚本 |
| Skill 路由表与实际目录不同步 | 低 | 低 | 每次新增模块目录时需同步更新 AGENTS.md 路由表；未来 CI 可检查一致性 |
| CHARTER.md 过于冗长无人阅读 | 低 | 低 | 控制在 1-2 页以内，使用结构化格式 (OKR 表格 + 编号 Red Lines) |
