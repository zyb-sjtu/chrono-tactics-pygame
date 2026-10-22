# 战后荒原背景资源

- 来源：用户本机提供的 `硝烟暮色中的荒废战场棋盘.png`，位于 `D:/download from edge/`；用户同时提供了透视战场设计稿。
- 接入文件：`backgrounds/battlefield.png`，PNG，真实尺寸 1672×941，2,265,886 字节。原样复制，没有重绘、裁切或改写图片内容。
- 原图与接入文件 SHA256 均为 `f3ae6033599a5cc9047a8509c3d3f2269e3604513aa29cb0ec7e4db1051f5d2a`。
- 未随图提供独立作者、来源链接或许可文本；来源记录为用户提供，项目原有授权约定继续适用。
- 清单将背景声明为必需资源，`display_size=[1672,941]`、`pivot=[0,0]`。透视渲染器核对真实解码尺寸，启动时按 contain 统一缩放并缓存，缺失/损坏拒绝启动。

目前没有提供新角色 PNG，因此四个 visual 明确使用临时几何回退。引入正式角色时，在本资源根增加 PNG/帧与状态映射即可；实际深度缓存、pivot、Clip、攻击/死亡与回溯链路已使用 dusk 测试素材通过集成验证，不需要把角色路径写入规则。

使用入口：

```powershell
.\.venv\Scripts\python.exe main.py --presentation presentations/war_torn_8x8.json
.\.venv\Scripts\python.exe main.py --presentation presentations/war_torn_8x8.json --debug-grid
```

不是平铺地砖资源包。背景外的场景/四角/HUD 在 presentation JSON 中维护，阵容/障碍在独立场景 JSON 中维护。具体坐标与校准边界见 [透视场景实施记录](../../../docs/PERSPECTIVE_BATTLEFIELD.md)。
