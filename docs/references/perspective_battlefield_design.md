# Chrono Tactics：透视战场背景与棋盘接入设计报告

-   用途：交付 Codex 的实施规格与验收清单
-   项目：`zyb-sjtu/chrono-tactics-pygame`
-   目标：将用户提供的古代战后战场背景接入为可交互的 8×8
    透视战棋场景，同时保持现有战斗规则、回溯和旧场景兼容
-   建议分支：`feature/perspective-battlefield`

## 0. 给 Codex 的执行指令

先检查当前工作树、`git status`、`AGENTS.md`、README、架构文档和测试命令。以实际代码为准，不假设文档和代码完全一致。不得覆盖用户未提交修改，不得删除或放宽旧测试，不得执行破坏性
Git 操作。

按本报告分阶段实施。先确认用户提供的原始背景 PNG
是否能从工作树或附件挂载目录读取；若不可访问，明确报告并请求文件，不得生成相似图片冒充原图。每阶段先实现、测试、汇报，再继续。最终必须提供实际修改文件、测试命令和真实结果、真实窗口截图（如果环境允许）以及尚未完成事项。本文是设计规范，不代表功能已经实现。

## 1. 目标和边界

### 目标

1.  将原图作为一张完整背景绘制，不重复平铺地砖。
2.  在原图可辨认的石砖区域上校准 8×8 逻辑棋盘。
3.  将逻辑格子投影为透视四边形，支持屏幕坐标和逻辑格坐标双向转换。
4.  复用当前单位规则、移动/攻击范围、行动顺序、胜负判定和回溯。
5.  复用现有 PNG、Sprite pivot、Clip 动画和 AssetManager 缓存。
6.  新增叠加式 HUD；旧矩形棋盘和旧右侧面板保持可用。
7.  提供调试网格、角点、中心点和行列编号，便于人工校准。
8.  新增独立场景和资源包，不修改原训练场与渡口场景。

### 本阶段不做

-   不重写战斗规则，不新增 AI、技能、存档、联网或地图编辑器。
-   不做随机地形、地面破坏、镜头移动或自动识别碎石障碍。
-   不要求第一版为每块砖单独制作图片。
-   不新增 NumPy/OpenCV 等依赖。
-   不把屏幕像素、透视矩阵或资源路径写进
    Unit、Board、规则快照或战斗判定。

### 核心决策

**固定背景 + 透视逻辑网格 + 独立角色资源 + 叠加式 HUD。**
背景负责环境纹理和砖缝；几何模块负责坐标映射；规则层只处理整数格坐标；资源层负责图片与动画；渲染层负责画面。

## 2. 当前项目基线与改造原则

根据已检查到的源码：

  --------------------------------------------------------------------------------------------------------------------
  文件                                           当前职责                           本次原则
  ---------------------------------------------- ---------------------------------- ----------------------------------
  `tactics/game.py`                              窗口、事件、主循环和渲染调度       增加新模式选择，旧模式保持

  `tactics/geometry.py`                          `BoardGeometry` 矩形格子映射       保留，新增透视几何类

  `tactics/board_renderer.py`                    矩形格子、范围、单位和血条绘制     保留旧渲染路径；新增透视渲染路径

  `tactics/assets.py`                            PNG、缩放缓存、Sprite pivot、Clip  复用并只做必要扩展

  `tactics/asset_manifest.py`                    严格校验图片、动画、视觉绑定和     扩展背景字段，旧清单继续兼容
                                                 `board.floor/obstacle`

  `tactics/effects.py`                           伤害数字、死亡表现和动画结算通知   检查并适配透视坐标

  `tactics/view_models.py`                       不可变 `BoardView` / `BattleView`  继续只读，不引入像素状态

  `tactics/controller.py`                        规则指令、玩家输入协调             继续只接收逻辑格坐标

  `tactics/panel.py`                             固定宽度右侧栏和按钮               旧模式保留；新建场景 HUD

  `tactics/content.py` / `tactics/scenario.py`   JSON 规则内容和场景合法性校验      与视觉配置分离

  `content/scenarios/training_ground.json`       8×8、双方各三个单位                作为回归基线，不修改

  `content/scenarios/river_crossing.json`        6×5 第二场景                       作为回归基线，不修改

  `assets/manifest.json`、`assets/skins/dusk/`   现有资源包                         保持兼容
  --------------------------------------------------------------------------------------------------------------------

旧 `BoardGeometry` 假设每格是固定大小矩形；旧 `BoardRenderer`
会逐格绘制矩形并可平铺 `board.floor`；`Game` 默认窗口由棋盘区域和 384px
侧栏构成；`effects.py` 部分定位依赖
`cell_rect()`。这些逻辑不能直接承担完整透视背景，不能只换一张 PNG
就算接入完成。

## 3. 目录与资源组织

推荐新增以下内容；如果仓库已有等价模块，优先复用，避免重复实现。

``` text
assets/skins/war_torn/
  manifest.json
  README.md
  backgrounds/
    battlefield.png       # 用户提供的原始背景，不改图像内容

content/scenarios/
  war_torn.json            # 新的 8×8 规则场景

presentations/
  war_torn_8x8.json        # 背景、透视角点、HUD、调试配置

tactics/
  perspective_geometry.py
  presentation_layout.py
  perspective_board_renderer.py
  scene_hud.py
  # geometry.py、board_renderer.py、assets.py、effects.py、game.py 按需修改

tests/
  test_perspective_geometry.py
  test_presentation_layout.py
  test_perspective_rendering.py
  # 保留现有测试
```

### 背景接入

-   先确认原始 PNG 可读，读取实际宽高、格式；对话预览约为
    1672×941，但必须以实际文件为准。
-   可读取时，复制到
    `assets/skins/war_torn/backgrounds/battlefield.png`，记录资源来源和许可信息。
-   不可读取时停止背景接入步骤并报告，不得使用生成的替代图。
-   背景是必需资源；缺失或解码失败时启动阶段给出清晰错误。
-   角色美术未提供时可暂用现有几何回退验证交互，但最终报告必须标记为临时回退。

## 4. 视觉规范

### 视口与背景

-   初始设计视口 1280×720，接近原图 16:9。
-   读取真实图像尺寸，等比例缩放并保持完整构图，不拉伸、不随意裁切。
-   新模式背景占据完整游戏视口，不再为右侧 384px 固定面板预留棋盘空间。
-   背景、棋盘、角色、特效和鼠标映射共用同一套缩放和平移参数。
-   首版不要求动态镜头；如果支持窗口 resize，必须统一重建几何缓存。

### 棋盘与地块

-   逻辑棋盘首版为 8 列×8 行。
-   每格是逻辑单元，屏幕表现是四边形，不是 64×64 像素矩形。
-   选择原图中可辨认的地砖区域，标记四个外角后投影内部网格。
-   逻辑行列方向必须根据实际砖缝校准，不可假设列轴水平、行轴垂直。
-   默认不画粗重的完整网格线；使用原图已有砖缝。
-   移动范围：低饱和灰青色半透明填充；攻击范围：暗红色半透明填充；目标格：细亮边框；当前行动者：金色边框；选中单位：浅色圆环。
-   调试模式显示四角、所有格线、中心点和 `(col,row)` 编号。
-   背景中的旗帜、碎石、裂缝等装饰不自动成为障碍。障碍只由场景 JSON
    明确指定。

### 角色与深度

-   角色 PNG 使用 Alpha 通道；默认脚底中心 pivot `(0.5, 1.0)`。
-   角色的逻辑占格不因图片尺寸改变。
-   脚底锚点放在投影格子的站立点/近侧边中点；不要用精灵左上角定位。
-   近远缩放首版可依据棋盘行方向插值，但不得修改逻辑坐标。
-   单位和障碍按屏幕空间脚底 Y 坐标排序，稳定 UID 作为次序键。
-   单位本体绘制完后，再绘制选中框和血条，避免被相邻大精灵遮住。
-   HUD 最后绘制。

### HUD

新增 `SceneHUD`，不要将新布局塞进旧 `InfoPanel`
的大量条件分支。保留回合数、当前行动者、选中单位属性、回溯、跳过阶段、结束行动、近期日志和行动顺序。建议将紧凑半透明状态卡放在左上方较暗区域，按钮与状态卡组合布置；最终位置必须结合实际背景窗口检查，避免遮挡棋盘中央、两杆军旗和角色。

HUD 的 `hit_test()` 只返回现有 `UIAction`，仍由 Controller
判定是否合法；HUD 不得直接修改单位或回溯历史。

## 5. 透视几何设计

### 接口

新增 `PerspectiveBoardGeometry`，保留原 `BoardGeometry` 行为。至少提供：

``` python
cell_polygon(cell)  # 屏幕上的四个顶点
cell_center(cell)   # 格子屏幕中心
cell_anchor(cell)   # 角色脚底/站立点
cell_at(screen_pos) # 鼠标像素转逻辑格；棋盘外返回 None
depth_at(cell)      # 用于绘制排序的屏幕深度
```

Controller、Board、Unit 和 ViewModel 仍只处理 `(col,row)`。

### 单应性变换

使用平面单应性（Homography）将逻辑矩形映射到背景透视四边形。配置角点按逻辑顺序定义：

-   `p00`：逻辑外角 `(0,0)`
-   `p10`：逻辑外角 `(cols,0)`
-   `p11`：逻辑外角 `(cols,rows)`
-   `p01`：逻辑外角 `(0,rows)`

注意 `cols`、`rows`
是外边界坐标，不是最后一个格子的索引。四角在屏幕上可以倾斜，行列方向应沿实际地砖纹理。

对每个格子，投影
`(col,row)`、`(col+1,row)`、`(col+1,row+1)`、`(col,row+1)`
四点。初始化时计算并缓存矩阵 `H` 和逆矩阵
`H⁻¹`，只在角点或视口变化时重建。不得每帧求解矩阵。

### 鼠标反向映射

1.  屏幕坐标先逆转背景缩放和平移，转换为原图参考坐标。
2.  用 `H⁻¹` 转成连续逻辑坐标 `(u,v)`。
3.  检查变换分母、有限数和范围。
4.  若 `0 <= u < cols` 且 `0 <= v < rows`，返回
    `(floor(u), floor(v))`，否则返回 `None`。
5.  使用明确的半开区间规则处理共享边界，避免同一像素随机命中不同格。

### 数值与依赖

-   不新增 NumPy/OpenCV 依赖；优先用纯 Python 计算四点映射和 3×3
    逆矩阵。
-   拒绝重复、共线、退化角点，给出具体配置错误。
-   防止除零、非有限坐标和不可逆矩阵。
-   角点数据必须通过实际原图校准，不可猜测后写成正式值。
-   若单一 Homography
    对画作中的砖缝拟合不够好，先调整棋盘范围和四角；确实无法满足视觉要求时，把逐行/逐列校准作为后续扩展，不要首版直接开发复杂编辑器。

### 缩放一致性

角点保存在原图参考坐标系。背景按等比例缩放至视口并记录实际缩放率和偏移；网格投影与鼠标输入必须使用同一变换。背景留边不能被映射为棋盘格。

## 6. Presentation 配置和资源接口

规则、资源和视觉布局分开： -
`content/scenarios/war_torn.json`：行列、单位阵容、逻辑坐标、障碍。 -
`assets/skins/war_torn/manifest.json`：图片、动画、视觉绑定、资源路径、显示尺寸和
pivot。 -
`presentations/war_torn_8x8.json`：背景模式、角点、参考视口、HUD、调试开关。

建议 presentation 至少包含
`schema_version`、`id`、`mode`、`scenario_file`、`asset_root`、`viewport.reference_size`、`viewport.background_fit`、`board.cols/rows/reference_image_size/corners`、`hud`
和 `debug`。字段名可按项目风格调整，但 schema 必须严格校验。

配置示意（角点是占位值，不能用于正式运行）：

``` json
{
  "schema_version": 1,
  "id": "war_torn_8x8",
  "mode": "perspective",
  "scenario_file": "scenarios/war_torn.json",
  "asset_root": "assets/skins/war_torn",
  "viewport": {
    "reference_size": [1280, 720],
    "background_fit": "contain"
  },
  "board": {
    "cols": 8,
    "rows": 8,
    "reference_image_size": [0, 0],
    "corners": {
      "p00": [0, 0],
      "p10": [0, 0],
      "p11": [0, 0],
      "p01": [0, 0]
    }
  },
  "hud": {"layout": "overlay", "safe_margin": 24},
  "debug": {
    "show_grid": false,
    "show_cell_centers": false,
    "show_coordinates": false
  }
}
```

占位角点为零时，正式运行必须明确报错或进入校准模式，不得静默显示错误棋盘。

复用现有 `data_files.py` 的 `read_json()`、`fields()`、`rooted_path()`
等严格校验工具。路径必须是相对路径并解析在允许的资源根目录内。背景资源必需；旧
`board.floor` / `board.obstacle` 配置仍然有效。背景不能被缩放成 64×64
地砖。CLI 显式参数、presentation 配置和默认值的优先级必须明确并测试。

## 7. 渲染管线与模块职责

### 绘制顺序

1.  清屏；
2.  完整背景；
3.  调试网格（仅开启时）；
4.  移动/攻击/目标格高亮；
5.  地面阴影；
6.  障碍和角色，按屏幕脚底 Y + 稳定 UID 排序；
7.  当前行动者/选中标记、血条和标签；
8.  攻击、死亡、伤害数字等战斗特效；
9.  场景 HUD；
10. `pygame.display.flip()`。

### 渲染器隔离

首选新增 `PerspectiveBoardRenderer`： - 旧 `BoardRenderer`
继续服务矩形模式； - 新渲染器绘制完整背景和透视四边形； - 两者都接收只读
`BoardView`，不查询或修改 Battle； - 通过 `Game`
选择渲染器，避免在旧渲染器中堆积大量模式分支； - 复用 AssetManager
的图片、Sprite、Clip 与缓存。

高亮使用 `pygame.draw.polygon()` 或透明 Surface，不能用轴对齐
`pygame.Rect` 替代。调试网格与正式高亮分别控制。

### 特效适配

检查 `tactics/effects.py` 对 `cell_rect()`、`cell_center()` 和
`geometry.bounds` 的使用： - 伤害数字锚定目标格中心/站立点上方； -
攻击动画锚定攻击者脚底； - 死亡表现锚定目标格中心/脚底； -
裁剪使用当前视口或投影区域； - 如需按远近调整粒子尺寸，增加
`cell_scale(cell)` 等明确接口； - 保持当前 resolution token / generation
协议、输入锁定和回溯代次清理； - 像素坐标和动画时钟不进入战斗快照。

## 8. 新场景与 CLI

新增 `content/scenarios/war_torn.json`，使用
8×8、双方各三个单位，优先复用现有 `vanguard`、`scout`、`guard`、`dummy`
定义。红方木桩仍按当前规则由玩家手动操作，不增加
AI。少量障碍只放在明确的格子上，中央保留通路。坐标必须在角点校准后确定，不要预先声称固定坐标一定对应某块砖。

建议增加入口：

``` powershell
python main.py --presentation presentations/war_torn_8x8.json
python main.py --presentation presentations/war_torn_8x8.json --debug-grid
```

具体参数名可按现有 CLI 调整，但需更新 README。无 `--presentation`
时旧默认行为不变。以下旧用法必须继续可用：

``` powershell
python main.py
python main.py --geometry
python main.py --scenario scenarios/river_crossing.json
python main.py --scenario scenarios/river_crossing.json --geometry
python main.py --scenario scenarios/river_crossing.json --assets assets/skins/dusk
```

明确 `--presentation` 与 `--scenario`、`--assets`、`--content-root`
同时出现时的优先级。`--geometry`
与透视模式的组合也必须有明确行为并通过测试，不得静默切换到意外配置。

## 9. 分阶段实施计划

### A. 检查与资源确认

检查工作树、规范、测试；确认原图可访问并读取真实尺寸；列出预计修改文件。缺图时停止资源接入。

### B. 资源和配置

新增战场资源包、背景 manifest 字段和 presentation
解析；严格检查角点、行列、资源引用和路径。旧清单必须继续加载。

### C. 透视几何

实现正向/反向映射、四边形、中心、锚点和深度；加入 debug
grid。完成边界和缩放测试。

### D. 透视渲染

绘制背景、高亮、角色和障碍；复用资源缓存；旧渲染器保持不变。完成后先做真实窗口校准。

### E. 输入、HUD、特效

接入反向点击映射和 HUD；适配攻击/死亡/伤害文字；保持
token、输入锁定和回溯语义。

### F. 场景校准

角点贴合地砖；确认行列方向；配置双方阵容与障碍；关闭 debug
后检查角色大小、深度和 UI。

### G. 回归和文档

运行完整测试，启动真实窗口，更新
README、资源规范和架构文档。报告中区分自动化验证和人工视觉检查。

每个阶段先运行对应测试，不要一次性大规模重构。

## 10. 自动化测试与验收

### 几何测试

-   四角映射正确；
-   64 个格子中心反向映射回原格；
-   每格四边形顶点顺序一致、格子相邻边连续；
-   内部点命中正确，棋盘外/留边返回 `None`；
-   共享边界遵守半开区间规则；
-   重复、共线、退化角点被拒绝；
-   变换分母接近零、非有限坐标不导致崩溃；
-   背景缩放/偏移后映射仍正确；
-   行列反转能被测试发现。

### 资源和配置测试

-   旧 `assets/manifest.json` 和 `assets/skins/dusk/manifest.json`
    继续通过；
-   背景必需资源缺失时启动阶段报出具体路径；
-   可选角色图缺失时保留几何回退；
-   未知背景 ID、错误 schema、非法角点、未知字段和越界路径被拒绝；
-   从不同工作目录启动时路径行为符合文档；
-   背景和缩放缓存不在每帧重复加载。

### 战斗集成测试

对新场景执行选择、移动、攻击、跳过、结束行动、击杀、胜负、连续回溯。相同初始场景和输入序列下，矩形模式与透视模式的完整
`BattleView`
应一致，至少包含单位位置、生命、行动顺序、阶段、轮数、日志、胜负、回溯和表现
token。

### 真实窗口检查

-   背景无拉伸，网格与主要砖缝视觉对齐；
-   近处、中部、远处点击均命中正确格；
-   HUD 与棋盘点击区域不冲突；
-   高亮保留原图纹理；
-   脚底、血条、选中标记稳定；
-   角色近远遮挡正确；
-   攻击、死亡、伤害数字和回溯正常；
-   旧矩形模式仍可运行。

Surface
自动化不能替代真实窗口检查；不要把像素哈希当成唯一跨平台视觉标准。

## 11. 性能、风险与约束

-   背景 Surface 在启动时加载并缓存；每帧禁止磁盘 IO 和重复缩放。
-   透视矩阵只在角点/视口变化时重算；64 个格子的多边形可预计算。
-   不让规则层读取透视矩阵或屏幕像素。
-   新 HUD 独立于旧 `InfoPanel`，减少回归风险。
-   如果画作中的砖缝不是严格平面投影，先调整棋盘范围和四角；单应性无法满足时再提议逐行/逐列校准。
-   若原图不可访问，不能伪造替代图；若真实角色素材缺失，明确说明几何回退状态。
-   不得以降低旧测试覆盖、删除旧模式或改动战斗规则来解决渲染问题。

## 12. 最终交付物

1.  用户提供的背景原图，路径和真实尺寸已确认；
2.  `assets/skins/war_torn/manifest.json` 与资源说明；
3.  `presentations/war_torn_8x8.json`，含实际校准角点；
4.  `content/scenarios/war_torn.json`，双方各三个单位的独立场景；
5.  `PerspectiveBoardGeometry` 及单元测试；
6.  背景渲染、透视高亮和角色深度排序；
7.  场景 HUD、输入与特效适配；
8.  新 CLI 入口，旧命令保持兼容；
9.  README、资源规范和架构文档更新；
10. 自动化测试结果和真实窗口检查记录；
11. 一张实际游戏窗口截图（若环境无法生成，明确说明；不能用设计示意图冒充）；
12. 最终变更摘要、未完成项和需人工确认的美术事项。

## 13. 验收清单

-   [ ] 原始背景 PNG 已接入，真实尺寸和路径已确认。
-   [ ] 背景按比例显示，没有重复平铺地砖。
-   [ ] 8×8 逻辑棋盘已校准，调试模式可显示角点、网格、中心和坐标。
-   [ ] 正向投影、反向点击、边界和缩放测试通过。
-   [ ] 背景、网格、角色、特效共用同一套视口变换。
-   [ ] 移动/攻击高亮沿透视四边形绘制。
-   [ ] 角色脚底、深度排序、血条和选中标记正常。
-   [ ] HUD 与棋盘输入互不干扰。
-   [ ] 攻击、死亡、伤害数字和回溯正常。
-   [ ] 新场景配置独立，旧场景 JSON 未被意外修改。
-   [ ] 默认启动、`--geometry`、渡口和 dusk 资源路径仍然工作。
-   [ ] 完整旧测试和新增测试通过。
-   [ ] 真实 Pygame 窗口已检查，结果如实记录。
-   [ ] README 与资源来源/许可信息已更新。
-   [ ] 最终报告明确区分已完成、未完成和人工校准项。

## 14. 给 Codex 的最终任务摘要

请在当前 `chrono-tactics-pygame`
工作树中，以新增透视场景模式的方式完成该功能。第一目标不是重写游戏，也不是制作大量角色美术，而是让用户提供的战场背景成为可交互的
8×8 透视棋盘。

按"资源确认 → 配置 → 透视几何 → 调试网格 → 独立渲染器 → 点击与 HUD →
特效 → 新场景 →
回归测试"的顺序实现。旧矩形模式必须保留。战斗状态仍由现有规则和
Controller
管理；新增模块负责把逻辑格投影到背景，并把鼠标输入反向映射回逻辑格。

若原图不可访问、角点无法合理贴合地砖，或现有架构与本报告假设不符，请先报告证据与影响，再做最小安全调整；不得猜测资源路径、伪造测试结果或进行无关的大规模重构。
