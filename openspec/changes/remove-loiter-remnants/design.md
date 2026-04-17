## Context

当前运行时代码已经把 `SCAN` 完成后的标准路径改为“直接决策投弹点并进入转场”，不再执行 `scan -> loiter -> forced_strike`。但输入契约和周边工具仍保留 loiter 语义：

- `FieldProfile` 仍要求 `loiter_point`，并对其做围栏校验。
- field editor 仍把 `loiter_point` 视为默认字段、导入必填字段和导出字段。
- `data/fields/*.json`、`config.example.json`、`.env.example`、`docs/user_manual.md` 仍公开 loiter/rescan 术语。

这导致“运行逻辑已移除盘旋，但配置和文档仍要求盘旋存在”的双轨状态。

## Goals / Non-Goals

**Goals:**

- 从标准任务输入契约中移除 `loiter_point`。
- 让 field editor、场地样例、公开配置样例和文档与四阶段任务链保持一致。
- 保留底层飞控模式枚举中的 `LOITER`，避免误删与飞控兼容相关的基础能力。
- 通过测试更新验证新 schema 和工具链行为。

**Non-Goals:**

- 不重构当前 `ENROUTE` / `RELEASE` / `LANDING` 运行时实现。
- 不移除飞控底层 `ArduPlaneMode.LOITER` 枚举或 override detector 中对该模式的识别。
- 不处理历史 archived changes 或 archived specs 的历史内容。

## Decisions

### 1. 将 `loiter_point` 作为 breaking schema removal 处理

`loiter_point` 仍是 `FieldProfile` 和 field editor 的必填输入，这会持续把旧盘旋语义注入系统。最直接且一致的做法是把它从当前 schema 中彻底删除，而不是保留为“可选但不用”的死字段。

备选方案：
- 保留字段但忽略：拒绝。会让场地 JSON、编辑器 UI 和校验逻辑继续携带错误业务语义。
- 保留字段并重命名为其他含义：拒绝。当前四阶段流程没有对应的等待点语义，强行复用会制造新的歧义。

### 2. 只清理标准任务输入面，不碰底层飞控模式枚举

`LOITER` 在 ArduPlane 模式枚举、override 检测和 autonomy 状态识别中仍属于底层飞控事实，不等于业务状态机中的 loiter 分支。本 change 仅删除任务主链残余契约，不删除这些底层兼容项。

备选方案：
- 全仓库删除所有 `LOITER` 文本：拒绝。会误伤飞控协议层和安全检测语义。

### 3. field editor 与 field profile 一起收敛

如果只删后端 `FieldProfile.loiter_point`，field editor 会继续导出旧字段；如果只改 editor，运行时又仍要求旧字段。两者必须一起改，连同样例数据和测试一起收敛。

备选方案：
- 先改后端，之后再改 editor：拒绝。中间状态会让导入导出和测试全部不一致。

### 4. 旧公开配置参数按“失效配置接口”处理

`StrikerSettings` 已经不再声明 `loiter_timeout_s`、`max_scan_cycles`、`forced_strike_enabled`，但 `config.example.json` 和 `.env.example` 仍在公开它们。该 change 将把这些示例接口删掉，并把 spec 对齐为“标准任务配置不得暴露这些字段”。

## Risks / Trade-offs

- [Risk] 旧的 `field.json` 文件若仍包含 `loiter_point`，清理后可能需要同步更新样例与导入测试。
  → Mitigation: 同时更新 `data/fields/*/field.json`、field editor 测试和 field profile 单测夹具。

- [Risk] field editor 页面或脚本可能在仓库其他位置还引用 `loiter_point`。
  → Mitigation: 实施前后执行全仓库关键字检索，确认只在历史/OpenSpec 记录中保留必要痕迹。

- [Risk] 误删底层 `LOITER` 飞控兼容逻辑。
  → Mitigation: 仅删除小写 `loiter` 业务配置和输入面引用，保留 `flight/modes.py`、override detector、flight controller 中的模式识别。
