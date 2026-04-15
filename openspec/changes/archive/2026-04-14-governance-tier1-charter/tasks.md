## 1. CHARTER.md — 项目宪章

- [x] 1.1 创建 `CHARTER.md`，编写 Mission Statement（项目使命声明：Striker 自主固定翼无人机飞控系统，精准空投任务）
- [x] 1.2 定义 3+ 个 Objectives，每个含 2+ 可度量 Key Results（覆盖飞行安全、任务成功率、代码质量、自主运行可靠性）
- [x] 1.3 编写 10 条 Red Lines（RL-01 ~ RL-10），逐条对应 meta_development_plan.md 的关键约束提醒：不自动ARM / Safety Monitor 不关闭 / Override 终态 / pymavlink 不泄漏 / GPS 必校验 / 禁止硬编码 / 先调研后写码 / field profile 必校验 / schema 必通过 / forced-strike 围栏内校验
- [x] 1.4 验证 CHARTER.md 非空行数 ≤ 80

## 2. AGENTS.md — AI 宪法级编码规范

- [x] 2.1 创建 `AGENTS.md`，编写文件头部（用途说明、适用范围声明）
- [x] 2.2 编写命名约定规则 (R01)：snake_case modules, PascalCase classes, UPPER_SNAKE constants, snake_case.py files，含正反示例
- [x] 2.3 编写类型标注规则 (R02)：mypy --strict 强制，所有函数参数+返回值必须有类型注解
- [x] 2.4 编写 Import 顺序规则 (R03)：stdlib → third-party → local，空行分隔，ruff I-sort 强制
- [x] 2.5 编写日志规范规则 (R04)：structlog only，禁止 print() 和 stdlib logging（tests/ 目录 print 例外）
- [x] 2.6 编写严禁盲目落码规则 (R05)：新增/修改模块前必须先代码搜索调研
- [x] 2.7 编写能力发现优先规则 (R06)：实现通用函数前必查 REGISTRY.md
- [x] 2.8 编写包治理防腐墙规则 (R07)：pkg/ 变更必须 version bump + REGISTRY.md 同步，禁止 src↔pkg 和 pkg↔pkg 双向依赖
- [x] 2.9 编写 Skill 路由表 (R08)：紧凑 markdown 表格，覆盖 core/, comms/, flight/, safety/, vision/, payload/, config/, telemetry/, utils/ 共 9 个模块目录
- [x] 2.10 验证 AGENTS.md 有效指令行数 < 100（排除空行、注释行、水平分割线）

## 3. AGENTS.local.md — 个人覆盖模板

- [x] 3.1 创建 `AGENTS.local.md` 模板文件，头部注释说明覆盖语义（后出现规则覆盖先出现规则）
- [x] 3.2 注释中明确标注 Red Lines (RL-01~RL-10) 和安全规则不可被本地覆盖
- [x] 3.3 提供可覆盖项示例注释（如：line-length、indent-width 等风格偏好）

## 4. 集成验证

- [x] 4.1 确认 `.gitignore` 已包含 `AGENTS.local.md`（Phase 0 已配置，仅需验证）
- [x] 4.2 运行 `wc -l` 等工具验证 CHARTER.md ≤ 80 非空行
- [x] 4.3 运行自定义行数统计验证 AGENTS.md < 100 有效指令行
- [x] 4.4 确认 Skill 路由表中列出的 9 个模块目录名与 meta_development_plan.md Phase 2-7 的模块目录名一致
