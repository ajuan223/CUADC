# Striker 项目宪章 (Project Charter)

## 使命 (Mission)

Striker 是一套自主固定翼无人机飞行控制系统，专为精准空投任务设计。
系统从起飞到降落实现全自主闭环，在安全围栏约束下完成扫场侦察、目标锁定与载荷投放。

## OKR

### O1: 飞行安全零事故
- **KR1.1** 全任务生命周期内未捕获异常 (unhandled exception) 数量 = 0
- **KR1.2** Safety Monitor 协程存活率 = 100% (从 ARM 到 COMPLETED/OVERRIDE)
- **KR1.3** 人工 Override 从触发到系统响应延迟 < 500ms

### O2: 任务成功率可量化
- **KR2.1** SITL 全任务测试通过率 ≥ 95% (正常路径 + 降级路径)
- **KR2.2** 弹道解算已知答案测试 (KAT) 误差 < 0.1m
- **KR2.3** SCAN↔LOITER 超时重扫循环正确执行率 = 100%

### O3: 代码质量持续达标
- **KR3.1** `ruff check .` + `mypy src/ --strict` 零错误
- **KR3.2** 单元测试覆盖率 ≥ 80% (业务逻辑模块)
- **KR3.3** AGENTS.md 有效指令行数 < 100 行

### O4: 自主运行可靠性
- **KR4.1** 心跳丢失检测延迟 < 5s
- **KR4.2** 场地配置 (Field Profile) 校验失败时拒绝起飞率 = 100%
- **KR4.3** 强制投弹随机点 100% 落在围栏内且通过二次校验

## Red Lines (不可违反)

| ID | 约束 |
|----|------|
| RL-01 | **不自动 ARM** — ARM 操作必须有人工确认或预飞检查通过 |
| RL-02 | **Safety Monitor 不关闭** — 安全监控协程从启动到程序终止始终运行 |
| RL-03 | **Override 是终态** — 人工接管后系统不得自动恢复自主模式 |
| RL-04 | **pymavlink 不泄漏** — 仅 `src/striker/comms/` 可 import pymavlink |
| RL-05 | **GPS 必校验** — 所有 GPS 坐标必须通过 `validate_gps()` |
| RL-06 | **禁止硬编码** — 所有可变参数必须走配置系统 |
| RL-07 | **先调研后写码** — AI 新增/修改模块前必须先代码搜索调研 |
| RL-08 | **Field Profile 必校验** — 无有效场地配置不得起飞 |
| RL-09 | **Schema 必通过** — 围栏/跑道/航点必须通过 pydantic 校验 |
| RL-10 | **Forced-strike 围栏内校验** — 强制投弹坐标必须经 point_in_polygon 二次校验 |
