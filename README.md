# 🛩️ Striker

**Striker** — 无人机搜查打击飞控自动飞行系统  
*Autonomous fixed-wing UAV search-and-strike flight control system*

Striker 是一个运行在机载计算机 (树莓派5 / NVIDIA Orin) 上的自动飞控软件，通过 MAVLink 协议与 CUAV X7 (ArduPlane 固件) 飞控进行高频通信，实现无人固定翼飞机的全自主搜查与打击任务。

## 系统要求

- **Python**: 3.13+
- **包管理器**: [uv](https://github.com/astral-sh/uv)
- **飞控**: CUAV X7 (ArduPlane 固件)
- **机载计算机**: 树莓派5 / NVIDIA Orin

## 快速开始

```bash
# 1. 安装 uv (如尚未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 同步依赖
uv sync

# 3. 验证安装
uv run python -m striker

# 4. 运行测试
uv run pytest

# 5. 代码检查
uv run ruff check .
uv run mypy src/ --strict
```

## 项目结构

```
├── src/striker/          # 主源代码包
│   ├── __init__.py       # 版本号
│   ├── __main__.py       # 入口点
│   ├── exceptions.py     # 全局异常层次
│   └── py.typed          # PEP 561 类型标记
├── tests/                # 测试套件
├── pkg/                  # UV 工作区隔离包
├── data/fields/          # 场地配置
├── runtime_data/         # 运行时数据 (gitignored)
├── scripts/              # 自动化脚本
├── docs/                 # 文档
├── pyproject.toml        # 项目配置
└── uv.lock               # 依赖锁文件
```

## 开发阶段

## 许可证

私有项目，保留所有权利。
