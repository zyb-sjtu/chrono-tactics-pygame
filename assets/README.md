# 演示资源来源与替换

默认 9 张 PNG 由 `scripts/generate_demo_assets.py` 使用 Pygame 几何图形生成；M5 增加 [dusk 外观](skins/dusk/README.md) 的 17 张 PNG，由 `scripts/generate_dusk_assets.py` 生成。没有下载或引用第三方美术，不代表最终风格。资源无第三方素材许可要求；项目整体授权仍由仓库所有者决定，本文件不另设开源许可证。

透视扩展另有 [war_torn 背景](skins/war_torn/README.md)：用户提供的原始 PNG，来源、真实尺寸与 SHA256 单独记录，不由上述生成脚本重建。角色暂用几何回退，背景作为必需资源通过 presentation 使用。

| 文件 | 原始 / 基准显示尺寸 | 锚点 | 用途 |
| --- | --- | --- | --- |
| tiles/floor.png | 64×64 / 64×64 | (0.5, 0.5)，格子中心 | 地砖 |
| units/scout_idle_0/1.png | 64×96 / 64×96 | (0.5, 1)，格子脚底中心 | 2 帧、2 fps 循环待机 |
| units/scout_attack_0/1/2.png | 64×96 / 64×96 | (0.5, 1) | 3 帧、8 fps 非循环攻击 |
| units/scout_death_0/1/2.png | 64×96 / 64×96 | (0.5, 1) | 3 帧、5 fps 非循环死亡 |

重建演示 PNG（会覆盖上述指定文件，不改清单）：

```powershell
.\.venv\Scripts\python.exe scripts/generate_demo_assets.py
```

替换美术时修改 `manifest.json` 的文件、显示尺寸、pivot、帧列表及状态映射即可；不改单位 cell、移动力或战斗代码。文件相对本目录，使用正斜杠且不得逃逸资源根；图片当前限 PNG。角色与特效建议 RGBA，人物可以高于一个格子，点击仍按格子计算。

缓存 Surface 按只读方式共享，渲染代码不得原地 fill、set_alpha 或改像素；临时效果请使用独立副本或预生成的帧，避免一次播放污染其他单位的缓存图片。

当前定义对应四个 visual_id，只有斥候配置了图片与动画；其他 visual 的空对象明确表示几何回退。所有演示图片 optional=true，删除图片仍可用几何模式运行；清单格式错误、无效引用或必需图片不可用会在启动时报错。`--geometry` 完全跳过资源清单和图片加载。

新引入的外部素材须在此记录作者、原始链接、许可证/授权范围、原始与显示尺寸、锚点和修改记录。详见 [资源规范](../docs/ASSET_GUIDE.md) 与 [M4 实施记录](../docs/M4_IMPLEMENTATION.md)。
