# Chrono Tactics · 离线回溯战棋

仓库名称：`chrono-tactics-pygame`，阶段版本：`0.2.0`；M0–M5 已实施。发布状态以仓库 tag / Release 为准。

当前开发代码另有原图逐砖透视战场：**8×8 逻辑包围盒内的 28 块不规则有效地块**，完整背景、透视点击/高亮、脚底深度排序、独立 HUD 和 F3 网格。该扩展尚未单独发布，角色仍为几何回退。

按用户允许不规则地图的补充要求完成校准：保留单应性，20 个独立验证交点平均 **5.57 px**、最大 **11.42 px**；其中 9 个内部交点为 **3.86/6.00 px**（1280×720）。六个单位初始坐标/属性不变，void 通过原有场景障碍数据阻挡。实测点与拟合四角分开记录；近处边界仍有残差，详见 [校准报告、截图与限制](docs/WAR_TORN_CALIBRATION.md)。

项目仓库：[zyb-sjtu/chrono-tactics-pygame](https://github.com/zyb-sjtu/chrono-tactics-pygame)。这是私有仓库，需要登录有权限的 GitHub 账号访问。

使用 Python 和 Pygame 绘制，运行时不访问网络，不需要另行下载美术。默认显示随项目提供的演示地砖与斥候 PNG，也可用 --geometry 回到几何模式。默认棋盘 8×8，每格 64×64，侧栏 384 像素，窗口 896×512；渡口场景为 6×5，窗口 768×512。

## 整体规划与后续开发

已完成评审和 M1–M5：规则与表现分离、纯数据回溯、结算确认、JSON 内容/资源清单、PNG 缓存和实际素材动画。M5 增加 6×5 渡口场景及 `dusk` 外观；透视扩展继续复用战斗与回溯，仅增加表现与输入映射。经典/dusk 为程序生成素材，war_torn 背景为用户提供的原图。

| 文档 | 内容 |
| --- | --- |
| [意见评审](docs/ARCHITECTURE_REVIEW.md) | 哪些建议采纳、哪些调整，以及源码证据和原报告遗漏 |
| [整体架构](docs/ARCHITECTURE.md) | 模块职责、依赖、指令与视图、快照、动画和扩展入口 |
| [实施路线](docs/ROADMAP.md) | M0–M5、前置能力、小批次提交与验收标准 |
| [美术资源规范](docs/ASSET_GUIDE.md) | 路径、清单、缓存、透明图片、锚点、图层和动画 |
| [功能开发规范](docs/FEATURE_DEVELOPMENT.md) | 新功能的数据归属、回溯方案、扩展边界与完成条件 |
| [M1 实施与验收](docs/M1_IMPLEMENTATION.md) | M1 模块接口、场景示例、57 项检查与 8 帧像素对照 |
| [M2 实施与验收](docs/M2_IMPLEMENTATION.md) | Controller 接口、完整视图、75 项检查与 13 帧像素对照 |
| [M3 实施与验收](docs/M3_IMPLEMENTATION.md) | 纯数据快照、结算与代次协议、94 项检查及 13 帧像素对照 |
| [M4 实施与验收](docs/M4_IMPLEMENTATION.md) | JSON 格式、资源替换、缓存、动画、123 项检查与实际窗口 |
| [M5 实施与验收](docs/M5_IMPLEMENTATION.md) | 第二场景/外观、133 项回归、实际窗口、发布对应关系 |
| [扩展演练](docs/EXTENSION_EXERCISE.md) | 渡口试玩与仅通过 JSON/PNG 扩展的具体步骤 |
| [功能模板](docs/templates/FEATURE_TEMPLATE.md) | 可复制的规则、数据、回溯、表现与验收模板 |
| [源码发布](docs/RELEASE.md) | 提交树打包、SHA256 与解压验收 |
| [透视战场基线](docs/PERSPECTIVE_BATTLEFIELD.md) / [逐砖校准](docs/WAR_TORN_CALIBRATION.md) | 原图、28 格不规则地图、独立误差、实际截图、输入与脚底 |

架构整改 M0–M5 已落实，后续按实际功能需求继续开发；新增状态必须能回溯，新增美术通过资源与渲染入口接入。约束同时写入 [AGENTS.md](AGENTS.md)，实现进度见 [TASKS.md](TASKS.md)。

## 运行

当前机器已经配置好独立环境，无需激活或重新安装：

```powershell
cd E:\gamedesign
.\.venv\Scripts\python.exe main.py
```

如果旧版窗口还开着，请先关闭，再执行以上命令。

切回旧几何画面（不加载资源清单/图片），或选择关卡和资源目录：

```powershell
.\.venv\Scripts\python.exe main.py --geometry
.\.venv\Scripts\python.exe main.py --scenario scenarios/training_ground.json --assets assets
.\.venv\Scripts\python.exe main.py --scenario scenarios/river_crossing.json --assets assets/skins/dusk
.\.venv\Scripts\python.exe main.py --presentation presentations/war_torn_8x8.json
.\.venv\Scripts\python.exe main.py --presentation presentations/war_torn_8x8.json --debug-grid
```

默认内容/资源路径相对项目位置解析，与工作目录无关。--scenario 相对 content 根；显式传入 --content-root 或 --assets 时，目录相对当前工作目录或使用绝对路径。更换单位、地砖和动画只改 JSON/PNG，步骤见 [M4 记录](docs/M4_IMPLEMENTATION.md) 和 [资源来源](assets/README.md)。

透视入口固定 1280×720，F3 切换调试网格。`--presentation` 的路径相对项目根；它与 `--scenario`、`--assets`、`--content-root`、`--geometry` 互斥，冲突会报错退出，不隐含覆盖。`--debug-grid` 需要透视入口。快速体验：移动 A2 到内部坐标 `(4,3)`，再攻击 D1 `(5,3)`，击杀后退格恢复；坐标可用调试网格查看。

逐砖校准复核：`python -S scripts/fit_board.py --check`；原图标点、误差分区、配置再生成和真实窗口截图见 [校准报告](docs/WAR_TORN_CALIBRATION.md)。

在新机器安装（Python 3.9 或以上、可用的桌面环境）：

```powershell
git clone https://github.com/zyb-sjtu/chrono-tactics-pygame.git
cd chrono-tactics-pygame
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

首次安装依赖需要联网，安装后游戏可完全离线运行。如果使用本机 Miniconda 创建新环境时提示 SSL 模块不可用，可仅在当前 PowerShell 会话中先运行以下命令再安装依赖；其他 Python 安装通常不需要：

```powershell
$env:PATH = 'D:\Miniconda3;D:\Miniconda3\Library\bin;' + $env:PATH
```

## 战斗规则

- 3 个蓝方与 3 个红色木桩均为单位，具有生命、攻击、防御、速度、移动力；默认斥候使用带帽蓝色演示精灵，其余为蓝圆/红方块几何回退。侧栏显示 `生命: 80/100`，棋盘显示血条。基础数值在 `content/units.json`，阵容/实例覆盖在 `content/scenarios/training_ground.json`，仍为演示占位值。
- 入场时将双方单位按速度从高到低排序，同速按入场顺序排列。每轮各行动一次，全部行动后进入下一轮，按相同顺序继续。
- 每次行动分为**一次移动 → 一次攻击**。可以跳过移动、跳过攻击，或直接结束行动；成功攻击后，动画播放完毕再交接给下一位。
- 移动和攻击均按上下左右四方向计算，不允许斜走或斜向攻击。
- 移动目的地可以是移动力步数内的任意可达空格，按实际通路步数计算。障碍、友方和敌方单位均不能穿过或重叠。即使没有用满步数，也消耗本次移动机会，不能分段多次移动。
- 攻击仅能锁定距离 1 格的敌方单位，不能攻击自己、同阵营、斜向或更远的单位。必须先完成或跳过移动，才能攻击。
- 伤害为**攻击属性的 100%**，当前防御属性不减伤。例如攻击 10 对生命 100/100 的目标造成 10 点伤害，生命变为 90/100。伤害跳字显示攻击结算值，持续约 0.9 秒并向上浮动淡出；过量伤害下生命最低为 0。
- 生命归零即被击杀：几何模式播放约 0.65 秒闪烁/缩小/碎点淡出，图片模式按外观 death 帧播放（演示约 0.6 秒），然后消失。被击杀单位不再阻挡路径、不能被选为目标，也不会再次行动。
- 攻击动画期间锁定移动、攻击、结束行动和回溯，窗口仍能正常关闭；动画使用逐帧更新时间，没有阻塞式等待。
- 一方全灭后显示胜方，停止继续行动，仍可回溯最后一次行动并恢复被击杀单位。
- **双方均由玩家手动操作，没有 AI。** 红色木桩同样参与回合，可手动移动和攻击；不操作时不会自行行动。

## 操作

| 操作 | 效果 |
| --- | --- |
| 左键点击任意单位 | 查看其属性；查看其他单位不会改变当前行动者 |
| 当前行动者被选中时，点击绿色格 | 移动一次，进入攻击阶段 |
| 攻击阶段点击相邻敌方 | 扣血、显示伤害跳字；动画结束后进入下一单位行动 |
| 空格 / 侧栏“跳过移动/攻击” | 跳过当前阶段 |
| 回车 / 侧栏“结束行动” | 放弃剩余操作，进入下一单位行动 |
| 退格 Backspace / 右上角“回溯” | 回到上一单位行动开始前，可以连续回溯 |
| 点击窗口关闭按钮 | 退出并释放资源 |

金色方框标记当前行动者，白色圆环标记正在查看的单位。查看其他单位后，点击金框单位可继续行动。非法目的地或无效点击不会消耗行动。灰色方块为固定障碍，红色范围为四方向相邻攻击范围，目标格有额外边框。

回溯按完整的“单位行动回合”处理：例如斥候行动完轮到先锋，按退格会回到斥候开始行动前。会恢复双方全部单位的位置、当前/最大生命与其他属性、行动顺序、轮数、日志和战斗结束状态；此前被击杀的单位也会恢复。若先锋已走了一步，这一步也一并撤回。首个单位的首个行动没有上一行动可回溯，此时按钮禁用；回溯后产生的新行动会替换原来的后续历史。历史仅保存在本次游戏进程中。

开局可直接体验：速度最高的斥候 A2 先行动，点击**第 5 列、第 5 行**的绿色格（内部坐标 `(4, 4)`），再点击右边木桩 D2，即可看到 `-10` 跳字。动画结束后轮到先锋 A1，点击木桩可看到生命 `90/100`。此时按退格，斥候的位置与木桩的生命都会恢复。显示坐标以左上角第 1 列、第 1 行开始，代码中的坐标从 0 开始。

## 项目目录与职责

```text
E:\gamedesign\
├── main.py                  # 入口
├── requirements.txt         # pygame==2.6.1
├── .gitignore
├── .gitattributes
├── AGENTS.md                # 后续维护约定
├── TASKS.md                 # 已完成功能与验证边界
├── CHANGELOG.md             # 版本记录
├── README.md
├── SOURCE.md                # 各文本文件完整代码汇总
├── .github/workflows/ci.yml  # Windows/Linux × Python 3.9/3.12
├── scripts/export_source.py # 源码汇总生成与一致性检查
├── docs/
│   ├── ARCHITECTURE_REVIEW.md # 对原整改报告的源码核对与评审
│   ├── ARCHITECTURE.md      # M1–M5 扩展边界
│   ├── M1_IMPLEMENTATION.md # M1 接口与验证记录
│   ├── M2_IMPLEMENTATION.md # M2 指令、视图与验证记录
│   ├── M3_IMPLEMENTATION.md # M3 快照、结算确认与验证记录
│   ├── M4_IMPLEMENTATION.md # M4 内容、资源与验证记录
│   ├── M5_IMPLEMENTATION.md # M5 扩展与阶段交付记录
│   ├── EXTENSION_EXERCISE.md # 第二场景与外观演练
│   ├── RELEASE.md          # 提交树打包与解压验收
│   ├── PERSPECTIVE_BATTLEFIELD.md # 透视模式与校准记录
│   ├── WAR_TORN_CALIBRATION.md # 不规则地图、实测误差与运行截图
│   ├── calibration/         # 历史样带、正式40交点及独立误差报告
│   ├── templates/FEATURE_TEMPLATE.md # 可复制开发模板
│   ├── ROADMAP.md           # 阶段、前置与验收
│   ├── ASSET_GUIDE.md       # 美术资源与动画规范
│   ├── FEATURE_DEVELOPMENT.md # 后续开发约束
│   └── references/architecture_proposal.md # 用户原始意见
├── tactics\
│   ├── __init__.py
│   ├── settings.py          # 格子像素、侧栏等表现默认值
│   ├── models.py            # 单位状态、纯数据单位快照和攻击结果
│   ├── scenario.py          # 不可变场景、验证、默认阵容
│   ├── content.py           # 纯 JSON 定义/场景加载
│   ├── data_files.py        # 纯 JSON 与安全相对路径工具
│   ├── asset_manifest.py    # 纯清单、帧/状态引用验证
│   ├── assets.py            # PNG/缩放缓存、锚点与帧列表
│   ├── board.py             # 纯逻辑地图、空间查询与 BFS
│   ├── geometry.py          # 不依赖 Pygame 的坐标转换
│   ├── perspective_geometry.py # 纯单应投影/逆变换与缓存
│   ├── presentation_layout.py # 严格视觉布局配置
│   ├── actions.py           # UIAction 与操作结果
│   ├── controller.py        # 统一操作、选中 UID、代次与结算确认
│   ├── view_models.py       # 完整只读视图与独立表现数据
│   ├── board_renderer.py    # 只读视图驱动的棋盘绘制
│   ├── perspective_board_renderer.py # 整张背景与透视绘制
│   ├── scene_hud.py         # 独立叠加 UI 与动作命中
│   ├── battle.py            # 规则、结算编号、纯数据快照与回溯
│   ├── effects.py           # 伤害/击杀动画、逐帧更新与完成通知
│   ├── panel.py             # 字体回退、只读侧栏与动作命中
│   └── game.py              # 鼠标/键盘事件、主循环、退出清理
├── tests\
│   ├── test_battle.py       # 11 项战斗规则检查，无需创建窗口
│   ├── test_game.py         # 11 项窗口交互、绘制与字体检查
│   ├── test_effects.py      # 10 项几何动画、通知、清理和交互检查
│   ├── test_assets.py       # 16 项 PNG、缓存、渲染和动画检查
│   ├── test_milestone.py    # 6 项跨场景/外观集成验收
│   ├── test_release.py      # 4 项发布包损坏/来源/路径检查
│   ├── test_perspective_geometry.py # 8 项纯透视/遮罩几何检查
│   ├── test_presentation_layout.py # 6 项纯配置/背景检查
│   ├── test_perspective_rendering.py # 9 项显示/输入/战斗集成
│   ├── test_calibration.py  # 9 项观测、误差及标定/验证分离检查
│   ├── test_content.py      # 13 项无第三方包的内容/清单检查
│   ├── test_core.py         # 12 项无第三方包的 M1 核心检查
│   ├── test_controller.py   # 16 项无第三方包的协调与数据边界检查
│   ├── test_resolution.py   # 16 项无第三方包的快照和结算协议检查
│   ├── test_rendering.py    # 6 项只读视图、渲染、按钮和场景注入检查
│   └── test_rewind.py       # 12 项回溯、击杀及行动顺序检查
├── content/                 # units.json、训练场/渡口/war_torn 三个场景
├── presentations/war_torn_8x8.json # 参照角点、28格遮罩、视口、HUD、调试
├── assets/                  # 默认/dusk 共 26 张 PNG；war_torn 原始背景与独立清单
├── scripts/generate_demo_assets.py # 重建演示 PNG，不下载外部资源
├── scripts/generate_dusk_assets.py # 重建第二套演示 PNG
├── scripts/build_release.py # 从确切提交构建源码 ZIP 与 SHA256
├── scripts/verify_release.py # 校验并在解压目录验收
├── scripts/calibrate_board.py # 四角/内部点的可撤销草稿标点
├── scripts/fit_board.py     # 单应性多点标定、独立误差、配置一致性与真实截图
├── VERSION.txt             # 阶段版本 0.2.0
├── artifacts\               # 实际运行截图，不是游戏资源
│   ├── m4_assets.png        # 当前默认地砖/斥候素材
│   ├── m4_attack.png        # 素材攻击与跳字
│   ├── m4_death.png         # 素材死亡帧
│   ├── m4_revived.png       # 回溯恢复素材单位
│   ├── initial.png          # 开局移动范围
│   ├── selected.png         # 移动后可攻击目标
│   ├── damage_popup.png     # 实际攻击 10 的跳字
│   ├── after_attack.png     # 木桩生命 90/100
│   ├── enemy_turn.png       # 红方手动回合
│   ├── rewind.png           # 回溯后恢复位置和血量
│   ├── defeat.png           # 击杀动画中间帧
│   ├── defeat_disappeared.png # 击杀动画后消失
│   ├── defeat_result.png    # 击杀后交接回合
│   ├── defeat_rewind.png    # 回溯恢复被击杀单位
│   └── m1_custom_scenario.png # M1 第二场景实际窗口
└── .venv\                   # 本机独立环境，生成内容
```

完整文本文件内容见 [SOURCE.md](SOURCE.md)。虚拟环境和缓存不提交，运行截图随文档保留。更新文本文件后执行：

```powershell
python scripts/export_source.py
python scripts/export_source.py --check
```

## 源码压缩包

可在 GitHub 仓库中通过 Code → Download ZIP 下载源码，也可在本地 Git 仓库生成：

```powershell
.\.venv\Scripts\python.exe scripts/build_release.py --ref HEAD
$releaseCommit = git rev-parse HEAD
.\.venv\Scripts\python.exe scripts/verify_release.py --expected-commit $releaseCommit
```

源码包包含运行代码、两场景/外观、测试、文档、配置和截图，不包含 `.venv`、缓存或凭据；解压后按新机器安装步骤创建环境。输出 `dist/chrono-tactics-pygame-0.2.0-source.zip` 和 `.zip.sha256`，ZIP comment 记录确切提交，详见 [发布说明](docs/RELEASE.md)。这是 Python 源码包，未构建独立 EXE。

## 验证记录

当前总计 **165 项，本机 164 通过、1 项符号链接权限跳过**，dummy 与实际 Windows 显示分别验证。七组纯检查 80 项，另 4 项包完整性检查；逐砖误差另由真实原图交点独立测量，不以测试数量代替对齐证据。

透视功能实现时的基线为 **152 项：本机 151 通过、1 项符号链接权限跳过**，dummy 与 windows 实际窗口分别执行；当时六组纯检查 69 项，另 4 项包完整性检查可用 `-S`。矩形/透视完整战斗状态一致；旧几何 13 帧逐像素不变。这是功能/兼容性基线，不是接缝对齐验收，见 [透视实施记录](docs/PERSPECTIVE_BATTLEFIELD.md)。

M5 共 **133 项测试**，本机 **132 通过、1 项跳过**（Windows 无创建符号链接权限，其他路径检查通过）。四组核心/内容检查共 **57 项无需第三方包**，另 4 项发布完整性检查也可用 `-S`。dummy 与 Windows 实际窗口分别回归；两场景 × 三模式的完整状态一致，覆盖击杀、跨轮、战斗结束、连续回溯、旧通知、字体异常及异地 CLI/QUIT。真实窗口使用自动投递事件，非人工逐次点击。详见 [M5 记录](docs/M5_IMPLEMENTATION.md)。M4 的 123 项基线及 13 帧几何像素对照记录保留。

```powershell
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_core.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_controller.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_resolution.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_content.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_perspective_geometry.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_presentation_layout.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_release.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

v0.1.0 基线记录：2026-10-22，本机 Python 3.9.1 / Pygame 2.6.1 / SDL 2.28.4 实测 **41 项检查全部通过，退出码 0**。覆盖速度和同速顺序、四方向范围、路径阻挡、移动次数、敌我与攻击距离限制、攻击 100% 结算及忽略防御、过量伤害归零、跳字生命周期、动画期间锁定操作及正常关闭、实际画面中击杀形体消失、死亡后的行动顺序、连续和跨轮回溯、回溯恢复已死单位与当前/最大生命、回溯战斗结束状态，以及原有窗口和字体回退。

另外通过 `main.py` 实际入口创建窗口，使用 `windows` 显示驱动向事件队列投递鼠标和键盘事件，验证了两条完整流程，均退出码 0：默认配置下“移动 → 攻击 10 → 跳字 → 查看 90/100 → 红方回合 → 连续回溯”；测试场景下“攻击生命 5 的目标 → 击杀动画 → 形体消失 → 下一回合 → 回溯复活”。击杀场景仅在验证进程中设置目标生命为 5，没有改动游戏默认初始数据。已保存截图并查看跳字、扣血、击杀动画、消失和复活的实际画面。这是自动投递事件验证，并非人工鼠标逐次操作；其他系统尚未实测。

保留字体问题修复：优先直接加载 Windows 字体文件，失败后再扫描系统字体；扫描抛出 TypeError、OSError、ValueError 或 pygame.error 时，回退到 Pygame 内置字体与英文界面。不修改系统字体或注册表。

自动测试配置位于 [.github/workflows/ci.yml](.github/workflows/ci.yml)，使用虚拟显示驱动执行回归检查；它不能替代实际窗口的显示效果检查。远程运行结果见仓库 Actions 页面。CI 使用的动作版本参照 [checkout](https://github.com/actions/checkout) 和 [setup-python](https://github.com/actions/setup-python) 官方用法。

![M4 默认演示素材](artifacts/m4_assets.png)

以下为保留的几何模式画面：

![伤害跳字](artifacts/damage_popup.png)

![实际扣血和当前/最大生命](artifacts/after_attack.png)

![击杀动画中间帧](artifacts/defeat.png)
