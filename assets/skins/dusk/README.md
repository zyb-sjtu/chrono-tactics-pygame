# dusk 演示外观

17 张 PNG 由项目的 `scripts/generate_dusk_assets.py` 使用 Pygame 几何图形生成，没有引用第三方美术，不代表最终风格。项目授权仍由仓库所有者决定。

| 内容 | 数量 | 原始/显示尺寸 | pivot |
| --- | --- | --- | --- |
| 地砖 | 1 | 64×64 | (0.5,0.5) |
| 障碍 | 1 | 64×80 | (0.5,1) |
| 斥候 idle / attack / death | 2 / 3 / 3 | 64×96 | (0.5,1) |
| 木桩 idle / attack / death | 1 / 3 / 3 | 64×96 | (0.5,1) |

斥候 idle 2fps 循环，木桩 idle 单张；双方 attack 8fps、death 5fps 非循环。所有图片 optional=true；先锋与卫士明确使用几何回退。大精灵按脚底排序，规则占格和点击仍是一格。

在项目根重建（只覆盖上述 17 个指定文件，不改 manifest）：

```powershell
.\.venv\Scripts\python.exe scripts/generate_dusk_assets.py
.\.venv\Scripts\python.exe main.py --scenario scenarios/river_crossing.json --assets assets/skins/dusk
```

资源根自包含，没有引用根外 PNG。缓存 Surface 只读，来源、锚点、回退和替换约束同 [资源规范](../../../docs/ASSET_GUIDE.md)。
