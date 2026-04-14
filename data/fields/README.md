# Field Profiles (场地配置)

每个场地配置是一个独立的目录，位于 `data/fields/<name>/` 下，包含一个 `field.json` 文件。

## 目录结构

```
data/fields/
├── README.md              ← 本文件
├── sitl_default/
│   └── field.json         ← SITL 仿真默认场地
└── <your-field>/
    └── field.json         ← 自定义场地
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
   - `scan_waypoints`: 扫场航点序列和飞行高度
   - `loiter_point`: 盘旋等待点坐标和半径
   - `safety_buffer_m`: 安全缓冲区距离 (米)

3. 在运行时通过配置选择场地：
   ```bash
   export STRIKER_FIELD=my-field
   ```
   或在 `config.json` 中设置 `"field": "my-field"`。

## 注意事项

- 所有坐标使用 **WGS84** 坐标系
- 围栏多边形必须闭合 (首尾相连)
- 降落航线航向必须与跑道方向一致
- 扫场航点必须在围栏内部
- 盘旋点 + 半径不得超出围栏边界
