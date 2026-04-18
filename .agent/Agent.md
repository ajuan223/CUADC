# Agent.md — Skill 路由表

本文件是 `.agent/skills/` 的索引。按模块分类，供 Agent 快速定位适用的编码约束。

## 后端模块 (src/striker/)

| Skill | 目录 | 说明 |
|-------|------|------|
| `capability-registry` | `.agent/skills/capability-registry/` | 能力注册表规范，所有模块必须注册可复用函数 |
| `config-system-rules` | `.agent/skills/config-system-rules/` | 配置系统，`src/striker/config/` |
| `comms-mavlink-rules` | `.agent/skills/comms-mavlink-rules/` | MAVLink 通信层，`src/striker/comms/` |
| `core-fsm-rules` | `.agent/skills/core-fsm-rules/` | 状态机引擎 + 事件系统，`src/striker/core/` |
| `flight-control-rules` | `.agent/skills/flight-control-rules/` | 飞控指令封装，`src/striker/flight/` |
| `safety-monitor-rules` | `.agent/skills/safety-monitor-rules/` | 安全监控（围栏/电量/GPS/心跳），`src/striker/safety/` |
| `telemetry-rules` | `.agent/skills/telemetry-rules/` | 遥测日志，`src/striker/telemetry/` |
| `payload-release-rules` | `.agent/skills/payload-release-rules/` | 投弹释放机构，`src/striker/payload/` |
| `vision-interface-rules` | `.agent/skills/vision-interface-rules/` | 外部视觉系统接口，`src/striker/vision/` |
| `utils-rules` | `.agent/skills/utils-rules/` | 纯工具函数，`src/striker/utils/` |
| `field-profile-rules` | `.agent/skills/field-profile-rules/` | 场地配置数据模型 + 校验，`src/striker/config/field_profile.py` + `data/fields/` |

## Web 前端

| Skill | 目录 | 说明 |
|-------|------|------|
| `field-editor-rules` | `.agent/skills/field-editor-rules/` | AMap 地图编辑器，`src/field_editor/`，**GCJ-02/WGS84 转换红线** |

## SITL 仿真

| Skill | 目录 | 说明 |
|-------|------|------|
| `sitl-autodebug-loop` | `.agent/skills/sitl-autodebug-loop/` | SITL 自动调试循环，反复起飞→扫描→投弹→降落直到全链路通过 |
| `sitl-fullchain-rules` | `.agent/skills/sitl-fullchain-rules/` | SITL 全链路集成测试启动流程、端口映射、故障排查 |
| `sitl-param-merge-rules` | `.agent/skills/sitl-param-merge-rules/` | SITL 参数合并规则，不覆盖动力学/PID/传感器参数 |

## OpenSpec 工作流

| Skill | 目录 | 说明 |
|-------|------|------|
| `openspec-new-change` | `.agent/skills/openspec-new-change/` | 新建变更 |
| `openspec-continue-change` | `.agent/skills/openspec-continue-change/` | 推进变更到下一阶段 |
| `openspec-ff-change` | `.agent/skills/openspec-ff-change/` | 快速推进，一次性生成所有 artifact |
| `openspec-apply-change` | `.agent/skills/openspec-apply-change/` | 实施变更 |
| `openspec-propose` | `.agent/skills/openspec-propose/` | 一步生成完整提案 |
| `openspec-explore` | `.agent/skills/openspec-explore/` | 探索模式，头脑风暴 |
| `openspec-archive-change` | `.agent/skills/openspec-archive-change/` | 归档已完成的变更 |
| `openspec-bulk-archive-change` | `.agent/skills/openspec-bulk-archive-change/` | 批量归档 |

## 通用

| Skill | 目录 | 说明 |
|-------|------|------|
| `testing-rules` | `.agent/skills/testing-rules/` | 测试代码规范，`tests/` |
