# Field Profiles (场地配置)

每个场地配置是一个独立的目录，位于 `data/fields/<name>/` 下，包含一个 `field.json` 文件。

## 目录结构

```
data/fields/
├── README.md              ← 本文件
├── sitl_default/
│   ├── field.json         ← SITL 仿真默认场地
│   └── sitl_merged.param  ← 该场地的 SITL 行为层合并参数
└── <your-field>/
    ├── field.json         ← 自定义场地
    └── sitl_merged.param  ← 该场地的 SITL 行为层合并参数
```

## 创建新场地

1. 复制 `sitl_default` 目录：
   ```bash
   cp -r data/fields/sitl_default data/fields/my-field
   ```

2. 编辑 `data/fields/my-field/field.json`，修改以下内容：
   - `name`: 场地名称
   - `boundary.polygon`: 地理围栏多边形坐标 (WGS84, 顺时针闭合)
   - `landing`: 降落进近航点、着陆点、下滑道角度和航向
   - `scan`: 扫场高度、间距和航向
   - `attack_run`: 投弹进场距离、退出距离和航点接受半径
   - `safety_buffer_m`: 安全缓冲区距离 (米)

3. 为该场地提供 `data/fields/my-field/sitl_merged.param`：
   - 可以先复制任一已验证场地的 `sitl_merged.param` 作为起点
   - 仅覆盖任务行为层参数，不要把飞控硬件 / PID / 传感器参数整包带入 SITL

4. 在运行时通过配置选择场地：
   ```bash
   export STRIKER_FIELD=my-field
   ```
   或在 `config.json` 中设置 `"field": "my-field"`。

## 注意事项

- 所有坐标使用 **WGS84** 坐标系
- 围栏多边形必须闭合 (首尾相连)
- 每个需要用于 SITL 的场地目录都必须提供对应的 `sitl_merged.param`
- `sitl_merged.param` 只应包含行为层参数覆盖；SITL 动力学基线仍来自 `plane.parm`
- 降落航线航向必须与跑道方向一致
- 扫场航点必须在围栏内部
- 程序化推导出的降落进近点必须位于围栏内
