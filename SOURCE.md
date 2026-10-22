# 完整项目源码

本文件由 `python scripts/export_source.py` 生成。包含项目全部文本源码、配置和文档；不包含自身、二进制 PNG、截图、虚拟环境、缓存及压缩包。演示 PNG 可由 scripts/generate_demo_assets.py 与 scripts/generate_dusk_assets.py 重建。

## .gitattributes

```text
* text=auto eol=lf
*.png binary
*.zip binary
```

## .github/workflows/ci.yml

```yaml
name: Tests

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  regression:
    name: ${{ matrix.os }} / Python ${{ matrix.python }}
    runs-on: ${{ matrix.os }}
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-24.04, windows-2022]
        python: ['3.9', '3.12']
    env:
      SDL_VIDEODRIVER: dummy
      SDL_AUDIODRIVER: dummy
      PYGAME_HIDE_SUPPORT_PROMPT: '1'
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: ${{ matrix.python }}
          cache: pip
      - name: Verify core without site packages
        run: python -S -m unittest discover -s tests -p test_core.py -v
      - name: Verify controller without site packages
        run: python -S -m unittest discover -s tests -p test_controller.py -v
      - name: Verify snapshots and resolutions without site packages
        run: python -S -m unittest discover -s tests -p test_resolution.py -v
      - name: Verify content and manifest without site packages
        run: python -S -m unittest discover -s tests -p test_content.py -v
      - name: Verify perspective geometry without site packages
        run: python -S -m unittest discover -s tests -p test_perspective_geometry.py -v
      - name: Verify presentation configuration without site packages
        run: python -S -m unittest discover -s tests -p test_presentation_layout.py -v
      - name: Verify calibration observations without site packages
        run: python -S -m unittest discover -s tests -p test_calibration.py -v
      - name: Verify measured map matches runtime presentation
        run: python -S scripts/fit_board.py --check
      - name: Install dependencies
        run: python -m pip install -r requirements.txt
      - name: Check source bundle
        run: python scripts/export_source.py --check
      - name: Run regression tests
        run: python -m unittest discover -s tests -v
      - name: Build committed source release
        run: python scripts/build_release.py
      - name: Verify extracted release offline
        run: python scripts/verify_release.py --expected-commit ${{ github.sha }}
```

## .gitignore

```text
.venv/
__pycache__/
*.py[cod]
artifacts/*
!artifacts/*.png
dist/
.delivery/
build/
.pytest_cache/
.coverage
htmlcov/
.env
.env.*
!.env.example
*.pem
*.key
```

## AGENTS.md

````markdown
# 项目维护与后续开发约定

## 先确认实际状态

- 阶段版本是 v0.2.0，M1–M5 已实施：规则/表现分离、纯数据回溯与结算确认、JSON/PNG 链路、第二场景/外观与开发模板。发布状态以 tag/Release 为准；以 `TASKS.md` 区分现有能力和规划。
- 当前透视模式采用 8×8 逻辑包围盒内 28 块不规则石砖，按用户允许不规则地图的补充完成校准；角色仍为几何回退。先读 `docs/WAR_TORN_CALIBRATION.md`，原 `docs/PERSPECTIVE_BATTLEFIELD.md` 的旧四角/152项是历史基线。
- 实测40顶点分20标定/20独立验证；保留单应性与有效格遮罩，没有控制网格。模型四角是拟合估计，不得冒充原图观测；扩图须补真实交点及验证、Scenario void 阻挡，运行 `python -S scripts/fit_board.py --check`。不以旧2×6统计或外推点冒充整图结果。
- 修改玩法、结构或资源入口前，阅读 [整体架构](docs/ARCHITECTURE.md)、[实施路线](docs/ROADMAP.md) 与 [功能开发规范](docs/FEATURE_DEVELOPMENT.md)。接入美术时同时遵守 [资源规范](docs/ASSET_GUIDE.md)。用户提供的原始报告是评审材料，当前开发决策以这些评审后文档为准。

## 开发边界

- 这是离线 Python/Pygame 战棋原型。保留几何绘制作为无素材时的默认回退，后续美术通过统一资源与渲染层接入；具体玩法按用户需求推进。
- 业务规则放在 `tactics/battle.py`，空间与路径规则放在 `tactics/board.py`。Board 显式接收 Scenario，不恢复像素坐标或绘图入口；坐标由 Geometry 转换，绘制由 BoardRenderer 读取 BoardView 完成。
- 应用操作统一经过 `Controller`，通过 `get_view_state()` 查询独立的 BattleView；不向 Game、Panel、Renderer、Effects 暴露活动 Unit/Board/Battle。Game 只做组装、输入适配、循环与清理；Panel 用 `hit_test(position)` 返回 UIAction，按钮矩形保持内部实现。
- `move_to/attack` 对当前行动者提交指令，与查看谁的属性无关；鼠标通过 `click_cell` 保留“先选回行动者再操作”的交互。不要让未来 AI 模拟像素点击，也不以重建 Game 内部字段作为测试夹具；用 Scenario 构建局面。
- 表现接口为 `play_attack(AttackPresentation)/update(elapsed)->tuple[ResolutionToken,...]/clear()`。Controller 只接受当前结算编号与表现代次的完成通知，不以全局 busy 状态推进回合；动画不修改规则。素材动画沿用此接口，循环待机由 Renderer 更新，不进入阻塞队列。
- 默认内容从 `content/units.json` 和 `content/scenarios/training_ground.json` 加载，禁止重新在 Python 写第二份默认数值。JSON 引用和结构错误必须启动时定位；Unit.definition_id 属于快照与视图，外观/图片路径不进入规则状态。
- AssetManager 在显示初始化后加载 `assets/manifest.json`；预载原图、帧列表和显示尺寸，绘制时只读缓存。图片按解析后的路径缓存、缩放按路径/尺寸缓存，缺失也缓存并按资源 ID 记录一次。路径不得逃逸资源根。
- 当前支持 PNG、显式帧列表、idle 循环及 attack/death 非循环，不假装支持图集切帧、音频或热重载。大精灵与死亡形体按脚底/稳定 ID 排序，全部标签、高亮和血条在形体之后绘制。`--geometry` 完全绕过资源加载；可选图片缺失使用几何回退，必需图片/清单错误不能静默忽略。
- AttackResult、UnitSnapshot、TurnSnapshot 均为独立不可变值；行动队列快照存 UID。回溯重建 Unit，跨回溯的旧实体引用不再有效，调用方按 UID 重新查询。新 Unit 字段必须同步快照与恢复，字段覆盖测试不得绕过。
- 结算编号在同一 Battle 中单调递增且不回溯；Controller 成功回溯或程序化 restart 时先提升表现代次并作废待确认，再清理表现、恢复/重建规则。失败回溯不改变代次或表现；新异步效果必须沿用匹配确认入口。
- 后续功能必须建立在可扩展边界上：先明确规则入口、数据归属、回溯策略、表现/资源接入和验收证据。前置能力缺失时先补齐最小必要部分，与需求一并交付；不能以架构未完成为由无限延后任务，也不为每个小改动制造额外批准流程。
- 新增规则代码不依赖 Pygame；渲染、UI、动画和未来 AI 不直接改战斗状态。UI/AI 共用合法性校验和指令入口，避免复制规则。
- 新增运行状态必须明确快照与恢复行为；新增资源、图片、字体、动画进度不得进入规则快照。对外视图和结算结果使用独立数据与稳定 ID，不向表现层泄露可变实体。
- 图片集中加载和缓存，不在每帧读盘；路径相对资源根解析。替换美术不能改变占格、移动、攻击或回溯语义。
- 透视配置在 presentations/，规则场景仍在 content/；矩阵、像素、资源与 HUD 不进规则/快照。完整背景只按 contain 缓存，深度预载只处理单位/障碍；沿用统一脚底/尺度/表现矩形接口与屏幕 Y 排序。不要改原图来掩盖网格误差，也不要把装饰自动当障碍。
- 抽象和模块必须有实际调用方。不提前创建空的插件、ECS、通用注册中心或未使用扩展层。结构性整改使用专用分支、分阶段验证与审查差异。

## 验证和维护

- 修改代码、测试或配置时，同步维护 `TASKS.md` 和 `CHANGELOG.md`；行为或操作变化同步到 `README.md`。
- 保留直接读取字体文件和字体扫描异常的回退逻辑，避免启动时再次因 Windows 字体注册表异常崩溃。
- 完成修改后运行 `python -m unittest discover -s tests -v`，并说明真实窗口与无窗口测试的验证边界。
- 修改规则、场景、几何或棋盘视图后，另运行 `python -S -m unittest discover -s tests -p test_core.py -v`，保证无第三方包时仍可运行。不要为兼容旧测试把 Pygame 加回核心。
- 修改协调、动作或完整视图后，另运行 `python -S -m unittest discover -s tests -p test_controller.py -v`。CI 在安装依赖前执行这两组检查。
- 修改快照、结算或动画交接后，另运行 `python -S -m unittest discover -s tests -p test_resolution.py -v`；CI 安装依赖前执行三组共 44 项检查。真实动画还需完整回归验证，纯测试不能代替实际完成通知与清理检查。
- 修改内容或清单后，另运行 `python -S -m unittest discover -s tests -p test_content.py -v`，CI 安装依赖前合计 57 项；原图/缩放缓存和实际资源链路由 `test_assets.py` 及真实窗口检查。Windows 无创建符号链接权限时该项可明确跳过，路径越界等其他检查仍须通过。
- 涉及透视几何/布局时，另以 `-S` 运行 test_perspective_geometry.py 与 test_presentation_layout.py；六组共 71 项。test_perspective_rendering.py 覆盖缓存、背景、HUD、CLI、资源动画和矩形/透视完整状态一致；真实窗口仍需单独观察校准和遮挡。
- 校准工具/观测变化另以 `-S` 运行 test_calibration.py；七组纯检查共80项。用 `scripts/fit_board.py --check` 重算正式地图原图观测和独立误差；`calibrate_board.py` 的2×6仅历史诊断。先确认实测对应，再决定是否升级映射，不以测试绿灯替代对齐验收。
- 保留原有行为覆盖；接口迁移时可调整测试夹具，不为保留旧字段访问而保留架构漏洞。新增架构边界在相应阶段就加入检查，不推迟到最终验收。
- 使用 `python scripts/export_source.py` 更新 `SOURCE.md`，再用 `python scripts/export_source.py --check` 检查一致性。
- 后续需求参考 `docs/templates/FEATURE_TEMPLATE.md`；换场景/外观参考 `docs/EXTENSION_EXERCISE.md`。新增内容要补真实集成，不能只验证文件存在。阶段发布按 `docs/RELEASE.md` 从确切提交打包并验证解压产物。
- 不提交虚拟环境、缓存、安装器、凭据或 `dist/`、`.delivery/` 中的生成文件。`artifacts/*.png` 是随文档交付的运行截图。
````

## CHANGELOG.md

````markdown
# 更新记录

## 未发布 · 不规则逐砖地图校准

- 用户允许不规则地图后，以 28 块可辨石砖建立有效区，保留六单位初始坐标/数值，36 个 void 由现有 Scenario 障碍数据阻挡；不改 Battle、路径算法、伤害、快照或 token。
- 保留 PerspectiveBoardGeometry 的单应性公式，增加参照逻辑矩形和有效格遮罩；四角实测基线不达标后，对同一单应性作离线多点标定，没有升级控制网格。原图40观测/模型估计分开保存。
- 20 标定与20独立验证隔离，1280×720 验证平均5.567316px/最大11.419992px，独立内部9点3.855241/6.002102px；近处边界仍有残差，明确报告不确定性。
- 四边形选中、统一脚底/标签/血条/跳字，几何死亡形体接入脚底Y/UID排序；可见形体点击与地面逆投影分开，void不命中。原三个障碍在有效区外不画图外岩石；独立障碍脚底另用明确夹具验收。
- 新增可复算标定/配置检查工具和实际窗口截图；完整165项，本机164通过/1项权限跳过，七组纯80项；CI/解压验收纳入实测配置检查，旧训练场/渡口/矩形完整回归保留。

## 诊断历史 · 不规则地图需求补充前

- 实际 Windows F3 网格确认旧选区未核对真实整砖跨度，不能把明显错位只解释为原画不规则；正式四角、单位初始位置、运行几何/渲染及规则均未改。
- 保留原图坐标观测与可重算报告：已确认2×6砖带的5个独立内部点，均值5.555742px/最大11.713753px，仅局部满足阈值，完整8×8明确未通过。
- 新增纯测量/完整性检查、四角与内部点的交互草稿工具（标点、撤销、预览、保存）和两张实际游戏截图；不自动导出正式配置，不将外推点伪装成81个实测控制点。
- 全量159项，本机158通过/1项符号链接权限跳过；新增6项纯测量和1项UI流程，CI增加纯校准组，SOURCE与开发状态同步。继续实现依赖完整8×8整砖对应或允许砖块细分的明确条件。

## 未发布 · 透视战场

- 原样接入用户 1672×941 战场 PNG，新增独立 war_torn 场景、必需背景清单与 presentation 布局；保留原训练场/渡口、单位定义和现有战斗规则。
- 纯 Python 单应投影与逆向拾取、半开边界、contain 共享变换和缓存；拒绝退化角点、错误背景尺寸、未知字段和越界路径。
- 独立透视 Renderer 与 SceneHUD，透明四边形、脚底/屏幕 Y 深度排序、形体后血条；复用 AssetManager/Clip，启动预载离散深度尺度，绘制不读盘/缩放。字体异常保留英文降级。
- Geometry 提供脚底/尺度/表现矩形，Effects 沿用结算 token 与清理协议；新增 --presentation/--debug-grid 和 F3，旧 CLI 保持，混用配置明确拒绝。
- 新增 19 项检查，共 152 项，本机 151 通过、1 项符号链接权限跳过；dummy/windows 分别验证，矩形/透视状态一致，旧几何 13 帧逐像素不变，新增 4 张实际窗口截图。
- 六组纯检查共 69 项；CI 与解压验收纳入新模式，SOURCE 纳入 presentations。当前角色为临时几何回退，绘画砖缝与单应细分局部有偏差，最终美术校准待确认。

## 0.2.0 - 2026-10-22

### M5 · 扩展演练与阶段交付

- 新增 6×5 渡口场景，复用单位定义；新增自包含 dusk 清单与 17 张项目生成 PNG，含地砖、障碍、斥候和木桩动画。既有运行代码、单位定义和默认场景不变。
- 增加可复制功能开发模板和演练手册，明确新状态、指令、回溯、独立视图、资源与 token 取消的责任和验收。
- 新增 6 项两场景 × 三模式集成与 4 项包完整性检查，共 133 项；本机 132 通过、1 项符号链接权限跳过。Windows 实际窗口与 dummy 分别验收，新增 4 张运行截图。
- 增加 VERSION、从提交树构建源码 ZIP/SHA256、校验并解压运行验收的标准库工具。CI 四平台组合同时执行完整回归和产物检查，新增 v* tag 触发；不构建 EXE。
- 同步 TASKS、README、架构/路线/资源文档和 SOURCE。最终发布对应 tag、Release 和 ZIP comment 中的同一提交。

### M4 · 内容与资源接入

- 默认单位定义和训练场迁到 JSON，保留 default_scenario() 入口；严格验证格式、版本、重复 ID/键、定义引用、属性和出生局面，错误包含文件位置。
- Unit/UnitSnapshot/View 增加 definition_id，攻击结果补充双方定义 ID 和行动位置；用于关联外观，不改变移动、伤害、顺序或回溯算法。
- 新增纯 manifest 解析与 Pygame AssetManager；校验根目录边界、PNG 路径、尺寸、锚点、动画帧/状态引用。原图按路径、缩放按路径与尺寸缓存，可选失败缓存并报告一次，必需缺失启动时拒绝。
- 默认渲染实际接入项目脚本生成的地砖和 64×96 斥候 PNG，支持循环待机、非循环攻击/死亡、脚底锚点、按脚底排序及独立高亮/血条层。
- 素材动画沿用 M3 token 完成确认；等待当前阻塞任务，不等待循环待机。缺失帧按几何效果回退，回溯/重开清理旧形体及通知。
- 新增 --geometry、--scenario、--content-root、--assets 启动参数；默认路径不依赖工作目录。显式几何模式无需资源清单，错误配置清晰退出。
- 新增 13 项纯内容/清单与 16 项实际 PNG/渲染检查，共 123 项；本机 122 通过，1 项 Windows 符号链接权限跳过。57 项可在无第三方包环境执行（含该跳过项）。
- 路径断言比较规范化结果，兼容 Windows CI 临时目录的 8.3 短路径别名；根目录边界与符号链接逃逸校验保持启用。
- 无窗口与 Windows 实际窗口回归完成；几何模式 13 帧与 M3 一致，素材模式验证透明度、缩放、图层、攻击/死亡、复活及异地目录入口，新增 4 张截图。
- SOURCE 汇总纳入 content/assets 文本；演示 PNG 及来源/制作约定随源码交付。M5 扩展与发布演练仍未实施。

### M3 · 纯数据回溯与结算确认

- AttackResult 改为结算编号、行动/目标 UID、目标位置/阵营、完整伤害、前后生命及击杀等不可变值，不保留活动实体引用。
- 新增覆盖 Unit 全部字段的 UnitSnapshot；TurnSnapshot 只存单位值、UID 顺序槽位、轮数、阶段、结果与日志，回溯按 UID 重建运行单位。
- Battle 为合法攻击分配单调递增且不回溯的编号，finish_attack 必须匹配当前编号，重复或错误编号无效。
- AttackPresentation 携带 ResolutionToken（表现代次、结算编号）；Effects.update 返回完成通知，Controller 验证后交接，不再轮询全局 busy。
- 成功回溯及程序化 restart 先作废旧代次，再清除表现、恢复/重建状态；失败回溯不产生副作用。没有新增玩家重开按钮或快捷键。
- 保留原 75 项覆盖，新增 16 项纯数据/协议检查与 3 项真实动画通知检查，共 94 项通过；44 项无需第三方包并纳入 CI 安装依赖前步骤。
- Windows 13 个关键画面与 M2 逐像素一致；覆盖击杀形体消失、连续回溯复活、重开清理、结算中关闭和 5×4 注入场景。
- 保持 100% 攻击伤害、行动顺序、动画时长及上一行动回溯语义；磁盘存档、外部内容与美术资源尚未实施。

### M2 · 操作协调与完整界面视图

- 新增无 Pygame 的 Controller，统一选择、移动、按 UID 攻击、跳过、结束与回溯；返回成功/失败及原因，沿用 Battle 的唯一规则实现。
- 新增不可变 BattleView/UnitView，覆盖完整属性、棋盘范围、选中/行动者、队列、双语日志、结束状态和按钮可用状态。
- InfoPanel 只读取视图，通过 UIAction 命中接口返回意图；Game 缩减为组装、键鼠适配、更新/绘制调度与退出，不保留可变规则对象兼容字段。
- Controller 接管输入锁定与动画结束交接，Effects 只接收独立 AttackPresentation；击杀、动画时长、100% 攻击伤害与上一行动回溯语义保持不变。
- 迁移测试夹具为 Scenario，保留原 57 项覆盖，新增 18 项协调、只读数据、按钮边界与依赖检查，共 75 项通过；28 项可在 `python -S` 下运行并纳入 CI 安装依赖前步骤。
- Windows 实际窗口自动交互验证通过；13 个关键画面与 M1 逐像素一致，包含查看、英文界面、敌方行动、击杀、回溯和战斗结束。
- M3 内部结果/快照 ID 化与结算协议、M4 资源接入仍未实施。

### M1 · 规则与渲染职责分离

- 提取不可变 UnitSpawn/Scenario、默认场景和验证；Board 必须显式接收场景，每局创建独立单位状态。
- Board 不再依赖 Pygame、固定像素尺寸或默认阵容，仅管理逻辑地图、空间查询和 BFS。
- 新增纯数值 BoardGeometry，棋盘、特效、点击与侧栏使用同一套场景尺寸。
- 新增 BoardRenderer 与最小只读 BoardView；渲染器不接收活动 Unit/Board/Battle，不查询战斗合法性。
- 迁移原有 41 项测试入口而保留行为断言，新增 16 项场景、几何、依赖边界和渲染检查，共 57 项通过。
- 12 项核心检查可使用 `python -S` 在无第三方包的环境运行，并加入 CI 的依赖安装前步骤。
- 默认场景 8 个关键画面与重构前逐像素一致；Windows 实际窗口验证 5×4 场景、攻击、回溯和退出。
- M2 控制器/完整 UI 视图、M3 结算与快照迁移、M4 美术资源接入仍未实施。

### 2026-10-22 · 架构评审与整体规划

- 对照 v0.1.0 源码审阅用户的架构整改报告，记录采纳、调整与补充意见。
- 制定规则、应用协调、表现/资源分层及稳定 ID、只读视图、快照和动画完成契约。
- 增加分阶段路线、资源/动画制作与接入规范、后续功能开发要求，并更新 AGENTS 与 TASKS。
- 源码汇总脚本纳入 docs，保证规划文档与源码汇总一起交付。
- 本次没有实施 M1–M5 重构，也没有增加玩法、修改伤害或回溯语义。

## 0.1.0 - 2026-10-22

首次仓库交付，包含当前已实现的完整离线战棋原型。

- 8×8 棋盘、64 像素格子、蓝色友方、红色训练木桩和固定障碍。
- 单位生命、攻击、防御、速度、移动力；按速度排序行动，移动与攻击各一次。
- 四方向路径范围、障碍及单位阻挡、相邻敌方攻击、跳过阶段和结束行动。
- 当前/最大生命值与血条；伤害按攻击力 100% 结算，显示上浮淡出的伤害数字。
- 生命归零后播放几何击杀动画并消失，退出行动队列；一方全灭后结束战斗。
- 退格键及界面按钮回溯上一单位行动，可恢复被击杀单位并连续回溯。
- 修复 Pygame Windows 字体扫描出现非字符串注册表项时的启动异常。
- 41 项规则、交互、动画、回溯及字体回归检查；附实际 Windows 窗口截图。
- 提供 README、任务进度、源码汇总脚本和 Windows/Linux 自动测试配置；源码压缩包不包含虚拟环境和缓存。
````

## README.md

````markdown
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
````

## TASKS.md

````markdown
# 项目进度

阶段版本：`0.2.0`，M0–M5 已实施；发布状态以仓库 tag / Release 为准。已实现能力与后续规划分开记录。

当前另已实施未单独发布的透视战场扩展。按用户允许不规则地图的补充完成 28 格逐砖校准；正式角色美术仍待接入。

## 已实现能力

| ID | 状态 | 内容 |
| --- | --- | --- |
| BOARD-01 | 已完成 | 默认 8×8 棋盘，每格 64×64；项目内生成演示图片，保留几何模式 |
| UNIT-01 | 已完成 | 双方各 3 个单位、固定障碍、点击查看属性 |
| TURN-01 | 已完成 | 速度排序、四方向移动、相邻攻击、手动操作双方、跳过与交接 |
| COMBAT-01 | 已完成 | 当前/最大生命与血条，攻击力 100% 伤害，伤害跳字 |
| COMBAT-02 | 已完成 | 击杀动画、消失、死亡单位退出队列、一方全灭结束战斗 |
| REWIND-01 | 已完成 | 回溯上一单位行动开始前、连续回溯、恢复死亡单位和战斗状态 |
| FIX-01 | 已完成 | Windows 系统字体扫描异常回退，保留英文降级界面 |
| QA-01 | 已完成 | 165 项，本机 164 通过、1 项符号链接权限跳过；七组纯检查 80 项与包完整性 4 项无需第三方包；dummy/实际 Windows、战斗/回溯/矩形兼容验收 |
| ASSET-01 | 已完成 | JSON 单位/场景、清单验证、PNG 与缩放缓存、可选缺失回退、必需缺失拒绝、静态和循环/非循环素材接入 |
| DELIVERY-01 | 已完成 | 运行文档、源码汇总生成脚本、忽略规则和自动测试配置 |
| EXTENSION-01 | 已完成 | 6×5 渡口场景、17 PNG 的 dusk 外观；复用现有运行代码；可复制功能开发模板 |
| RELEASE-01 | 已完成 | VERSION、提交树源码 ZIP、SHA256、解压验收脚本；四组 CI 包含产物检查，发布见 tag/Release |
| PERSPECTIVE-01 | 已完成 | 原始 1672×941 背景、纯单应投影/拾取、严格布局、完整背景/透明高亮/深度排序、HUD、CLI/F3、特效与回溯适配 |
| PERSPECTIVE-02 | 美术待接入 | 角色暂为明确几何回退；近处边界存在阈值内残差，未声称每个破损接缝像素重合 |
| CALIBRATION-01 | 已完成，按不规则地图补充需求 | 28 块真实石砖/40 交点，20 标定+20 独立验证；全体验证均值5.57/最大11.42px，独立内部3.86/6.00px；原单应性+有效区遮罩，无控制网格；脚底/形体点击/真实截图，见校准报告 |

CI 配置覆盖 Windows / Linux 与 Python 3.9 / 3.12。远程执行结果以 GitHub Actions 为准，配置存在不代表运行已通过。

路径检查比较解析后的规范路径，兼容 Windows CI 临时目录的 8.3 短路径别名；不通过跳过或放宽根目录边界来解决平台差异。

当前没有 AI、网络、存档或独立 EXE。数值仍为演示占位值，防御暂不参与伤害计算。

## 架构规划与实施状态

| ID | 阶段 | 状态 | 内容与验收重点 |
| --- | --- | --- | --- |
| ARCH-00 | M0 | 已完成 | 评审用户意见、整体架构、资源与功能开发规范、分阶段路线；后续约束写入 AGENTS |
| ARCH-01 | M1 | 已完成 | 场景注入、纯逻辑 Board、Geometry、BoardRenderer 与最小 BoardView；57 项检查及 8 帧一致性验收 |
| ARCH-02 | M2 | 已完成 | Controller 统一操作与动画交接、完整只读 View、UIAction 命中；Game/表现不持有可变战斗对象，75 项检查及 13 帧一致性验收 |
| ARCH-03 | M3 | 已完成 | ID 化 AttackResult、纯数据快照/UID 重建、结算编号与表现代次确认；拒绝重复/过期通知，94 项检查及 13 帧一致性验收 |
| ARCH-04 | M4 | 已完成 | 内容/资源清单、路径/引用验证、缓存和真实默认渲染链路；123 项测试、几何像素对照及素材窗口验收 |
| ARCH-05 | M5 | 已完成 | 第二场景/外观、开发模板、133 项回归、真实窗口、四组 CI 与 0.2.0 提交树源码交付链路 |

实现与验证见 [M1](docs/M1_IMPLEMENTATION.md)、[M2](docs/M2_IMPLEMENTATION.md)、[M3](docs/M3_IMPLEMENTATION.md)、[M4](docs/M4_IMPLEMENTATION.md) 和 [M5 实施记录](docs/M5_IMPLEMENTATION.md)。架构整改阶段已落实；后续按真实功能需求与开发模板推进。当前演示素材不是最终美术，尚无图集切帧、音频、热重载或磁盘存档。

阶段依赖、提交拆分和完成条件见 [ROADMAP](docs/ROADMAP.md)，技术边界见 [ARCHITECTURE](docs/ARCHITECTURE.md)。每个阶段同步增加所需边界测试，不等全部迁移后才测试。

后续技能、AI、美术、地图、存档等需求，须先明确扩展点与最小必要前置，按 [FEATURE_DEVELOPMENT](docs/FEATURE_DEVELOPMENT.md) 实施。此表不是新增玩法承诺。
````

## VERSION.txt

```text
0.2.0
```

## assets/README.md

````markdown
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
````

## assets/manifest.json

```text
{
  "schema_version": 1,
  "images": {
    "tile.floor": {"path":"tiles/floor.png","display_size":[64,64],"pivot":[0.5,0.5],"optional":true},
    "scout.idle.0": {"path":"units/scout_idle_0.png","display_size":[64,96],"pivot":[0.5,1.0],"optional":true},
    "scout.idle.1": {"path":"units/scout_idle_1.png","display_size":[64,96],"pivot":[0.5,1.0],"optional":true},
    "scout.attack.0": {"path":"units/scout_attack_0.png","display_size":[64,96],"pivot":[0.5,1.0],"optional":true},
    "scout.attack.1": {"path":"units/scout_attack_1.png","display_size":[64,96],"pivot":[0.5,1.0],"optional":true},
    "scout.attack.2": {"path":"units/scout_attack_2.png","display_size":[64,96],"pivot":[0.5,1.0],"optional":true},
    "scout.death.0": {"path":"units/scout_death_0.png","display_size":[64,96],"pivot":[0.5,1.0],"optional":true},
    "scout.death.1": {"path":"units/scout_death_1.png","display_size":[64,96],"pivot":[0.5,1.0],"optional":true},
    "scout.death.2": {"path":"units/scout_death_2.png","display_size":[64,96],"pivot":[0.5,1.0],"optional":true}
  },
  "animations": {
    "scout.idle": {"frames":["scout.idle.0","scout.idle.1"],"fps":2,"loop":true},
    "scout.attack": {"frames":["scout.attack.0","scout.attack.1","scout.attack.2"],"fps":8,"loop":false},
    "scout.death": {"frames":["scout.death.0","scout.death.1","scout.death.2"],"fps":5,"loop":false}
  },
  "visuals": {
    "unit.scout": {"idle":"scout.idle","attack":"scout.attack","death":"scout.death"},
    "unit.vanguard": {},
    "unit.guard": {},
    "unit.dummy": {}
  },
  "board": {"floor":"tile.floor"}
}
```

## assets/skins/dusk/README.md

````markdown
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
````

## assets/skins/dusk/manifest.json

```text
{
  "schema_version": 1,
  "images": {
    "tile.floor": {"path":"tiles/floor.png","display_size":[64,64],"pivot":[0.5,0.5],"optional":true},
    "tile.obstacle": {"path":"tiles/obstacle.png","display_size":[64,80],"pivot":[0.5,1],"optional":true},
    "scout.idle.0": {"path":"units/scout_idle_0.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "scout.idle.1": {"path":"units/scout_idle_1.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "scout.attack.0": {"path":"units/scout_attack_0.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "scout.attack.1": {"path":"units/scout_attack_1.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "scout.attack.2": {"path":"units/scout_attack_2.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "scout.death.0": {"path":"units/scout_death_0.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "scout.death.1": {"path":"units/scout_death_1.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "scout.death.2": {"path":"units/scout_death_2.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "dummy.idle": {"path":"units/dummy_idle_0.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "dummy.attack.0": {"path":"units/dummy_attack_0.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "dummy.attack.1": {"path":"units/dummy_attack_1.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "dummy.attack.2": {"path":"units/dummy_attack_2.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "dummy.death.0": {"path":"units/dummy_death_0.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "dummy.death.1": {"path":"units/dummy_death_1.png","display_size":[64,96],"pivot":[0.5,1],"optional":true},
    "dummy.death.2": {"path":"units/dummy_death_2.png","display_size":[64,96],"pivot":[0.5,1],"optional":true}
  },
  "animations": {
    "scout.idle": {"frames":["scout.idle.0","scout.idle.1"],"fps":2,"loop":true},
    "scout.attack": {"frames":["scout.attack.0","scout.attack.1","scout.attack.2"],"fps":8,"loop":false},
    "scout.death": {"frames":["scout.death.0","scout.death.1","scout.death.2"],"fps":5,"loop":false},
    "dummy.attack": {"frames":["dummy.attack.0","dummy.attack.1","dummy.attack.2"],"fps":8,"loop":false},
    "dummy.death": {"frames":["dummy.death.0","dummy.death.1","dummy.death.2"],"fps":5,"loop":false}
  },
  "visuals": {
    "unit.scout": {"idle":"scout.idle","attack":"scout.attack","death":"scout.death"},
    "unit.dummy": {"idle":"dummy.idle","attack":"dummy.attack","death":"dummy.death"},
    "unit.vanguard": {},
    "unit.guard": {}
  },
  "board": {"floor":"tile.floor","obstacle":"tile.obstacle"}
}
```

## assets/skins/war_torn/README.md

````markdown
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
````

## assets/skins/war_torn/manifest.json

```text
{
  "schema_version": 1,
  "images": {
    "battlefield": {"path":"backgrounds/battlefield.png","display_size":[1672,941],"pivot":[0,0],"optional":false}
  },
  "animations": {},
  "visuals": {"unit.vanguard":{},"unit.scout":{},"unit.guard":{},"unit.dummy":{}},
  "board": {"background":"battlefield"}
}
```

## content/scenarios/river_crossing.json

```text
{
  "schema_version": 1,
  "id": "river_crossing",
  "cols": 6,
  "rows": 5,
  "obstacles": [[2,0],[2,1],[3,3],[0,4]],
  "spawns": [
    {"uid":"A2","definition_id":"scout","team":"ally","cell":[1,2],"overrides":{"health":80}},
    {"uid":"A1","definition_id":"guard","team":"ally","cell":[0,3]},
    {"uid":"R1","definition_id":"dummy","team":"enemy","cell":[4,2],"overrides":{"name":"桥头木桩","health":5}},
    {"uid":"R2","definition_id":"dummy","team":"enemy","cell":[5,4],"overrides":{"name":"后卫木桩","health":10,"speed":8}}
  ]
}
```

## content/scenarios/training_ground.json

```text
{
  "schema_version": 1,
  "id": "training_ground",
  "cols": 8,
  "rows": 8,
  "obstacles": [[3,1],[3,2],[3,3],[4,5],[4,6]],
  "spawns": [
    {"uid":"A1","definition_id":"vanguard","team":"ally","cell":[1,1]},
    {"uid":"A2","definition_id":"scout","team":"ally","cell":[1,3],"overrides":{"health":80}},
    {"uid":"A3","definition_id":"guard","team":"ally","cell":[2,6]},
    {"uid":"D1","definition_id":"dummy","team":"enemy","cell":[6,1],"overrides":{"name":"木桩1"}},
    {"uid":"D2","definition_id":"dummy","team":"enemy","cell":[5,4],"overrides":{"name":"木桩2","speed":9}},
    {"uid":"D3","definition_id":"dummy","team":"enemy","cell":[6,6],"overrides":{"name":"木桩3","speed":8}}
  ]
}
```

## content/scenarios/war_torn.json

```text
{
  "schema_version": 1,
  "id": "war_torn",
  "cols": 8,
  "rows": 8,
  "obstacles": [
    [
      0,
      0
    ],
    [
      1,
      0
    ],
    [
      2,
      0
    ],
    [
      3,
      0
    ],
    [
      4,
      0
    ],
    [
      5,
      0
    ],
    [
      6,
      0
    ],
    [
      7,
      0
    ],
    [
      0,
      1
    ],
    [
      1,
      1
    ],
    [
      2,
      1
    ],
    [
      3,
      1
    ],
    [
      4,
      1
    ],
    [
      5,
      1
    ],
    [
      6,
      1
    ],
    [
      7,
      1
    ],
    [
      0,
      2
    ],
    [
      1,
      2
    ],
    [
      2,
      2
    ],
    [
      7,
      2
    ],
    [
      0,
      3
    ],
    [
      7,
      3
    ],
    [
      0,
      4
    ],
    [
      7,
      4
    ],
    [
      0,
      5
    ],
    [
      7,
      5
    ],
    [
      0,
      6
    ],
    [
      7,
      6
    ],
    [
      0,
      7
    ],
    [
      1,
      7
    ],
    [
      2,
      7
    ],
    [
      3,
      7
    ],
    [
      4,
      7
    ],
    [
      5,
      7
    ],
    [
      6,
      7
    ],
    [
      7,
      7
    ]
  ],
  "spawns": [
    {
      "uid": "A2",
      "definition_id": "scout",
      "team": "ally",
      "cell": [
        1,
        4
      ],
      "overrides": {
        "health": 80
      }
    },
    {
      "uid": "A1",
      "definition_id": "vanguard",
      "team": "ally",
      "cell": [
        1,
        6
      ]
    },
    {
      "uid": "A3",
      "definition_id": "guard",
      "team": "ally",
      "cell": [
        2,
        6
      ]
    },
    {
      "uid": "D1",
      "definition_id": "dummy",
      "team": "enemy",
      "cell": [
        5,
        3
      ],
      "overrides": {
        "health": 5
      }
    },
    {
      "uid": "D2",
      "definition_id": "dummy",
      "team": "enemy",
      "cell": [
        6,
        2
      ],
      "overrides": {
        "speed": 9
      }
    },
    {
      "uid": "D3",
      "definition_id": "dummy",
      "team": "enemy",
      "cell": [
        6,
        5
      ],
      "overrides": {
        "speed": 8
      }
    }
  ]
}
```

## content/units.json

```text
{
  "schema_version": 1,
  "units": [
    {"id":"vanguard","name":"先锋","role":"近卫","max_health":100,"attack":10,"defense":5,"speed":12,"movement":3,"visual_id":"unit.vanguard"},
    {"id":"scout","name":"斥候","role":"侦察","max_health":100,"attack":10,"defense":5,"speed":14,"movement":4,"visual_id":"unit.scout"},
    {"id":"guard","name":"卫士","role":"守备","max_health":120,"attack":10,"defense":5,"speed":10,"movement":2,"visual_id":"unit.guard"},
    {"id":"dummy","name":"木桩","role":"训练木桩","max_health":100,"attack":10,"defense":5,"speed":11,"movement":3,"visual_id":"unit.dummy"}
  ]
}
```

## docs/ARCHITECTURE.md

````markdown
# 整体架构与扩展边界

状态：M1–M5 已实施。规则与 Controller 不依赖 Pygame；内容/清单用纯加载器验证，图片由资源层缓存，界面、动画和快照保持职责分离。M5 在不修改运行代码的情况下交付第二场景/外观并验证一致性，见 [M5 验收记录](M5_IMPLEMENTATION.md)。当前接口见 [M4 记录](M4_IMPLEMENTATION.md)，进度见 [TASKS](../TASKS.md)。

后续透视扩展沿用这些边界：`presentation_layout` 与 `perspective_geometry` 为纯布局/数学，`PerspectiveBoardRenderer` 与 `SceneHUD` 是独立表现实现；Game 选择组装，不在旧渲染器/侧栏堆条件。规则与快照完全不感知透视模式。资源与效果复用统一脚底/尺度接口，见 [透视实施记录](PERSPECTIVE_BATTLEFIELD.md)。

最简单的划分：规则决定“能做什么、结果是什么”；协调层决定“接收哪次操作、何时继续”；表现层负责“输入来自哪里、画面怎样显示”。替换图片不应影响伤害，增加技能不应要求改写主循环。

## 现状与目标

现状：`models` 存放运行 Unit、不可变 UnitSnapshot/AttackResult；`content` 读取单位定义与场景 JSON，`scenario` 验证局面；`Board` 管理逻辑地图；`Geometry` 转换坐标；`BoardRenderer`/`Panel` 读取只读视图。`Controller` 管理操作和结算确认，`Battle` 管理规则与纯数据回溯。`asset_manifest` 验证纯清单，`assets` 缓存 PNG/缩放和帧列表；Renderer 更新循环待机，Effects 播放阻塞动画并返回 token。`Game` 组装这些模块，不决定图片路径或玩法。

目标仍使用 Python/Pygame，先维持当前平铺模块结构。模块职责稳定后才考虑按包分组，避免为目录美观改动所有导入。

```text
tactics/
  models.py          运行单位、纯数据单位快照和攻击结果、坐标
  scenario.py        场景定义、验证、初始状态构建
  content.py         JSON 单位定义、生成引用与场景加载
  data_files.py      纯 JSON 校验、重复键拒绝、根目录内路径
  asset_manifest.py  纯资源清单与帧/状态引用验证
  board.py           地图状态、空间查询、路径规则
  battle.py          指令合法性、伤害、行动顺序、回溯
  controller.py      指令入口、选中状态、输入锁定、结算协调
  view_models.py     只读的界面快照与表现事件
  geometry.py        逻辑格与像素坐标转换
  board_renderer.py  地图、单位、血条、高亮、图层
  panel.py           属性面板、按钮绘制及命中动作
  effects.py         伤害跳字、受击/死亡等表现
  assets.py          PNG 原图/缩放缓存、锚点、帧列表与表现形体值
  game.py            初始化、组装、事件循环与退出
```

这些模块均有实际调用方。M4 在既有边界接入外部内容和资源，没有创建消息总线、通用插件注册中心或未使用扩展目录。

## 依赖方向

```mermaid
flowchart TD
  Game[Game 组装与循环] --> Input[键鼠适配 / Panel 命中]
  Input --> Controller[Controller 指令入口]
  Controller --> Battle[Battle 规则与回溯]
  Battle --> Board[Board 地图与路径]
  Board --> Models[Models 纯数据]
  Scenario[Scenario 场景数据] --> Models
  Game --> Scenario
  Controller --> View[只读视图与表现事件]
  View --> Render[棋盘渲染 / Panel / Effects]
  Render --> Assets[AssetManager]
  Game --> Render
  EffectsDone[表现完成通知] --> Controller
```

箭头表示调用或数据交付，规则不会反向读取画面。表现完成通知仅用于交接确认，不授权表现层扣血或改变回合。

| 区域 | 可以依赖 | 不应依赖 |
| --- | --- | --- |
| models / scenario / board / battle | 标准库与同层纯数据、规则 | Pygame、窗口、图片、文件播放时间、按钮布局 |
| controller / view_models | 规则、数据、一个很小的表现接口 | Pygame 事件、Surface、Rect、Font、渲染器实现 |
| geometry | 场景尺寸和布局参数、基础数值类型 | 战斗合法性、伤害和资源加载 |
| renderer / panel / effects / assets | Pygame、只读视图、资源与布局 | 改写 Unit/Battle、自己计算第二套移动或攻击规则 |
| game | 组装上述模块、适配操作系统输入 | 重复实现指令校验、伤害或回溯 |

M1–M4 的规则、协调、快照、数据加载和渲染/资源边界已有测试；核心、内容和纯清单可在无第三方包的环境运行。AssetManager 与真实图片/动画需要 Pygame 显示环境。

## 数据模型

### 定义与状态分开

| 数据 | 内容 | 生命周期 |
| --- | --- | --- |
| UnitDefinition | 定义 ID、名称、基础属性、外观 ID；后续可关联技能定义 | 场景加载时读取，战斗期间按只读数据使用 |
| UnitState | 实例 UID、定义 ID、阵营、格子、当前/最大生命和实际属性 | 由规则修改，进入回溯快照 |
| ScenarioDefinition | 场景 ID、逻辑尺寸、地形/障碍、生成位置、单位定义引用 | 加载并验证后构建 Board/Battle |
| BattleState | 轮数、行动槽位、阶段、存活状态、结果、规则新增状态 | 统一变更、统一回溯 |
| PresentationState | 选中 UID、镜头、按钮悬停、动画进度、渲染代次 | 应用/表现层管理，不进入规则快照 |

当前 UnitDefinition 包含定义 ID、基础属性及 visual_id，JSON 生成记录引用 definition_id 并可覆盖少量实例值。Unit/UnitSnapshot/View 保存 definition_id，表现层按定义映射到 visual_id，再从清单选择图片/动画。规则不查询文件或外观。暂不增加技能定义/装备等未使用注册类型。

UID 在同场战斗中唯一且不会因死亡或队列压缩而重新编号。资源 ID、定义 ID 和场景 ID 与文件名解耦。不要用中文名称、像素位置、数组下标或图片路径关联战斗对象。

场景验证至少覆盖坐标边界、重复 UID、出生格重叠、障碍冲突、定义缺失、生命上下限和有效阵营。空阵容、单方阵容和初始死亡单位应有明确的拒绝或结束策略；不能隐含依赖“队列第 0 个一定可行动”。

### 地图与屏幕分开

Board 使用场景中的行列数，位置一律为从 0 开始的 `(列, 行)`。Geometry 接收原点、格子像素大小和行列数，返回数值坐标/边界，Pygame Rect 在表现层构造。

默认仍是 8×8、64 像素格子。使尺寸可注入不等于本次增加自由缩放、镜头或地图编辑功能。精灵可比格子大，不能因此改变移动距离、阻挡和鼠标落格规则。

## 指令、结果与只读视图

Controller 接收逻辑操作，如选中 UID、`move_to(cell)`、`attack(target_id)`、跳过、结束行动、回溯。鼠标像素和键盘码先在输入适配处转为这些操作；Panel 对外提供 `hit_test(position) -> UIAction | None`，不公开按钮矩形供主循环逐个判断。

规则层保留唯一的校验与结算实现。操作结果应明确成功/失败及原因，非法指令不消耗机会、不改变状态，也不创建攻击动画。后续 AI 同样调用该入口，不能直接修改单位坐标和生命。

视图建议至少包含以下纯数据，具体类型按迁移阶段落地：

```text
BattleView
  revision / presentation_generation
  board: rows, cols, terrain, obstacles
  units: tuple[UnitView(uid, cell, team, hp, max_hp, stats, visual_id)]
  active_uid, selected_uid, phase, round_number, winner
  move_cells, attack_cells, target_cells: frozenset[Cell]
  order_uids, log_entries, can_undo, input_locked

AttackResolved
  resolution_id, actor_uid, target_uid, target_cell
  damage, previous_hp, current_hp, killed
```

DTO 不保留可变 Unit/Battle 引用；嵌套集合也使用只读形式或独立副本。`frozen` 数据类中的可变对象不会自动变为只读。Renderer 只显示计算好的可达格与目标格，不调用 Battle 查询合法性。

实际接口：`get_view_state()` 返回 BattleView，其中 `board` 是 BoardView，`units` 是完整阵容的 UnitView 元组，`active/selected` 是独立 UnitView，`order` 仅包含存活单位。日志使用双语元组，按钮提供可用状态，另有 input_locked、presentation_generation 和可空 pending_resolution。M4 在单位显示值中保留 definition_id；visual_id 由 Game 装配的定义映射交给 AssetManager，不让 Controller 读取美术清单。

Controller 的 `select/move_to/attack/click_cell/handle_action/undo` 返回 ActionResult，包含 `accepted` 与失败 `reason`，支持布尔判断。显式移动/攻击提交给当前行动者，不依赖查看对象；鼠标 `click_cell` 额外保留“查看行动者时才尝试移动/攻击”的交互策略。二者最终调用同一 Battle 校验。UIAction 仅包括跳过阶段、结束行动、回溯。

初期不用全局消息总线。普通函数调用、返回值和一个有明确消费位置的事件列表即可。日志最终可从结构化结果格式化，避免规则到处拼接界面文字；第一轮迁移保留现有双语显示行为。

## 动画与结算协议

保持现有语义：合法攻击立即计算生命和击杀，进入 resolving；表现层根据结果绘制跳字与死亡形体；协调层收到有效完成通知后调用规则交接一次。

Game 在启动时将表现适配器交给 Controller。M3 接口为 `play_attack(AttackPresentation)/update(elapsed)->tuple[ResolutionToken,...]/clear()`：播放结果、逐帧更新并返回完成通知、清除旧表现。规则不导入适配器，协调层不导入 Pygame。未传适配器时使用 NullPresentation，攻击仍先进入 resolving，再在下一次 update 返回通知并交接。

AttackResult 包含结算编号、双方 UID、目标位置/阵营、伤害/生命变化及击杀标记，M4 补充双方 definition_id 和 actor_cell，供表现选择素材和位置。AttackPresentation 组合 token 与独立结果。Controller.update 消费通知并匹配确认，不以 Effects.busy 为交接条件；没有把显示帧或路径写入结果。

每次结算有编号，每次回溯/重开场景提升表现代次。只有当前代次、当前结算的完成通知有效，重复通知无效。动画播放不改变已结算的伤害；待机循环和环境特效不是阻塞任务，不参与行动交接的等待。

结算编号由 Battle 分配，合法攻击才消耗编号，同一 Battle 内单调递增且不回溯。代次由 Controller 管理，成功回溯及程序化 restart 先提升代次、清空待确认，再清理表现和恢复规则。restart 重建同一 Scenario 的战斗，允许结算编号从 1 开始，但旧代次通知不能命中新战斗。当前没有玩家重开菜单；一个表现适配器属于一个 Controller 生命周期。

死亡的规则状态与临时死亡形体分开：状态可已判定死亡，表现保留该位置的短暂形体，播放完成后销毁。回溯必须先使旧表现失效，再恢复规则状态并重建视图，不保留重复的死亡形体或伤害数字。

## 回溯与未来存档

当前内存快照为不可变 TurnSnapshot：完整 UnitSnapshot 元组、order_uids、index、round_number、phase、双语 log 元组和 winner。每个 UnitSnapshot 覆盖 Unit 的所有字段，不含活动实体、字典、字体或图片。回溯创建新 Unit，并按 UID 重建原入口顺序槽位；不因死亡压缩槽位，也不依赖快照前的对象身份。跨回溯的调用方必须按 UID 重新查询。

快照明确包含轮数、队列槽位、阶段、战斗结果、单位状态及日志所需数据。新增规则字段必须同时说明初始值、修改者、快照和恢复行为；将来引入随机规则时再将相应随机状态纳入快照。

历史仅在单位行动开始或战斗结束时记录，不支持恢复到 resolving 中途；待结算在这些边界必为 None。场景尺寸/障碍是当前不可变配置，不在每个行动快照重复保存。结算计数器、表现代次、待确认 token 属于不回溯的协议身份，不进入规则快照；以后引入可变地形或其他状态时再显式扩展快照。

图片缓存、动画帧、字体和显示时钟不得进入快照。选中状态在恢复后按现有规则重置到当前行动者。快照不是直接 pickle 整个对象图；如以后新增持久化，再基于已验证的纯数据格式增加 schema_version、内容版本和迁移策略。

## 内容和美术边界

当前 content/ 存放 schema_version=1 的单位定义和场景，assets/manifest.json 存放图片、显式帧列表、visual 状态和地砖/障碍映射。解析器拒绝未知字段、重复键/ID、无效引用及越出资源根的路径；AssetManager 在初始化显示后预载与转换 PNG，缓存失败和缩放。细则见 [资源规范](ASSET_GUIDE.md) 与 [M4 记录](M4_IMPLEMENTATION.md)。

默认路径已经使用地砖与斥候素材。SpriteBody 是只在表现层流转的当前帧形体值；Renderer 将单位、障碍和素材死亡形体排序后，再统一画标签、高亮和血条。Effects 继续画最上层伤害字及几何死亡回退。循环 idle 不进入结算队列，可选帧缺失则整段回退，--geometry 完全跳过资源清单。当前无图集、音频、自动重载或美术编辑器。

## 扩展入口

| 后续需求 | 主要扩展点 | 必须先具备的边界 |
| --- | --- | --- |
| 新地图/关卡 | 场景定义、地图加载与验证 | M1；外部数据文件依赖 M4 的内容验证 |
| 单位和地砖美术 | 资源清单、渲染器、图层 | M1–M4；不改战斗算法 |
| 动画、音效、镜头反馈 | 表现事件、资源、非阻塞播放器 | M2–M4；明确阻塞/非阻塞类别 |
| 技能、Buff、装备 | 规则定义、指令校验、结算结果、运行状态 | M1–M3；新增状态必须可回溯 |
| AI | 查询合法操作、提交同一指令入口 | M2–M3；不得依赖屏幕与模拟点击 |
| 存档/回放 | 纯数据快照、内容版本、序列化 | M3；明确版本和恢复策略 |
| 多窗口尺寸或不同显示比例 | Geometry、布局、渲染资源缩放 | M1；逻辑格子不跟随图片像素变化 |

这张表是开发入口，不是新增功能承诺。任何新需求先选择最小必要前置能力，再与需求一起交付，避免以“架构还没完成”为由无限延后。
````

## docs/ARCHITECTURE_REVIEW.md

````markdown
# 架构整改意见评审

状态：M0 历史评审，基线为 `ff67755` / `v0.1.0`。下文源码事实对应评审时的结构；后续 M1–M4 已实施，当前进度与验证见各阶段记录、[M4 实施记录](M4_IMPLEMENTATION.md) 和 TASKS。

评审材料：[用户提供的原报告](references/architecture_proposal.md)。本文将原报告中的建议与已经实现的能力分开记录。

## 结论

原报告的主要判断准确，适合作为渐进重构的起点。建议采纳“规则、应用协调、表现与资源分离”的方向，并补齐数据身份、回溯与动画协议、资源制作规范、功能开发准入和逐阶段验收。当前原型无需推翻，也不需要先建设通用游戏引擎。

M0 交付的是整体规划和后续开发约束，当时不包括运行代码重构。后续已完成 M1–M5：边界与纯数据迁移、内容/图片动画链路，以及第二场景/外观扩展和阶段交付链路；实际结果见各阶段实施记录和 TASKS。

## 对照源码的判断

下列位置对应上述基线，后续迁移后以 [整体架构](ARCHITECTURE.md) 为准。

| 原意见 | 源码事实 | 评审决定 |
| --- | --- | --- |
| 棋盘逻辑与渲染混合 | `board.py` 导入 Pygame；`reachable_cells` 处理路径，`draw` 同时查询 Battle、绘制范围与单位 | 采纳，优先拆分；逻辑尺寸也应由场景提供，不能仅移动绘图函数 |
| 主循环承担业务协调 | `game.py` 处理按钮矩形、调用攻击、读取 `pending_attack`、创建特效、决定动画后交接 | 采纳，新增协调层；它仍复用 Battle，不复制第二套伤害和回合规则 |
| 场景与 Board 绑定 | `Board.__init__` 直接创建双方单位；障碍和阵容放在 `models.py` | 采纳，先用简单场景数据注入，再按实际需要增加 JSON 加载 |
| 缺少资源加载中心 | 当前没有图片加载与缓存模块，全部使用程序绘制 | 采纳；第一批图片必须实际接入渲染器，不能只新增无人调用的管理类 |
| UI 布局向外泄露 | Game 直接访问侧栏的三个按钮矩形 | 采纳，UI 返回动作标识，应用层不认识按钮坐标 |
| 增加只读视图 | panel 与 board.draw 都直接拿到可变 Battle/Unit 对象 | 采纳；只读需要包含完整的数据结构，`frozen=True` 包着 Unit 引用并不等于只读 |
| 保留现有回归检查 | 当前 41 项测试覆盖了路径、战斗、动画、回溯和字体 | 保留行为覆盖；迁移测试入口和夹具是允许的，不应为保留旧字段访问而保留架构漏洞 |
| 第四阶段完善测试文档 | 逐层拆分会改变接口、导入路径与测试夹具 | 调整为每个阶段同时增加边界测试和更新文档，最后再做整体验收 |

## 必须补充的设计

### 1. 稳定 ID、定义数据与运行状态

当前已经有 `uid`，但攻击结果和快照仍保存 Unit 对象引用。它们支持现有内存回溯，却不能直接当作存档或回放格式。后续需要区分单位实例 ID、单位定义 ID、场景 ID 和外观 ID；图片、名称或列表下标均不应成为规则关联键。

先定义纯数据契约，再迁移快照。不要为了将来可能需要的存档，现在就加入磁盘存档界面。

### 2. 回溯是所有新状态都必须遵守的约束

技能冷却、状态效果、召唤物、地形变化等一旦加入，必须说明回溯时如何恢复。资源缓存、选中高亮和动画进度属于表现状态，不能混入战斗快照；回溯后应重建视图并清除过期动画。

当前“回到上一单位行动开始前”的语义必须保留，包括撤销当前单位未完成的操作、恢复被击杀单位和战斗结束状态。

### 3. 动画完成通知不能直接决定战斗规则

原报告允许暂留 `resolving`，这一点合理。当前阶段继续保持“先扣血，再播放动画，最后交接行动”。协调层负责输入锁定和完成确认，动画只上报结束。

迁移时应使用结算编号与表现代次识别完成通知。过期或重复通知不能推进另一次行动。待机循环、装饰粒子等非阻塞表现不能让战斗永久停在结算阶段。

### 4. 资源接入需要规范和实际验收

除加载与缓存外，还需要明确素材尺寸、透明背景、脚底锚点、图层、动画帧、缺失回退、路径根目录和来源信息。否则“有 AssetManager”仍不能保证美术替换时不改规则代码。

应以“替换一名单位的外观和一块地砖，不修改 Battle/Board，仍能移动、攻击、死亡并回溯”为验收实例。当前几何图形继续作为默认回退，不要求立即引入正式美术。

### 5. 为后续功能建立明确入口

新地图、技能、AI、装备和存档各自依赖不同基础能力。不要每次新增功能都直接修改 Game 或给 Unit 随意挂字段。开发前先填写扩展点、状态归属、回溯策略、资源需求和测试证据，具体见 [功能开发规范](FEATURE_DEVELOPMENT.md)。

## 优先顺序

1. M1：拆开纯规则、场景、几何转换和棋盘渲染。
2. M2：统一指令入口、只读视图、UI 动作与协调流程。
3. M3：稳定结果数据、纯数据快照和动画完成协议。
4. M4：资源清单、缓存和第一条可验证的美术接入链路。
5. M5：扩展演练、跨平台回归、真实窗口检查与开发准入落实。

各阶段依赖、验收和拆分提交见 [实施路线](ROADMAP.md)。M0 的评审结论保留供迁移对照，M1 的实际实现与测试证据单独记录。

## 暂缓

不在架构整改中同时加入技能玩法、AI、存档界面、联网或更换引擎。不先引入 ECS、全局事件总线、插件加载器、通用依赖注入框架或完整编辑器。出现实际需求后，再根据扩展成本决定是否需要进一步抽象。
````

## docs/ASSET_GUIDE.md

````markdown
# 美术、动画与资源接入规范

状态：M4 已实施 PNG、显式帧列表、锚点、加载/缩放缓存及几何回退；真实配置见 [manifest](../assets/manifest.json)，运行与限制见 [M4 记录](M4_IMPLEMENTATION.md)。图集切帧、move/hit 素材状态、音频和热重载尚未支持。

目标是让美术可以在约定接口内替换，同时保持格子规则、单位属性和回溯不变。正式美术风格、画幅和角色设定留给后续需求，本文件不提前限定视觉风格。

## 资源与规则分开

当前目录与后续扩展位置：

```text
content/
  units.json             单位定义、基础属性、外观 ID
  scenarios/             地图尺寸、障碍与阵容
assets/
  manifest.json          外观 ID → 文件、帧、锚点
  tiles/
  units/
  # obstacles/ effects/ ui/ 按实际资源需求再创建
  README.md              资源来源与制作约定
```

目录在实际接入时创建，不用空目录冒充资源支持。`content/` 只表达规则；`assets/` 只表达表现。一个单位的图片替换不改变占格、阻挡、阵营、生命或伤害。

使用小写英文点分 ID，如 `unit.scout.idle`、`tile.floor`。实例 `A2` 引用单位定义，定义引用外观，外观再引用资源 ID，不把 `A2.png` 作为规则关联约定。

## 静态图片与锚点

第一轮支持 PNG，角色和特效使用 RGBA 透明背景。默认棋盘格仍为 64×64；素材原始分辨率可更高，统一由资源层生成显示尺寸，渲染器不在每帧重复缩放。

锚点是图片内的相对位置，不是单位逻辑位置。例如角色使用 `(0.5, 1.0)` 脚底中心，将该点对齐格子底部中心；地砖可使用中心锚点。画布留白与实际角色尺寸由美术规范记录，不通过改变单位 cell 补偿对齐。

角色可以高出格子，选中和点击仍按逻辑格子计算。血条、高亮和伤害字在专门图层绘制，不能被大精灵遮住。

当前 schema_version=1，完整根对象要求 images、animations、visuals、board。以下展示图片条目；其余字段与完整示例见实际 manifest 和 M4 记录：

```json
{
  "schema_version": 1,
  "images": {
    "tile.floor": {
      "path": "tiles/floor.png",
      "display_size": [64, 64],
      "pivot": [0.5, 0.5],
      "optional": true
    },
    "unit.scout.idle": {
      "path": "units/scout_idle.png",
      "display_size": [64, 96],
      "pivot": [0.5, 1.0],
      "optional": true
    }
  },
  "animations": {},
  "visuals": {},
  "board": {"floor":"tile.floor"}
}
```

路径相对资源根目录解析，与启动命令所在目录无关。解析后的文件不得越出资源根目录。业务代码不拼接 `E:\...` 等机器路径，也不散落图片文件名。

## 动画契约

当前角色外观支持 `idle / attack / death` 状态映射；idle 可是单图或循环动画，attack/death 必须是非循环动画。move/hit 待实际需求再扩展，不要求首批素材拥有全部状态。

当前动画条目为 frames（图片 ID 列表）、fps、loop；帧尺寸/锚点/缺失策略由所引用图片条目指定。有实际图集素材后再加入切帧，避免一次实现多套未使用格式。

- idle 可以循环，是非阻塞表现。
- attack、death 按一次播放处理，沿用结算编号与表现代次完成确认；未来 hit 应遵循同一约束。
- death 最后进入隐藏，不回到 idle。规则中已死亡的单位不得因动画循环重新出现。
- 攻击伤害仍在合法指令结算时计算。素材中的打击帧可对齐跳字和闪光，但不自行决定伤害或多扣一次生命。
- 攻击结算等待关联的阻塞表现完成；待机、环境装饰、可选镜头反馈不能无限延长回合。
- 缺失攻击/死亡帧时使用明确的几何效果回退，仍只发送一次有效完成通知。
- 回溯时终止旧代次的动画、伤害字和临时死亡形体，恢复后的活单位使用正常外观。

后续音效沿用表现事件入口，不通过音效长度决定伤害和回合；未实际接入前不增加音频依赖。

## 加载和缓存

AssetManager 集中解析清单、加载原图、生成缩放/切帧结果。初始化和图片格式转换发生在 Pygame 显示环境准备后，规则与场景解析不要求窗口存在。

原图按解析后的路径缓存（含失败），派生 Surface 按路径/目标尺寸缓存，Sprite 按资源 ID/目标尺寸保留各自 pivot，Clip 按动画 ID/比例缓存。重复请求不读盘或缩放，不同显示尺寸不会误复用；帧列表复用相同图片缓存。clear_cache/preload 是显式开发入口，不提供热重载菜单或文件监视。

几何 fallback 由 renderer/effects 提供，不能让资源管理器创建或修改 Unit/Battle。

| 异常 | 处理约定 |
| --- | --- |
| 可选图片缺失、无法解码 | 返回明确缺失信息，记录资源 ID/路径一次，使用约定几何回退 |
| 场景引用不存在的单位定义、清单结构错误、重复 ID | 初始化时报出位置与原因，不静默构造错误战斗 |
| 必需资源缺失 | 初始化时报出清晰错误，不在绘制到某帧才随机崩溃 |
| 中文系统字体不可用或扫描异常 | 保留现有系统字体优先与内置字体/英文回退，不因资源整改删除该修复 |

## 图层顺序

透视模式使用 `board.background` 引用必需 PNG（optional=false、pivot=[0,0]），native/display 尺寸须匹配 presentation.reference_image_size。整图仅按 contain 缩放并缓存，不平铺、不按深度尺度重复缩放。四角在原图坐标系，背景、网格、拾取共用同一变换；角色/障碍预载有限深度尺度。角色脚底为投影站立点，按屏幕 Y/稳定 UID 排序，HUD 最后绘制。实际例子见 [透视战场](PERSPECTIVE_BATTLEFIELD.md)。旧 floor/obstacle 入口继续可用。

1. 地砖、地面装饰。
2. 移动/攻击范围与目标格提示。
3. 角色与障碍阴影。
4. 障碍、单位、临时死亡形体，按脚底高度和稳定 ID 排序。
5. 当前行动者/选中高亮、血条。
6. 战斗闪光、伤害文字等上层反馈。
7. 侧栏与其他 UI。

具体视觉风格可调整，但调整图层不能改变点击落格与战斗校验。资源说明记录作者、来源、许可信息、原始尺寸、显示尺寸和锚点，便于团队后续替换与发布。

## 首次接入验收

- 无图片文件时，当前几何模式仍可启动、移动、攻击、击杀、回溯和退出。
- 用一张测试地砖和一个测试单位图片接入实际 renderer，替换只涉及清单与资源。
- 同一文件通过多个资源 ID 请求也只加载一次；缩放和帧列表缓存分别命中。图集切帧不在当前验收范围。
- 从不同工作目录启动也能定位资源，缺失和损坏文件有可定位结果。
- 大于格子的精灵、透明边缘和脚底锚点显示正确；高亮、血条和跳字可读。
- 击杀后形体消失，回溯后单位恢复，旧动画完成回调不推进新行动。
- 自动化负责路径、缓存和状态；真实窗口另查透明度、缩放、图层和动画观感，不以单个像素哈希代替跨平台视觉检查。
````

## docs/EXTENSION_EXERCISE.md

````markdown
# M5 扩展演练：渡口与 dusk 外观

这次只添加数据、素材、工具、文档与验收测试。`main.py`、`tactics/*.py`、原单位定义和原场景不变；不复制 Board/Battle，不在 Game 按场景名分支。

## 第二场景

[river_crossing.json](../content/scenarios/river_crossing.json) 使用已有 schema_version=1：6×5，四处障碍，斥候/卫士与两只木桩，共用 [units.json](../content/units.json)。生命、速度和名字的实例覆盖使用既有 overrides。默认训练场仍为 8×8、双方各三人。

```powershell
.\.venv\Scripts\python.exe main.py --scenario scenarios/river_crossing.json
.\.venv\Scripts\python.exe main.py --scenario scenarios/river_crossing.json --geometry
.\.venv\Scripts\python.exe main.py --scenario scenarios/river_crossing.json --assets assets/skins/dusk
```

开局 A2 在 `(1,2)`，生命 80/100；移动到 `(3,2)`，攻击右侧 R1（生命 5），实际伤害 10。R1 动画后消失并跳过行动，轮到 A1。回车结束 A1、再回车结束 R2，进入第二轮 A2。移动到 `(5,3)` 攻击下方 R2（生命 10），蓝方胜利。此时连续四次退格，依次回到第二轮 A2、第一轮 R2、第一轮 A1、最初 A2，木桩复活、位置和血量恢复。内部坐标从 0 开始；侧栏坐标从 1 开始。

这是一条便于检查击杀和回溯的演练路线，数值不代表平衡设计；红方仍由玩家手动操作。

## 第二套外观

[dusk/manifest.json](../assets/skins/dusk/manifest.json) 自包含地砖、障碍、斥候和木桩的 17 张 PNG。切换资源根，不修改 definition_id 或 visual_id。未配置图片的卫士/先锋继续几何回退；缺少可选图片按既有规则回退。

同一 dusk 外观也可用于原训练场：

```powershell
.\.venv\Scripts\python.exe main.py --assets assets/skins/dusk
```

人物显示 64×96、脚底锚点 `(0.5,1)`，占格始终一格。斥候待机循环不阻塞；攻击与死亡仍经 M3 token 确认，不把图片或动画时钟写入规则快照。来源与重建见 [dusk 说明](../assets/skins/dusk/README.md)。

## 可以直接复用的流程

新增关卡时复制一个 JSON，保留已支持的字段，用现有定义与 overrides，运行纯内容检查和实际入口。新增美术时复制自包含资源根，修改 manifest 的图片、尺寸、pivot、帧与 visual 状态，检查加载和真实窗口，再比较相同指令的 BattleView。

需要新增玩法字段时，先填写 [功能模板](templates/FEATURE_TEMPLATE.md)，明确规则、初始化、回溯、只读结果与表现边界；不能仅在 JSON 增加解析器不认识的字段。现有解析器会拒绝未知字段。

## 自动验收

[test_milestone.py](../tests/test_milestone.py) 对两张地图 × 三种模式执行相同输入，比较每个观察点的完整不可变 BattleView，包含移动范围、单位属性、血量、队列、日志、阶段、轮数、胜负、代次与结算 token。另检查伤害字、死亡表现、输入锁定、表现清理、旧通知、字体扫描异常及其他工作目录下的真实 CLI 入口和 QUIT。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_milestone.py -v
```

![dusk 渡口开局](../artifacts/m5_dusk_initial.png)

![dusk 击杀与跳字](../artifacts/m5_dusk_death.png)

![连续回溯后复活](../artifacts/m5_dusk_revived.png)
````

## docs/FEATURE_DEVELOPMENT.md

````markdown
# 后续功能开发规范

本规范与 [AGENTS.md](../AGENTS.md) 一起约束后续开发。目标是让每次新增功能都继续积累可维护性，而不是让主循环和 Unit 对象不断堆叠特殊分支。

可直接复制 [功能变更模板](templates/FEATURE_TEMPLATE.md)。仅新增关卡或美术时，参考已经交付的 [M5 扩展演练](EXTENSION_EXERCISE.md)，优先使用现有 JSON/PNG 入口。

当前基础能力仍以 [TASKS.md](../TASKS.md) 的实现状态为准。遇到尚未就绪的边界，先补齐需求所需的最小前置并一并交付，不把规划中的模块当成现成 API，也不为形式要求所有阶段一次完成。

## 开始编码前

在任务或变更说明中写清下面的最小设计。普通小改动用几句话即可，不需要每次另写长文或额外询问用户确认。

```text
需求与玩家可见行为：
前置架构能力及当前状态：
规则入口与合法性校验：
新增数据、唯一归属及初始化：
回溯/死亡/战斗结束时怎样处理：
界面、资源、动画及缺失回退：
验证方法与文档更新：
```

同一数据应有一个权威修改入口：初始状态由场景构建；战斗状态由规则改变；选中和交接由协调层组织；图片与动画由表现层管理。

## 必须遵守的边界

1. 新玩法通过规则与 Controller 指令入口实现，Renderer、Panel、动画和未来 AI 不直接改生命、位置、回合或历史。
2. 不把 Surface、Rect、Font、图片路径、动画时钟写入规则模型和回溯快照。核心新增代码不得导入 Pygame。
3. UI 与 AI 共用合法性校验，非法操作不消耗行动，不创建副作用。不得为某一输入方式复制一套规则。
4. 新规则状态必须有初始值、修改者、死亡/移除行为和回溯恢复方案。恢复后形成同一逻辑局面，不能只恢复画面。
5. 交给 UI/动画的是独立只读数据或结果事件，不是活动实体引用。延迟完成通知需匹配当前结算与表现代次。
6. 新外观走资源清单与缓存，不在每帧加载图片，不通过精灵尺寸、颜色或透明度决定阻挡和攻击距离。
7. Game 保持生命周期和适配职责。仅换一张图片、增加一个技能或加入一个地图，不应持续增加主循环中的玩法分支。
8. 不建立无调用者的抽象、空的扩展目录、第二套战斗状态或过期兼容层。若引入新接口，应能指出当前调用方与验证例子。

现有耦合按 M1–M4 逐步迁移；不能以“旧代码已经这样”为由继续增加相同依赖。

## 典型功能怎样接入

| 功能 | 应做 | 应避免 |
| --- | --- | --- |
| 新角色 | 数据定义 + 实例 ID + 外观引用，验证属性和出生位置 | 在 Game 中按角色名字写特殊分支 |
| 新地图 | 新场景数据，通过同一个构建器初始化 | 复制一份 Board 类或改全局格子数来切场景 |
| 范围技能 | 规则层计算合法范围和目标，返回命中结果，UI 仅显示 | 用红色高亮格是否存在判断是否能造成伤害 |
| Buff/冷却 | 规则拥有持续时间、触发时机与快照字段 | 让动画计时器控制 Buff 剩余回合 |
| 召唤/复活 | 稳定实例 ID、队列规则、占格验证与完整快照 | 只向渲染列表追加图片，回溯时丢失单位 |
| AI | 查询纯数据状态、选择合法指令并提交 | 导入窗口、模拟鼠标、直接改坐标绕过移动次数 |
| 新美术 | 清单、锚点、图层和动画映射，保留 fallback | 在 Battle 中访问文件或保存帧对象 |
| 存档 | 版本化纯数据和恢复验证 | pickle 包含窗口、字体与可变对象引用的整个游戏 |

这是一张归属表，具体玩法必须由真实需求确定；本次不实施这些功能。

## 测试要求按修改内容选择

- **规则变化**：正常与非法操作、边界和敌我限制、状态无副作用、死亡及行动顺序。
- **新增状态**：行动前后和回溯后的逻辑状态对照；跨轮、死亡、战斗结束；涉及随机性时覆盖可重现状态。
- **协调变化**：动画锁定、重复/过期完成通知、取消旧表现、输入与 AI 使用同一入口。
- **资源变化**：缓存、尺寸、路径、缺失/损坏处理；真实窗口检查锚点、图层和透明背景。
- **规则边界迁移**：在不安装/禁止导入 Pygame 的独立进程测试核心；读 DTO 不能改动核心状态。

只为新增契约和真实风险增加测试，不为文件改名或普通文档调整堆叠镜像测试。旧 41 项检查的行为覆盖要保留；接口迁移时调整夹具，不把原测试的字段访问当成永久公开 API。

## 合并与发布前的完成条件

- [ ] 前置能力实际存在；新增模块有真实调用；依赖符合 [整体架构](ARCHITECTURE.md)。
- [ ] 玩家要求的行为已实现，非目标玩法未被顺带修改。
- [ ] 新状态和异步表现经过回溯、死亡和交接检查。
- [ ] 自动化验证通过；需要观察的真实窗口结果单独说明。
- [ ] TASKS 的完成/未开始状态、CHANGELOG 和 README 与实际一致。
- [ ] `python scripts/export_source.py` 及 `--check` 通过，相关文档链接有效。
- [ ] 不提交环境、缓存或凭据；资源与来源说明随交付维护。
- [ ] 结构性修改使用专用分支，分阶段审查差异；版本发布对应通过验证的提交。

CI 能自动检查的边界在相应迁移阶段加入，不宣称现在已有完整架构检查器。涉及不可逆接口或数据格式变化时，补一份简短决策记录，包含选择、取舍、迁移和回退办法；没有这类变化时不增加形式化流程。
````

## docs/M1_IMPLEMENTATION.md

````markdown
# M1 实施与验收记录

状态：代码和本机验收完成。评审前基线为 `b072548`；实施分支为 `refactor/m1-rule-render-separation`。远程结果以对应 PR / Actions 为准，任务状态见 [TASKS](../TASKS.md)。

本文件保留 M1 完成时的接口与验收记录。后续 Controller、完整视图与 UIAction 已在 M2 实施，快照与结算确认已在 M3 实施，当前调用方式见 [M2](M2_IMPLEMENTATION.md) 和 [M3 记录](M3_IMPLEMENTATION.md)；下文的“留给 M2/M3”属于当时阶段边界。

## 范围和结果

本阶段完成场景、逻辑地图、数值几何和棋盘绘制分离，没有增加玩法，没有改动 Battle 的伤害、行动顺序或回溯算法。默认 8×8、64 像素、6 名单位与 5 个障碍保持原样。

| 模块 | 实际职责 |
| --- | --- |
| models.py | 可变的 Unit 运行状态，不再决定默认阵容 |
| scenario.py | 不可变 UnitSpawn/Scenario、验证与默认场景；为每局创建新的 Unit |
| board.py | 从 Scenario 接收逻辑尺寸和状态，只提供空间查询、邻格与 BFS；无 Pygame、像素转换和绘制 |
| geometry.py | 纯数值 BoardGeometry，提供 cell_at、cell_rect、cell_center 与 bounds |
| view_models.py | 最小 BoardView/BoardUnitView 与只读棋盘投影，不含活动实体引用 |
| board_renderer.py | 只读取 BoardView 和 Geometry，绘制地格、范围、单位、高亮及血条 |
| game.py | 在组装处选择场景和 Geometry，调用 Renderer；旧输入/动画协调暂留到 M2 |
| panel.py / effects.py | 接收实际棋盘宽高或同一 Geometry，不再使用全局固定地图像素尺寸 |

## 关键决策

### 显式注入场景

`Board(scenario)` 不提供隐式默认场景，只有应用组装处的 `Game()` 使用 `default_scenario()`。测试和后续关卡都使用同一入口，不必修改 Board。

Scenario 将集合与坐标规范为不可变数据。复用场景创建多个 Board 时，单位状态相互独立；场景模板不会随移动、扣血或回溯被改变。

初始化拒绝越界、出生格重叠、障碍冲突、重复 UID、非法属性、空阵容、单方阵容或初始死亡单位。当前仅支持 ally/enemy；初始单位要求 `0 < health <= max_health`，防止进入不存在的首位行动者。这是新增场景 API 的初始化约定，不改变默认场景的玩法。

### 几何与规则独立

Board 的行列数来自场景；CELL_SIZE、侧栏宽度和最小窗口高度仅属于表现默认值。Geometry 返回数字元组，不返回 Pygame Rect。

默认窗口仍为 896×512。小于 8 行的注入场景保留至少 512 像素窗口高度，以保证现有侧栏完整；空余区域是背景，不计入逻辑地图。M1 不增加窗口缩放操作或地图选择菜单。

### 提前实现最小棋盘视图

M2 规划了完整 View，但 M1 若继续将 Battle 交给 Renderer，就没有完成绘制边界。因此本次仅提前实现棋盘所需的独立值：单位显示属性、障碍、选中/行动 UID、合法移动格、攻击展示格和目标格。

`build_board_view` 复用现有规则查询，不复制合法性算法；Renderer 不拿到可变 Unit/Board/Battle。完整 Panel 视图和 Controller 留给 M2，AttackResult / TurnSnapshot 的对象引用迁移留给 M3。

### 不保留旧的像素兼容接口

删除 Board.draw、Board.rect、Board.cell_at。原有测试中的像素操作迁移为 `game.geometry.cell_center(cell)` / `cell_at(pixel)`，没有为了兼容旧测试把 Pygame 放回核心。原 41 项测试的行为覆盖保留。

## 当前可用的场景扩展入口

下例使用的 API 已实现；无需额外数据加载库：

```python
from tactics.board import Board
from tactics.battle import Battle
from tactics.scenario import Scenario, UnitSpawn

scene = Scenario(
    "small", 5, 4,
    (
        UnitSpawn("blue", "Blue", "ally", "test", (0, 0),
                  speed=20, movement=4, attack=17),
        UnitSpawn("red", "Red", "enemy", "test", (3, 0),
                  health=50, speed=5),
    ),
    frozenset(((1, 0),)),
)
board = Board(scene)
battle = Battle(board)
assert battle.move((2, 0))  # 绕过障碍，实际移动 4 步。
assert battle.attack(board.enemies[0])
assert board.enemies[0].health == 33
battle.finish_attack()     # 纯规则调用方明确确认结算结束。
assert battle.undo()
assert board.enemies[0].health == 50
```

如需窗口，在安装 Pygame 后使用 `from tactics.game import Game; Game(scene).run()`。这不是 JSON 场景加载器，外部内容清单属于 M4。

## 自动化验证

```powershell
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_core.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\export_source.py --check
```

本机 Python 3.9.1 / Pygame 2.6.1：原 41 项行为检查加 16 项新增检查，共 **57 项通过**。其中 **12 项核心检查**在 `python -S` 下运行，禁用第三方包路径；独立子进程还明确拒绝导入 Pygame，实际跑通移动、扣血、交接和回溯。

新增覆盖场景不可变与局间隔离、默认数据不变、非法场景拒绝、不同尺寸场景、四方向真实路径、非零原点与不同格子尺寸、边界落格、只读视图、Renderer 不查询规则、图层裁剪恢复以及注入场景的窗口交互。

CI 在安装 requirements 之前执行上述 `-S` 核心检查，再安装 Pygame 执行完整回归。平台继续覆盖 Windows/Linux 与 Python 3.9/3.12。

## Windows 实际窗口与像素对照

使用 `windows` 显示驱动，在改动前、改动后以同一状态和固定动画时间保存画面，将每个画面的 RGBA 字节逐一比较：

| 画面 | 对照结果 |
| --- | --- |
| 默认开局与移动范围 | 逐像素一致 |
| 移动后攻击范围 | 逐像素一致 |
| 攻击后 0.2 秒的伤害跳字 | 逐像素一致 |
| 攻击后交接下一单位 | 逐像素一致 |
| 回溯到上一行动 | 逐像素一致 |
| 击杀后 0.2 秒的死亡动画 | 逐像素一致 |
| 死亡动画结束后消失 | 逐像素一致 |
| 回溯恢复被击杀单位 | 逐像素一致 |

另外在真实窗口跑通 5×4 场景的鼠标事件、攻击 17、生命 50→33、回溯恢复 50 和 QUIT 清理。查看了重构后的伤害、死亡画面和第二场景截图，布局正常。验证通过程序调用和投递事件完成，不是人工逐次点击。

像素对照是本次纯重构的迁移证据，不是以后更换美术必须维持原画面的永久约束；也不宣称不同操作系统的字体会产生相同像素。

![M1 注入的第二场景](../artifacts/m1_custom_scenario.png)

## M1 完成时留给后续的内容

- M2：Controller、完整 UI 视图、UIAction 命中封装（现已完成，见 M2 记录）。
- M3：ID 化结算结果、纯数据快照和结算/表现代次协议（现已完成，见 M3 记录）。
- M4：外部 JSON 内容、AssetManager、图片/动画素材加载。
- M5：完整的后续扩展与资源交付演练。
````

## docs/M2_IMPLEMENTATION.md

````markdown
# M2 实施与验收记录

状态：代码与本机验收完成，2026-10-22。基线为 M1 合并提交 `431b403`，实施分支为 `refactor/m2-controller-view-separation`。远程执行结果以对应 PR / Actions 为准，任务状态见 [TASKS](../TASKS.md)。

本文件保留 M2 完成时的接口与验收记录。M3 已将内部结果/快照迁为纯数据，并以结算编号和代次确认替代 busy 轮询；当前协议及迁移方式见 [M3 记录](M3_IMPLEMENTATION.md)。下文“留给 M3”属于当时阶段边界。

## 范围与数据归属

本阶段只重整操作协调和表现边界，玩家操作、速度顺序、移动范围、100% 攻击伤害、击杀动画及回溯语义保持一致。没有增加技能、AI、存档、图片或新玩法。

| 模块 | M2 实际职责 |
| --- | --- |
| controller.py | 私有持有 Board/Battle、选中 UID；接收操作，协调动画锁定、完成交接和回溯清理 |
| actions.py | UIAction 动作标识；不可变 ActionResult，提供 accepted、失败 reason 和布尔判断 |
| view_models.py | 保留 BoardView，增加完整 UnitView/BattleView 和独立 AttackPresentation |
| panel.py | 只读 BattleView；内部维护按钮矩形，对外 hit_test 返回 UIAction |
| effects.py | 只读 AttackPresentation 的 UID、位置、阵营、伤害、击杀值，维护临时动画 |
| game.py | 场景与模块组装、键鼠到逻辑操作的转换、更新/绘制循环和退出清理 |
| board.py / battle.py | 沿用 M1 代码与唯一规则实现，本阶段没有修改 |

选中状态不进入规则快照；回溯或行动交接后重置到当前行动者。Game 不再提供 board/battle/selected 可变字段，也没有为旧测试保留兼容入口。

## 实际调用链

```text
鼠标像素 ── Geometry.cell_at ── Controller.click_cell
侧栏点击 ── Panel.hit_test ── UIAction ── Controller.handle_action
键盘按键 ── UIAction ────────────────── Controller.handle_action
                                              ↓
                                        Battle / Board
                                              ↓
                           BattleView / AttackPresentation（独立值）
                                              ↓
                              BoardRenderer / Panel / Effects
```

`Controller(scenario, presentation=None)` 显式接收已验证场景。后续 AI、脚本或测试可直接使用逻辑指令，不需要窗口、像素或模拟点击：

```python
from tactics.actions import UIAction
from tactics.controller import Controller
from tactics.scenario import default_scenario

controller = Controller(default_scenario())
assert controller.move_to((4, 4))
assert controller.attack("D2")
assert controller.get_view_state().input_locked
controller.update(0)  # 无窗口适配器在下一次更新完成表现交接
assert controller.get_view_state().active.uid == "A1"
assert controller.handle_action(UIAction.UNDO)
assert controller.get_view_state().active.cell == (1, 3)
```

`select(uid)` 只改变查看对象。显式 `move_to/attack` 始终对当前行动者发指令，合法性由 Battle 校验；鼠标 `click_cell` 保留“先选回当前行动者，再点格子移动/攻击”的原有交互。失败返回 ActionResult(False, reason)，不会消耗行动或创建动画。结束状态下仍能查看存活单位和回溯，已禁用的跳过/结束操作不改变查看对象。

## 只读视图与表现接口

BattleView 一次性构建同一局面的独立值，包含：

- board：尺寸、障碍、存活单位显示值、行动/选中 UID 及合法范围；继续供既有 Renderer 使用。
- units：完整阵容的 UnitView 元组，包含所有属性与位置，保留死亡单位以便查询结算与恢复。
- active/selected：独立 UnitView 或 None；order 仅包含存活单位。
- phase、round_number、winner、双语 log 元组，以及 can_undo/can_skip/can_end_turn/input_locked。

所有视图数据类均 frozen，嵌套集合使用 tuple/frozenset，坐标和日志复制成元组。旧视图不会随移动、扣血、交接或回溯改变；按 UID 比较身份，不要求对象引用相同。Panel 和 Renderer 不接收规则对象，也不自行计算合法范围。

Game 启动时将 CombatEffects 交给 Controller。小型表现接口只有 `play_attack(values)`、`update(elapsed)`、`busy` 和 `clear()`，通过普通对象注入，没有消息总线或空注册框架。Controller 将内部 AttackResult 转成只含值的 AttackPresentation；Effects 从此不再拿到活动 Unit。

合法攻击立即扣血，进入 resolving；所有操作入口在此阶段均被规则/协调层拒绝，QUIT 由 Game 独立处理。Controller.update 更新表现，busy 为假后调用 finish_attack 并选中新行动者；后续重复 update 不再次交接。回溯成功后清空表现并重置选中 UID，失败不清空表现。

未传表现对象时使用 NullPresentation，支持无窗口调用；攻击仍先进入 resolving，在下一次 update 完成。测试另注入可手动保持 busy 的适配器，验证任意长时间都不能越过未结束的表现。

## 迁移与后续开发

测试通过 Scenario/UnitSpawn 构造低血量、最终击杀和 800/1000 生命局面，不再任意改写 Game 内部 Board/Battle。旧 Game.board_click/undo 入口已删除，调用方改为 controller.click_cell/undo；旧 Panel 按钮 Rect 改为 hit_test。

M2 的 AttackPresentation 是当前规则到表现的边界转换。规则内部 AttackResult、TurnSnapshot 仍含实体引用；没有结算编号、表现代次或异步完成通知。下一阶段 M3 在此入口继续迁移内部结果与快照，加入重复/过期通知校验。当前只验证 busy 轮询的单次交接，不宣称已解决未来异步通知协议。

新增操作时先在 Controller 建入口，调用 Battle 的同一合法性校验；新增显示值在 View 构建处复制。新增按钮只改 Panel 布局与 UIAction 映射，不在 Game 中加入玩法分支。图片、字体与动画帧继续只属于表现层，资源清单和缓存留给 M4。

## 自动化验收

本机 Python 3.9.1 / Pygame 2.6.1 / SDL 2.28.4：**75 项检查通过，退出码 0**。原 57 项行为覆盖保留，新增 16 项控制器检查与 2 项侧栏边界检查。

```powershell
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_core.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_controller.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

前两组共 **28 项**，无需第三方包或窗口。核心独立子进程禁止导入 Pygame，实际跑通 Controller 移动、攻击、锁定、交接和回溯；CI 在安装依赖前执行两组检查。新增覆盖深层不可变、旧视图独立、按 UID 操作、非法指令无副作用、全部入口锁定、重复更新单次交接、表现清理、最终击杀恢复、跨轮与双方操作、按钮半开区间及自定义棋盘宽度。导入检查约束 Game/表现模块不直接依赖可变规则对象。

完整 75 项分别通过 dummy 显示驱动和本机 Windows 实际窗口运行。CI 配置覆盖 Windows/Linux × Python 3.9/3.12，远程结果需以 Actions 实际结论为准。

## Windows 画面对照

改动前后使用 `windows` 显示驱动，以相同场景、输入和固定动画时间捕获 RGBA 字节。以下 **13 帧逐像素一致**：开局、查看其他单位、移动后、伤害跳字、下一单位、回溯、敌方回合、英文界面、击杀动画、击杀后消失、回溯复活、战斗结束、结束后回溯。

另外验证攻击结算时 QUIT 正常释放 display/font；5×4 注入场景继续通过真实窗口的点击、攻击 17、生命 50→33、回溯及绘制检查。查看了默认伤害画面，侧栏与禁用按钮布局正常。上述为自动事件和程序调用验证，并非人工逐次鼠标操作。像素基线保存在本机忽略目录 `.delivery/m2-before`、`.delivery/m2-after`，不作为游戏资源提交。

像素一致性只用于本次保行为重构验收，不限制将来更换美术，也不要求不同系统字体产生相同像素。
````

## docs/M3_IMPLEMENTATION.md

````markdown
# M3 实施与验收记录

状态：代码和本机验收完成，2026-10-22。基线为 M2 合并提交 `babeffd`，实施分支为 `refactor/m3-snapshot-resolution-contract`。远程执行结果以对应 PR / Actions 为准，任务状态见 [TASKS](../TASKS.md)。

本文件记录 M3 完成时的接口。后续 M4 已增加 definition_id 及真实资源加载，当前接入方式见 [M4 记录](M4_IMPLEMENTATION.md)；下文“尚未实现资源”属于 M3 当时的边界。

## 结果与范围

本阶段将规则结算和历史迁为独立不可变值，按 UID 恢复单位，并使动画交接匹配结算编号与表现代次。默认阵容、移动、速度顺序、100% 攻击伤害、击杀动画时长与“回到上一单位行动开始前”的语义保持一致，没有增加 AI、技能、磁盘存档或资源加载。

| 数据 / 模块 | 当前实现 |
| --- | --- |
| models.UnitSnapshot | frozen；包含 Unit 全部字段，用 capture/create_unit 在运行实体与独立值间转换 |
| models.AttackResult | frozen；结算编号、行动/目标 UID、目标位置/阵营、完整伤害、前后生命、击杀标记 |
| battle.TurnSnapshot | frozen；单位快照元组、order_uids、index、round_number、phase、双语 log 元组、winner |
| battle.Battle | 合法攻击分配单调编号；finish_attack 必须匹配当前编号；回溯按 UID 重建 Unit 和顺序槽位 |
| view_models.ResolutionToken | frozen；generation 与 resolution_id 的组合身份 |
| view_models.AttackPresentation | frozen；token + result，不含活动实体 |
| controller.Controller | 表现代次、当前待确认 token、验证完成通知、回溯/重开前使旧表现失效 |
| effects.CombatEffects | 更新跳字和死亡形体，阻塞效果全部完成后只返回一次 token；clear 取消待通知 |

Game、Panel、BoardRenderer、Board、Scenario、Geometry 没有增加 M3 玩法分支。Game 仍只调用 Controller.update，无需了解通知和快照细节。

## 快照、身份与恢复

历史在单位行动开始或战斗结束时记录。每个单位的 UID、名称、阵营、职业、坐标、当前/最大生命、攻击、防御、速度和移动力均保存为独立值；集合与坐标使用元组。队列保存原始速度排序的 UID 槽位，包含死亡单位，不因死亡压缩。

恢复时重新创建整份运行阵容，再按 order_uids 关联同一批新 Unit，恢复轮数、槽位、阶段、结果和日志，清空待结算。死亡状态仍由 health 决定，存活查询和路径/队列过滤沿用原规则。旧 Unit 对象不会被重新挂回战斗；外部跨回溯保存对象引用不再有效，应按 UID 查询。测试相应迁移了对象身份断言，原有行为断言保留。

新增 Unit 字段必须同步 UnitSnapshot。字段覆盖测试比较两个数据类的完整字段集合，避免悄悄漏存新属性。新增其他规则状态也必须显式扩展 TurnSnapshot，不能只恢复画面。

不进入快照的内容：

- 场景尺寸与障碍：当前为不可变配置；未来可变地形需要新增恢复字段。
- 结算计数器：属于协议身份，在同一个 Battle 中只增不减；回溯重打得到新编号。
- 表现代次、待确认 token、选中 UID：由 Controller 管理；恢复后选中当前行动者。
- 图片、字体、Surface、动画年龄和效果列表：只属于表现层。

当前历史不保存 resolving 中途，不提供任意时刻恢复 API；记录边界上的 pending_attack 必为 None。快照可通过 asdict 转为基本值并由 JSON 编码，是独立性检查；本阶段没有定义磁盘格式、版本迁移或加载接口。

## 结算与表现完成协议

```text
合法攻击 → Battle 立即扣血并生成 AttackResult(resolution_id, ...)
        → Controller 记录 ResolutionToken(当前代次, resolution_id)
        → Effects 播放 AttackPresentation(token, result)
        → Effects.update 返回已完成 token 的元组
        → Controller.complete_presentation 校验当前代次与当前 token
        → Battle.finish_attack(resolution_id) 再次匹配当前结算
        → 交接一次、清空待确认、选中新行动者
```

错误编号、错误代次、旧回合通知、重复通知或没有待确认时的通知都返回失败，保持当前局面不变。收到一批新旧混合通知时也只接受当前有效的一次。Controller 不再以全局 busy 为完成信号；无完成通知时即使 busy 为假也不交接，未来待机或环境动画持续 busy 也不能拖住已经完成的攻击。

表现适配器的新接口：

```python
play_attack(event: AttackPresentation)  # event.token / event.result
update(elapsed) -> tuple               # 本帧完成的 ResolutionToken；无完成时返回 ()
clear()                               # 取消旧形体、数字和尚未发出的通知
```

当前 CombatEffects 只包含本次攻击的阻塞效果：死亡约 0.65 秒结束，跳字约 0.9 秒结束，二者全部结束后返回一次 token。busy 保留供显示/测试查询，Controller 不读取它。未来接入待机/环境效果时应与阻塞攻击任务分开管理，不能加入攻击完成判定。

NullPresentation 保留无窗口行为：播放后排入一次完成 token，下一次 update 取出并清空。旧适配器如果只实现 busy 或 update 返回 None，必须迁移到此接口，不保留模糊的兼容路径。

## 回溯与重开先作废旧表现

成功回溯时先增加 generation、清空待确认，再调用 clear，最后恢复规则并重置选中。即使 clear 期间旧回调重入，或已在传输中的通知无法取消，旧 token 也已失效。不可回溯时不增加代次、不清理表现。

新增 `Controller.restart()` 是程序化生命周期入口，重建当前不可变 Scenario 的战斗并清理历史。它允许取消结算中的旧表现；新 Battle 编号从 1 开始，但代次已经增加，旧编号相同的通知不能命中新战斗。没有新增玩家快捷键、按钮或菜单。一个表现适配器属于一个 Controller 生命周期；不同 Controller 不共用在途回调。

### 接口取舍、迁移与回退

本次保留平铺模块和普通函数调用，不引入消息总线、ECS 或通用序列化框架。小型 token 返回接口足以支持当前逐帧动画；未来异步完成也走同一 `complete_presentation` 校验，不直接改回合。

迁移：原 AttackResult.actor/target 改为 UID 与值；原 AttackPresentation 平铺字段改为 token/result；原 finish_attack() 改为 finish_attack(resolution_id)；跨回溯对象引用改为按 UID 查找。旧 M2 示例中的 Controller 移动、按 UID 攻击、update、undo 调用仍有效。BattleView 新增 presentation_generation 与 pending_resolution；比较恢复后的逻辑局面时应单独看不回溯的代次。

这些是内部开发接口变更，没有已发布的外部数据格式需要迁移。需要回退整个阶段时可使用 M2 基线 `babeffd` 的完整代码与测试；不要局部恢复旧动画接口或把实体引用重新塞回新快照。

## 验收证据

本机 Python 3.9.1 / Pygame 2.6.1 / SDL 2.28.4：**94 项检查通过，退出码 0**。保留原 75 项覆盖，新增 16 项快照/协议检查与 3 项真实效果通知/清理检查。

```powershell
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_core.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_controller.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_resolution.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

前三组共 **44 项**，在无第三方包环境通过；核心独立子进程明确禁止导入 Pygame。CI 在安装依赖前执行三组，再运行完整回归，矩阵继续为 Windows/Linux × Python 3.9/3.12；远程结果见对应 Actions。

新增检查覆盖：快照深层不可变、完整字段与基本值编码、运行实体变化不污染历史、按 UID 重建全部属性和规范槽位、死亡/跨轮恢复、零伤害/过量伤害与生命变化、编号不回溯、错误/重复/过期完成、回溯重打、结算中重开且编号相同、清理前作废及清理时旧回调、混合通知批次、实际跳字/死亡通知只发一次，以及连续击杀/回溯/重开无重复残留。

完整 94 项分别在 dummy 显示驱动与本机 Windows 实际窗口通过。固定场景、操作和动画时间捕获的 **13 帧与 M2 逐像素一致**：开局、查看、移动、跳字、交接、回溯、敌方回合、英文界面、击杀动画、消失、复活、战斗结束、结束后回溯。额外保留 5×4 场景的实际窗口交互及结算中 QUIT 释放 display/font。验证通过程序调用和自动事件完成，并非人工逐次操作。

像素基线保存在本机忽略目录 `.delivery/m3-before`、`.delivery/m3-after`。本阶段未变动绘图和布局，因此无需新增相同的游戏截图作为素材；后续换美术不受像素一致性约束。

下一阶段 M4 接入内容/资源清单、验证、图片/缩放缓存和真实素材链路；不将当前几何动画称为素材动画加载。
````

## docs/M4_IMPLEMENTATION.md

````markdown
# M4 实施与验收记录

状态：代码和本机验收完成，2026-10-22。基线为 M3 合并提交 `d827ba9`，实施分支 `feature/m4-content-assets`。远程结果以对应 PR / Actions 为准，进度见 [TASKS](../TASKS.md)。

## 结果与边界

默认启动现在实际加载 JSON 单位/场景、资源清单及项目内生成的 PNG，显示地砖和带帽斥候，支持循环待机、非循环攻击/死亡。其他单位与障碍继续使用几何回退；--geometry 完全不加载资源清单。当前没有图集切帧、move/hit 素材状态、音频、自动重载或美术编辑器。

移动、伤害、行动顺序、立即扣血、死亡退出占格/队列、上一行动回溯及 M3 token 确认不变。Unit/UnitSnapshot/View 增加 definition_id，AttackResult 补充双方定义 ID 和行动位置；这些是纯标识/坐标，不含图片路径或播放时钟。新增字段已经纳入快照完整性检查。

| 模块 | 实际职责 |
| --- | --- |
| data_files.py | UTF-8 JSON、重复键拒绝、严格字段/数值/版本检查、安全相对路径 |
| content.py | 不可变 UnitDefinition/GameContent；读取定义、生成记录和覆盖值，调用既有 Scenario 验证 |
| scenario.py | 保留 Python 场景接口；default_scenario() 读取同一默认 JSON，不维护第二份阵容/数值 |
| asset_manifest.py | 无 Pygame 的图片、显式帧列表、visual 状态和 board 引用验证 |
| assets.py | 显示初始化后加载/转换 PNG，缓存原图/缩放/Sprite/Clip，提供锚点与 SpriteBody 表现值 |
| board_renderer.py | 地砖、范围、按脚底排序的障碍/单位/临时素材形体，再统一绘制标签/高亮/血条；更新非阻塞待机 |
| effects.py | 播放攻击/死亡素材或几何回退，维护跳字，阻塞效果完成后返回一次 M3 token |
| game.py / main.py | 组装和启动参数；不硬编码资源文件名、定义 ID 或新玩法分支 |

## 内容格式与身份

`content/units.json` 根字段为 schema_version=1、units 数组；每项必须有 id、name、role、max_health、attack、defense、speed、movement、visual_id。定义 ID 唯一，数值为非负整数（max_health>0），布尔值不能充当整数。

`content/scenarios/*.json` 必须有 schema_version、id、cols、rows、obstacles 和 spawns。生成记录为：

```json
{"uid":"A2","definition_id":"scout","team":"ally","cell":[1,3],"overrides":{"health":80}}
```

overrides 可覆盖 name、health、max_health、attack、defense、speed、movement，不允许未知键。未提供 health 时使用本次 max_health；默认斥候通过实例覆盖保留 80/100。木桩共用 dummy 定义，通过实例名称和速度覆盖保持原阵容。未知定义、重复 UID、出生冲突、越界、非法生命/阵营仍在初始化拒绝。

定义与状态分开：每局复制定义数值创建新的运行 Unit，定义本身不可变，运行中不动态回读 JSON。保存 definition_id 可在回溯后关联同一外观；AssetManager 使用 Game 装配的“定义 ID → visual_id”映射，规则不读取资源清单。

Python 手写 Scenario 仍可构造完整属性，definition_id 默认为空；未绑定外观时使用几何。JSON 生成记录必须引用已存在定义；加载的每个定义都必须有已声明的 visual（空对象 {} 明确表示几何回退），不能用拼错外观 ID 静默隐藏问题。

## 清单与替换流程

`assets/manifest.json` 的 schema_version=1，根字段必须有 images、animations、visuals、board 四个对象。未知字段、重复 JSON 键/跨图片动画 ID、无效引用均拒绝。实际完整示例已随项目交付，不需要生成额外注册代码。

图片条目：path、display_size（两个正整数）、pivot（0–1 相对坐标）、optional（布尔值）。路径相对资源根，使用正斜杠，只支持 .png；绝对路径、Windows 盘符/UNC、反斜杠和解析后越界的路径拒绝，解析也检查符号链接逃逸。

动画条目：frames 是非空图片 ID 列表，fps 为有限正数，loop 为布尔值。visual 可有 idle、attack、death：idle 接单图或循环动画，attack/death 只能接非循环动画。board 可声明 floor、obstacle 图片。未声明的状态使用几何；没有静默接受未知引用。

替换地砖或斥候只需：

1. 将 PNG 放进资源根内，更新图片 path、基准显示尺寸及 pivot。
2. 在 images 中为每个动画帧声明图片，再修改 animations 的 frames/fps；角色通过 visuals 的状态映射选片段。
3. 单位定义保持 visual_id；如果新增一个外观，增加 visuals 条目后修改定义的 visual_id。
4. 重启游戏验证。资源不改变 cell、占格、路径、生命或伤害；没有每帧读文件或热更新菜单。

默认格子 64 像素，清单显示尺寸以此为基准，资源层按 Geometry 比例缩放。单位/障碍/死亡形体将 pivot 对齐格子底部中心，地砖对齐格子中心。斥候画幅 64×96，高出格子但不扩展点击区域；Renderer 按脚底行和稳定 ID 排序形体，最后统一绘制标签/高亮/血条。形体裁剪在棋盘边界，跳字及侧栏仍位于上层。

演示图片均由 [生成脚本](../scripts/generate_demo_assets.py) 绘制，无外部下载；来源、尺寸、锚点及授权说明见 [assets/README](../assets/README.md)。这些是接口验证素材，不是最终美术交付。

## 缓存与失败策略

- 原图以解析后的路径为键，包括缺失/解码失败；多个 ID 引用同一文件也只读取一次。
- 缩放 Surface 以路径和目标尺寸为键；Sprite 以资源 ID/尺寸为键保留不同 pivot；Clip 以动画 ID/比例为键复用帧缓存。
- 初始化显示后预载全部声明图片与片段；重复绘制、待机更新和攻击播放不读盘、不重复缩放。请求新尺寸时只生成一次派生图。
- 可选文件失败按 ID/路径记录一次，缓存 None 并使用几何。任意帧不可用时整个片段回退，避免残缺动画永久锁定结算。
- 必需图片（即使未在当前画面使用）在启动时校验，缺失/损坏立即报错。内容、格式和引用错误同样拒绝，CLI 以 Configuration error 和文件/字段原因退出；资源失败后的窗口会清理。
- clear_cache/preload 提供显式开发期清理/重建入口，不实现文件监视。开发者重载前应取消旧表现，正常使用直接重启进程。

没有 PNG 时保留合法 manifest 可走可选缺失回退；如果连资源清单也不需要，使用 --geometry。几何模式仍需要合法规则内容文件，不能把错误场景静默换成另一个关卡。系统字体扫描异常与英文/内置字体回退保持原样。

## 动画、交接与恢复

Renderer 单独推进循环待机，不影响 Controller/Battle。Effects 在合法攻击后解析 actor_definition_id 对应攻击片段和被击杀目标的 death 片段，画面位置来自独立结果坐标，保持立即扣血。

非循环片段和伤害跳字是本次结算的阻塞任务，全部完成后只发一次原 token。死亡片段结束即移除临时 SpriteBody，不切回 idle；规则中目标已不存在于存活 BoardView。可选素材缺失时使用原几何死亡形体与跳字，仍按 M3 确认。回溯/restart 清除图片形体、几何形体、跳字和尚未发出的通知，恢复单位重新显示正常 idle；晚到旧 token 仍由 Controller 拒绝。

默认攻击片段 3 帧/8 fps，死亡片段 3 帧/5 fps；默认跳字约 0.9 秒，因此默认交接时机仍由较长跳字控制。自定义非循环素材更长时会等待实际片段结束，测试已覆盖 1 秒死亡片段；循环待机绝不进入等待。

## 运行与验证

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe main.py --geometry
.\.venv\Scripts\python.exe main.py --scenario scenarios/training_ground.json --assets assets
.\.venv\Scripts\python.exe scripts/generate_demo_assets.py
```

默认根路径相对项目文件，允许从其他工作目录启动。--scenario 相对所选 content 根；显式 --content-root/--assets 接受当前工作目录相对路径或绝对目录。需要从外部路径传入场景时先选对应 content 根，不绕过根目录内引用约束。

本机 Python 3.9.1 / Pygame 2.6.1 / SDL 2.28.4：123 项测试，122 通过，1 项因 Windows 无创建符号链接权限跳过，整体退出码 0。无窗口与 Windows 实际窗口两次完整回归均完成。新增 13 项纯内容/清单、16 项 PNG/缓存/渲染/动画检查，原 94 项覆盖保留；旧颜色断言明确在几何模式验证，素材另有真实链路检查。

四组 `python -S` 共 57 项（含上述跳过项），验证内容、清单、核心和协调不依赖 Pygame；独立子进程还禁止导入 Pygame，并从其他工作目录读取默认文件和跑通战斗/回溯。CI 在安装依赖前运行四组，随后安装依赖、检查 SOURCE 并运行完整回归；平台继续覆盖 Windows/Linux × Python 3.9/3.12，结果以 Actions 实际结论为准。

自动化覆盖多 ID 单次读盘、不同缩放缓存、负缓存/一次报告、显式重载、透明度与锚点、所有形体之后的血条、绘制裁剪、无素材像素回退、清单单独替换、规则结果一致、长死亡片段等待、恢复无残留、必需缺失/损坏/结构/引用错误等。符号链接项在支持的系统实际建链验证；Windows 跳过该项时，绝对路径、盘符、反斜杠和 .. 逃逸检查仍运行。

路径断言统一比较 resolve 后的规范路径，兼容 Windows CI 将 RUNNER~1 等 8.3 别名解析为长目录名的行为；生产路径验证仍检查解析后的根目录边界。

实际 Windows 额外检查默认素材、攻击、斥候死亡/消失、胜负、回溯复活与旧通知拒绝；main.py 的默认/几何两种入口从其他工作目录启动并在结算中 QUIT 正常释放。几何模式 13 帧与 M3 逐像素一致。检查了如下截图中的透明边缘、脚底位置、缩放、图层与侧栏；操作由程序调用和自动事件完成，并非人工逐次点击。

![默认素材链路](../artifacts/m4_assets.png)

![素材死亡验证场景](../artifacts/m4_death.png)

## 后续

M5 将正式交付第二场景和第二套外观、开发模板及阶段发布验收。当前临时测试数据和颜色替换证明 M4 链路可用，不提前把系统扩展演练或最终美术标记完成。
````

## docs/M5_IMPLEMENTATION.md

````markdown
# M5 扩展、验收与阶段交付

M5 交付第二场景 `river_crossing`、第二套 `dusk` 外观、可复制功能模板，以及可重建/校验的 0.2.0 源码发布链路。具体演练步骤见 [EXTENSION_EXERCISE](EXTENSION_EXERCISE.md)，后续开发从 [模板](templates/FEATURE_TEMPLATE.md) 和 [规范](FEATURE_DEVELOPMENT.md) 开始。

## 扩展成本

- 场景仅增加一个 JSON：尺寸 6×5、四单位、四障碍，共用既有单位定义和实例覆盖字段。
- 外观仅增加独立 manifest 与 17 张项目脚本生成的 PNG；已有 9 张经典素材保留。
- `main.py`、`tactics/*.py`、`content/units.json` 和默认场景相对 M4 完全未改。没有新增规则分支、运行状态、快照字段、兼容层或未使用框架。
- 新增 6 项扩展集成与 4 项包完整性测试。打包/校验为离线 Python 标准库脚本；PNG 重建使用已有 Pygame。

## 本机实际验证

环境：Windows、Python 3.9.1、Pygame 2.6.1 / SDL 2.28.4。

| 验收 | 结果/边界 |
| --- | --- |
| 完整回归 | 133 项，本机 132 通过、1 项符号链接创建权限跳过；不放宽路径校验 |
| 无第三方包 | 既有四组 57 项（56 通过、同一权限项跳过）；发布完整性另 4 项可用 `-S` 执行 |
| 场景 × 外观 | 两场景 × geometry/classic/dusk，逐观察点比较完整 BattleView，一致 |
| 实际窗口 | windows SDL 驱动；六条操作链、击杀、跨轮、胜利、连续回溯、形体清理、QUIT 释放通过 |
| 字体与 CLI | 强制模拟字体扫描 TypeError，英文回退仍可绘制；其他工作目录实际 main.py 参数与关闭通过 |
| 截图检查 | 观察开局、死亡/跳字、连续回溯复活；锚点、透明度、图层与侧栏显示正常 |
| 发布包 | CI 构建提交树并检查解压后的 SOURCE/CLI/六项集成；最终包记录合并提交与 SHA256 |

实际窗口由事件与公开指令自动驱动，不是人工逐次点击。截图是实际绘制的 Surface；dummy 测试不能替代真实窗口检查。保留 M4 的几何 13 帧对照证据，本阶段没有改绘制或规则代码，不重复宣称新做了逐像素对照。

## CI 与版本对应

`.github/workflows/ci.yml` 覆盖 Windows 2022 / Ubuntu 24.04 × Python 3.9 / 3.12，依赖安装前跑四组纯检查，之后跑完整回归、SOURCE 校验、提交树打包和解压验收。平台字体或符号链接能力不同，跳过原因必须在日志中可见。

工作流在 PR、main 和 `v*` tag 触发。远程成功状态以该提交的 Actions 为准，文档存在不构成 CI 成功证据。最终发布以仓库 `v0.2.0` tag 和同名 Release 为准；包内 ZIP comment、SHA256 和 Release 说明标识实际提交。构建与验证命令见 [RELEASE](RELEASE.md)。

## 后续边界

M0–M5 架构规划已落实；后续按真实功能需求继续开发。技能/Buff 要同步规则、指令、快照和只读结果；AI 共用 Controller；新美术走清单、缓存与表现 token。当前仍无 AI、联网、存档、音频、图集切帧、热重载和独立 EXE，数值和美术是演示内容。

![经典外观渡口](../artifacts/m5_classic_initial.png)

![dusk 外观渡口](../artifacts/m5_dusk_initial.png)
````

## docs/PERSPECTIVE_BATTLEFIELD.md

````markdown
# 透视战场：实现与验收

本文保留首版透视功能的实现历史，包含旧四角、64格细分和152项基线，不能作为当前地图配置。用户补充允许不规则地图后，已完成28格校准、20点独立验证5.57/11.42px与165项回归；现状、真实截图和限制见 [逐砖校准报告](WAR_TORN_CALIBRATION.md)。

本功能基于已发布 v0.2.0，以独立透视模式接入用户背景。设计依据见 [用户设计稿](references/perspective_battlefield_design.md)；其中的示意零角点没有用于运行。本次只改变表现与输入映射，规则、Controller、Unit、ViewModel 和规则快照未修改。无 AI、技能、存档、网络或新依赖。

## 使用与参数约定

```powershell
cd E:\gamedesign
.\.venv\Scripts\python.exe main.py --presentation presentations/war_torn_8x8.json
.\.venv\Scripts\python.exe main.py --presentation presentations/war_torn_8x8.json --debug-grid
```

窗口固定 1280×720，不支持 resize 或镜头。F3 在正式画面和四角/网格/中心/编号之间切换；只改表现，不影响行动。鼠标、空格、回车、退格与旧版一致；HUD 标签/背景会消费点击，按钮只返回 UIAction，仍由 Controller 校验。默认角色是临时蓝圆/红方块，正式角色美术尚未提供。

`--presentation` 与 `--scenario`、`--assets`、`--content-root`、`--geometry` **互斥**，不采用隐含覆盖优先级；冲突清楚报错并退出 2。`--debug-grid` 需要 presentation。无 presentation 时原入口、几何模式、训练场和渡口/dusk 均保持原行为。默认路径和 presentation 路径相对项目根，与当前工作目录无关；显式资源/内容目录在旧模式仍按当前工作目录解析。

Python API 可用 `Game(scenario, presentation_file=...)` 注入独立 Scenario 夹具，尺寸必须匹配布局；CLI 不提供绕过互斥的参数。正式入口使用布局引用的 war_torn.json。

## 数据与职责

| 文件 | 实际职责 |
| --- | --- |
| `content/scenarios/war_torn.json` | 独立 8×8、双方各 3 人、3 个显式障碍；不修改旧两张地图 |
| `assets/skins/war_torn/manifest.json` | 必需完整背景、临时几何角色绑定；原图不改像素 |
| `presentations/war_torn_8x8.json` | 背景参考尺寸、四角、视口、HUD、调试开关；不含规则数值 |
| `tactics/presentation_layout.py` | 使用既有严格 JSON/路径工具；拒绝未知字段、版本、路径逃逸、零/退化角点、尺寸与 HUD 越界 |
| `tactics/perspective_geometry.py` | 纯 Python 单应矩阵/逆矩阵、contain 变换、缓存 64 格多边形/中心/脚底/尺度、半开反向命中 |
| `tactics/perspective_board_renderer.py` | 完整背景、透明四边形、阴影、屏幕脚底 Y/稳定 ID 排序、全部形体后的标记与血条 |
| `tactics/scene_hud.py` | 独立半透明状态/属性/按钮卡与队列/日志卡；复用已修复的字体加载 |
| `tactics/geometry.py` | 矩形模式补充脚底、尺度、表现形体矩形接口，原有矩形映射不变 |
| `tactics/effects.py` | 通过同一几何接口定位跳字/攻击/死亡，token/generation、锁定和清理流程不变 |
| `tactics/assets.py` / `asset_manifest.py` | 兼容新增 board.background；验证实际尺寸、缓存整图；只为单位/障碍预载离散深度尺寸 |
| `tactics/game.py` / `main.py` | 选择组装模式、CLI 互斥、HUD 点击消费和 F3；初始化失败释放显示资源 |

背景不是 64×64 地砖。contain 缩放率 `min(1280/1672,720/941)`，偏移居中；图片、投影、反向点击共用 BackgroundFit。没有每帧 IO、缩放或矩阵求解；F3 仅重建调试层。人物站立点为投影 `(col+0.5,row+0.82)`，位于格内近侧；深度尺寸量化到 1/8，范围 0.5–1.5，启动时预载有限组合。

PNG 以该站立点作脚底锚定；临时几何形体、标签和选中环围绕逻辑格中心绘制，点击形体中心仍命中同一格，避免斜向投影时点到邻格。几何死亡与跳字使用相同表现形体矩形，规则占格不变。

## 首版校准与实际试玩（历史）

原图真实为 1672×941，SHA256 与来源见 [资源记录](../assets/skins/war_torn/README.md)。下列旧四角以原图坐标保存，但只有目测选区，没有真实整砖计数与独立误差验收，当前已确认不是有效8×8整砖边界：

| 逻辑外角 | 原图坐标 |
| --- | --- |
| p00 / (0,0) | (1060,270) |
| p10 / (8,0) | (1530,452) |
| p11 / (8,8) | (892,898) |
| p01 / (0,8) | (340,568) |

列轴向画面右下，行轴向左下，不假定屏幕横纵轴就是棋盘轴。区域避开两杆主要军旗；左上属性卡与上方日志卡没有占用当前棋盘。石砖是绘画纹理，大小、裂缝和接缝并非严格的规则平面网格：当前 64 格是这个区域的均匀透视细分，**不能保证每条格线都恰好等于一块原画砖缝**。截图记录当前首版校准；最终美术级接缝与角点仍需人工认可，可编辑 JSON 后重启检查。未据此新增多点编辑器或逐行校准。

开局 A2 在 `(1,4)`；点击 `(4,3)` 移动，再点击 D1 `(5,3)`，造成 10 点伤害并击杀生命 5 的训练木桩。动画完成后退格，可恢复初始位置和木桩生命 5。其他木桩生命保持 100，数值仍是演示值。图片中的旗帜、碎石和裂缝不自动阻挡；只使用 JSON 的 `(0,1)`、`(7,6)`、`(6,0)` 三个障碍。

## 自动化与实际窗口结果

新增 7 项几何、5 项配置、7 项渲染/集成，共 19 项；保留全部 133 项旧检查，总计 **152 项**。本机 Windows Python 3.9.1 / Pygame 2.6.1 / SDL 2.28.4：dummy 与 windows 实际窗口分别执行，**151 通过，1 项符号链接创建权限跳过**。六组纯检查合计 69 项（68 通过、同一权限跳过），另 4 项包完整性检查可使用 `-S`。

```powershell
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_perspective_geometry.py -v
.\.venv\Scripts\python.exe -S -m unittest discover -s tests -p test_presentation_layout.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_perspective_rendering.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

- 数学检查：四角、64 中心、内部点、相邻边、半开边界、留边、非有限输入、分母为零、退化/反序四角、contain 后反向命中。
- 配置/资源：旧清单兼容、背景 ID/必需标记、缺失/损坏/真实尺寸不匹配、严格字段/路径、互斥 CLI 与异地目录真实 main.py；失败后关闭显示资源。
- 战斗：同一 Scenario/操作在矩形与透视下逐点比较完整 BattleView，一致；覆盖查看远近单位、移动、攻击锁定、三次击杀、跨轮、胜利、连续回溯、复活及拒绝旧 token。快速全灭夹具仅将三只木桩生命设为 5，不改交付场景/单位定义。
- 资源表现：临时组合 dusk PNG 与背景，实际走 idle/attack/death、按屏幕脚底排序和回溯清理；在禁止 image.load/smoothscale 的绘制阶段仍能运行。背景/高亮保留原纹理。
- 旧画面：13 帧几何截图与 M4 留存基线逐像素一致，包含跳字、死亡、回溯、英文降级和结束状态；不是用删旧测试实现兼容。
- 真实窗口：windows 驱动保存并查看下列 4 张实际绘制画面；点击由事件自动投递，不是人工鼠标逐次试玩。字体扫描异常时 HUD 英文回退，结算中 QUIT 正常释放。
- CI：Windows/Linux × Python 3.9/3.12 增加两组依赖安装前检查；SOURCE 导出包含 presentations；交付包解压验证同时运行 M5 与透视集成。远程结果以当前 PR/Actions 为准。

## 首版待确认事项（历史，现状见逐砖校准报告）

角色仍为临时几何回退；当前角点是首版可交互校准，原画局部砖缝与严格单应网格存在偏差，需要最终美术确认。窗口暂不支持 resize、相机、音频、图集或编辑器；这些没有标记为已实现。新增规则状态仍须按功能模板补快照/恢复，本次没有改变玩法和防御计算。

![实际窗口：透视战场](../artifacts/perspective_initial.png)

![实际窗口：调试网格](../artifacts/perspective_debug.png)

![实际窗口：击杀与伤害](../artifacts/perspective_attack.png)

![实际窗口：回溯复活](../artifacts/perspective_revived.png)
````

## docs/RELEASE.md

````markdown
# 阶段源码发布

版本值在 `VERSION.txt`，本阶段为 0.2.0。交付是 Python 源码 ZIP，运行需要 Python 和 requirements.txt；不含虚拟环境或独立 EXE。首次安装 Pygame 需要联网，之后可离线运行。

## 构建并验证

先提交所有交付内容，再构建指定提交。脚本只读取已提交 Git 树，不会把工作区尚未提交的修改打进包：

```powershell
.\.venv\Scripts\python.exe scripts/build_release.py --ref HEAD
$releaseCommit = git rev-parse HEAD
.\.venv\Scripts\python.exe scripts/verify_release.py --expected-commit $releaseCommit
Get-FileHash dist/chrono-tactics-pygame-0.2.0-source.zip -Algorithm SHA256
```

产物：`dist/chrono-tactics-pygame-0.2.0-source.zip` 和 `.zip.sha256`。构建使用 git archive；ZIP comment 保存格式、版本、完整提交 SHA，不把生成元数据混入 SOURCE 扫描。相同提交重复构建字节一致；未提交文件、`.git`、`.venv`、缓存、`.delivery` 和旧包不进入交付。

校验器检查 SHA256、ZIP CRC、路径、版本与指定提交，然后临时解压，用调用者已有 Python/Pygame 离线执行 SOURCE 一致性、`main.py --help`、实测地图/正式配置一致性、M5 与透视集成检查（含标点 UI）。不代表安装独立运行时或人工点击；独立对齐误差见校准报告，完整回归在打包前执行。已发布 v0.2.0 保留原附件；未发布扩展只进入当前提交验收，不覆盖已发布附件。

显式校验其他位置的文件：

```powershell
.\.venv\Scripts\python.exe scripts/verify_release.py C:\Downloads\chrono-tactics-pygame-0.2.0-source.zip --expected-commit <完整提交SHA>
```

SHA256 用于检出损坏，ZIP 内的提交声明不是数字签名。确认来源时，以有权限访问的 GitHub tag/Release 及该提交的 Actions 记录为准。

## 发布门槛

1. 更新 TASKS/CHANGELOG/README/SOURCE，审查实际改动；本地完整回归、纯逻辑检查和实际窗口通过。
2. PR 在 Windows/Linux × Python 3.9/3.12 通过；四组均包含从当前提交构建和解压验收。
3. 合并后基于同一提交构建最终 ZIP、校验并确认工作区干净。tag `v0.2.0` 指向该提交；tag 的四组 CI 也通过后发布 Release。
4. Release 附带该 ZIP 与 SHA256，发布说明写明实际验收与限制。流水线不自动发布，避免未经验收的 tag 直接生成公开结果。

源码包中的文档不硬编码自身最终提交 SHA（否则修改文档会改变 SHA）；实际提交以 tag、Release 和 ZIP comment 为准。测试/记录数量与本机权限差异见 [M5 验收](M5_IMPLEMENTATION.md)。
````

## docs/ROADMAP.md

````markdown
# 架构实施路线与验收

状态：M0–M5 已实施，阶段版本 `0.2.0`（发布状态以 tag/Release 为准）。第二场景与第二套演示外观已通过同一运行链路接入，磁盘存档未实现。

本路线以当前 41 项行为检查为迁移基线。测试数量可增加，导入和夹具可随接口迁移，关键行为不能丢失。每个阶段在专用分支完成小批次提交，先验证、再审查差异并合并；不在一次提交中同时迁移架构和改动玩法。

## 阶段计划

| 阶段 / 任务 ID | 前置 | 实际交付 | 验收证据 |
| --- | --- | --- | --- |
| M0 / ARCH-00 | v0.1.0 | 意见评审、整体架构、资源规范、开发约束、路线与状态记录 | 本次文档、源码汇总一致；原游戏回归通过 |
| M1 / ARCH-01（已完成） | M0 | Scenario 纯数据初始化；Board 去除 Pygame；Geometry、BoardRenderer 和最小 BoardView 实际接管旧绘制 | 57 项检查通过；12 项无第三方包；8 帧逐像素一致；5×4 场景实际窗口验收，详见 M1 实施记录 |
| M2 / ARCH-02（已完成） | M1 | Controller 操作入口、完整只读 View、UIAction 命中接口；Game 缩减为组装与循环 | 75 项检查通过，28 项无第三方包；13 帧与 M1 一致；完整交互与输入锁定通过，详见 M2 实施记录 |
| M3 / ARCH-03（已完成） | M2 | ID 化结算结果、纯数据快照/UID 重建、结算编号与表现代次；回溯清除旧表现 | 94 项检查通过，44 项无第三方包；错误/重复/过期通知无效；死亡及跨轮恢复一致；13 帧与 M2 一致，详见 M3 实施记录 |
| M4 / ARCH-04（已完成） | M3 | JSON 内容/资源清单、验证、图片/缩放缓存；默认地砖与斥候静态/动画素材链路、几何回退 | 123 项测试，本机 122 通过/1 项权限跳过；57 项无需第三方包；13 帧几何模式一致；替换、缓存、回退与素材窗口验收，详见 M4 记录 |
| M5 / ARCH-05（已完成） | M1–M4 | 渡口场景、dusk 外观、开发模板、四组 CI/产物检查、真实窗口与 0.2.0 交付链路 | 133 项测试，本机 132 通过/1 项权限跳过；两场景 × 三模式状态一致；提交树打包与解压验收，见 M5 记录 |

M1–M4 可以继续细分为下列小提交，不以“文件已经创建”作为完成条件。

## 建议提交顺序

### M1：先隔离已存在的职责

1. 提取默认场景和 Scenario 验证，Board 从场景接收尺寸、单位和障碍。
2. 引入 Geometry 数值坐标转换，迁移旧坐标边界测试。
3. 将绘制原样迁到 BoardRenderer，保留血条、选中与范围显示。
4. 为规则导入边界增加检查，建立两个数据不同的测试场景。

这个阶段不引入图片、技能或新地图玩法。若临时保留兼容入口，应记录调用方和删除时点；不能通过让 Board 再次导入 Pygame 来维持旧测试写法。

### M2：再收拢操作流程

1. 将现有逻辑操作搬到 Controller，仍调用同一套 Battle 方法。
2. 引入包含单位、棋盘、范围、队列、日志与按钮可用状态的只读 View。
3. Renderer/Panel 改读 View；Panel 返回动作标识；输入适配负责键鼠转换。
4. Game 只保留初始化、输入转换、更新与绘制调度、退出清理。

测试夹具通过 Scenario 构建局面，不以任意改写 Game 内部字段作为长期测试接口。

### M3：让回溯与动画具备稳定契约

1. 攻击结果使用实例 ID、目标位置和生命变化等独立值。
2. 将内存快照迁为纯数据，覆盖现有全部回溯状态。
3. 加入结算编号、表现代次和完成确认；重复、过期确认无效。
4. 校验死亡形体消失与回溯恢复无重复残留，战斗结束后仍能回溯。

暂不增加磁盘存档，也不改变“攻击立即扣血、动画后交接”的行为。

### M4：接入内容与第一批资源

1. 用简单 JSON + 显式验证接入场景/单位定义与外观引用；先满足现有模型，不建设万能数据格式。
2. 实现 [资源规范](ASSET_GUIDE.md) 中的路径解析、清单和缓存。
3. 在渲染器中接入地砖和一名单位的图片替换，几何回退保持可用。
4. 接入非循环攻击/死亡动画和完成通知；待机循环不阻塞行动。
5. 使用可自生成的测试 PNG 验证加载缓存；无需先采购或制作正式美术。

资源模块必须被默认渲染路径实际使用，不能只通过孤立的加载单测。

### M5：验证扩展成本

1. 增加一个场景数据实例，证明不用修改 Board/Battle 即可改变阵容与障碍。
2. 用第二套外观清单切换相同逻辑单位，证明外观不影响移动、伤害和回溯。
3. 检查默认几何模式、图片模式、中文字体回退与真实窗口关闭。
4. 在 Windows/Linux × Python 3.9/3.12 执行完整回归，发布时记录真实结果。

演练是架构验收，不默认为用户增加技能、AI 或存档玩法。

## 每个阶段共同的完成条件

- 默认阵容、障碍、四方向路径、相邻攻击、速度及同速顺序、100% 攻击伤害保持一致。
- 生命显示、死亡不再阻挡、死亡队列跳过、结算锁定与窗口关闭保持一致。
- 回溯仍返回上一单位行动开始前，可连续恢复死亡、轮数和战斗结束状态。
- 新模块有真实调用方，没有第二套规则、未使用扩展框架或长期无主的兼容层。
- 相应边界测试在该阶段就加入，不集中推迟到 M5。
- 更新 TASKS、CHANGELOG、README 和 SOURCE；文档状态与代码实现一致。
- 自动化结果与真实窗口检查分别报告，失败未修复时不标记完成。

## 后续功能安排原则

| 用户未来提出的需求 | 最小必要前置 | 完成该需求时的附加验收 |
| --- | --- | --- |
| 只换角色/地图图片 | M1–M4 的资源渲染边界 | 同一场战斗数据在两套外观下结算一致 |
| 新技能、Buff、装备 | M1–M3 的状态、指令、结算与回溯 | 新增状态可恢复；非法使用不消耗行动 |
| AI 对手 | M2–M3 的指令和状态查询 | 不导入 Pygame、不模拟点击、不绕过合法性校验 |
| 更多关卡 | M1 的场景入口；文件配置需要 M4 | 配置错误可定位，不需要复制 Board 代码 |
| 存档与回放 | M3 的纯数据状态 | 明确版本、缺失定义及恢复校验策略 |

这不是要求每个小功能等待所有阶段结束。如果一个功能只依赖已稳定的边界，就直接实施；若需要缺失的边界，先补齐最小前置并与功能一并验证。用户明确改变规则时同步调整本计划，不额外制造逐项批准流程。

## 当前下一步

M1–M5 已完成，见 [M5 实施与验收](M5_IMPLEMENTATION.md) 及各阶段记录。几何模式保持原画面，两套素材只改变表现。

后续按用户实际需求推进，使用 [开发模板](templates/FEATURE_TEMPLATE.md) 记录最小必要设计与验收。扩展演练见 [EXTENSION_EXERCISE](EXTENSION_EXERCISE.md)，阶段发布见 [RELEASE](RELEASE.md)。不自动进入技能、AI 或存档开发。
````

## docs/WAR_TORN_CALIBRATION.md

````markdown
# War Torn：不规则逐砖地图与单应性校准

用户明确补充：**不要求完整 n×n 矩形区域，但每个小地块必须与图片对齐**。据此采用 28 块可辨认石砖组成的不规则地图，保留 8×8 逻辑包围盒及六个单位的初始坐标、定义和数值。没有把大石砖再等分，也没有挪动单位掩盖几何误差。

## 诊断与坐标链

旧配置将原图四点 `(1060,270)/(1530,452)/(892,898)/(340,568)` 之间的目测区域直接均分为 8×8；该区实际约跨 4–5 列、6 行大石砖，四角未对应同一整砖区域的外边界。主因是选区和砖块计数错误；没有发现矩阵行列颠倒或重复缩放，未重写运行时单应性公式。

| 项目 | 实际值 |
| --- | --- |
| 原始 PNG | 1672×941；文件内容未修改 |
| SHA256 | `f3ae6033599a5cc9047a8509c3d3f2269e3604513aa29cb0ec7e4db1051f5d2a` |
| 参考视口 | 1280×720 |
| contain 比例 | `720/941 = 0.7651434643995749` |
| 理论偏移 | `(0.34006376195532084, 0)` |
| 缓存背景 | 1279×720，整数 blit 位置 `(0,0)` |

背景、网格、脚底、特效和地面拾取共用 `BackgroundFit`。缓存尺寸/blit 取整差异不到 1 px，无法解释旧网格跨越砖块中央的错位。所有观测和配置角点均在原始 PNG 坐标系中，测量时才转到视口。

## 地图与四角标定

有效格为 row=2 的 col=3…6，以及 row=3…6 的 col=1…6，共 28 格。其余 36 格在场景 JSON 中显式不可通行，不画假石砖，也不作为可选地面。四方向逻辑邻接不变。

参考矩形的逻辑原点 `(1,3)`、跨度 `6×4`，仅用于建立同一个单应性，并非不规则地图外轮廓。row=2 的四块石砖在参照矩形外，但都属于已观测、验证的地图。F3 的 `REF p00/p10/p11/p01` 同时显示逻辑顶点编号。

先用参考矩形的四个真实交点精确标定，再测其余 36 点：平均 **13.605058 px**、最大 **27.442275 px**，未达标。四角正确后，局部非规则绘画和人工读点误差仍会使单次四点解不稳定。

接着先对**同一个单应性**做多点标定，未直接升级控制网格：40 个实测交点按奇偶分组，20 点仅用于离线最小二乘，另外 20 点只验证、不参与求解；四个参考外角全部属于验证组。运行时仍由原 `PerspectiveBoardGeometry` 计算投影/逆变换，不执行拟合，没有逐格形变。

| 参考顶点 | 原图人工观测 | 多点模型估计，原图坐标 |
| --- | --- | --- |
| p00 `(1,3)` | `(771,288)` | `(785.806252,286.443252)` |
| p10 `(7,3)` | `(1491,527)` | `(1493.022837,531.157249)` |
| p11 `(7,7)` | `(1029,845)` | `(1042.659639,844.366933)` |
| p01 `(1,7)` | `(308,458)` | `(298.787556,467.715916)` |

**配置四角是模型估计，不能当成人工精确点选值。** 它们估计真实边界交点的位置；观测、预测、误差分别保存，不将拟合值回填成实测。四个外角接受同样的非零误差验收，没有把拟合四角的零残差混入平均数。

## 实际误差

正式数据：[40 个原图交点](calibration/war_torn_map_observations.json)；可重算结果：[完整误差报告](calibration/war_torn_map_report.json)。以下均为 1280×720 下的欧氏距离。

| 样本 | 数量 | 平均 px | 最大 px |
| --- | --- | --- | --- |
| 独立验证，含地图边界 | 20 | **5.567316** | **11.419992** |
| 其中独立内部交点，四周都有有效格 | 9 | **3.855241** | **6.002102** |
| 远处独立验证 | 6 | 4.807837 | 11.391354 |
| 中部独立验证 | 7 | 3.475779 | 7.207970 |
| 近处独立验证，含外边界 | 7 | 8.309834 | 11.419992 |
| 标定点，另列，不能当独立验证 | 20 | 4.807673 | 10.442478 |
| 全部观测顶点 | 40 | 5.187494 | 11.419992 |

独立整体及内部交点达到均值≤6/最大≤12 px 的目标，因此**不实现 `CalibratedGridGeometry` 或 9×9 控制点模式**。近处边界仍有约 8–11 px 残差，未声称每个分区均值都≤6，或每个破损砖缝像素完全重合。人工读点估计有约 3–6 个原图像素不确定性；这是观测点估值，不是零误差或亚像素测量。

最初的 2×6 样带保留为历史证据：[旧观测](calibration/war_torn_observations.json)、[旧报告](calibration/war_torn_report.json)。其 5.56/11.71 px 仅属于当时局部粗标点；正式地图采用重新放大核对的数据，不混用统计。

## 运行与复核

```powershell
.\.venv\Scripts\python.exe main.py --presentation presentations/war_torn_8x8.json --debug-grid
.\.venv\Scripts\python.exe -S scripts/fit_board.py --check --report docs/calibration/war_torn_map_report.json
.\.venv\Scripts\python.exe scripts/fit_board.py --check --screenshot artifacts/calibration_validation.png
```

`fit_board.py` 默认只测量；`--check` 验证正式配置与标定、遮罩和原图尺寸一致。显式 `--write-presentation` 才重新生成四角。校验原图散列、所有地块顶点的真实观测、标定/验证分离、远中近覆盖、重复、越界和退化数据；阈值失败时非零退出。CI 和解压验收也运行检查。

已有交互读点工具：

```powershell
.\.venv\Scripts\python.exe scripts/calibrate_board.py --pick --cols 6 --rows 4
```

先标四角，再逐行标内部点；Backspace/Z 撤销，P 预览，S 保存草稿，Esc 退出。草稿不自动替换正式地图。此工具处理矩形参照区；尚无不规则地图鼠标绘制编辑器。不规则边界及样本角色在 JSON 编辑后运行 `fit_board.py`，不能用预测点补全不可辨认砖面。

## 定位与输入

- 单位、PNG 动画统一用脚底 `cell_anchor`；几何角色表现矩形以脚底为底边。标签、血条和伤害跳字由同一脚底/尺度派生。
- 选中框、移动/攻击范围和目标框使用投影四边形。地面共享边界按半开区间归属右/下一逻辑格；若该格为 void 则不命中，不向邻格吸附。
- 角色身体可能高于地面格，Game 先由 Renderer 按相同脚底/精灵透明像素检测可见形体，再逆投影地面；HUD 优先。Renderer 只读 BoardView，操作仍经 Controller。
- 独立障碍底部落在对应脚底；PNG 攻击/死亡及几何死亡形体一并按屏幕脚底 Y、稳定 UID 排序。伤害文字保留覆盖层。
- 原三个障碍坐标在有效区外，继续作为 void 阻挡，不在图外画岩石。障碍定位用同一 Scenario 增加 `(3,6)` 障碍的注入夹具验收，截图注明夹具；未将额外障碍写入正式场景。
- Battle、Board 寻路、伤害、行动顺序、快照和结算 token 的代码/语义未改；地图形状通过已有 Scenario 障碍数据约束移动。训练场、渡口、矩形/几何模式保留。

## 文件与验证

| 文件组 | 变更 |
| --- | --- |
| `tactics/perspective_geometry.py` | 原单应性增加参照矩形/有效格遮罩；脚底表现矩形 |
| `tactics/presentation_layout.py`、`game.py` | 可选配置、void/出生格校验、形体输入 |
| `tactics/perspective_board_renderer.py`、`effects.py` | 有效区绘制、四边形选中、脚底与死亡深度排序 |
| `presentations/war_torn_8x8.json`、`content/scenarios/war_torn.json` | 标定四角、参照区、28 格遮罩、36 格阻挡；单位数据不变 |
| `scripts/fit_board.py`、`docs/calibration/war_torn_map_*.json` | 可复算单应性、独立验证、配置一致性、实际游戏截图 |
| 四个校准/透视测试模块、CI、`scripts/verify_release.py` | 输入/边界/兼容/脚底检查、标定纳入交付检查 |
| README/TASKS/CHANGELOG/AGENTS/SOURCE | 维护与验收记录 |

完整套件 **165 项，本机 164 通过、1 项因 Windows 无符号链接权限跳过**。dummy 与 Windows 实际驱动分别运行；七组纯核心/内容/几何/配置/校准共 80 项可用 `-S`，另 4 项纯包完整性通过。覆盖 28 个地面中心、远中近形体、void、共享边、范围、三次击杀/胜利/连续回溯、拒绝旧 token 和矩形/透视完整 BattleView 一致性。

截图来自实际 Windows SDL 窗口的 Game Surface；F3、点击和退出以事件调用验证，不声称人工逐次点击。交点核对使用原始图片，截图没有用手绘棋盘替代。

## 限制与后续

仅 28 块已观测石砖开放，其他可见铺石仍是背景；文件名 8×8 表示逻辑包围盒。角色仍为几何回退。未新增控制网格、地图编辑器、resize、相机或玩法。扩图先补真实交点、独立验证和 void 数据；误差超目标后再评估控制网格，不靠移动单位或将预测值冒充观测消除报告误差。

![诊断前实际 F3](../artifacts/calibration_before.png)

![校准后实际完整有效网格、中心、编号和参考角点](../artifacts/calibration_after.png)

![实际游戏验证点：绿圈观测、红点预测、短线为残差](../artifacts/calibration_validation.png)

![实际战斗攻击范围](../artifacts/calibration_attack_range.png)

![实际伤害文字与死亡形体](../artifacts/calibration_death.png)

![独立障碍验收夹具：同一场景增加 (3,6) 障碍，仅用于脚底验收](../artifacts/calibration_obstacle_fixture.png)
````

## docs/calibration/war_torn_map_observations.json

```text
{
  "schema_version": 1,
  "image": "assets/skins/war_torn/backgrounds/battlefield.png",
  "sha256": "f3ae6033599a5cc9047a8509c3d3f2269e3604513aa29cb0ec7e4db1051f5d2a",
  "image_size": [
    1672,
    941
  ],
  "viewport_size": [
    1280,
    720
  ],
  "logical_size": [
    8,
    8
  ],
  "reference_region": [
    1,
    3,
    6,
    4
  ],
  "cells": [
    [
      3,
      2
    ],
    [
      4,
      2
    ],
    [
      5,
      2
    ],
    [
      6,
      2
    ],
    [
      1,
      3
    ],
    [
      2,
      3
    ],
    [
      3,
      3
    ],
    [
      4,
      3
    ],
    [
      5,
      3
    ],
    [
      6,
      3
    ],
    [
      1,
      4
    ],
    [
      2,
      4
    ],
    [
      3,
      4
    ],
    [
      4,
      4
    ],
    [
      5,
      4
    ],
    [
      6,
      4
    ],
    [
      1,
      5
    ],
    [
      2,
      5
    ],
    [
      3,
      5
    ],
    [
      4,
      5
    ],
    [
      5,
      5
    ],
    [
      6,
      5
    ],
    [
      1,
      6
    ],
    [
      2,
      6
    ],
    [
      3,
      6
    ],
    [
      4,
      6
    ],
    [
      5,
      6
    ],
    [
      6,
      6
    ]
  ],
  "observations": [
    {
      "node": [
        3,
        2
      ],
      "image": [
        1084,
        316
      ],
      "role": "calibration",
      "band": "far"
    },
    {
      "node": [
        4,
        2
      ],
      "image": [
        1195,
        350
      ],
      "role": "validation",
      "band": "far"
    },
    {
      "node": [
        5,
        2
      ],
      "image": [
        1311,
        385
      ],
      "role": "calibration",
      "band": "far"
    },
    {
      "node": [
        6,
        2
      ],
      "image": [
        1437,
        424
      ],
      "role": "validation",
      "band": "far"
    },
    {
      "node": [
        7,
        2
      ],
      "image": [
        1576,
        469
      ],
      "role": "calibration",
      "band": "far"
    },
    {
      "node": [
        1,
        3
      ],
      "image": [
        771,
        288
      ],
      "role": "validation",
      "band": "far"
    },
    {
      "node": [
        2,
        3
      ],
      "image": [
        874,
        321
      ],
      "role": "calibration",
      "band": "far"
    },
    {
      "node": [
        3,
        3
      ],
      "image": [
        990,
        356
      ],
      "role": "validation",
      "band": "far"
    },
    {
      "node": [
        4,
        3
      ],
      "image": [
        1103,
        395
      ],
      "role": "calibration",
      "band": "far"
    },
    {
      "node": [
        5,
        3
      ],
      "image": [
        1223,
        434
      ],
      "role": "validation",
      "band": "far"
    },
    {
      "node": [
        6,
        3
      ],
      "image": [
        1352,
        479
      ],
      "role": "calibration",
      "band": "far"
    },
    {
      "node": [
        7,
        3
      ],
      "image": [
        1491,
        527
      ],
      "role": "validation",
      "band": "far"
    },
    {
      "node": [
        1,
        4
      ],
      "image": [
        685,
        333
      ],
      "role": "calibration",
      "band": "middle"
    },
    {
      "node": [
        2,
        4
      ],
      "image": [
        771,
        359
      ],
      "role": "validation",
      "band": "middle"
    },
    {
      "node": [
        3,
        4
      ],
      "image": [
        883,
        401
      ],
      "role": "calibration",
      "band": "middle"
    },
    {
      "node": [
        4,
        4
      ],
      "image": [
        1002,
        445
      ],
      "role": "validation",
      "band": "middle"
    },
    {
      "node": [
        5,
        4
      ],
      "image": [
        1123,
        490
      ],
      "role": "calibration",
      "band": "middle"
    },
    {
      "node": [
        6,
        4
      ],
      "image": [
        1255,
        541
      ],
      "role": "validation",
      "band": "middle"
    },
    {
      "node": [
        7,
        4
      ],
      "image": [
        1393,
        596
      ],
      "role": "calibration",
      "band": "middle"
    },
    {
      "node": [
        1,
        5
      ],
      "image": [
        567,
        369
      ],
      "role": "validation",
      "band": "middle"
    },
    {
      "node": [
        2,
        5
      ],
      "image": [
        655,
        406
      ],
      "role": "calibration",
      "band": "middle"
    },
    {
      "node": [
        3,
        5
      ],
      "image": [
        769,
        454
      ],
      "role": "validation",
      "band": "middle"
    },
    {
      "node": [
        4,
        5
      ],
      "image": [
        889,
        501
      ],
      "role": "calibration",
      "band": "middle"
    },
    {
      "node": [
        5,
        5
      ],
      "image": [
        1012,
        552
      ],
      "role": "validation",
      "band": "middle"
    },
    {
      "node": [
        6,
        5
      ],
      "image": [
        1140,
        609
      ],
      "role": "calibration",
      "band": "middle"
    },
    {
      "node": [
        7,
        5
      ],
      "image": [
        1288,
        673
      ],
      "role": "validation",
      "band": "middle"
    },
    {
      "node": [
        1,
        6
      ],
      "image": [
        429,
        411
      ],
      "role": "calibration",
      "band": "near"
    },
    {
      "node": [
        2,
        6
      ],
      "image": [
        529,
        457
      ],
      "role": "validation",
      "band": "near"
    },
    {
      "node": [
        3,
        6
      ],
      "image": [
        646,
        508
      ],
      "role": "calibration",
      "band": "near"
    },
    {
      "node": [
        4,
        6
      ],
      "image": [
        765,
        561
      ],
      "role": "validation",
      "band": "near"
    },
    {
      "node": [
        5,
        6
      ],
      "image": [
        889,
        620
      ],
      "role": "calibration",
      "band": "near"
    },
    {
      "node": [
        6,
        6
      ],
      "image": [
        1023,
        685
      ],
      "role": "validation",
      "band": "near"
    },
    {
      "node": [
        7,
        6
      ],
      "image": [
        1165,
        755
      ],
      "role": "calibration",
      "band": "near"
    },
    {
      "node": [
        1,
        7
      ],
      "image": [
        308,
        458
      ],
      "role": "validation",
      "band": "near"
    },
    {
      "node": [
        2,
        7
      ],
      "image": [
        398,
        510
      ],
      "role": "calibration",
      "band": "near"
    },
    {
      "node": [
        3,
        7
      ],
      "image": [
        515,
        568
      ],
      "role": "validation",
      "band": "near"
    },
    {
      "node": [
        4,
        7
      ],
      "image": [
        628,
        628
      ],
      "role": "calibration",
      "band": "near"
    },
    {
      "node": [
        5,
        7
      ],
      "image": [
        759,
        694
      ],
      "role": "validation",
      "band": "near"
    },
    {
      "node": [
        6,
        7
      ],
      "image": [
        889,
        766
      ],
      "role": "calibration",
      "band": "near"
    },
    {
      "node": [
        7,
        7
      ],
      "image": [
        1029,
        845
      ],
      "role": "validation",
      "band": "near"
    }
  ],
  "annotation": "Native PNG seam-center observations inspected in magnified source crops. Estimated manual uncertainty 3-6 native pixels, larger at worn joints. Alternating parity split keeps all four reference rectangle corners in independent validation. Model-generated corner estimates are stored separately from these observations; no projected vertices are labelled as measured. Irregular 28-tile mask retains all six original logical unit cells."
}
```

## docs/calibration/war_torn_map_report.json

```text
{
  "image_sha256": "f3ae6033599a5cc9047a8509c3d3f2269e3604513aa29cb0ec7e4db1051f5d2a",
  "viewport_size": [
    1280,
    720
  ],
  "scale": 0.7651434643995749,
  "offset": [
    0.34006376195532084,
    0.0
  ],
  "playable_cells": 28,
  "method": "One homography refined offline; runtime PerspectiveBoardGeometry formula unchanged.",
  "reference_region": [
    1,
    3,
    6,
    4
  ],
  "fitted_corners_image": {
    "p00": [
      785.8062519854639,
      286.44325233527604
    ],
    "p10": [
      1493.02283721993,
      531.1572489530942
    ],
    "p11": [
      1042.6596392405297,
      844.3669334366049
    ],
    "p01": [
      298.78755614375797,
      467.71591609752414
    ]
  },
  "observed_reference_corners_image": {
    "p00": [
      771,
      288
    ],
    "p10": [
      1491,
      527
    ],
    "p11": [
      1029,
      845
    ],
    "p01": [
      308,
      458
    ]
  },
  "four_observed_corners_baseline": {
    "count": 36,
    "mean_px": 13.605057700552218,
    "max_px": 27.442274938900766
  },
  "calibration": {
    "count": 20,
    "mean_px": 4.807673228910535,
    "max_px": 10.442477862768744
  },
  "independent_validation": {
    "count": 20,
    "mean_px": 5.567315763585733,
    "max_px": 11.41999211967498
  },
  "all_vertices": {
    "count": 40,
    "mean_px": 5.187494496248133,
    "max_px": 11.41999211967498
  },
  "independent_interior": {
    "count": 9,
    "mean_px": 3.855241185859837,
    "max_px": 6.002101554331281
  },
  "bands": {
    "far": {
      "count": 6,
      "mean_px": 4.807837170217445,
      "max_px": 11.391353551582771
    },
    "middle": {
      "count": 7,
      "mean_px": 3.4757789343163403,
      "max_px": 7.207970336328134
    },
    "near": {
      "count": 7,
      "mean_px": 8.309834244313658,
      "max_px": 11.41999211967498
    }
  },
  "threshold_met": true,
  "full_rectangular_8x8": false,
  "points": [
    {
      "node": [
        3,
        2
      ],
      "image": [
        1084,
        316
      ],
      "role": "calibration",
      "band": "far",
      "predicted_image": [
        1080.0697921993747,
        314.3087438919754
      ],
      "error_px": 3.27378419167604
    },
    {
      "node": [
        4,
        2
      ],
      "image": [
        1195,
        350
      ],
      "role": "validation",
      "band": "far",
      "predicted_image": [
        1190.2088694929646,
        349.6706252904999
      ],
      "error_px": 3.6745547252828534
    },
    {
      "node": [
        5,
        2
      ],
      "image": [
        1311,
        385
      ],
      "role": "calibration",
      "band": "far",
      "predicted_image": [
        1308.851522367961,
        387.7627132475154
      ],
      "error_px": 2.6778426017199477
    },
    {
      "node": [
        6,
        2
      ],
      "image": [
        1437,
        424
      ],
      "role": "validation",
      "band": "far",
      "predicted_image": [
        1437.0221060327408,
        428.91389309853264
      ],
      "error_px": 3.759871234889329
    },
    {
      "node": [
        7,
        2
      ],
      "image": [
        1576,
        469
      ],
      "role": "calibration",
      "band": "far",
      "predicted_image": [
        1575.9163859173018,
        473.5080841241113
      ],
      "error_px": 3.449924360854747
    },
    {
      "node": [
        1,
        3
      ],
      "image": [
        771,
        288
      ],
      "role": "validation",
      "band": "far",
      "predicted_image": [
        785.8062519854639,
        286.44325233527604
      ],
      "error_px": 11.391353551582771
    },
    {
      "node": [
        2,
        3
      ],
      "image": [
        874,
        321
      ],
      "role": "calibration",
      "band": "far",
      "predicted_image": [
        882.3558752377736,
        319.8517507660421
      ],
      "error_px": 6.453527121674999
    },
    {
      "node": [
        3,
        3
      ],
      "image": [
        990,
        356
      ],
      "role": "validation",
      "band": "far",
      "predicted_image": [
        986.1531051602166,
        355.76809591758916
      ],
      "error_px": 2.948769938827149
    },
    {
      "node": [
        4,
        3
      ],
      "image": [
        1103,
        395
      ],
      "role": "calibration",
      "band": "far",
      "predicted_image": [
        1098.0458406869918,
        394.4856812725476
      ],
      "error_px": 3.811015016273398
    },
    {
      "node": [
        5,
        3
      ],
      "image": [
        1223,
        434
      ],
      "role": "validation",
      "band": "far",
      "predicted_image": [
        1219.0196089539077,
        436.34552299090893
      ],
      "error_px": 3.5350117429595445
    },
    {
      "node": [
        6,
        3
      ],
      "image": [
        1352,
        479
      ],
      "role": "calibration",
      "band": "far",
      "predicted_image": [
        1350.2266705701336,
        481.7463310360737
      ],
      "error_px": 2.5013324440445417
    },
    {
      "node": [
        7,
        3
      ],
      "image": [
        1491,
        527
      ],
      "role": "validation",
      "band": "far",
      "predicted_image": [
        1493.0228372199304,
        531.1572489530942
      ],
      "error_px": 3.5374618277630256
    },
    {
      "node": [
        1,
        4
      ],
      "image": [
        685,
        333
      ],
      "role": "calibration",
      "band": "middle",
      "predicted_image": [
        680.8727503568576,
        325.5004292373722
      ],
      "error_px": 6.549813583854788
    },
    {
      "node": [
        2,
        4
      ],
      "image": [
        771,
        359
      ],
      "role": "validation",
      "band": "middle",
      "predicted_image": [
        778.0597800622454,
        361.9862144874186
      ],
      "error_px": 5.865111463716077
    },
    {
      "node": [
        3,
        4
      ],
      "image": [
        883,
        401
      ],
      "role": "calibration",
      "band": "middle",
      "predicted_image": [
        882.9047079962697,
        401.34691453920067
      ],
      "error_px": 0.27527120921527526
    },
    {
      "node": [
        4,
        4
      ],
      "image": [
        1002,
        445
      ],
      "role": "validation",
      "band": "middle",
      "predicted_image": [
        996.3497676256354,
        443.93626103803996
      ],
      "error_px": 4.399186773408743
    },
    {
      "node": [
        5,
        4
      ],
      "image": [
        1123,
        490
      ],
      "role": "calibration",
      "band": "middle",
      "predicted_image": [
        1119.498380800686,
        490.1684986912177
      ],
      "error_px": 2.682341217503711
    },
    {
      "node": [
        6,
        4
      ],
      "image": [
        1255,
        541
      ],
      "role": "validation",
      "band": "middle",
      "predicted_image": [
        1253.651165970423,
        540.5319034092786
      ],
      "error_px": 1.092432936890221
    },
    {
      "node": [
        7,
        4
      ],
      "image": [
        1393,
        596
      ],
      "role": "calibration",
      "band": "middle",
      "predicted_image": [
        1400.3520505782699,
        595.6060937412525
      ],
      "error_px": 5.633441690118532
    },
    {
      "node": [
        1,
        5
      ],
      "image": [
        567,
        369
      ],
      "role": "validation",
      "band": "middle",
      "predicted_image": [
        565.8078626684804,
        368.3285975908011
      ],
      "error_px": 1.0468696717041603
    },
    {
      "node": [
        2,
        5
      ],
      "image": [
        655,
        406
      ],
      "role": "calibration",
      "band": "middle",
      "predicted_image": [
        663.2929897128848,
        408.35072272960804
      ],
      "error_px": 6.595322549495995
    },
    {
      "node": [
        3,
        5
      ],
      "image": [
        769,
        454
      ],
      "role": "validation",
      "band": "middle",
      "predicted_image": [
        768.8610712603954,
        451.69127219038603
      ],
      "error_px": 1.7697034422975442
    },
    {
      "node": [
        4,
        5
      ],
      "image": [
        889,
        501
      ],
      "role": "calibration",
      "band": "middle",
      "predicted_image": [
        883.560880881674,
        498.7808157262852
      ],
      "error_px": 4.494773111995415
    },
    {
      "node": [
        5,
        5
      ],
      "image": [
        1012,
        552
      ],
      "role": "validation",
      "band": "middle",
      "predicted_image": [
        1008.6308338264325,
        550.1277797157743
      ],
      "error_px": 2.949177915869502
    },
    {
      "node": [
        6,
        5
      ],
      "image": [
        1140,
        609
      ],
      "role": "calibration",
      "band": "middle",
      "predicted_image": [
        1145.5438807845032,
        606.3368781149106
      ],
      "error_px": 4.705901798516729
    },
    {
      "node": [
        7,
        5
      ],
      "image": [
        1288,
        673
      ],
      "role": "validation",
      "band": "middle",
      "predicted_image": [
        1296.0657886753477,
        668.1330394000606
      ],
      "error_px": 7.207970336328134
    },
    {
      "node": [
        1,
        6
      ],
      "image": [
        429,
        411
      ],
      "role": "calibration",
      "band": "near",
      "predicted_image": [
        439.0698761562441,
        415.5015965148594
      ],
      "error_px": 8.439736251045368
    },
    {
      "node": [
        2,
        6
      ],
      "image": [
        529,
        457
      ],
      "role": "validation",
      "band": "near",
      "predicted_image": [
        536.3953795677992,
        459.61594739587196
      ],
      "error_px": 6.002101554331281
    },
    {
      "node": [
        3,
        6
      ],
      "image": [
        646,
        508
      ],
      "role": "calibration",
      "band": "near",
      "predicted_image": [
        642.2357421434587,
        507.5897952401758
      ],
      "error_px": 2.897248352754742
    },
    {
      "node": [
        4,
        6
      ],
      "image": [
        765,
        561
      ],
      "role": "validation",
      "band": "near",
      "predicted_image": [
        757.7595089642778,
        559.9528019135618
      ],
      "error_px": 5.597657716528402
    },
    {
      "node": [
        5,
        6
      ],
      "image": [
        889,
        620
      ],
      "role": "calibration",
      "band": "near",
      "predicted_image": [
        884.3592972791572,
        617.3361935983505
      ],
      "error_px": 4.0941958308460125
    },
    {
      "node": [
        6,
        6
      ],
      "image": [
        1023,
        685
      ],
      "role": "validation",
      "band": "near",
      "predicted_image": [
        1023.7082089948733,
        680.4983306624625
      ],
      "error_px": 3.4867871267372244
    },
    {
      "node": [
        7,
        6
      ],
      "image": [
        1165,
        755
      ],
      "role": "calibration",
      "band": "near",
      "predicted_image": [
        1177.8341897273367,
        750.3584120962137
      ],
      "error_px": 10.442477862768744
    },
    {
      "node": [
        1,
        7
      ],
      "image": [
        308,
        458
      ],
      "role": "validation",
      "band": "near",
      "predicted_image": [
        298.787556143758,
        467.71591609752414
      ],
      "error_px": 10.2445866054385
    },
    {
      "node": [
        2,
        7
      ],
      "image": [
        398,
        510
      ],
      "role": "calibration",
      "band": "near",
      "predicted_image": [
        395.3362929558614,
        516.6022512207514
      ],
      "error_px": 5.447319393156913
    },
    {
      "node": [
        3,
        7
      ],
      "image": [
        515,
        568
      ],
      "role": "validation",
      "band": "near",
      "predicted_image": [
        500.82507957448723,
        570.0152770629938
      ],
      "error_px": 10.954912278057362
    },
    {
      "node": [
        4,
        7
      ],
      "image": [
        628,
        628
      ],
      "role": "calibration",
      "band": "near",
      "predicted_image": [
        616.5559187463,
        628.6142476415122
      ],
      "error_px": 8.768967922047146
    },
    {
      "node": [
        5,
        7
      ],
      "image": [
        759,
        694
      ],
      "role": "validation",
      "band": "near",
      "predicted_image": [
        744.0965395928538,
        693.1929644471313
      ],
      "error_px": 11.41999211967498
    },
    {
      "node": [
        6,
        7
      ],
      "image": [
        889,
        766
      ],
      "role": "calibration",
      "band": "near",
      "predicted_image": [
        885.351832697661,
        764.7159467735619
      ],
      "error_px": 2.959228068647654
    },
    {
      "node": [
        7,
        7
      ],
      "image": [
        1029,
        845
      ],
      "role": "validation",
      "band": "near",
      "predicted_image": [
        1042.65963924053,
        844.366933436605
      ],
      "error_px": 10.46280230942786
    }
  ]
}
```

## docs/calibration/war_torn_observations.json

```text
{
  "schema_version": 1,
  "status": "diagnostic_only",
  "image": "assets/skins/war_torn/backgrounds/battlefield.png",
  "sha256": "f3ae6033599a5cc9047a8509c3d3f2269e3604513aa29cb0ec7e4db1051f5d2a",
  "image_size": [1672, 941],
  "viewport_size": [1280, 720],
  "physical_span": [2, 6],
  "corners": {"p00":[1169,278],"p10":[1392,342],"p11":[757,694],"p01":[515,568]},
  "samples": [
    {"node":[1,1],"image":[1196,349],"band":"far"},
    {"node":[1,2],"image":[1103,395],"band":"middle"},
    {"node":[1,3],"image":[1000,445],"band":"middle"},
    {"node":[1,4],"image":[883,503],"band":"near"},
    {"node":[1,5],"image":[765,561],"band":"near"}
  ],
  "annotation": "Manually read seam-center intersections from native PNG. Four corners define a visible 2x6 stone strip; five interior landmarks are independent of the homography. This is not an 8x8 game calibration; no projected/interpolated point is an observation. Seam width and hand annotation introduce several source pixels of uncertainty."
}
```

## docs/calibration/war_torn_report.json

```text
{
  "image_sha256": "f3ae6033599a5cc9047a8509c3d3f2269e3604513aa29cb0ec7e4db1051f5d2a",
  "viewport_size": [
    1280,
    720
  ],
  "scale": 0.7651434643995749,
  "offset": [
    0.34006376195532084,
    0.0
  ],
  "measured_physical_span": [
    2,
    6
  ],
  "interior": {
    "count": 5,
    "mean_px": 5.555742450788599,
    "max_px": 11.713753031428595
  },
  "bands": {
    "far": {
      "count": 1,
      "mean_px": 0.5573474339180795,
      "max_px": 0.5573474339180795
    },
    "middle": {
      "count": 2,
      "mean_px": 4.957335080837491,
      "max_px": 6.4567896284244375
    },
    "near": {
      "count": 2,
      "mean_px": 8.653347329174967,
      "max_px": 11.713753031428595
    }
  },
  "points": [
    {
      "node": [
        1,
        1
      ],
      "observed_image": [
        1196,
        349
      ],
      "predicted_image": [
        1195.6332979159592,
        348.3706126911767
      ],
      "band": "far",
      "error_viewport_px": 0.5573474339180795
    },
    {
      "node": [
        1,
        2
      ],
      "observed_image": [
        1103,
        395
      ],
      "predicted_image": [
        1106.5870081675023,
        392.25098871598135
      ],
      "band": "middle",
      "error_viewport_px": 3.457880533250545
    },
    {
      "node": [
        1,
        3
      ],
      "observed_image": [
        1000,
        445
      ],
      "predicted_image": [
        1007.4781687030768,
        441.09000441631093
      ],
      "band": "middle",
      "error_viewport_px": 6.4567896284244375
    },
    {
      "node": [
        1,
        4
      ],
      "observed_image": [
        883,
        503
      ],
      "predicted_image": [
        896.4989793291396,
        495.77851052266146
      ],
      "band": "near",
      "error_viewport_px": 11.713753031428595
    },
    {
      "node": [
        1,
        5
      ],
      "observed_image": [
        765,
        561
      ],
      "predicted_image": [
        771.3810113907315,
        557.4343470106937
      ],
      "band": "near",
      "error_viewport_px": 5.592941626921337
    }
  ],
  "local_threshold_met": true,
  "requested_8x8_verified": false,
  "reason": "This is a diagnostic strip, not a measured complete 8x8 region. No acceptance claim or automatic config export.",
  "extent_diagnostic": {
    "search_origins": "integer col,row in [-16,8] relative to diagnostic strip",
    "warning": "EXTRAPOLATION ONLY; not measured corners, not a proof of global image topology. y>=160 is a loose necessary paving bound, not a segmentation mask.",
    "candidates_inside_png": [
      {
        "origin_node": [
          -7,
          -6
        ],
        "predicted_corners_image": [
          [
            1007.766781394511,
            8.885847752626422
          ],
          [
            1632.1834571864924,
            133.2467125647118
          ],
          [
            1106.5870081675023,
            392.25098871598135
          ],
          [
            421.15897472028377,
            161.16958254357505
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -8,
          -5
        ],
        "predicted_corners_image": [
          [
            888.7975662918429,
            10.879845993751086
          ],
          [
            1487.9434231661612,
            136.57248819849127
          ],
          [
            894.9700207505363,
            399.51176449899776
          ],
          [
            260.08070922354034,
            164.88360115261818
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -7,
          -5
        ],
        "predicted_corners_image": [
          [
            950.3469531657903,
            23.79206924207277
          ],
          [
            1584.3797286976273,
            156.80351192608458
          ],
          [
            1007.4781687030768,
            441.09000441631093
          ],
          [
            320.6409876543209,
            187.2641116478799
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -10,
          -4
        ],
        "predicted_corners_image": [
          [
            712.5869153296396,
            0.49459353695966957
          ],
          [
            1254.9293141154353,
            120.70087350206545
          ],
          [
            584.5655523730104,
            368.1951343316052
          ],
          [
            44.79247269732835,
            147.42343777420805
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -9,
          -4
        ],
        "predicted_corners_image": [
          [
            768.5368403275751,
            12.895490762376134
          ],
          [
            1341.7469408008071,
            139.94337411166592
          ],
          [
            679.2307253403918,
            406.9139805057519
          ],
          [
            96.69226478601212,
            168.65088608874672
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -8,
          -4
        ],
        "predicted_corners_image": [
          [
            827.3508168948523,
            25.931184355455535
          ],
          [
            1434.1530003505206,
            160.4245105479345
          ],
          [
            782.7719460871547,
            449.26320433444204
          ],
          [
            152.13102349374344,
            191.32580129996083
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -7,
          -4
        ],
        "predicted_corners_image": [
          [
            889.2545358094605,
            39.65169704889443
          ],
          [
            1532.7050263457245,
            182.26785610681048
          ],
          [
            896.4989793291396,
            495.77851052266146
          ],
          [
            211.48350069326378,
            215.60146005288604
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -6,
          -4
        ],
        "predicted_corners_image": [
          [
            954.4980404684621,
            54.112449157715226
          ],
          [
            1638.0372671259283,
            205.6139873569656
          ],
          [
            1021.9926156067783,
            547.106455600652
          ],
          [
            275.1792957234271,
            241.65357206416033
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -8,
          -3
        ],
        "predicted_corners_image": [
          [
            761.9513330512061,
            41.950742260006855
          ],
          [
            1375.9750880604395,
            186.2220557530164
          ],
          [
            656.990495141114,
            505.03785383650916
          ],
          [
            34.83130264387665,
            220.05828602162282
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -7,
          -3
        ],
        "predicted_corners_image": [
          [
            824.1255390388966,
            56.559223267544084
          ],
          [
            1476.6693235413761,
            209.8812212095559
          ],
          [
            771.3810113907315,
            557.4343470106937
          ],
          [
            92.52265220087281,
            246.48376693016579
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -6,
          -3
        ],
        "predicted_corners_image": [
          [
            889.7680322756171,
            71.98261469655351
          ],
          [
            1584.5939708335945,
            235.2392476638973
          ],
          [
            898.402306432735,
            615.6163592687833
          ],
          [
            154.63259752959434,
            274.9331824338416
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -6,
          -2
        ],
        "predicted_corners_image": [
          [
            820.4872712286111,
            91.10911727443413
          ],
          [
            1526.2649212996964,
            267.57283102756986
          ],
          [
            757.0,
            693.9999999999999
          ],
          [
            22.295363327089905,
            311.46783379840235
          ]
        ],
        "all_y_at_least_160": false
      },
      {
        "origin_node": [
          -5,
          -2
        ],
        "predicted_corners_image": [
          [
            890.3492357143417,
            108.5765189440677
          ],
          [
            1645.4598273853105,
            297.37481722847207
          ],
          [
            900.8366809351335,
            768.8901727182925
          ],
          [
            87.23017237373969,
            345.276866607815
          ]
        ],
        "all_y_at_least_160": false
      }
    ],
    "candidates_above_loose_paving_bound": 0
  }
}
```

## docs/references/architecture_proposal.md

````markdown
# 原始架构整改意见（评审材料）

以下保留用户提供的意见原文内容，仅规范化行尾空白以便纳入仓库。原文中的要求和实施状态属于提案；当前采纳后的开发决策、实施状态分别见上级目录的 ARCHITECTURE_REVIEW.md、ARCHITECTURE.md、ROADMAP.md 及项目 TASKS.md。

---

# Chrono Tactics 战棋 Demo 项目架构整改报告

**项目名称：** Chrono Tactics · 离线回溯战棋
**项目仓库：** https://github.com/zyb-sjtu/chrono-tactics-pygame
**整改目标：** 建立职责清晰、模块解耦、便于后续功能扩展和自动化测试的项目架构。
**整改原则：** 保留现有功能、渐进式重构、控制抽象复杂度、以测试验证行为一致性。

## 一、整改背景与目标

当前项目已实现 8×8 网格棋盘、单位属性管理、四方向移动、攻击结算、速度排序、战斗特效及行动回溯等功能。现有代码按照 `board.py`、`battle.py`、`effects.py`、`game.py`、`models.py` 和 `panel.py` 等模块进行了初步拆分，并具有 41 项现有回归检查。

随着项目继续开发，预计将引入美术资源、角色动画、技能系统、AI 对手、多地图配置和存档等功能。现有结构虽然能够满足当前原型的运行需求，但部分模块仍然承担多种职责，模块之间也存在直接访问内部状态的情况。

本次整改不以增加文件数量或引入设计模式为目标，而是建立稳定的模块边界，使新增功能能够在较小的修改范围内完成，并尽量避免对既有战斗规则造成影响。

具体目标如下：

1. 分离游戏规则、应用流程和 Pygame 表现层。
2. 将地图配置与地图逻辑解耦，支持后续新增关卡。
3. 统一图片资源的加载、缓存和访问方式。
4. 明确玩家指令、战斗结果与动画流程之间的交互契约。
5. 保持现有功能及操作方式不变，完善回归测试和开发文档。

## 二、现有架构问题

### 2.1 地图逻辑与渲染职责混合

当前 `tactics/board.py` 同时承担单位与障碍物管理、BFS 移动范围计算、空间查询和地图绘制等职责。

绘制代码直接使用 Pygame 绘图接口，并且会读取战斗对象以判断当前移动范围、攻击范围和选中状态。

这导致地图状态管理、战术规则和视觉表现之间存在耦合。后续替换地砖、增加地图装饰或修改单位绘制方式时，容易反复修改同一模块。

**整改要求：** 将地图状态与寻路逻辑保留在 `board.py`，将格子到屏幕坐标的转换放入 `geometry.py`，将地图、单位、障碍物及高亮绘制迁移至 `board_renderer.py`。

### 2.2 主循环承担过多流程协调职责

当前 `tactics/game.py` 同时处理键鼠事件、按钮命中测试、战斗操作、特效触发和动画结束后的行动交接。

例如，主循环直接读取 `battle.pending_attack`，再将其传给 `effects.play_attack()`。这使主循环需要了解战斗模块的内部状态。

**整改要求：** 新增 `controller.py` 作为应用协调层，集中处理玩家操作、战斗调用、特效生命周期和行动交接。`game.py` 主要负责 Pygame 初始化、事件接收、帧更新和绘制调度。

### 2.3 场景配置与地图初始化绑定

当前 `Board` 初始化时直接创建双方单位并加载固定障碍物，初始场景定义与地图对象存在绑定。

如果后续新增不同地图、单位阵容或测试场景，就需要修改现有初始化逻辑。

**整改要求：** 新增 `scenario.py`，统一管理场景定义、初始单位、起始位置和障碍物配置。地图对象通过场景数据初始化，不再负责决定默认关卡内容。

### 2.4 美术资源管理尚未建立

目前单位、地砖、障碍物和击杀效果均使用程序绘制的几何图形，项目尚无统一的图片资源管理模块。

如果直接在各个绘制函数中加载图片，容易造成资源路径分散、重复读取、缩放逻辑不统一和资源缺失难以定位等问题。

**整改要求：** 新增 `assets.py`，统一负责资源路径解析、图片加载、缓存和缩放。游戏逻辑对象不保存 Pygame 图片对象，资源管理与战斗状态分离。

### 2.5 界面布局与事件处理耦合

当前 `game.py` 直接访问 `panel.undo_button`、`panel.skip_button` 等按钮矩形，主循环需要了解侧栏内部的布局细节。

**整改要求：** 由 `panel.py` 提供统一的按钮命中测试接口，返回明确的 UI 动作标识。主循环只处理动作结果，不依赖具体按钮的位置和尺寸。

## 三、目标架构设计

整改后采用三层结构，不引入复杂的插件系统或依赖注入框架。

### 3.1 游戏规则层

负责表达游戏状态和规则，不依赖 Pygame。

- `models.py`：单位、格子坐标等基础数据模型。
- `scenario.py`：场景定义和默认阵容。
- `board.py`：地图状态、障碍物、单位位置查询和 BFS 寻路。
- `battle.py`：攻击结算、行动顺序、回合推进、战斗结束和回溯。

该层不负责图片加载、按钮绘制或窗口事件处理。

### 3.2 应用协调层

负责接收操作、调用规则和协调战斗流程。

- `controller.py`：统一处理移动、攻击、跳过、结束行动和回溯等操作，协调攻击结果与动画完成后的行动交接。
- `view_models.py`：定义提供给表现层的只读视图数据，例如当前行动者、选中单位、可移动格、攻击范围和可攻击目标。

该层负责组织流程，但不直接绘制图形。

### 3.3 表现层与资源层

负责窗口、输入、绘制、动画和美术资源。

- `game.py`：Pygame 主循环、事件分发和生命周期管理。
- `geometry.py`：格子坐标与屏幕坐标转换。
- `board_renderer.py`：地砖、单位、障碍物、血条和战术高亮的绘制。
- `panel.py`：属性面板、按钮、日志和行动顺序展示。
- `effects.py`：伤害跳字、击杀动画及后续战斗特效。
- `assets.py`：图片资源加载、缓存和缩放。

建议目录如下：

```text
chrono-tactics-pygame/
├── main.py
├── assets/
│   ├── tiles/
│   ├── units/
│   ├── obstacles/
│   ├── effects/
│   └── ui/
├── tactics/
│   ├── models.py
│   ├── scenario.py
│   ├── settings.py
│   ├── board.py
│   ├── battle.py
│   ├── controller.py
│   ├── view_models.py
│   ├── geometry.py
│   ├── board_renderer.py
│   ├── assets.py
│   ├── effects.py
│   ├── panel.py
│   └── game.py
├── tests/
├── docs/
│   └── REFACTOR_REPORT.md
├── scripts/
├── README.md
├── TASKS.md
├── CHANGELOG.md
└── SOURCE.md
```

以上为目标结构，不要求一次性创建所有抽象或扩展模块。只有在职责已经明确、存在实际调用需求时才增加相应模块。

## 四、核心接口与数据契约

### 4.1 地图渲染接口

`Board` 提供地图数据、单位位置和寻路结果；`BoardRenderer` 接收地图数据与视图状态后完成绘制。

渲染器不直接调用 `Battle` 的规则方法，也不负责决定某个格子是否合法。

视图数据至少包含：

- 当前行动者和选中单位的 ID。
- 当前阶段。
- 可移动格集合。
- 攻击范围集合。
- 可攻击目标格集合。

### 4.2 控制器接口

控制器统一提供以下操作：

- `move_to(cell)`：请求移动。
- `attack(target_id)`：请求攻击。
- `skip_phase()`：跳过当前阶段。
- `end_turn()`：结束当前行动。
- `undo()`：回溯上一单位行动。
- `update(elapsed)`：推进非阻塞动画及必要的行动交接。
- `get_view_state()`：生成供表现层使用的状态数据。

上述方法为目标接口示意。实施时应尽量复用现有 `Battle` 方法，避免同时维护两套战斗规则。

### 4.3 战斗结果与动画解耦

攻击结算应产生明确的结果数据，包括攻击者、目标、伤害量和是否击杀等信息。

表现层根据结果播放动画；动画结束后由协调层推进下一次行动。

第一阶段允许保留现有 `resolving` 阶段和 `pending_attack` 机制，以确保行为一致。后续如确有必要，再逐步将战斗结果与表现层的动画时序进一步解耦。

### 4.4 资源管理接口

`AssetManager` 统一管理资源路径与缓存，并提供按资源 ID 获取图片的接口。

单位数据只保存稳定的单位 ID、阵营、职业、坐标和战斗属性。图片对象、动画帧、缩放结果及渲染偏移均由表现层维护。

资源缺失应产生明确错误或使用预先约定的占位资源，不得导致战斗规则和单位状态异常。

## 五、整改实施计划

### 第一阶段：职责拆分

1. 将初始阵容和障碍配置提取至 `scenario.py`。
2. 将 Pygame 绘制代码从 `board.py` 迁移至 `board_renderer.py`。
3. 将屏幕坐标转换提取至 `geometry.py`。
4. 保持 `Board` 的 BFS 寻路和空间查询行为不变。

**验收标准：** 初始单位位置、障碍物布局、移动范围、攻击范围、选中状态和血条显示与原版一致。

### 第二阶段：操作流程解耦

1. 新增 `controller.py`，统一接收玩家操作并调用战斗规则。
2. 新增 `view_models.py`，为表现层提供明确的状态数据。
3. 将按钮命中测试封装在 `panel.py`。
4. 减少 `game.py` 对战斗内部临时字段的直接访问。

**验收标准：** 移动、攻击、跳过、结束行动、击杀、回溯及窗口关闭行为保持一致；动画期间的操作锁定不被破坏。

### 第三阶段：资源管理基础建设

1. 新增 `assets.py`，建立统一的图片加载和缓存机制。
2. 建立 `assets/` 目录及资源命名规范。
3. 预留地砖、单位、障碍物、特效和 UI 图标的资源映射。
4. 暂时保留原有几何绘制作为无资源时的默认表现。

**验收标准：** 资源只加载一次，缺失资源可定位，当前无美术资源的版本仍能正常启动和运行。

### 第四阶段：测试与文档完善

1. 保留全部 41 项现有回归检查。
2. 新增场景配置、地图渲染数据、资源缓存和控制器操作测试。
3. 更新 `README.md`、`TASKS.md` 和 `CHANGELOG.md`。
4. 更新源码汇总脚本，确保 `SOURCE.md` 与实际代码一致。
5. 使用 GitHub Actions 执行回归测试，并单独检查真实窗口的显示效果。

**验收标准：** 所有自动化测试通过；原有交互流程保持一致；文档、源码汇总与项目目录同步。

## 六、验收与质量要求

整改完成后应满足以下要求：

| 检查项 | 验收要求 |
|---|---|
| 规则独立性 | `models.py`、`board.py`、`battle.py` 不依赖 Pygame |
| 渲染隔离 | `board_renderer.py` 不决定移动、攻击和回溯规则 |
| 场景扩展 | 可以通过独立场景配置初始化不同阵容或障碍布局 |
| 流程协调 | `game.py` 不直接承担完整的战斗业务流程 |
| 资源管理 | 图片集中加载和缓存，不在每帧重复读取文件 |
| 功能回归 | 原有 41 项测试继续通过 |
| 测试覆盖 | 新增架构接口与资源管理测试 |
| 文档一致性 | README、任务记录、更新日志和源码汇总同步更新 |

自动化测试通过并不等于真实窗口的视觉表现已通过验收。对于后续美术资源，还需检查透明背景、缩放、图层顺序、血条可读性、选中高亮和动画播放效果。

## 七、风险控制与暂缓事项

本次整改以最小行为变化为原则，不同时引入新玩法。

- 暂不增加 AI、技能系统、存档和联网功能。
- 暂不迁移至 Unity、Godot 或其他游戏引擎。
- 暂不建立复杂的抽象工厂、插件机制或全面的 `Protocol`/`ABC` 体系。
- 不将 Pygame 图片对象写入单位模型或战斗回溯快照。
- 不改变当前攻击伤害、行动顺序、寻路规则和回溯语义。
- 任何涉及行为变化的修改都必须增加相应测试，并在文档中明确记录。

建议在独立分支中完成整改，先通过自动化测试，再审查差异并合并，避免直接修改稳定版本。

## 八、整改结论

Chrono Tactics 当前已经具备可继续迭代的基础结构，没有必要推翻现有实现。下一阶段的重点是明确规则层、协调层和表现层的职责边界，提取地图渲染、场景配置和资源管理，并完善自动化验证。

整改完成后，新增地砖和角色美术应主要影响资源管理与渲染模块；新增地图应主要影响场景配置；新增技能和 AI 应主要扩展规则与协调模块，而不必持续修改主循环。

**最终目标是建立一套可持续扩展的战棋原型架构，而不是在当前规模下提前构建完整游戏引擎。**

**实施状态：** 本报告为整改方案。实际代码修改、自动化测试和合并均须在具备仓库写入权限的环境中完成并验证。
````

## docs/references/perspective_battlefield_design.md

````markdown
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
````

## docs/templates/FEATURE_TEMPLATE.md

````markdown
# 功能变更模板

复制本模板到任务说明或 PR；小功能可以压缩成几句话。未涉及的项目注明原因，不要求新增空模块。规范见 [功能开发规范](../FEATURE_DEVELOPMENT.md)。

## 玩家行为与范围

- 触发条件、当前行为、预期行为：
- 具体示例（输入 → 结果）：
- 明确不涉及的玩法：
- 所需前置能力及当前实现位置：

## 数据与指令

| 数据/状态 | 唯一归属与初始化 | 修改入口与合法性 | 死亡/结束行为 | 快照/恢复 |
| --- | --- | --- | --- | --- |
| 填写实际字段；纯外观不加规则状态 | content / Scenario / Battle / Controller / presentation | Controller 指令 → 规则验证 | 明确保留、移除或重置 | 新 Unit 字段同步 UnitSnapshot 与恢复；资源不入快照 |

- UI 和未来 AI 共用哪个指令？失败是否无状态、副作用和行动消耗？
- 外部拿到的是哪些独立只读视图/结果？实例用 UID、定义用 definition_id，避免保留跨回溯实体引用。
- 有延迟表现时：阻塞还是非阻塞？匹配哪个结算 token？回溯/重开怎样清理，旧通知怎样拒绝？
- 只有真实需要才新增模块/抽象；写明当前调用方。

## 内容和美术

- 新定义、场景和 schema 变化：
- 素材来源/授权、PNG 路径、尺寸、脚底 pivot、状态与帧速率：
- 必需/可选资源与失败回退：
- 清单预载/缓存、图层、点击占格是否仍符合规范：
- 数据格式若不兼容，说明迁移、回退与错误提示；没有格式变化则省略。

## 验收证据

- [ ] 正常操作；敌我/范围/资源不足等非法操作无副作用。
- [ ] 新状态经过连续回溯、跨轮、死亡、结束后恢复；快照字段覆盖检查通过。
- [ ] 异步效果锁定、完成一次、重复/旧 token、回溯后取消表现通过。
- [ ] 同一指令在几何/两套素材下规则状态一致；资源缺失行为符合清单约定。
- [ ] 按改动运行相关纯测试与完整回归，记录实际通过/跳过/失败及原因。
- [ ] 需要观察时，记录实际窗口驱动和截图；自动投递事件与人工操作分开说明。
- [ ] 更新 TASKS、CHANGELOG、README、资源来源和相关接口说明，重新导出 SOURCE。
- [ ] 在专用分支审查差异；发布时包、tag、Release 对应同一提交并验证解压产物。

填写实际命令、结果、截图位置和仍未验证的限制：
````

## main.py

```python
"""Run the offline tactics prototype."""

from tactics.game import Game
from tactics.data_files import DataError
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario",
                        help="JSON path relative to content root")
    parser.add_argument("--content-root", help="unit definitions and scenarios root")
    parser.add_argument("--assets", help="asset root containing manifest.json")
    parser.add_argument("--geometry", action="store_true", help="use geometry without loading asset files")
    parser.add_argument("--presentation", help="presentation JSON path relative to project root (exclusive with content/asset flags)")
    parser.add_argument("--debug-grid", action="store_true", help="show perspective corners, grid, centers and coordinates (F3 toggles)")
    args = parser.parse_args()
    try:
        Game(content_root=args.content_root, scenario_file=args.scenario,
             asset_root=args.assets, geometric=args.geometry,
             presentation_file=args.presentation, debug_grid=args.debug_grid).run()
    except DataError as error:
        parser.exit(2, "Configuration error: {}\n".format(error))
```

## presentations/war_torn_8x8.json

```text
{
  "schema_version": 1,
  "id": "war_torn_8x8",
  "mode": "perspective",
  "scenario_file": "scenarios/war_torn.json",
  "asset_root": "assets/skins/war_torn",
  "viewport": {
    "reference_size": [
      1280,
      720
    ],
    "background_fit": "contain"
  },
  "board": {
    "cols": 8,
    "rows": 8,
    "reference_image_size": [
      1672,
      941
    ],
    "corners": {
      "p00": [
        785.8062519854639,
        286.44325233527604
      ],
      "p10": [
        1493.02283721993,
        531.1572489530942
      ],
      "p11": [
        1042.6596392405297,
        844.3669334366049
      ],
      "p01": [
        298.78755614375797,
        467.71591609752414
      ]
    },
    "reference_region": [
      1,
      3,
      6,
      4
    ],
    "cells": [
      [
        3,
        2
      ],
      [
        4,
        2
      ],
      [
        5,
        2
      ],
      [
        6,
        2
      ],
      [
        1,
        3
      ],
      [
        2,
        3
      ],
      [
        3,
        3
      ],
      [
        4,
        3
      ],
      [
        5,
        3
      ],
      [
        6,
        3
      ],
      [
        1,
        4
      ],
      [
        2,
        4
      ],
      [
        3,
        4
      ],
      [
        4,
        4
      ],
      [
        5,
        4
      ],
      [
        6,
        4
      ],
      [
        1,
        5
      ],
      [
        2,
        5
      ],
      [
        3,
        5
      ],
      [
        4,
        5
      ],
      [
        5,
        5
      ],
      [
        6,
        5
      ],
      [
        1,
        6
      ],
      [
        2,
        6
      ],
      [
        3,
        6
      ],
      [
        4,
        6
      ],
      [
        5,
        6
      ],
      [
        6,
        6
      ]
    ]
  },
  "hud": {
    "layout": "overlay",
    "safe_margin": 24
  },
  "debug": {
    "show_grid": false,
    "show_cell_centers": false,
    "show_coordinates": false
  }
}
```

## requirements.txt

```text
pygame==2.6.1
```

## scripts/build_release.py

```python
"""Build a reproducible source ZIP from an exact committed Git tree."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def build(ref="HEAD", output_dir=None):
    commit = git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    version = git("show", commit + ":VERSION.txt").decode().strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("VERSION.txt must contain a numeric semantic version")
    folder = Path(output_dir) if output_dir else ROOT / "dist"
    folder.mkdir(parents=True, exist_ok=True)
    name = "chrono-tactics-pygame-{}".format(version)
    archive = folder / (name + "-source.zip")
    git("archive", "--format=zip", "--prefix=" + name + "/", "--output=" + str(archive.resolve()), commit)
    with zipfile.ZipFile(archive, "a") as package:
        package.comment = json.dumps({"format": "chrono-tactics-source-v1", "version": version,
                                      "commit": commit}, sort_keys=True).encode("ascii")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(digest + "  " + archive.name + "\n", encoding="ascii")
    return {"archive": str(archive.resolve()), "checksum": str(checksum.resolve()),
            "version": version, "commit": commit, "sha256": digest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.ref, args.output_dir), indent=2))
```

## scripts/calibrate_board.py

```python
"""Inspect measured seams or collect a draft homography calibration; never changes gameplay config."""

import argparse
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tactics.data_files import DataError, fields, read_json, rooted_path, version
from tactics.perspective_geometry import BackgroundFit, PerspectiveBoardGeometry, pair
from tactics.presentation_layout import size_pair

DEFAULT = ROOT / "docs/calibration/war_torn_observations.json"
CORNER_NAMES = ("p00", "p10", "p11", "p01")


def load_observations(path):
    data = read_json(path)
    label = str(path)
    fields(data, ("schema_version", "status", "image", "sha256", "image_size", "viewport_size",
                  "physical_span", "corners", "samples", "annotation"), (), label)
    version(data, label)
    if data["status"] not in ("diagnostic_only", "draft"):
        raise DataError(label + ": observations must be diagnostic_only or draft")
    image = rooted_path(ROOT, data["image"], label + ".image")
    raw = image.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or len(raw) < 24:
        raise DataError(label + ": invalid native PNG")
    if hashlib.sha256(raw).hexdigest() != data["sha256"]:
        raise DataError(label + ": background SHA256 changed; recheck annotations")
    native = struct.unpack(">II", raw[16:24])
    if native != size_pair(data["image_size"], label + ".image_size"):
        raise DataError(label + ": native image size differs from observations")
    span = size_pair(data["physical_span"], label + ".physical_span")
    viewport = size_pair(data["viewport_size"], label + ".viewport_size")
    fields(data["corners"], CORNER_NAMES, (), label + ".corners")
    try:
        geometry = PerspectiveBoardGeometry(*span,
            tuple(data["corners"][key] for key in CORNER_NAMES), native, viewport)
    except (TypeError, ValueError) as error:
        raise DataError(label + ": " + str(error)) from error
    if not isinstance(data["samples"], list) or not data["samples"]:
        raise DataError(label + ": independent interior samples are required")
    seen = set()
    for sample in data["samples"]:
        fields(sample, ("node", "image", "band"), (), label + ".sample")
        node = pair(sample["node"], "sample node")
        point = pair(sample["image"], "sample image")
        if (any(type(v) is not int for v in node)
                or not (0 < node[0] < geometry.cols and 0 < node[1] < geometry.rows)
                or not (0 <= point[0] < native[0] and 0 <= point[1] < native[1])
                or node in seen or sample["band"] not in ("far", "middle", "near")):
            raise DataError(label + ": duplicate, outside, or invalid interior sample")
        seen.add(node)
    return data, geometry


def measure(data, geometry):
    """Only held-out observations enter error statistics; four fitted corners do not."""
    errors = []
    for sample in data["samples"]:
        projected = geometry.project(sample["node"])
        observed = geometry.fit.to_screen(sample["image"])
        errors.append({"node": sample["node"], "observed_image": sample["image"],
                       "predicted_image": list(geometry.fit.to_image(projected)),
                       "band": sample["band"], "error_viewport_px": math.dist(projected, observed)})

    def statistics(points):
        values = [point["error_viewport_px"] for point in points]
        return {"count": len(values), "mean_px": sum(values)/len(values), "max_px": max(values)}

    summary = statistics(errors)
    report = {"image_sha256": data["sha256"], "viewport_size": list(geometry.viewport_size),
              "scale": geometry.fit.scale, "offset": list(geometry.fit.offset),
              "measured_physical_span": data["physical_span"], "interior": summary,
              "bands": {band: statistics([p for p in errors if p["band"] == band])
                        for band in ("far", "middle", "near") if any(p["band"] == band for p in errors)},
              "points": errors, "local_threshold_met": summary["mean_px"] <= 6 and summary["max_px"] <= 12,
              "requested_8x8_verified": False,
              "reason": "This is a diagnostic strip, not a measured complete 8x8 region. No acceptance claim or automatic config export."}
    return report


def inspect_extent(geometry):
    """Finite diagnostic search, never promotes extrapolated vertices to measurements."""
    candidates = []
    for row in range(-16, 9):
        for col in range(-16, 9):
            nodes = ((col,row),(col+8,row),(col+8,row+8),(col,row+8))
            try:
                points = [geometry.fit.to_image(geometry.project(node)) for node in nodes]
            except ValueError:
                continue
            if all(0 <= x <= geometry.reference_size[0] and 0 <= y <= geometry.reference_size[1]
                   for x,y in points):
                candidates.append({"origin_node": [col,row], "predicted_corners_image": points,
                                   "all_y_at_least_160": all(y >= 160 for _,y in points)})
    return {"search_origins": "integer col,row in [-16,8] relative to diagnostic strip",
            "warning": "EXTRAPOLATION ONLY; not measured corners, not a proof of global image topology. y>=160 is a loose necessary paving bound, not a segmentation mask.",
            "candidates_inside_png": candidates,
            "candidates_above_loose_paving_bound": sum(c["all_y_at_least_160"] for c in candidates)}


def capture_game(data, geometry, output):
    import pygame
    from tactics.game import Game

    game = Game(presentation_file="presentations/war_torn_8x8.json", debug_grid=True)
    try:
        geometry = replace(geometry, viewport_size=game.screen.get_size())
        game.draw()
        font = pygame.font.Font(None, 18)
        polygon = [geometry.fit.to_screen(data["corners"][key]) for key in CORNER_NAMES]
        pygame.draw.polygon(game.screen, (255,210,70), polygon, 2)
        for key, point in zip(CORNER_NAMES, polygon):
            pygame.draw.circle(game.screen, (255,210,70), point, 5, 1)
            game.screen.blit(font.render("REF " + key, True, (255,230,90)), (point[0]+6,point[1]-20))
        for sample in data["samples"]:
            observed = geometry.fit.to_screen(sample["image"])
            predicted = geometry.project(sample["node"])
            pygame.draw.line(game.screen, (255,160,110), observed, predicted, 2)
            pygame.draw.circle(game.screen, (80,255,170), observed, 4, 1)
            pygame.draw.circle(game.screen, (255,140,140), predicted, 2)
            game.screen.blit(font.render("REF {},{}".format(*sample["node"]), True, (110,255,180)),
                             (observed[0]+5,observed[1]+4))
        pygame.display.flip()
        pygame.event.pump()
        pygame.image.save(game.screen, str(output))
        print("Actual Game diagnostic screenshot; SDL driver=" + pygame.display.get_driver())
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        game.run()
    finally:
        pygame.quit()


def pick(image_path, cols, rows, output):
    """Four corners followed by row-major interior samples; saves raw mouse observations only."""
    import pygame

    raw = image_path.read_bytes()
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1280,720))
    pygame.display.set_caption("Homography calibration DRAFT - native image coordinates")
    original = pygame.image.load(str(image_path)).convert_alpha()
    fit = BackgroundFit(original.get_size(), screen.get_size())
    background = pygame.transform.smoothscale(original, tuple(round(v*fit.scale) for v in original.get_size()))
    font = pygame.font.Font(None, 22)
    order = [(0,0),(cols,0),(cols,rows),(0,rows)]
    order += [(col,row) for row in range(1,rows) for col in range(1,cols)]
    points, geometry, error, preview = [], None, "", True
    clock = pygame.time.Clock()
    running = True
    try:
        while running:
            changed = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                      and event.pos[1] >= 76 and len(points) < len(order)):
                    point = fit.to_image(event.pos)
                    if 0 <= point[0] < original.get_width() and 0 <= point[1] < original.get_height():
                        points.append(tuple(round(v,2) for v in point))
                        changed = True
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_BACKSPACE,pygame.K_z) and points:
                        points.pop()
                        changed = True
                    elif event.key == pygame.K_p:
                        preview = not preview
                    elif event.key == pygame.K_s:
                        result = {"schema_version":1,"status":"draft", "image":image_path.relative_to(ROOT).as_posix(),
                                  "sha256":hashlib.sha256(raw).hexdigest(), "image_size":list(original.get_size()),
                                  "viewport_size":[1280,720],"physical_span":[cols,rows],
                                  "corners":dict(zip(CORNER_NAMES,points[:4])),
                                  "samples":[{"node":node,"image":point,"band":"far" if node[1]<rows/3 else "near" if node[1]>rows*2/3 else "middle"}
                                             for node,point in zip(order[4:],points[4:])],
                                  "annotation":"Draft raw clicks only. Verify stone counts and independent seam landmarks before runtime adoption."}
                        output.parent.mkdir(parents=True,exist_ok=True)
                        output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                        error = "DRAFT saved: " + str(output)
            if changed:
                geometry, error = None, ""
                if len(points) >= 4:
                    try:
                        geometry = PerspectiveBoardGeometry(cols,rows,tuple(points[:4]),original.get_size())
                    except ValueError as problem:
                        error = str(problem)
            screen.fill((21,30,42))
            screen.blit(background,tuple(round(v) for v in fit.offset))
            if preview and geometry is not None:
                for row in range(rows):
                    for col in range(cols):
                        pygame.draw.polygon(screen,(140,215,235),geometry.cell_polygon((col,row)),1)
            for index,point in enumerate(points):
                screen_point = fit.to_screen(point)
                pygame.draw.circle(screen,(80,255,160),screen_point,4,1)
                screen.blit(font.render(str(order[index]),True,(245,230,150)),screen_point)
            next_point = str(order[len(points)]) if len(points)<len(order) else "all observations collected"
            bar = pygame.Surface((1280,76),pygame.SRCALPHA)
            bar.fill((15,22,30,220))
            screen.blit(bar,(0,0))
            for index,line in enumerate(("DRAFT: pick real seam intersections. Next="+next_point,
                                         "Left: mark | Backspace/Z: undo | P: preview | S: save draft | Esc: quit",
                                         error)):
                screen.blit(font.render(line,True,(240,232,206)),(12,6+index*22))
            pygame.display.flip()
            clock.tick(30)
    finally:
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations",type=Path,default=DEFAULT)
    parser.add_argument("--report",type=Path)
    parser.add_argument("--screenshot",type=Path,help="actual Game with F3 plus observed seam overlay")
    parser.add_argument("--pick",action="store_true",help="open draft four-corner and interior-point picker")
    parser.add_argument("--cols",type=int,default=8)
    parser.add_argument("--rows",type=int,default=8)
    parser.add_argument("--output",type=Path,default=ROOT/".delivery/war_torn_calibration_draft.json")
    args = parser.parse_args()
    try:
        if args.pick:
            if args.cols < 2 or args.rows < 2:
                raise DataError("calibration requires at least 2 rows/columns for interior samples")
            pick(ROOT/"assets/skins/war_torn/backgrounds/battlefield.png",args.cols,args.rows,args.output)
            return
        data, geometry = load_observations(args.observations)
        report = measure(data,geometry)
        report["extent_diagnostic"] = inspect_extent(geometry)
        encoded = json.dumps(report,ensure_ascii=False,indent=2)+"\n"
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(encoded,encoding="utf-8")
        print(encoded)
        if args.screenshot:
            capture_game(data,geometry,args.screenshot)
    except (OSError,ValueError,KeyError,TypeError) as error:
        parser.exit(2,"Calibration error: {}\n".format(error))


if __name__ == "__main__":
    main()
```

## scripts/export_source.py

```python
"""Build or check the complete, deterministic SOURCE.md text-file bundle."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "SOURCE.md"
SUFFIXES = {".py", ".md", ".txt", ".yml", ".yaml", ".toml", ".json"}


def source_files():
    files = {path for path in ROOT.iterdir()
             if path.is_file() and (path.suffix in SUFFIXES or path.name in (".gitignore", ".gitattributes"))
             and path != OUTPUT}
    for folder in ("tactics", "tests", "scripts", ".github", "docs", "content", "assets", "presentations"):
        files.update(path for path in (ROOT / folder).rglob("*")
                     if path.is_file() and path.suffix in SUFFIXES)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def render():
    parts = ["# 完整项目源码\n\n本文件由 `python scripts/export_source.py` 生成。包含项目全部文本源码、配置和文档；不包含自身、二进制 PNG、截图、虚拟环境、缓存及压缩包。演示 PNG 可由 scripts/generate_demo_assets.py 与 scripts/generate_dusk_assets.py 重建。\n"]
    for path in source_files():
        name = path.relative_to(ROOT).as_posix()
        language = {".py": "python", ".md": "markdown", ".yml": "yaml", ".yaml": "yaml"}.get(path.suffix, "text")
        fence = "````" if path.suffix == ".md" else "```"
        content = path.read_text(encoding="utf-8-sig").rstrip()
        parts.append("\n## {}\n\n{}{}\n{}\n{}\n".format(name, fence, language, content, fence))
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if SOURCE.md needs updating")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8-sig") != expected:
            parser.exit(1, "SOURCE.md is stale. Run: python scripts/export_source.py\n")
        print("SOURCE.md is up to date ({} files).".format(len(source_files())))
    else:
        with OUTPUT.open("w", encoding="utf-8", newline="\n") as output:
            output.write(expected)
        print("SOURCE.md generated ({} files).".format(len(source_files())))


if __name__ == "__main__":
    main()
```

## scripts/fit_board.py

```python
"""Refine ONE homography from native-image observations; keep holdouts independent."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tactics.data_files import DataError, fields, read_json, rooted_path, version
from tactics.perspective_geometry import PerspectiveBoardGeometry, pair, transform
from tactics.presentation_layout import size_pair

DEFAULT = ROOT / "docs/calibration/war_torn_map_observations.json"
PRESENTATION = ROOT / "presentations/war_torn_8x8.json"
NAMES = ("p00", "p10", "p11", "p01")


def solve(matrix, values):
    rows = [list(row)+[value] for row,value in zip(matrix,values)]
    for col in range(len(values)):
        pivot = max(range(col,len(values)), key=lambda r: abs(rows[r][col]))
        rows[col],rows[pivot] = rows[pivot],rows[col]
        divisor = rows[col][col]
        if abs(divisor) < 1e-12:
            raise DataError("calibration observations do not determine a homography")
        rows[col] = [v/divisor for v in rows[col]]
        for row in range(len(values)):
            if row != col:
                factor = rows[row][col]
                rows[row] = [a-factor*b for a,b in zip(rows[row],rows[col])]
    return tuple(row[-1] for row in rows)


def fit_corners(data):
    """Offline linear least squares. Only role=calibration is allowed into the fit."""
    ox,oy,width,height = data["reference_region"]
    iw,ih = data["image_size"]
    equations,values = [],[]
    for item in data["observations"]:
        if item["role"] != "calibration":
            continue
        u,v = (item["node"][0]-ox)/width,(item["node"][1]-oy)/height
        x,y = item["image"][0]/iw,item["image"][1]/ih
        equations.extend(((u,v,1,0,0,0,-x*u,-x*v),(0,0,0,u,v,1,-y*u,-y*v)))
        values.extend((x,y))
    normal = [[sum(row[i]*row[j] for row in equations) for j in range(8)] for i in range(8)]
    rhs = [sum(row[i]*v for row,v in zip(equations,values)) for i in range(8)]
    matrix = (*solve(normal,rhs),1)
    return tuple(tuple(v*d for v,d in zip(transform(matrix,p),(iw,ih)))
                 for p in ((0,0),(1,0),(1,1),(0,1)))


def load_map(path=DEFAULT):
    data = read_json(path)
    label = str(path)
    fields(data,("schema_version","image","sha256","image_size","viewport_size","logical_size",
                 "reference_region","cells","observations","annotation"),(),label)
    version(data,label)
    image = rooted_path(ROOT,data["image"],label+".image")
    raw = image.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or len(raw) < 24 or hashlib.sha256(raw).hexdigest() != data["sha256"]:
        raise DataError("native background changed or invalid PNG; recheck observations")
    native = struct.unpack(">II",raw[16:24])
    if native != size_pair(data["image_size"],label+".image_size"):
        raise DataError("native image dimensions differ from observations")
    cols,rows = size_pair(data["logical_size"],label+".logical_size")
    viewport = size_pair(data["viewport_size"],label+".viewport_size")
    if not isinstance(data["observations"],list):
        raise DataError("observations must be a list")
    observed = {}
    for item in data["observations"]:
        fields(item,("node","image","role","band"),(),label+".observation")
        node,point = pair(item["node"],"node"),pair(item["image"],"image point")
        if (any(type(v) is not int for v in node) or not (0 <= node[0] <= cols and 0 <= node[1] <= rows)
                or not (0 <= point[0] < native[0] and 0 <= point[1] < native[1]) or node in observed
                or item["role"] not in ("calibration","validation") or item["band"] not in ("far","middle","near")):
            raise DataError("duplicate or invalid native observation")
        observed[node] = point
    if any(sum(item["role"]==role for item in data["observations"]) < 4 for role in ("calibration","validation")):
        raise DataError("at least four calibration and four independent validation points required")
    if any(not any(p["role"]=="validation" and p["band"]==band for p in data["observations"])
           for band in ("far","middle","near")):
        raise DataError("independent validation must cover far, middle and near bands")
    corners = fit_corners(data)
    geometry = PerspectiveBoardGeometry(cols,rows,corners,native,viewport,data["reference_region"],data["cells"])
    needed = {(c+dx,r+dy) for c,r in geometry.cells for dx,dy in ((0,0),(1,0),(1,1),(0,1))}
    if needed != observed.keys():
        raise DataError("every playable tile vertex must have a real observation, with no unused nodes")
    return data,geometry


def statistics(points):
    values = [item["error_px"] for item in points]
    return {"count":len(values),"mean_px":sum(values)/len(values),"max_px":max(values)}


def measure_map(data,geometry):
    points = [{**item,"predicted_image":list(geometry.fit.to_image(geometry.project(item["node"]))),
               "error_px":math.dist(geometry.project(item["node"]),geometry.fit.to_screen(item["image"]))}
              for item in data["observations"]]
    ox,oy,width,height = data["reference_region"]
    nodes = ((ox,oy),(ox+width,oy),(ox+width,oy+height),(ox,oy+height))
    observed = {tuple(item["node"]):item["image"] for item in points}
    baseline = PerspectiveBoardGeometry(geometry.cols,geometry.rows,tuple(observed[n] for n in nodes),
        geometry.reference_size,geometry.viewport_size,geometry.reference_region,geometry.cells)
    baseline_points = [{"error_px":math.dist(baseline.project(p["node"]),baseline.fit.to_screen(p["image"]))}
                       for p in points if tuple(p["node"]) not in nodes]
    validation = [p for p in points if p["role"]=="validation"]
    cells = frozenset(geometry.cells)
    interior = [p for p in validation if all((p["node"][0]+dx,p["node"][1]+dy) in cells
                for dx,dy in ((-1,-1),(0,-1),(0,0),(-1,0)))]
    metrics = statistics(validation)
    all_metrics = statistics(points)
    return {"image_sha256":data["sha256"],"viewport_size":list(geometry.viewport_size),
            "scale":geometry.fit.scale,"offset":list(geometry.fit.offset),"playable_cells":len(geometry.cells),
            "method":"One homography refined offline; runtime PerspectiveBoardGeometry formula unchanged.",
            "reference_region":data["reference_region"],"fitted_corners_image":dict(zip(NAMES,geometry.corners)),
            "observed_reference_corners_image":dict(zip(NAMES,(observed[n] for n in nodes))),
            "four_observed_corners_baseline":statistics(baseline_points),
            "calibration":statistics([p for p in points if p["role"]=="calibration"]),
            "independent_validation":metrics,"all_vertices":all_metrics,
            "independent_interior":statistics(interior) if interior else None,
            "bands":{band:statistics([p for p in validation if p["band"]==band]) for band in ("far","middle","near")},
            "threshold_met":metrics["mean_px"] <= 6 and metrics["max_px"] <= 12
                            and all_metrics["mean_px"] <= 6 and all_metrics["max_px"] <= 12,
            "full_rectangular_8x8":False,"points":points}


def check_presentation(data,geometry,path=PRESENTATION):
    board = read_json(path)["board"]
    if (board.get("reference_region") != data["reference_region"] or board.get("cells") != data["cells"]
            or board["reference_image_size"] != data["image_size"]
            or [board["cols"],board["rows"]] != data["logical_size"]
            or any(math.dist(board["corners"][name],point) > 1e-5 for name,point in zip(NAMES,geometry.corners))):
        raise DataError("presentation differs from measured calibration; regenerate explicitly with --write-presentation")


def capture_game(data,geometry,output):
    """Capture the actual Game/F3 surface; optional measured-point overlay is diagnostic UI."""
    import pygame
    from tactics.game import Game
    game = Game(presentation_file=PRESENTATION.relative_to(ROOT).as_posix(),debug_grid=True)
    try:
        game.draw()
        for item in data["observations"]:
            if item["role"] != "validation":
                continue
            measured = geometry.fit.to_screen(item["image"])
            projected = geometry.project(item["node"])
            pygame.draw.line(game.screen,(255,180,130),measured,projected,1)
            pygame.draw.circle(game.screen,(80,255,150),measured,4,1)
            pygame.draw.circle(game.screen,(255,140,140),projected,2)
        pygame.display.flip()
        pygame.event.pump()
        output.parent.mkdir(parents=True,exist_ok=True)
        pygame.image.save(game.screen,str(output))
        print("Actual Game/F3 capture; SDL driver="+pygame.display.get_driver())
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        game.run()
    finally:
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations",type=Path,default=DEFAULT)
    parser.add_argument("--report",type=Path)
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--write-presentation",action="store_true")
    parser.add_argument("--screenshot",type=Path,help="actual Game/F3 with held-out seam markers")
    args = parser.parse_args()
    try:
        data,geometry = load_map(args.observations)
        report = measure_map(data,geometry)
        if not report["threshold_met"]:
            raise DataError("measured alignment does not meet 6/12 px thresholds")
        if args.write_presentation:
            config = read_json(PRESENTATION)
            config["board"].update(corners=dict(zip(NAMES,geometry.corners)),
                                   reference_region=data["reference_region"],cells=data["cells"])
            PRESENTATION.write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        if args.check:
            check_presentation(data,geometry)
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        if args.screenshot:
            check_presentation(data,geometry)
            capture_game(data,geometry,args.screenshot)
        print(json.dumps({k:v for k,v in report.items() if k != "points"},ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as error:
        parser.exit(2,"Calibration error: {}\n".format(error))


if __name__ == "__main__":
    main()
```

## scripts/generate_demo_assets.py

```python
"""Rebuild the named programmer-art PNGs; never fetch external artwork."""

import argparse
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parents[1]


def generate(root):
    root = Path(root)
    (root / "tiles").mkdir(parents=True, exist_ok=True)
    (root / "units").mkdir(parents=True, exist_ok=True)
    tile = pygame.Surface((64, 64), pygame.SRCALPHA)
    tile.fill((43, 62, 72))
    for rect in ((2, 2, 29, 29), (33, 2, 29, 29), (2, 33, 29, 29), (33, 33, 29, 29)):
        pygame.draw.rect(tile, (51, 73, 80), rect, border_radius=3)
        pygame.draw.line(tile, (66, 89, 94), (rect[0]+3, rect[1]+2), (rect[0]+24, rect[1]+2))
    pygame.image.save(tile, str(root / "tiles/floor.png"))
    for state, count in (("idle", 2), ("attack", 3), ("death", 3)):
        for index in range(count):
            image = pygame.Surface((64, 96), pygame.SRCALPHA)
            body = pygame.Surface((64, 96), pygame.SRCALPHA)
            y = -index if state == "idle" else 0
            pygame.draw.ellipse(body, (8, 18, 24, 90), (10, 85, 44, 9))
            pygame.draw.polygon(body, (24, 82, 130), ((17, 50+y), (47, 50+y), (54, 86), (10, 86)))
            pygame.draw.circle(body, (69, 156, 239), (32, 64+y), 21)
            pygame.draw.circle(body, (146, 207, 255), (32, 64+y), 21, 2)
            pygame.draw.circle(body, (198, 222, 230), (32, 36+y), 13)
            pygame.draw.polygon(body, (38, 100, 157), ((17, 35+y), (32, 14+y), (49, 35+y)))
            pygame.draw.rect(body, (255, 204, 109), (21, 45+y, 23, 6), border_radius=2)
            if state == "attack":
                pygame.draw.arc(body, (255, 225, 144), (25-index*4, 28, 36, 49), -.9, 1.3, 3+index)
            if state == "death":
                size = (64-index*9, 96-index*14)
                body = pygame.transform.smoothscale(body, size)
                body.set_alpha(220-index*85)
                image.blit(body, ((64-size[0])//2, 96-size[1]))
            else:
                image.blit(body, (0, 0))
            pygame.image.save(image, str(root / "units" / ("scout_{}_{}.png".format(state, index))))
    print("Generated 9 demo PNGs in " + str(root.resolve()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    generate(parser.parse_args().output)
```

## scripts/generate_dusk_assets.py

```python
"""Generate the second self-contained programmer-art skin, without external art."""

import argparse
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parents[1]


def generate(root):
    root = Path(root)
    for folder in ("tiles", "units"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    floor = pygame.Surface((64, 64), pygame.SRCALPHA)
    floor.fill((34, 39, 61))
    for y in (2, 34):
        pygame.draw.rect(floor, (49, 56, 81), (2, y, 60, 28), border_radius=4)
        pygame.draw.line(floor, (72, 85, 115), (6, y+2), (58, y+2), 2)
    pygame.draw.circle(floor, (83, 108, 129), (12, 18), 2)
    pygame.image.save(floor, str(root / "tiles/floor.png"))
    obstacle = pygame.Surface((64, 80), pygame.SRCALPHA)
    pygame.draw.polygon(obstacle, (79, 91, 115), ((8, 70), (12, 27), (31, 10), (54, 24), (57, 70)))
    pygame.draw.polygon(obstacle, (116, 132, 156), ((12, 27), (31, 10), (36, 44), (8, 70)))
    pygame.draw.line(obstacle, (168, 191, 209), (31, 16), (36, 57), 2)
    pygame.image.save(obstacle, str(root / "tiles/obstacle.png"))
    for role in ("scout", "dummy"):
        for state, count in (("idle", 2 if role == "scout" else 1), ("attack", 3), ("death", 3)):
            for index in range(count):
                body = pygame.Surface((64, 96), pygame.SRCALPHA)
                pygame.draw.ellipse(body, (9, 12, 25, 110), (9, 85, 46, 9))
                if role == "scout":
                    dy = -index if state == "idle" else 0
                    pygame.draw.polygon(body, (31, 73, 121), ((13, 84), (19, 47+dy), (45, 47+dy), (54, 84)))
                    pygame.draw.circle(body, (58, 126, 214), (32, 64+dy), 20)
                    pygame.draw.circle(body, (140, 214, 249), (32, 64+dy), 20, 2)
                    pygame.draw.polygon(body, (65, 142, 211), ((19, 42+dy), (20, 27+dy), (32, 18+dy), (44, 27+dy), (45, 42+dy)))
                    pygame.draw.rect(body, (203, 223, 242), (25, 35+dy, 14, 6), border_radius=2)
                    pygame.draw.polygon(body, (164, 209, 245), ((13, 53), (27, 53), (27, 70), (20, 77), (13, 70)))
                else:
                    pygame.draw.rect(body, (76, 36, 39), (27, 28, 10, 63))
                    pygame.draw.rect(body, (175, 60, 70), (10, 43, 44, 38), border_radius=6)
                    pygame.draw.rect(body, (244, 142, 139), (10, 43, 44, 38), 2, border_radius=6)
                    pygame.draw.line(body, (108, 45, 48), (20, 46), (20, 77), 3)
                    pygame.draw.line(body, (108, 45, 48), (43, 46), (43, 77), 3)
                    pygame.draw.circle(body, (255, 186, 139), (32, 62), 10, 2)
                if state == "attack":
                    pygame.draw.arc(body, (237, 207, 151), (25-index*3, 27, 36, 52), -.9, 1.3, 3+index)
                image = pygame.Surface((64, 96), pygame.SRCALPHA)
                if state == "death":
                    size = (64-index*10, 96-index*17)
                    body = pygame.transform.smoothscale(body, size)
                    body.set_alpha(210-index*80)
                    image.blit(body, ((64-size[0])//2, 96-size[1]))
                else:
                    image.blit(body, (0, 0))
                pygame.image.save(image, str(root / "units" / "{}_{}_{}.png".format(role, state, index)))
    print("Generated 17 dusk PNGs in " + str(root.resolve()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "assets/skins/dusk")
    generate(parser.parse_args().output)
```

## scripts/verify_release.py

```python
"""Verify source archive integrity and exercise the extracted game offline."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import zipfile


def verify(archive, expected_commit=None):
    archive = Path(archive).resolve()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    sidecar = archive.with_suffix(archive.suffix + ".sha256").read_text(encoding="ascii").strip()
    if sidecar != digest + "  " + archive.name:
        raise ValueError("SHA256 or checksum filename mismatch")
    with zipfile.ZipFile(archive) as package, tempfile.TemporaryDirectory(prefix="chrono-release-") as temp:
        info = json.loads(package.comment)
        if info.get("format") != "chrono-tactics-source-v1":
            raise ValueError("Unknown package format")
        if not re.fullmatch(r"[0-9a-f]{40}", info["commit"]):
            raise ValueError("Invalid commit provenance")
        if expected_commit and info["commit"] != expected_commit:
            raise ValueError("Unexpected source commit")
        if not re.fullmatch(r"\d+\.\d+\.\d+", info["version"]):
            raise ValueError("Invalid package version")
        prefix = "chrono-tactics-pygame-" + info["version"]
        names = package.namelist()
        if not names or len(names) != len(set(names)) or package.testzip():
            raise ValueError("Empty, duplicate or corrupt ZIP entries")
        for entry in package.infolist():
            path = PurePosixPath(entry.filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in entry.filename
                    or ":" in entry.filename or path.parts[0] != prefix
                    or any(p in {".git", ".venv", ".delivery", "dist", "__pycache__"} for p in path.parts)
                    or (entry.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError("Unsafe or unwanted archive entry: " + entry.filename)
        package.extractall(temp)
        root = Path(temp) / prefix
        if (root / "VERSION.txt").read_text(encoding="utf-8").strip() != info["version"]:
            raise ValueError("Source version differs from archive metadata")
        env = dict(os.environ, PYTHONPATH=str(root), PYGAME_HIDE_SUPPORT_PROMPT="1",
                   SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        for args in (("scripts/export_source.py", "--check"), ("main.py", "--help"),
                     ("-S", "scripts/fit_board.py", "--check"),
                     ("-m", "unittest", "discover", "-s", "tests", "-p", "test_milestone.py", "-v"),
                     ("-m", "unittest", "discover", "-s", "tests", "-p", "test_perspective_rendering.py", "-v")):
            subprocess.run([sys.executable, *args], cwd=root, env=env, check=True, timeout=180)
    print("Verified version={} commit={} sha256={}".format(info["version"], info["commit"], digest))
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    default_version = (Path(__file__).resolve().parents[1] / "VERSION.txt").read_text(encoding="utf-8").strip()
    parser.add_argument("archive", type=Path, nargs="?",
                        default=Path("dist/chrono-tactics-pygame-{}-source.zip".format(default_version)))
    parser.add_argument("--expected-commit")
    args = parser.parse_args()
    try:
        verify(args.archive, args.expected_commit)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        parser.exit(1, "Release verification failed: {}\n".format(error))
```

## tactics/__init__.py

```python
"""Offline tactics prototype with manually controlled battle turns."""
```

## tactics/actions.py

```python
"""Semantic UI actions; no keyboard codes or button geometry in the controller."""

from dataclasses import dataclass
from enum import Enum


class UIAction(Enum):
    SKIP_PHASE = "skip_phase"
    END_TURN = "end_turn"
    UNDO = "undo"


@dataclass(frozen=True)
class ActionResult:
    accepted: bool
    reason: str = ""

    def __bool__(self):
        return self.accepted
```

## tactics/asset_manifest.py

```python
"""Version-one manifest parsing and references, without Pygame or image I/O."""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .data_files import DataError, fields, number, read_json, rooted_path, text, version


@dataclass(frozen=True)
class ImageSpec:
    asset_id: str
    path: Path
    display_size: Tuple[int, int]
    pivot: Tuple[float, float]
    optional: bool


@dataclass(frozen=True)
class AnimationSpec:
    asset_id: str
    frames: Tuple[str, ...]
    fps: float
    loop: bool


@dataclass(frozen=True)
class Manifest:
    images: Tuple[ImageSpec, ...]
    animations: Tuple[AnimationSpec, ...]
    visuals: Tuple[Tuple[str, Tuple[Tuple[str, str], ...]], ...]
    board: Tuple[Tuple[str, str], ...]


def load_manifest(root):
    root = Path(root)
    path = root / "manifest.json"
    label = str(path)
    data = read_json(path)
    fields(data, ("schema_version", "images", "animations", "visuals", "board"), (), label)
    version(data, label)
    for key in ("images", "animations", "visuals", "board"):
        if not isinstance(data[key], dict):
            raise DataError(label + "." + key + ": expected an object")
    images = []
    for asset_id, record in data["images"].items():
        where = label + " images." + text(asset_id, label)
        fields(record, ("path", "display_size", "pivot", "optional"), (), where)
        image_path = rooted_path(root, record["path"], where)
        if image_path.suffix.lower() != ".png":
            raise DataError(where + ": only PNG files are supported")
        size, pivot = record["display_size"], record["pivot"]
        if not isinstance(size, list) or len(size) != 2 or not isinstance(pivot, list) or len(pivot) != 2:
            raise DataError(where + ": display_size/pivot must be pairs")
        for value in size:
            number(value, where + ".display_size", minimum=1, integer=True)
        for value in pivot:
            if number(value, where + ".pivot") > 1:
                raise DataError(where + ": pivot must be between 0 and 1")
        if type(record["optional"]) is not bool:
            raise DataError(where + ": optional must be boolean")
        images.append(ImageSpec(asset_id, image_path, tuple(size), tuple(pivot), record["optional"]))
    animations = []
    for asset_id, record in data["animations"].items():
        where = label + " animations." + text(asset_id, label)
        if asset_id in data["images"]:
            raise DataError(where + ": id also used by an image")
        fields(record, ("frames", "fps", "loop"), (), where)
        if not isinstance(record["frames"], list) or not record["frames"]:
            raise DataError(where + ": frames must be a nonempty array")
        for frame in record["frames"]:
            if text(frame, where + ".frames") not in data["images"]:
                raise DataError(where + ": unknown frame " + frame)
        if number(record["fps"], where + ".fps") <= 0 or type(record["loop"]) is not bool:
            raise DataError(where + ": fps must be positive and loop boolean")
        animations.append(AnimationSpec(asset_id, tuple(record["frames"]), record["fps"], record["loop"]))
    by_animation = {item.asset_id: item for item in animations}
    visuals = []
    for visual_id, record in data["visuals"].items():
        where = label + " visuals." + text(visual_id, label)
        fields(record, (), ("idle", "attack", "death"), where)
        for state, asset_id in record.items():
            text(asset_id, where + "." + state)
            if state == "idle" and asset_id in data["images"]:
                continue
            clip = by_animation.get(asset_id)
            if clip is None or clip.loop != (state == "idle"):
                raise DataError(where + ": " + state + " needs a known " +
                                ("looping idle animation or image" if state == "idle" else "non-looping animation"))
        visuals.append((visual_id, tuple(record.items())))
    fields(data["board"], (), ("floor", "obstacle", "background"), label + ".board")
    for state, asset_id in data["board"].items():
        if text(asset_id, label + ".board." + state) not in data["images"]:
            raise DataError(label + ".board: unknown image " + asset_id)
        if state == "background" and data["images"][asset_id]["optional"]:
            raise DataError(label + ".board.background: background image must be required (optional=false)")
    return Manifest(tuple(images), tuple(animations), tuple(visuals), tuple(data["board"].items()))
```

## tactics/assets.py

```python
"""PNG loading, cached display sizes, pivots and explicit-frame clips."""

from dataclasses import dataclass
import logging

import pygame

from .asset_manifest import load_manifest
from .data_files import DataError, number


@dataclass(frozen=True)
class Sprite:
    surface: pygame.Surface
    pivot: tuple

    def blit(self, surface, anchor):
        width, height = self.surface.get_size()
        surface.blit(self.surface, (round(anchor[0] - width * self.pivot[0]),
                                    round(anchor[1] - height * self.pivot[1])))


@dataclass(frozen=True)
class Clip:
    frames: tuple
    fps: float
    loop: bool

    @property
    def duration(self):
        return len(self.frames) / self.fps

    def finished(self, age):
        return not self.loop and age >= self.duration

    def frame_at(self, age):
        index = int(max(0, age) * self.fps)
        return self.frames[index % len(self.frames) if self.loop else min(index, len(self.frames) - 1)]


@dataclass(frozen=True)
class SpriteBody:
    uid: str
    cell: tuple
    sprite: Sprite


class AssetManager:
    def __init__(self, root, definitions=()):
        self.manifest = load_manifest(root)
        self._images = {item.asset_id: item for item in self.manifest.images}
        self._animations = {item.asset_id: item for item in self.manifest.animations}
        self._visuals = {key: dict(states) for key, states in self.manifest.visuals}
        self._bindings = {item.definition_id: item.visual_id for item in definitions}
        for definition_id, visual_id in self._bindings.items():
            if visual_id not in self._visuals:
                raise DataError("{}: definition {}: unknown visual {}".format(root, definition_id, visual_id))
        self.clear_cache()
        # Validate all required files now, including unused entries.
        self.preload()

    @property
    def issues(self):
        return tuple(self._issues)

    def clear_cache(self):
        """Explicit development reload; no automatic filesystem checks per frame."""
        self._originals = {}
        self._scaled = {}
        self._sprites = {}
        self._clips = {}
        self._reported = set()
        self._issues = []

    def get_image(self, asset_id, scale=1):
        if number(scale, "image scale") <= 0:
            raise DataError("image scale must be positive")
        spec = self._images[asset_id]
        size = tuple(max(1, round(value * scale)) for value in spec.display_size)
        key = (asset_id, size)
        if key in self._sprites:
            return self._sprites[key]
        if spec.path not in self._originals:
            try:
                if pygame.display.get_surface() is None:
                    raise DataError("AssetManager requires an initialized display surface")
                self._originals[spec.path] = pygame.image.load(str(spec.path)).convert_alpha()
            except (OSError, ValueError, pygame.error) as error:
                if isinstance(error, DataError):
                    raise
                self._originals[spec.path] = str(error)
        original = self._originals[spec.path]
        if isinstance(original, str):
            message = "{} ({}): {}".format(asset_id, spec.path, original)
            if not spec.optional:
                raise DataError("required image unavailable: " + message)
            if asset_id not in self._reported:
                self._reported.add(asset_id)
                self._issues.append(message)
                logging.getLogger(__name__).warning("optional image unavailable: %s", message)
            self._sprites[key] = None
            return None
        image_key = (spec.path, size)
        if image_key not in self._scaled:
            self._scaled[image_key] = (original if size == original.get_size()
                                       else pygame.transform.smoothscale(original, size))
        sprite = Sprite(self._scaled[image_key], spec.pivot)
        self._sprites[key] = sprite
        return sprite

    def get_clip(self, asset_id, scale=1):
        if number(scale, "clip scale") <= 0:
            raise DataError("clip scale must be positive")
        key = (asset_id, scale)
        if key not in self._clips:
            spec = self._animations[asset_id]
            frames = tuple(self.get_image(frame, scale) for frame in spec.frames)
            self._clips[key] = Clip(frames, spec.fps, spec.loop) if all(frames) else None
        return self._clips[key]

    def visual(self, definition_id, state, scale=1):
        visual_id = self._bindings.get(definition_id)
        asset_id = self._visuals.get(visual_id, {}).get(state)
        if asset_id is None:
            return None
        if asset_id in self._images:
            image = self.get_image(asset_id, scale)
            return Clip((image,), 1, True) if image is not None else None
        return self.get_clip(asset_id, scale)

    def board_image(self, state, scale=1):
        asset_id = dict(self.manifest.board).get(state)
        return self.get_image(asset_id, scale) if asset_id else None

    def background(self, reference_size, scale):
        """Validate native reference pixels and cache the complete contain-fitted image."""
        asset_id = dict(self.manifest.board).get("background")
        if asset_id is None:
            raise DataError("perspective presentation needs board.background in asset manifest")
        spec = self._images[asset_id]
        sprite = self.get_image(asset_id, scale)
        if (spec.display_size != tuple(reference_size) or spec.pivot != (0, 0)
                or self._originals[spec.path].get_size() != tuple(reference_size)):
            raise DataError("{}: background native/display size must match presentation {} and pivot [0,0]".format(
                spec.path, reference_size))
        return sprite

    def preload(self, scale=1):
        for asset_id in self._images:
            self.get_image(asset_id, scale)
        for asset_id in self._animations:
            self.get_clip(asset_id, scale)

    def preload_units(self, scales):
        """Cache discrete depth sizes without scaling the full background at each depth."""
        for scale in scales:
            for definition_id in self._bindings:
                for state in ("idle", "attack", "death"):
                    self.visual(definition_id, state, scale)
            self.board_image("obstacle", scale)
```

## tactics/battle.py

```python
"""Speed order and one move / one adjacent attack per turn; no AI."""

from dataclasses import dataclass
from typing import Optional, Tuple

from .models import AttackResult, UnitSnapshot


@dataclass(frozen=True)
class TurnSnapshot:
    units: Tuple[UnitSnapshot, ...]
    order_uids: Tuple[str, ...]
    index: int
    round_number: int
    phase: str
    log: Tuple[Tuple[str, str], ...]
    winner: Optional[str]


class Battle:
    def __init__(self, board):
        self.board = board
        # Python's stable sort preserves entry order when speeds are equal.
        self.entry_order = tuple(sorted(board.units, key=lambda unit: -unit.speed))
        self.index = 0
        self.round_number = 1
        self.phase = "move"
        self.winner = None
        self.pending_attack = None
        # Protocol identity is monotonic for this battle, never rewound with gameplay.
        self._next_resolution_id = 1
        self.log = []
        self.notify("按速度从高到低行动，双方均手动操作", "Speed order; both teams are controlled manually.")
        self.history = [self._snapshot()]

    @property
    def order(self):
        return tuple(unit for unit in self.entry_order if unit.alive)

    @property
    def active_unit(self):
        return None if self.finished else self.entry_order[self.index]

    @property
    def finished(self):
        return self.winner is not None

    @property
    def can_undo(self):
        return self.phase != "resolving" and len(self.history) > 1

    def _snapshot(self):
        return TurnSnapshot(tuple(UnitSnapshot.capture(unit) for unit in self.board.units),
                            tuple(unit.uid for unit in self.entry_order), self.index, self.round_number,
                            self.phase, tuple(tuple(message) for message in self.log), self.winner)

    def undo(self):
        """Restore the previous unit turn's start, discarding this turn as well."""
        if not self.can_undo:
            return False
        self.history.pop()
        snapshot = self.history[-1]
        self.board.units = tuple(state.create_unit() for state in snapshot.units)
        by_uid = {unit.uid: unit for unit in self.board.units}
        self.entry_order = tuple(by_uid[uid] for uid in snapshot.order_uids)
        self.index = snapshot.index
        self.round_number = snapshot.round_number
        self.phase = snapshot.phase
        self.log = list(snapshot.log)
        self.winner = snapshot.winner
        self.pending_attack = None
        return True

    def notify(self, chinese, english):
        self.log.append((chinese, english))
        self.log = self.log[-2:]

    def movement_range(self):
        return self.board.reachable_cells(self.active_unit) if self.phase == "move" else set()

    def attack_targets(self):
        if self.phase != "attack":
            return ()
        actor = self.active_unit
        neighbors = self.board.neighbors(actor.cell)
        return tuple(unit for unit in self.board.living_units
                     if unit.team != actor.team and unit.cell in neighbors)

    def move(self, destination):
        if destination not in self.movement_range():
            return False
        actor = self.active_unit
        actor.cell = destination
        self.phase = "attack"
        self.notify("{} 已移动；请选择相邻敌方攻击".format(actor.name),
                    "{} moved. Choose an adjacent enemy.".format(actor.uid))
        return True

    def attack(self, target):
        if target not in self.attack_targets():
            return False
        actor = self.active_unit
        damage = max(0, actor.attack)
        previous_hp = target.health
        target.health = max(0, target.health - damage)
        self.pending_attack = AttackResult(
            self._next_resolution_id, actor.uid, target.uid, tuple(target.cell), target.team,
            damage, previous_hp, target.health, not target.alive,
            actor.definition_id, target.definition_id, tuple(actor.cell),
        )
        self._next_resolution_id += 1
        self.phase = "resolving"
        self.notify("{} 攻击 {}，造成 {} 点伤害".format(actor.name, target.name, damage),
                    "{} attacked {} for {} damage.".format(actor.uid, target.uid, damage))
        if not target.alive:
            self.notify("{} 被击杀".format(target.name), "{} was defeated.".format(target.uid))
        return True

    def finish_attack(self, resolution_id):
        """Only the currently pending resolution may hand off, once."""
        if (self.phase != "resolving" or self.pending_attack is None
                or self.pending_attack.resolution_id != resolution_id):
            return False
        self.pending_attack = None
        self._advance()
        return True

    def skip_phase(self):
        if self.phase == "move":
            self.phase = "attack"
            self.notify("{} 跳过移动；请选择相邻敌方".format(self.active_unit.name),
                        "{} skipped movement. Choose a target.".format(self.active_unit.uid))
        elif self.phase == "attack":
            self.end_turn()

    def end_turn(self):
        if self.phase not in ("move", "attack"):
            return False
        self.notify("{} 结束行动".format(self.active_unit.name),
                    "{} ended their turn.".format(self.active_unit.uid))
        self._advance()
        return True

    def _advance(self):
        teams = {unit.team for unit in self.board.living_units}
        if len(teams) <= 1:
            self.winner = next(iter(teams), "draw")
            self.phase = "finished"
            self.history.append(self._snapshot())
            return
        # Keep entry slots stable so deaths before/after the current slot cannot
        # shift the actor or cause an extra/skipped turn at the round boundary.
        for step in range(1, len(self.entry_order) + 1):
            absolute_index = self.index + step
            next_index = absolute_index % len(self.entry_order)
            if self.entry_order[next_index].alive:
                self.round_number += absolute_index // len(self.entry_order)
                self.index = next_index
                break
        self.phase = "move"
        self.history.append(self._snapshot())
```

## tactics/board.py

```python
"""Scenario-owned logical grid, spatial queries and blocked-path movement."""

from collections import deque

from .scenario import Scenario


class Board:
    def __init__(self, scenario: Scenario):
        self.scenario_id = scenario.scenario_id
        self.cols = scenario.cols
        self.rows = scenario.rows
        self.units = scenario.create_units()
        self.obstacles = scenario.obstacles

    @property
    def allies(self):
        return tuple(unit for unit in self.units if unit.team == "ally")

    @property
    def enemies(self):
        return tuple(unit for unit in self.units if unit.team == "enemy")

    def unit_at(self, cell):
        return next((unit for unit in self.living_units if unit.cell == cell), None)

    @property
    def living_units(self):
        # Keep the complete roster for undo; defeated units leave play immediately.
        return tuple(unit for unit in self.units if unit.alive)

    def neighbors(self, cell):
        col, row = cell
        return tuple((x, y) for x, y in ((col - 1, row), (col + 1, row),
                                        (col, row - 1), (col, row + 1))
                     if 0 <= x < self.cols and 0 <= y < self.rows)

    def reachable_cells(self, unit):
        """BFS counts real orthogonal steps; all occupied cells block paths."""
        blocked = set(self.obstacles) | {other.cell for other in self.living_units if other is not unit}
        distances = {unit.cell: 0}
        queue = deque([unit.cell])
        while queue:
            cell = queue.popleft()
            if distances[cell] >= unit.movement:
                continue
            for neighbor in self.neighbors(cell):
                if neighbor not in blocked and neighbor not in distances:
                    distances[neighbor] = distances[cell] + 1
                    queue.append(neighbor)
        return set(distances) - {unit.cell}
```

## tactics/board_renderer.py

```python
"""Draw detached board views, with no battle queries or state mutations."""

import pygame

from .geometry import BoardGeometry
from .view_models import BoardView


class BoardRenderer:
    def __init__(self, geometry: BoardGeometry, assets=None):
        self.geometry = geometry
        self.assets = assets
        self.elapsed = 0
        self.scale = geometry.cell_size / 64
        self.label_font = None

    def _size(self, value):
        return max(1, round(value * self.scale))

    def _rect(self, cell):
        return pygame.Rect(self.geometry.cell_rect(cell))

    def update(self, elapsed):
        self.elapsed += max(0, elapsed)

    def draw(self, surface, view: BoardView, bodies=()):
        if (view.cols, view.rows) != (self.geometry.cols, self.geometry.rows):
            raise ValueError("board view and geometry dimensions do not match")
        if self.label_font is None:
            self.label_font = pygame.font.Font(None, self._size(20))
        old_clip = surface.get_clip()
        surface.set_clip(old_clip.clip(pygame.Rect(self.geometry.bounds)))
        try:
            self._draw(surface, view, bodies)
        finally:
            surface.set_clip(old_clip)

    def _draw(self, surface, view, bodies):
        floor = self.assets.board_image("floor", self.scale) if self.assets else None
        for row in range(view.rows):
            for col in range(view.cols):
                color = (42, 55, 70) if (row + col) % 2 else (48, 63, 79)
                rect = self._rect((col, row))
                pygame.draw.rect(surface, color, rect)
                if floor is not None:
                    floor.blit(surface, rect.center)
                pygame.draw.rect(surface, (66, 81, 97), rect, self._size(1))

        for cells, color in ((view.move_cells, (54, 109, 103)), (view.attack_cells, (125, 65, 74))):
            for cell in cells:
                pygame.draw.rect(surface, color, self._rect(cell).inflate(-self._size(4), -self._size(4)),
                                 border_radius=self._size(4))
        for cell in view.target_cells:
            pygame.draw.rect(surface, (255, 161, 128),
                             self._rect(cell).inflate(-self._size(5), -self._size(5)), self._size(3))

        overrides = {body.uid: body for body in bodies}
        # Feet determine overlap; all overlays are drawn after every body.
        drawables = [(cell[1], "obstacle:{}:{}".format(*cell), "obstacle", cell) for cell in view.obstacles]
        drawables += [(unit.cell[1], unit.uid, "unit", unit) for unit in view.units
                      if unit.uid not in overrides]
        drawables += [(body.cell[1], body.uid, "sprite", body) for body in bodies]
        for _, _, kind, item in sorted(drawables, key=lambda item: item[:2]):
            if kind == "obstacle":
                self._draw_obstacle(surface, item)
            elif kind == "sprite":
                item.sprite.blit(surface, self._rect(item.cell).midbottom)
            else:
                self._draw_unit(surface, item)

        for unit in view.units:
            rect = self._rect(unit.cell)
            label = self.label_font.render(unit.uid, True, (255, 255, 255))
            surface.blit(label, label.get_rect(center=rect.center))
            self._draw_overlay(surface, view, unit, rect)

    def _draw_obstacle(self, surface, cell):
        sprite = self.assets.board_image("obstacle", self.scale) if self.assets else None
        if sprite is not None:
            sprite.blit(surface, self._rect(cell).midbottom)
            return
        block = self._rect(cell).inflate(-self._size(12), -self._size(12))
        pygame.draw.rect(surface, (111, 124, 135), block, border_radius=self._size(5))
        pygame.draw.line(surface, (146, 157, 166), block.topleft, block.bottomright, self._size(2))
        pygame.draw.line(surface, (146, 157, 166), block.topright, block.bottomleft, self._size(2))

    def _draw_unit(self, surface, unit):
        rect = self._rect(unit.cell)
        clip = self.assets.visual(unit.definition_id, "idle", self.scale) if self.assets else None
        if clip is not None:
            clip.frame_at(self.elapsed).blit(surface, rect.midbottom)
            return
        if unit.team == "ally":
            pygame.draw.circle(surface, (69, 156, 239), rect.center, self._size(21))
            pygame.draw.circle(surface, (146, 207, 255), rect.center, self._size(21), self._size(2))
        else:
            block = rect.inflate(-self._size(24), -self._size(24))
            pygame.draw.rect(surface, (231, 88, 94), block, border_radius=self._size(3))
            pygame.draw.rect(surface, (255, 153, 146), block, self._size(2), border_radius=self._size(3))

    def _draw_overlay(self, surface, view, unit, rect):
        if unit.uid == view.active_uid:
            pygame.draw.rect(surface, (255, 219, 116),
                             rect.inflate(-self._size(4), -self._size(4)), self._size(3))
        if unit.uid == view.selected_uid:
            pygame.draw.circle(surface, (246, 248, 252), rect.center, self._size(27), self._size(2))
        bar = pygame.Rect(rect.x + self._size(10), rect.y + self._size(58), self._size(44), self._size(4))
        pygame.draw.rect(surface, (26, 31, 39), bar)
        fill = bar.copy()
        fill.width = round(bar.width * min(1, unit.health / max(1, unit.max_health)))
        pygame.draw.rect(surface, (105, 218, 153), fill)
```

## tactics/content.py

```python
"""Validated JSON unit definitions and scenario construction; standard library only."""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .data_files import DataError, PROJECT_ROOT, fields, number, read_json, rooted_path, text, version
from .scenario import Scenario, UnitSpawn

STATS = ("max_health", "attack", "defense", "speed", "movement")


@dataclass(frozen=True)
class UnitDefinition:
    definition_id: str
    name: str
    role: str
    max_health: int
    attack: int
    defense: int
    speed: int
    movement: int
    visual_id: str


@dataclass(frozen=True)
class GameContent:
    scenario: Scenario
    definitions: Tuple[UnitDefinition, ...]


def load_content(root=None, scenario_file="scenarios/training_ground.json"):
    root = PROJECT_ROOT / "content" if root is None else Path(root)
    unit_path = root / "units.json"
    data = read_json(unit_path)
    label = str(unit_path)
    fields(data, ("schema_version", "units"), (), label)
    version(data, label)
    if not isinstance(data["units"], list) or not data["units"]:
        raise DataError(label + ": units must be a nonempty array")
    definitions = {}
    for index, record in enumerate(data["units"]):
        where = "{} units[{}]".format(unit_path, index)
        fields(record, ("id", "name", "role", "visual_id") + STATS, (), where)
        for key in ("id", "name", "role", "visual_id"):
            text(record[key], where + "." + key)
        for key in STATS:
            number(record[key], where + "." + key, minimum=1 if key == "max_health" else 0, integer=True)
        if record["id"] in definitions:
            raise DataError(where + ": duplicate definition id " + record["id"])
        definitions[record["id"]] = UnitDefinition(record["id"], record["name"], record["role"],
                                                *(record[key] for key in STATS), record["visual_id"])
    path = rooted_path(root, scenario_file, "scenario_file")
    data = read_json(path)
    label = str(path)
    fields(data, ("schema_version", "id", "cols", "rows", "spawns", "obstacles"), (), label)
    version(data, label)
    if not isinstance(data["spawns"], list) or not isinstance(data["obstacles"], list):
        raise DataError(label + ": spawns and obstacles must be arrays")
    spawns = []
    for index, record in enumerate(data["spawns"]):
        where = "{} spawns[{}]".format(path, index)
        fields(record, ("uid", "definition_id", "team", "cell"), ("overrides",), where)
        definition_id = text(record["definition_id"], where + ".definition_id")
        if definition_id not in definitions:
            raise DataError(where + ": unknown definition " + definition_id)
        definition = definitions[definition_id]
        overrides = record.get("overrides", {})
        fields(overrides, (), ("name", "health") + STATS, where + ".overrides")
        values = {key: getattr(definition, key) for key in ("name", "role") + STATS}
        values["health"] = overrides.get("max_health", definition.max_health)
        values.update(overrides)
        try:
            spawns.append(UnitSpawn(record["uid"], team=record["team"], cell=record["cell"],
                                    definition_id=definition_id, **values))
        except (TypeError, ValueError) as error:
            raise DataError(where + ": " + str(error)) from error
    try:
        scenario = Scenario(data["id"], data["cols"], data["rows"], tuple(spawns), data["obstacles"])
    except (TypeError, ValueError) as error:
        raise DataError(label + ": " + str(error)) from error
    return GameContent(scenario, tuple(definitions.values()))
```

## tactics/controller.py

```python
"""Application operations and animation handoff, independent of Pygame.

The injected presentation provides play_attack(values), update(seconds) returning
completion tokens, and clear(). It never receives live entities. A no-op supports callers
without a window; a successful attack still resolves on the next update().
"""

from .actions import ActionResult, UIAction
from .battle import Battle
from .board import Board
from .scenario import Scenario
from .view_models import AttackPresentation, BattleView, ResolutionToken, build_battle_view


class NullPresentation:
    def __init__(self):
        self._completed = ()

    def play_attack(self, result):
        self._completed = (result.token,)

    def update(self, elapsed):
        completed, self._completed = self._completed, ()
        return completed

    def clear(self):
        self._completed = ()


class Controller:
    def __init__(self, scenario: Scenario, presentation=None):
        self._scenario = scenario
        self._board = Board(scenario)
        self._battle = Battle(self._board)
        self._presentation = NullPresentation() if presentation is None else presentation
        self._selected_uid = self._battle.active_unit.uid
        self._generation = 0
        self._pending_resolution = None

    def _unit(self, uid):
        return next((unit for unit in self._board.units if unit.uid == uid), None)

    def _select_active(self):
        actor = self._battle.active_unit
        self._selected_uid = actor.uid if actor is not None else None

    def get_view_state(self) -> BattleView:
        return build_battle_view(self._board, self._battle, self._unit(self._selected_uid),
                                 self._generation, self._pending_resolution)

    def select(self, uid: str) -> ActionResult:
        if self._battle.phase == "resolving":
            return ActionResult(False, "resolving")
        unit = self._unit(uid)
        if unit is None or not unit.alive:
            return ActionResult(False, "unknown_or_dead_unit")
        self._selected_uid = uid
        return ActionResult(True)

    def move_to(self, cell) -> ActionResult:
        """Move the active actor; legality remains exclusively in Battle."""
        if not self._battle.move(cell):
            return ActionResult(False, "illegal_move")
        self._select_active()
        return ActionResult(True)

    def attack(self, target_uid: str) -> ActionResult:
        target = self._unit(target_uid)
        if target is None or not self._battle.attack(target):
            return ActionResult(False, "illegal_target")
        result = self._battle.pending_attack
        self._select_active()
        self._pending_resolution = ResolutionToken(self._generation, result.resolution_id)
        self._presentation.play_attack(AttackPresentation(self._pending_resolution, result))
        return ActionResult(True)

    def click_cell(self, cell) -> ActionResult:
        """Inspect any living unit, or move/attack when inspecting the active actor."""
        if self._battle.phase == "resolving":
            return ActionResult(False, "resolving")
        if cell is None:
            return ActionResult(False, "outside_board")
        unit = self._board.unit_at(cell)
        actor = self._battle.active_unit
        if actor is not None and self._selected_uid == actor.uid:
            if self.move_to(cell):
                return ActionResult(True)
            if unit is not None and self.attack(unit.uid):
                return ActionResult(True)
        if unit is not None:
            return self.select(unit.uid)
        return ActionResult(False, "no_action")

    def handle_action(self, action: UIAction) -> ActionResult:
        if self._battle.phase == "resolving":
            return ActionResult(False, "resolving")
        if action is UIAction.UNDO:
            return self.undo()
        if action is UIAction.SKIP_PHASE and self._battle.phase in ("move", "attack"):
            self._battle.skip_phase()
        elif action is UIAction.END_TURN and self._battle.end_turn():
            pass
        else:
            return ActionResult(False, "unavailable_action")
        self._select_active()
        return ActionResult(True)

    def undo(self) -> ActionResult:
        if not self._battle.can_undo:
            return ActionResult(False, "undo_unavailable")
        self._invalidate_presentation()
        self._battle.undo()
        self._select_active()
        return ActionResult(True)

    def _invalidate_presentation(self):
        # Invalidate callbacks before clearing effects or rebuilding rule entities.
        self._generation += 1
        self._pending_resolution = None
        self._presentation.clear()

    def restart(self) -> ActionResult:
        """Programmatic lifecycle entry; no new keyboard command or menu."""
        self._invalidate_presentation()
        self._board = Board(self._scenario)
        self._battle = Battle(self._board)
        self._select_active()
        return ActionResult(True)

    def complete_presentation(self, token: ResolutionToken) -> ActionResult:
        if (self._pending_resolution is None or token != self._pending_resolution
                or token.generation != self._generation):
            return ActionResult(False, "stale_resolution")
        if not self._battle.finish_attack(token.resolution_id):
            return ActionResult(False, "stale_resolution")
        self._pending_resolution = None
        self._select_active()
        return ActionResult(True)

    def update(self, elapsed):
        for token in self._presentation.update(max(0, elapsed)):
            self.complete_presentation(token)
```

## tactics/data_files.py

```python
"""Small strict JSON helpers shared by content and asset-manifest loaders."""

import json
import math
from pathlib import Path, PureWindowsPath

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DataError(ValueError):
    pass


def read_json(path):
    path = Path(path)

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DataError("duplicate key: " + key)
            result[key] = value
        return result

    try:
        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)
    except (OSError, ValueError) as error:
        raise DataError("{}: {}".format(path, error)) from error


def fields(value, required, optional, label):
    if not isinstance(value, dict):
        raise DataError(label + ": expected an object")
    missing = set(required) - value.keys()
    unknown = value.keys() - set(required) - set(optional)
    if missing or unknown:
        raise DataError("{}: missing {}, unknown {}".format(label, sorted(missing), sorted(unknown)))
    return value


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise DataError(label + ": expected a nonempty string")
    return value


def number(value, label, minimum=0, integer=False):
    valid = type(value) is int if integer else type(value) in (int, float)
    if not valid or (type(value) is float and not math.isfinite(value)) or value < minimum:
        raise DataError(label + ": invalid number")
    return value


def version(data, label):
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise DataError(label + ": schema_version must be 1")


def rooted_path(root, value, label):
    text(value, label)
    if "\\" in value or PureWindowsPath(value).drive or Path(value).is_absolute():
        raise DataError(label + ": expected a relative forward-slash path")
    root = Path(root).resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise DataError(label + ": path escapes root: " + value)
    return path
```

## tactics/effects.py

```python
"""Non-blocking damage popups and geometric defeat animations."""

import math
from dataclasses import dataclass

import pygame

from .geometry import BoardGeometry
from .assets import Clip, Sprite, SpriteBody
from .view_models import AttackPresentation

DAMAGE_DURATION = 0.9
DEATH_DURATION = 0.65


@dataclass
class DamageText:
    cell: tuple
    amount: int
    age: float = 0.0


@dataclass
class DeathEffect:
    cell: tuple
    team: str
    uid: str
    age: float = 0.0


@dataclass
class SpriteEffect:
    uid: str
    cell: tuple
    clip: Clip
    age: float = 0.0


class CombatEffects:
    def __init__(self, geometry: BoardGeometry, assets=None):
        self.geometry = geometry
        self.assets = assets
        self.sprites = []
        self.damage_texts = []
        self.deaths = []
        self._pending_token = None
        self.damage_font = pygame.font.Font(None, 32)
        self.label_font = pygame.font.Font(None, 20)

    @property
    def busy(self):
        return bool(self.damage_texts or self.deaths or self.sprites)

    def play_attack(self, event: AttackPresentation):
        self.clear()
        self._pending_token = event.token
        result = event.result
        attack = self.assets.visual(result.actor_definition_id, "attack", self.geometry.cell_scale(result.actor_cell)) if self.assets else None
        if attack is not None:
            self.sprites.append(SpriteEffect(result.actor_uid, result.actor_cell, attack))
        self.damage_texts.append(DamageText(result.target_cell, result.damage))
        if result.killed:
            death = self.assets.visual(result.target_definition_id, "death", self.geometry.cell_scale(result.target_cell)) if self.assets else None
            if death is not None:
                self.sprites.append(SpriteEffect(result.target_uid, result.target_cell, death))
            else:
                self.deaths.append(DeathEffect(result.target_cell, result.target_team, result.target_uid))

    def clear(self):
        self.damage_texts.clear()
        self.deaths.clear()
        self.sprites.clear()
        self._pending_token = None

    def update(self, elapsed):
        for effect in self.damage_texts + self.deaths + self.sprites:
            effect.age += max(0, elapsed)
        self.damage_texts = [effect for effect in self.damage_texts if effect.age < DAMAGE_DURATION]
        self.deaths = [effect for effect in self.deaths if effect.age < DEATH_DURATION]
        self.sprites = [effect for effect in self.sprites if not effect.clip.finished(effect.age)]
        if self._pending_token is not None and not self.busy:
            token, self._pending_token = self._pending_token, None
            return (token,)
        return ()

    def body_views(self):
        bodies = tuple(SpriteBody(effect.uid, effect.cell, effect.clip.frame_at(effect.age))
                       for effect in self.sprites)
        if hasattr(self.geometry, "depth_at"):
            # Geometric defeat bodies share the renderer's foot-Y/UID ordering with PNG clips.
            bodies += tuple(SpriteBody(effect.uid, effect.cell, Sprite(self._death_layer(effect), (.5, 1)))
                            for effect in self.deaths)
        return bodies

    def _death_layer(self, effect):
        body_rect = self.geometry.body_rect(effect.cell)
        cell_size = body_rect[2]
        scale = self.geometry.cell_scale(effect.cell)
        progress = effect.age / DEATH_DURATION
        layer = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        size = max(1, round(max(4, 42 * (1 - progress * 0.6)) * scale))
        color = (69, 156, 239) if effect.team == "ally" else (231, 88, 94)
        if int(effect.age * 20) % 2 == 0:
            color = (255, 224, 192)
        center = (cell_size // 2, cell_size // 2)
        if effect.team == "ally":
            pygame.draw.circle(layer, color, center, size // 2)
        else:
            rect = pygame.Rect(0, 0, size, size)
            rect.center = center
            pygame.draw.rect(layer, color, rect, border_radius=3)
        label = self.label_font.render(effect.uid, True, "white")
        layer.blit(label, label.get_rect(center=center))
        for index in range(6):
            angle = index * math.tau / 6
            radius = (8 + 23 * progress) * scale
            point = (round(center[0] + math.cos(angle) * radius),
                     round(center[1] + math.sin(angle) * radius))
            pygame.draw.circle(layer, (255, 192, 132), point, max(1, round(3 * (1 - progress) * scale)))
        layer.set_alpha(round(255 * (1 - progress)))
        return layer

    def draw(self, surface):
        old_clip = surface.get_clip()
        surface.set_clip(old_clip.clip(pygame.Rect(self.geometry.bounds)))
        if not hasattr(self.geometry, "depth_at"):
            for effect in self.deaths:
                surface.blit(self._death_layer(effect), self.geometry.body_rect(effect.cell)[:2])

        for effect in self.damage_texts:
            progress = effect.age / DAMAGE_DURATION
            text = "-{}".format(effect.amount)
            label = self.damage_font.render(text, True, (255, 217, 150))
            shadow = self.damage_font.render(text, True, (37, 21, 28))
            alpha = round(255 * min(1, (1 - progress) * 3))
            label.set_alpha(alpha)
            shadow.set_alpha(alpha)
            _, cell_y, _, _ = self.geometry.body_rect(effect.cell)
            x = self.geometry.cell_anchor(effect.cell)[0]
            y = max(self.geometry.bounds[1] + 5, cell_y + 8 - round(progress * 30))
            rect = label.get_rect(midtop=(x, y))
            surface.blit(shadow, rect.move(2, 2))
            surface.blit(label, rect)
        surface.set_clip(old_clip)
```

## tactics/game.py

```python
"""Window lifecycle, input dispatch, and the main render loop."""

import pygame

from .actions import UIAction
from .assets import AssetManager
from .board_renderer import BoardRenderer
from .controller import Controller
from .effects import CombatEffects
from .geometry import BoardGeometry
from .panel import InfoPanel
from .content import load_content
from .data_files import DataError, PROJECT_ROOT
from .presentation_layout import load_presentation
from .perspective_board_renderer import PerspectiveBoardRenderer
from .scene_hud import SceneHUD
from .settings import CELL_SIZE, FPS, MIN_WINDOW_HEIGHT, PANEL_WIDTH


class Game:
    def __init__(self, scenario=None, *, content_root=None, scenario_file=None,
                 asset_root=None, geometric=False, presentation_file=None, debug_grid=False):
        layout = load_presentation(presentation_file) if presentation_file is not None else None
        if layout is not None:
            if any(value is not None for value in (content_root,scenario_file,asset_root)) or geometric:
                raise DataError("--presentation cannot be combined with --scenario, --assets, --content-root or --geometry")
            scenario_file, asset_root = layout.scenario_file, layout.asset_root
        elif debug_grid:
            raise DataError("--debug-grid needs --presentation")
        scenario_file = scenario_file or "scenarios/training_ground.json"
        content = load_content(content_root, scenario_file)
        scenario = content.scenario if scenario is None else scenario
        if layout is not None:
            self.geometry = layout.geometry
            if (scenario.cols,scenario.rows) != (self.geometry.cols,self.geometry.rows):
                raise DataError("presentation board dimensions differ from scenario")
            cells = frozenset(self.geometry.cells)
            voids = {(c,r) for r in range(scenario.rows) for c in range(scenario.cols)} - cells
            if not voids <= set(scenario.obstacles):
                raise DataError("presentation void cells must be blocked in scenario.obstacles")
            if any(unit.cell not in cells for unit in scenario.units):
                raise DataError("scenario unit starts outside presentation playable cells")
            window_size = self.geometry.viewport_size
        else:
            self.geometry = BoardGeometry(scenario.cols, scenario.rows, CELL_SIZE)
            window_size = (self.geometry.width + PANEL_WIDTH, max(MIN_WINDOW_HEIGHT, self.geometry.height))
        # The prototype needs only display and fonts, so do not initialize audio.
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Grid Tactics - Battle Prototype")
        self.clock = pygame.time.Clock()
        try:
            self.assets = None if geometric else AssetManager(
                PROJECT_ROOT / "assets" if asset_root is None else asset_root, content.definitions)
            if self.assets is not None:
                self.assets.preload(CELL_SIZE / 64)
            if layout is not None:
                debug = dict(layout.debug)
                if debug_grid:
                    debug = dict.fromkeys(debug,True)
                self.renderer = PerspectiveBoardRenderer(self.geometry,self.assets,debug.items())
                self.panel = SceneHUD(window_size,layout.safe_margin)
            else:
                self.renderer = BoardRenderer(self.geometry, self.assets)
                self.panel = InfoPanel(self.geometry.width, window_size[1])
            self.effects = CombatEffects(self.geometry, self.assets)
            self.controller = Controller(scenario, self.effects)
        except Exception:
            pygame.quit()
            raise
        self.running = True

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3 and isinstance(self.renderer,PerspectiveBoardRenderer):
                self.renderer.toggle_debug()
            action = {pygame.K_BACKSPACE: UIAction.UNDO,
                      pygame.K_SPACE: UIAction.SKIP_PHASE,
                      pygame.K_RETURN: UIAction.END_TURN}.get(event.key)
            if action is not None:
                self.controller.handle_action(action)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self.panel.hit_test(event.pos)
            if action is not None:
                self.controller.handle_action(action)
            elif isinstance(self.panel,SceneHUD) and self.panel.contains(event.pos):
                return
            else:
                cell = (self.renderer.cell_at(event.pos,self.controller.get_view_state().board)
                        if isinstance(self.renderer,PerspectiveBoardRenderer) else self.geometry.cell_at(event.pos))
                self.controller.click_cell(cell)

    def update(self, elapsed):
        self.renderer.update(elapsed)
        self.controller.update(elapsed)

    def draw(self):
        self.screen.fill((21, 30, 42))
        view = self.controller.get_view_state()
        self.renderer.draw(self.screen, view.board, self.effects.body_views())
        self.effects.draw(self.screen)
        self.panel.draw(self.screen, view)
        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                elapsed = self.clock.tick(FPS) / 1000.0
                for event in pygame.event.get():
                    self.handle_event(event)
                if self.running:
                    self.update(elapsed)
                    self.draw()
        finally:
            pygame.quit()
```

## tactics/geometry.py

```python
"""Pure numeric conversion between logical grid cells and screen coordinates."""

from dataclasses import dataclass
from typing import Tuple

from .models import Cell


@dataclass(frozen=True)
class BoardGeometry:
    cols: int
    rows: int
    cell_size: int
    origin: Tuple[int, int] = (0, 0)

    def __post_init__(self):
        if any(type(value) is not int or value <= 0 for value in (self.cols, self.rows, self.cell_size)):
            raise ValueError("geometry dimensions and cell_size must be positive integers")
        if (not isinstance(self.origin, (tuple, list)) or len(self.origin) != 2
                or any(type(value) is not int for value in self.origin)):
            raise ValueError("origin must be a pair of integers")
        object.__setattr__(self, "origin", tuple(self.origin))

    @property
    def width(self):
        return self.cols * self.cell_size

    @property
    def height(self):
        return self.rows * self.cell_size

    @property
    def bounds(self):
        return (*self.origin, self.width, self.height)

    def cell_at(self, position):
        x, y = position[0] - self.origin[0], position[1] - self.origin[1]
        if 0 <= x < self.width and 0 <= y < self.height:
            return int(x // self.cell_size), int(y // self.cell_size)
        return None

    def cell_rect(self, cell: Cell):
        if (not isinstance(cell, (tuple, list)) or len(cell) != 2
                or any(type(value) is not int for value in cell)
                or not (0 <= cell[0] < self.cols and 0 <= cell[1] < self.rows)):
            raise ValueError("cell is outside the geometry: {}".format(cell))
        return (self.origin[0] + cell[0] * self.cell_size,
                self.origin[1] + cell[1] * self.cell_size, self.cell_size, self.cell_size)

    def cell_center(self, cell: Cell):
        x, y, width, height = self.cell_rect(cell)
        return x + width // 2, y + height // 2

    def cell_anchor(self, cell: Cell):
        x, y, width, height = self.cell_rect(cell)
        return x + width // 2, y + height

    def cell_scale(self, cell: Cell):
        self.cell_rect(cell)
        return self.cell_size / 64

    def body_rect(self, cell: Cell):
        return self.cell_rect(cell)
```

## tactics/models.py

```python
"""Runtime units and immutable rule values; no scene or rendering data."""

from dataclasses import asdict, dataclass
from typing import Tuple

Cell = Tuple[int, int]


@dataclass(eq=False)
class Unit:
    uid: str
    name: str
    team: str
    role: str
    cell: Cell
    health: int = 100
    max_health: int = 100
    attack: int = 10
    defense: int = 5
    speed: int = 10
    movement: int = 3
    definition_id: str = ""

    @property
    def alive(self):
        return self.health > 0


@dataclass(frozen=True)
class UnitSnapshot:
    """Complete unit values; no reference to a running entity or presentation."""

    uid: str
    name: str
    team: str
    role: str
    cell: Cell
    health: int
    max_health: int
    attack: int
    defense: int
    speed: int
    movement: int
    definition_id: str

    @classmethod
    def capture(cls, unit):
        values = asdict(unit)
        values["cell"] = tuple(unit.cell)
        return cls(**values)

    def create_unit(self):
        return Unit(**asdict(self))


@dataclass(frozen=True)
class AttackResult:
    resolution_id: int
    actor_uid: str
    target_uid: str
    target_cell: Cell
    target_team: str
    damage: int
    previous_hp: int
    current_hp: int
    killed: bool
    actor_definition_id: str = ""
    target_definition_id: str = ""
    actor_cell: Cell = (0, 0)
```

## tactics/panel.py

```python
"""System-font text and the selected-unit sidebar; no asset files required."""

import os
from pathlib import Path

import pygame

from .settings import MIN_WINDOW_HEIGHT, PANEL_WIDTH
from .actions import UIAction
from .view_models import BattleView


def load_fonts():
    """Try known files before registry-based discovery; always retain a fallback."""
    font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for filename in ("msyh.ttc", "simhei.ttf", "simsun.ttc"):
        path = font_dir / filename
        if path.is_file():
            try:
                return tuple(pygame.font.Font(str(path), size) for size in (25, 18, 15)), True
            except (OSError, ValueError, pygame.error):
                continue

    # Pygame 2.6.1 can raise TypeError for non-string Windows font entries.
    try:
        path = pygame.font.match_font("microsoftyahei,simhei,notosanscjksc,wenquanyizenhei,pingfangsc")
        if path:
            return tuple(pygame.font.Font(path, size) for size in (25, 18, 15)), True
    except (TypeError, OSError, ValueError, pygame.error):
        pass

    return tuple(pygame.font.Font(None, size) for size in (25, 18, 15)), False


class InfoPanel:
    def __init__(self, board_width=512, height=MIN_WINDOW_HEIGHT):
        self.board_width = board_width
        self.height = height
        fonts, self.chinese = load_fonts()
        self.title_font, self.font, self.small_font = fonts
        self._buttons = {
            UIAction.SKIP_PHASE: pygame.Rect(self.board_width + 24, 284, 162, 38),
            UIAction.END_TURN: pygame.Rect(self.board_width + 198, 284, 162, 38),
            UIAction.UNDO: pygame.Rect(self.board_width + 208, 14, 152, 32),
        }

    def hit_test(self, position):
        """Return intent only; the controller decides whether it is available."""
        return next((action for action, rect in self._buttons.items()
                     if rect.collidepoint(position)), None)

    def text(self, surface, value, y, color=(220, 230, 241), small=False, title=False, x=None, width=None):
        font = self.title_font if title else self.small_font if small else self.font
        x = self.board_width + 24 if x is None else x
        width = PANEL_WIDTH - 48 if width is None else width
        if font.size(value)[0] > width:
            while value and font.size(value + "...")[0] > width:
                value = value[:-1]
            value += "..."
        surface.blit(font.render(value, True, color), (x, y))

    def button(self, surface, rect, label, enabled=True):
        pygame.draw.rect(surface, (51, 76, 96) if enabled else (35, 43, 53), rect, border_radius=6)
        pygame.draw.rect(surface, (94, 131, 154) if enabled else (55, 64, 74), rect, 1, border_radius=6)
        text = self.small_font.render(label, True, (236, 241, 247) if enabled else (104, 117, 132))
        surface.blit(text, text.get_rect(center=rect.center))

    def draw(self, surface, view: BattleView):
        pygame.draw.rect(surface, (21, 30, 42), (self.board_width, 0, PANEL_WIDTH, self.height))
        cn = self.chinese
        selected = view.selected
        actor = view.active
        name = (actor.name if cn else actor.uid) if actor is not None else ""
        moving = view.phase == "move"
        self.text(surface, ("第 {} 回合" if cn else "ROUND {:02d}").format(view.round_number),
                  14, title=True, width=182)
        self.button(surface, self._buttons[UIAction.UNDO], "回溯 [退格]" if cn else "Undo [Backspace]", view.can_undo)
        if view.finished:
            winners = {"ally": ("蓝方获胜", "BLUE WINS"), "enemy": ("红方获胜", "RED WINS"),
                       "draw": ("平局", "DRAW")}
            self.text(surface, winners[view.winner][0 if cn else 1], 54, (255, 219, 116))
            status = "战斗结束 · 可以回溯最后一次行动" if cn else "Battle ended. Undo is available."
        else:
            self.text(surface, ("当前行动：{} [{}]" if cn else "Active: {} [{}]").format(name, actor.uid),
                      54, (255, 219, 116))
        if not view.finished and cn:
            phase = {"move": "移动阶段", "attack": "攻击阶段", "resolving": "攻击结算中"}[view.phase]
            team = "蓝方" if actor.team == "ally" else "红方"
            status = "{} · {} · 移动 {} / 攻击 {}".format(team, phase, int(moving), int(view.phase != "resolving"))
        elif not view.finished:
            status = "{} / {} / Move {} / Attack {}".format(actor.team.upper(), view.phase.upper(),
                                                           int(moving), int(view.phase != "resolving"))
        self.text(surface, status, 86, (132, 159, 185), small=True)
        pygame.draw.line(surface, (60, 77, 96), (self.board_width + 24, 116), (self.board_width + PANEL_WIDTH - 24, 116))
        if selected is None:
            self.text(surface, "点击单位查看属性" if cn else "Click a unit to inspect.", 134)
        else:
            name = selected.name if cn else selected.uid
            self.text(surface, ("查看：{} [{}]" if cn else "Inspect: {} [{}]").format(name, selected.uid), 130)
            role = selected.role if cn else selected.team.upper()
            label = "{} · 第 {} 列，第 {} 行" if cn else "{} / column {}, row {}"
            self.text(surface, label.format(role, selected.cell[0] + 1, selected.cell[1] + 1),
                      160, (132, 159, 185), small=True)
            stats = (("生命", "HP", "{}/{}".format(selected.health, selected.max_health)), ("攻击", "ATK", selected.attack),
                     ("防御", "DEF", selected.defense), ("速度", "SPD", selected.speed),
                     ("移动力", "MOVE", selected.movement), ("攻击范围", "RANGE", 1))
            for index, (chinese, english, value) in enumerate(stats):
                x = self.board_width + 24 + (index % 2) * 174
                self.text(surface, "{}: {}".format(chinese if cn else english, value),
                          192 + (index // 2) * 27, x=x, width=162)

        skip = ("跳过移动 [空格]" if moving else "跳过攻击 [空格]") if cn else (
            "Skip move [Space]" if moving else "Skip attack [Space]")
        self.button(surface, self._buttons[UIAction.SKIP_PHASE], skip, view.can_skip)
        self.button(surface, self._buttons[UIAction.END_TURN], "结束行动 [回车]" if cn else "End turn [Enter]", view.can_end_turn)
        if view.phase == "resolving":
            hint = "攻击动画播放中，结束后继续" if cn else "Resolving attack. Please wait."
        elif view.finished:
            hint = "战斗结束，可回溯上一单位行动" if cn else "Battle ended. Undo the previous turn."
        elif (selected.uid if selected else None) != (actor.uid if actor else None):
            hint = "点击金框单位，继续当前行动" if cn else "Click the gold-frame unit to act."
        elif moving:
            hint = "绿色：可移动；点击高亮格确认" if cn else "Green cells: click once to move."
        else:
            hint = "红色：攻击范围；点击敌方攻击" if cn else "Red range: click an enemy to attack."
        self.text(surface, hint, 334, (166, 207, 191), small=True)
        self.text(surface, "伤害 = 攻击 × 100% · 退格回溯" if cn else "Damage = ATK x 100% / Backspace undo",
                  357, (132, 159, 185), small=True)
        for index, message in enumerate(view.log):
            self.text(surface, message[0 if cn else 1], 385 + index * 21, small=True)

        self.text(surface, "行动顺序（速度↓，金色为当前）" if cn else "ORDER / SPD descending / gold = active",
                  433, (132, 159, 185), small=True)
        for index, unit in enumerate(view.order):
            name = unit.name if cn else unit.uid
            color = (255, 219, 116) if actor is not None and unit.uid == actor.uid else (161, 178, 196)
            label = "{}.{}({})".format(index + 1, name, unit.speed)
            self.text(surface, label, 459 + (index // 3) * 25, color, small=True,
                      x=self.board_width + 24 + (index % 3) * 114, width=108)
```

## tactics/perspective_board_renderer.py

```python
"""Full background, translucent projected ranges and screen-depth body sorting."""

import pygame


class PerspectiveBoardRenderer:
    def __init__(self, geometry, assets, debug=()):
        self.geometry = geometry
        self.cells = frozenset(geometry.cells)
        self.assets = assets
        self.elapsed = 0
        self.debug = dict(debug)
        self.background = assets.background(geometry.reference_size, geometry.fit.scale)
        assets.preload_units(geometry.scales)
        self.label_font = pygame.font.Font(None, 19)
        self.debug_font = pygame.font.Font(None, 16)
        self._debug_layer = self._build_debug_layer()
        self._range_layer = pygame.Surface(tuple(map(int, geometry.viewport_size)), pygame.SRCALPHA)

    def _build_debug_layer(self):
        layer = pygame.Surface(tuple(map(int, self.geometry.viewport_size)), pygame.SRCALPHA)
        for col,row in self.geometry.cells:
            cell = (col,row)
            polygon = self.geometry.cell_polygon(cell)
            center = self.geometry.cell_center(cell)
            if self.debug.get("show_grid"):
                pygame.draw.polygon(layer,(130,210,236,180),polygon,1)
            if self.debug.get("show_cell_centers"):
                pygame.draw.circle(layer,(255,210,90),center,2)
            if self.debug.get("show_coordinates"):
                label = self.debug_font.render("{},{}".format(col,row),True,(255,248,199))
                layer.blit(label,label.get_rect(center=center))
        if self.debug.get("show_grid"):
            ox,oy,w,h = self.geometry.reference_region
            nodes = ((ox,oy),(ox+w,oy),(ox+w,oy+h),(ox,oy+h))
            for name, point, node in zip(("p00","p10","p11","p01"),self.geometry.corners,nodes):
                screen = self.geometry.fit.to_screen(point)
                pygame.draw.circle(layer,(255,160,100),screen,5)
                label = self.debug_font.render("REF {} {}".format(name,node),True,(255,238,200))
                label_x = screen[0]-label.get_width()-8 if name == "p01" else screen[0]+6
                layer.blit(label,(label_x,screen[1]-18))
        return layer

    def update(self, elapsed):
        self.elapsed += max(0,elapsed)

    def toggle_debug(self):
        enabled = not any(self.debug.values())
        self.debug = dict.fromkeys(("show_grid","show_cell_centers","show_coordinates"),enabled)
        self._debug_layer = self._build_debug_layer()

    def cell_at(self, position, view):
        """Visible bodies use the same foot pivots as drawing, then fall back to floor picking."""
        for unit in sorted(view.units, key=lambda u: (self.geometry.depth_at(u.cell),u.uid), reverse=True):
            anchor = self.geometry.cell_anchor(unit.cell)
            clip = self.assets.visual(unit.definition_id,"idle",self.geometry.cell_scale(unit.cell))
            if clip:
                sprite = clip.frame_at(self.elapsed)
                width,height = sprite.surface.get_size()
                rect = pygame.Rect(round(anchor[0]-width*sprite.pivot[0]),
                                   round(anchor[1]-height*sprite.pivot[1]),width,height)
                if rect.collidepoint(position):
                    x,y = round(position[0]-rect.x),round(position[1]-rect.y)
                    if 0 <= x < width and 0 <= y < height and sprite.surface.get_at((x,y)).a:
                        return unit.cell
            else:
                rect = pygame.Rect(self.geometry.body_rect(unit.cell))
                if rect.collidepoint(position):
                    if unit.team != "ally" or ((position[0]-rect.centerx)**2+(position[1]-rect.centery)**2 <= (rect.width/2)**2):
                        return unit.cell
        return self.geometry.cell_at(position)

    def draw(self, surface, view, bodies=()):
        if (view.cols,view.rows) != (self.geometry.cols,self.geometry.rows):
            raise ValueError("board view and perspective geometry dimensions do not match")
        self.background.blit(surface,self.geometry.fit.offset)
        surface.blit(self._debug_layer,(0,0))
        layer = self._range_layer
        layer.fill((0,0,0,0))
        for cells, color in ((view.move_cells,(76,139,137,70)),(view.attack_cells,(150,57,59,85))):
            for cell in cells:
                pygame.draw.polygon(layer,color,self.geometry.cell_polygon(cell))
        for cell in view.target_cells:
            pygame.draw.polygon(layer,(255,186,146,225),self.geometry.cell_polygon(cell),2)
        surface.blit(layer,(0,0))

        overrides = {body.uid:body for body in bodies}
        drawables = [(self.geometry.depth_at(c),"obstacle:{}:{}".format(*c),"obstacle",c)
                     for c in view.obstacles if c in self.cells]
        drawables += [(self.geometry.depth_at(u.cell),u.uid,"unit",u) for u in view.units if u.uid not in overrides]
        drawables += [(self.geometry.depth_at(b.cell),b.uid,"sprite",b) for b in bodies]
        # Shadows precede all bodies. Cached sprites are never modified in-place.
        for _,_,kind,item in drawables:
            cell = item if kind == "obstacle" else item.cell
            x,y = self.geometry.cell_anchor(cell)
            scale = self.geometry.cell_scale(cell)
            pygame.draw.ellipse(surface,(42,33,29),(x-23*scale,y-6*scale,46*scale,11*scale))
        for _,_,kind,item in sorted(drawables,key=lambda entry:entry[:2]):
            cell = item if kind == "obstacle" else item.cell
            anchor = self.geometry.cell_anchor(cell)
            scale = self.geometry.cell_scale(cell)
            rect = pygame.Rect(self.geometry.body_rect(cell))
            if kind == "sprite":
                item.sprite.blit(surface,anchor)
                continue
            if kind == "obstacle":
                sprite = self.assets.board_image("obstacle",scale)
                if sprite:
                    sprite.blit(surface,anchor)
                else:
                    rock = rect.inflate(-rect.width*.3,-rect.height*.3)
                    rock.midbottom = tuple(round(v) for v in anchor)
                    pygame.draw.rect(surface,(92,89,84),rock,border_radius=6)
                    pygame.draw.line(surface,(172,159,133),rock.topleft,rock.bottomright,2)
                continue
            clip = self.assets.visual(item.definition_id,"idle",scale)
            if clip:
                clip.frame_at(self.elapsed).blit(surface,anchor)
            elif item.team == "ally":
                pygame.draw.circle(surface,(61,131,177),rect.center,rect.width//2)
                pygame.draw.circle(surface,(163,215,227),rect.center,rect.width//2,2)
            else:
                block = rect
                pygame.draw.rect(surface,(170,72,64),block,border_radius=3)
                pygame.draw.rect(surface,(235,162,128),block,2,border_radius=3)
        # Every mark and health bar remains above all large neighboring bodies.
        for unit in view.units:
            rect = pygame.Rect(self.geometry.body_rect(unit.cell))
            if unit.uid == view.active_uid:
                pygame.draw.polygon(surface,(239,204,113),self.geometry.cell_polygon(unit.cell),2)
            if unit.uid == view.selected_uid:
                pygame.draw.polygon(surface,(235,238,219),self.geometry.cell_polygon(unit.cell),3)
            label = self.label_font.render(unit.uid,True,(255,249,225))
            surface.blit(label,label.get_rect(center=rect.center))
            bar = pygame.Rect(rect.x,rect.top-7,rect.width,4)
            pygame.draw.rect(surface,(33,30,28),bar)
            fill = bar.copy()
            fill.width = round(bar.width*min(1,unit.health/max(1,unit.max_health)))
            pygame.draw.rect(surface,(116,192,151),fill)
```

## tactics/perspective_geometry.py

```python
"""Cached planar projection and inverse picking, with no graphics dependency."""

import math
from dataclasses import dataclass, field

EPSILON = 1e-9


def pair(value, label, positive=False):
    if (not isinstance(value, (tuple, list)) or len(value) != 2
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in value)
            or (positive and any(v <= 0 for v in value))):
        raise ValueError(label + " must be a finite pair" + (" of positive numbers" if positive else ""))
    return tuple(value)


@dataclass(frozen=True)
class BackgroundFit:
    image_size: tuple
    viewport_size: tuple

    def __post_init__(self):
        object.__setattr__(self, "image_size", pair(self.image_size, "image size", True))
        object.__setattr__(self, "viewport_size", pair(self.viewport_size, "viewport size", True))

    @property
    def scale(self):
        return min(v / i for v, i in zip(self.viewport_size, self.image_size))

    @property
    def offset(self):
        return tuple((v - i * self.scale) / 2 for v, i in zip(self.viewport_size, self.image_size))

    def to_screen(self, point):
        return tuple(v * self.scale + d for v, d in zip(point, self.offset))

    def to_image(self, point):
        return tuple((v - d) / self.scale for v, d in zip(point, self.offset))


def inverse(matrix):
    a, b, c, d, e, f, g, h, i = matrix
    adj = (e*i-f*h, c*h-b*i, b*f-c*e, f*g-d*i, a*i-c*g, c*d-a*f,
           d*h-e*g, b*g-a*h, a*e-b*d)
    determinant = a*adj[0] + b*adj[3] + c*adj[6]
    if abs(determinant) < EPSILON:
        raise ValueError("board corners produce a singular homography")
    return tuple(v / determinant for v in adj)


def transform(matrix, point):
    x, y = point
    denominator = matrix[6]*x + matrix[7]*y + matrix[8]
    if not math.isfinite(denominator) or abs(denominator) < EPSILON:
        raise ValueError("point is on the projection horizon")
    result = ((matrix[0]*x + matrix[1]*y + matrix[2])/denominator,
              (matrix[3]*x + matrix[4]*y + matrix[5])/denominator)
    if not all(math.isfinite(v) for v in result):
        raise ValueError("non-finite projection")
    return result


@dataclass(frozen=True)
class PerspectiveBoardGeometry:
    cols: int
    rows: int
    corners: tuple
    reference_size: tuple
    viewport_size: tuple = (1280, 720)
    reference_region: tuple = None
    cells: tuple = None
    _cell_set: frozenset = field(init=False, repr=False)
    _matrix: tuple = field(init=False, repr=False)
    _inverse: tuple = field(init=False, repr=False)
    _polygons: tuple = field(init=False, repr=False)
    _centers: tuple = field(init=False, repr=False)
    _anchors: tuple = field(init=False, repr=False)
    _scales: tuple = field(init=False, repr=False)
    fit: BackgroundFit = field(init=False)

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in (self.cols, self.rows)):
            raise ValueError("board dimensions must be positive integers")
        region = (0, 0, self.cols, self.rows) if self.reference_region is None else self.reference_region
        if (not isinstance(region, (tuple, list)) or len(region) != 4
                or any(type(v) is not int for v in region)
                or min(region[:2]) < 0 or min(region[2:]) <= 0
                or region[0]+region[2] > self.cols or region[1]+region[3] > self.rows):
            raise ValueError("reference_region must be an integer rectangle inside the logical board")
        object.__setattr__(self, "reference_region", tuple(region))
        cells = tuple((c,r) for r in range(self.rows) for c in range(self.cols)) if self.cells is None else self.cells
        if (not isinstance(cells, (tuple, list)) or not cells
                or any(not isinstance(p, (tuple, list)) or len(p) != 2
                       or any(type(v) is not int for v in p)
                       or not (0 <= p[0] < self.cols and 0 <= p[1] < self.rows) for p in cells)):
            raise ValueError("cells must be nonempty integer cells inside the logical board")
        cell_set = frozenset(tuple(p) for p in cells)
        if len(cell_set) != len(cells):
            raise ValueError("duplicate playable cell")
        object.__setattr__(self, "_cell_set", cell_set)
        object.__setattr__(self, "cells", tuple(sorted(cell_set, key=lambda p: (p[1],p[0]))))
        fit = BackgroundFit(self.reference_size, self.viewport_size)
        object.__setattr__(self, "reference_size", fit.image_size)
        object.__setattr__(self, "viewport_size", fit.viewport_size)
        object.__setattr__(self, "fit", fit)
        if not isinstance(self.corners, (tuple, list)) or len(self.corners) != 4:
            raise ValueError("board requires p00, p10, p11, p01 corners")
        corners = tuple(pair(p, "board corner") for p in self.corners)
        w, height = self.reference_size
        if any(not (0 <= x <= w and 0 <= y <= height) for x, y in corners):
            raise ValueError("board corners must be inside the reference image")
        points = tuple((x/w, y/height) for x, y in corners)
        for index in range(4):
            a, b, c = (points[(index+k) % 4] for k in range(3))
            if (b[0]-a[0])*(c[1]-b[1]) - (b[1]-a[1])*(c[0]-b[0]) <= EPSILON:
                raise ValueError("board corners must form a strictly convex clockwise screen polygon")
        object.__setattr__(self, "corners", corners)
        (x0,y0), (x1,y1), (x2,y2), (x3,y3) = points
        dx1, dx2, dx3 = x1-x2, x3-x2, x0-x1+x2-x3
        dy1, dy2, dy3 = y1-y2, y3-y2, y0-y1+y2-y3
        if abs(dx3) + abs(dy3) < EPSILON:
            g = h = 0.0
        else:
            denominator = dx1*dy2-dx2*dy1
            if abs(denominator) < EPSILON:
                raise ValueError("board corners produce a degenerate projection")
            g = (dx3*dy2-dx2*dy3)/denominator
            h = (dx1*dy3-dx3*dy1)/denominator
        matrix = (x1-x0+g*x1, x3-x0+h*x3, x0,
                  y1-y0+g*y1, y3-y0+h*y3, y0, g, h, 1.0)
        object.__setattr__(self, "_matrix", matrix)
        object.__setattr__(self, "_inverse", inverse(matrix))
        polygons, centers, anchors, scales = [], [], [], []
        for row in range(self.rows):
            for col in range(self.cols):
                if (col,row) not in self._cell_set:
                    for cache in (polygons, centers, anchors, scales):
                        cache.append(None)
                    continue
                polygon = tuple(self.project(p) for p in ((col,row),(col+1,row),(col+1,row+1),(col,row+1)))
                if any(not (-EPSILON <= x <= self.reference_size[0]+EPSILON
                            and -EPSILON <= y <= self.reference_size[1]+EPSILON)
                       for x,y in (self.fit.to_image(point) for point in polygon)):
                    raise ValueError("playable cell projects outside reference image")
                polygons.append(polygon)
                centers.append(self.project((col+.5, row+.5)))
                anchors.append(self.project((col+.5, row+.82)))
                # Quantize to a small, bounded set of preloaded sprite scales.
                edge = math.dist(polygon[0], polygon[1]) + math.dist(polygon[1], polygon[2])
                scales.append(round(max(.5, min(1.5, edge / 2 / 64)) * 8) / 8)
        for name, value in (("_polygons",polygons),("_centers",centers),("_anchors",anchors),("_scales",scales)):
            object.__setattr__(self, name, tuple(value))

    @property
    def bounds(self):
        return (0, 0, *self.viewport_size)

    def _index(self, cell):
        if (not isinstance(cell, (tuple, list)) or len(cell) != 2
                or any(type(v) is not int for v in cell)
                or tuple(cell) not in self._cell_set):
            raise ValueError("cell outside perspective board: {}".format(cell))
        return cell[1]*self.cols + cell[0]

    def project(self, logical_point):
        point = pair(logical_point, "logical point")
        ox, oy, width, height = self.reference_region
        x, y = transform(self._matrix, ((point[0]-ox)/width, (point[1]-oy)/height))
        return self.fit.to_screen((x*self.reference_size[0], y*self.reference_size[1]))

    def cell_at(self, position):
        try:
            x, y = self.fit.to_image(pair(position, "screen point"))
            if not (0 <= x < self.reference_size[0] and 0 <= y < self.reference_size[1]):
                return None
            u, v = transform(self._inverse, (x/self.reference_size[0], y/self.reference_size[1]))
            ox, oy, width, height = self.reference_region
            u, v = u*width+ox, v*height+oy
            # Snap roundoff on exact shared edges; ownership remains [left, right).
            u = round(u) if abs(u-round(u)) < EPSILON else u
            v = round(v) if abs(v-round(v)) < EPSILON else v
            if 0 <= u < self.cols and 0 <= v < self.rows:
                cell = math.floor(u), math.floor(v)
                return cell if cell in self._cell_set else None
        except (ValueError, TypeError, OverflowError):
            pass
        return None

    def cell_polygon(self, cell):
        return self._polygons[self._index(cell)]

    def cell_center(self, cell):
        return self._centers[self._index(cell)]

    def cell_anchor(self, cell):
        return self._anchors[self._index(cell)]

    def cell_scale(self, cell):
        return self._scales[self._index(cell)]

    def depth_at(self, cell):
        return self.cell_anchor(cell)[1]

    def body_rect(self, cell):
        x, y = self.cell_anchor(cell)
        size = round(42*self.cell_scale(cell))
        return round(x-size/2), round(y-size), size, size

    @property
    def scales(self):
        return tuple(sorted(s for s in set(self._scales) if s is not None))
```

## tactics/presentation_layout.py

```python
"""Strict, graphics-independent presentation configuration rooted in the project."""

from dataclasses import dataclass
from pathlib import Path

from .data_files import DataError, PROJECT_ROOT, fields, number, read_json, rooted_path, text, version
from .perspective_geometry import PerspectiveBoardGeometry


@dataclass(frozen=True)
class PresentationLayout:
    presentation_id: str
    scenario_file: str
    asset_root: Path
    geometry: PerspectiveBoardGeometry
    safe_margin: int
    debug: tuple


def size_pair(value, label):
    if not isinstance(value, list) or len(value) != 2:
        raise DataError(label + ": expected integer size pair")
    return tuple(number(v, label, minimum=1, integer=True) for v in value)


def load_presentation(filename, root=None):
    root = PROJECT_ROOT if root is None else Path(root)
    path = rooted_path(root, filename, "presentation path")
    label = str(path)
    data = read_json(path)
    fields(data, ("schema_version","id","mode","scenario_file","asset_root","viewport","board","hud","debug"), (), label)
    version(data, label)
    if data["mode"] != "perspective":
        raise DataError(label + ": mode must be perspective")
    scenario_file = text(data["scenario_file"], label + ".scenario_file")
    rooted_path(root / "content", scenario_file, label + ".scenario_file")
    asset_root = rooted_path(root, data["asset_root"], label + ".asset_root")
    viewport, board, hud, debug = (data[k] for k in ("viewport","board","hud","debug"))
    fields(viewport, ("reference_size","background_fit"), (), label + ".viewport")
    if viewport["background_fit"] != "contain":
        raise DataError(label + ": background_fit must be contain")
    viewport_size = size_pair(viewport["reference_size"], label + ".viewport.reference_size")
    fields(board, ("cols","rows","reference_image_size","corners"), ("reference_region","cells"), label + ".board")
    cols = number(board["cols"], label + ".board.cols", minimum=1, integer=True)
    rows = number(board["rows"], label + ".board.rows", minimum=1, integer=True)
    image_size = size_pair(board["reference_image_size"], label + ".board.reference_image_size")
    if any(key in board and board[key] is None for key in ("reference_region","cells")):
        raise DataError(label + ".board: optional region/cells cannot be null")
    fields(board["corners"], ("p00","p10","p11","p01"), (), label + ".board.corners")
    try:
        geometry = PerspectiveBoardGeometry(cols, rows, tuple(board["corners"][k] for k in ("p00","p10","p11","p01")),
                                            image_size, viewport_size, board.get("reference_region"), board.get("cells"))
    except ValueError as error:
        raise DataError(label + ".board.corners: " + str(error)) from error
    fields(hud, ("layout","safe_margin"), (), label + ".hud")
    margin = number(hud["safe_margin"], label + ".hud.safe_margin", minimum=0, integer=True)
    if (hud["layout"] != "overlay" or viewport_size[0] < 960 or viewport_size[1] < 600
            or 2*margin+860 > viewport_size[0] or 2*margin+254 > viewport_size[1]):
        raise DataError(label + ": overlay HUD needs viewport >= 960x600 and both cards inside safe margins")
    fields(debug, ("show_grid","show_cell_centers","show_coordinates"), (), label + ".debug")
    if any(type(v) is not bool for v in debug.values()):
        raise DataError(label + ".debug: expected booleans")
    return PresentationLayout(text(data["id"], label + ".id"), scenario_file, asset_root, geometry, margin,
                              tuple(debug.items()))
```

## tactics/scenario.py

```python
"""Immutable, validated scenario inputs and fresh runtime-unit construction."""

from dataclasses import asdict, dataclass
from typing import FrozenSet, Tuple

from .models import Cell, Unit


def _cell(value, label):
    if (not isinstance(value, (tuple, list)) or len(value) != 2
            or any(type(number) is not int for number in value)):
        raise ValueError("{} must be a pair of integer grid coordinates".format(label))
    return tuple(value)


@dataclass(frozen=True)
class UnitSpawn:
    uid: str
    name: str
    team: str
    role: str
    cell: Cell
    health: int = 100
    max_health: int = 100
    attack: int = 10
    defense: int = 5
    speed: int = 10
    movement: int = 3
    definition_id: str = ""

    def __post_init__(self):
        object.__setattr__(self, "cell", _cell(self.cell, "unit {} cell".format(self.uid)))


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    cols: int
    rows: int
    units: Tuple[UnitSpawn, ...]
    obstacles: FrozenSet[Cell] = frozenset()

    def __post_init__(self):
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ValueError("scenario_id must be a nonempty string")
        if any(type(value) is not int or value <= 0 for value in (self.cols, self.rows)):
            raise ValueError("scenario dimensions must be positive integers")
        object.__setattr__(self, "units", tuple(self.units))
        object.__setattr__(self, "obstacles", frozenset(_cell(cell, "obstacle") for cell in self.obstacles))
        for cell in self.obstacles:
            self._check_bounds(cell, "obstacle")
        occupied = set(self.obstacles)
        uids = set()
        teams = set()
        for spawn in self.units:
            if not isinstance(spawn, UnitSpawn):
                raise ValueError("scenario units must be immutable UnitSpawn values")
            if not isinstance(spawn.definition_id, str):
                raise ValueError("unit definition_id must be a string")
            for name in ("uid", "name", "role"):
                value = getattr(spawn, name)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("unit {} must be a nonempty string".format(name))
            if spawn.uid in uids:
                raise ValueError("duplicate unit uid: {}".format(spawn.uid))
            if spawn.team not in ("ally", "enemy"):
                raise ValueError("unit {} has an unknown team".format(spawn.uid))
            self._check_bounds(spawn.cell, spawn.uid)
            if spawn.cell in occupied:
                raise ValueError("unit {} overlaps an obstacle or another unit".format(spawn.uid))
            for name in ("health", "max_health", "attack", "defense", "speed", "movement"):
                value = getattr(spawn, name)
                if type(value) is not int or value < 0:
                    raise ValueError("unit {} {} must be a nonnegative integer".format(spawn.uid, name))
            if not 0 < spawn.health <= spawn.max_health:
                raise ValueError("unit {} must start alive with health <= max_health".format(spawn.uid))
            occupied.add(spawn.cell)
            uids.add(spawn.uid)
            teams.add(spawn.team)
        if teams != {"ally", "enemy"}:
            raise ValueError("a scenario must start with at least one living unit on each team")

    def _check_bounds(self, cell, label):
        if not (0 <= cell[0] < self.cols and 0 <= cell[1] < self.rows):
            raise ValueError("{} cell {} is outside the scenario".format(label, cell))

    def create_units(self):
        """Each battle owns its Unit instances; the reusable scenario stays unchanged."""
        return tuple(Unit(**asdict(spawn)) for spawn in self.units)


def default_scenario():
    # Local import keeps the public factory while content imports these data types.
    from .content import load_content
    return load_content().scenario
```

## tactics/scene_hud.py

```python
"""Overlay-only UI; hit testing returns intent without touching combat state."""

import pygame

from .actions import UIAction
from .panel import load_fonts


class SceneHUD:
    def __init__(self, viewport_size, margin=24):
        fonts, self.chinese = load_fonts()
        self.title_font, self.font, self.small_font = fonts
        self.card = pygame.Rect(margin,margin,350,254)
        self.history = pygame.Rect(margin+370,margin,490,112)
        x,y = self.card.topleft
        self._buttons = {UIAction.UNDO:pygame.Rect(x+12,y+210,100,32),
                         UIAction.SKIP_PHASE:pygame.Rect(x+122,y+210,104,32),
                         UIAction.END_TURN:pygame.Rect(x+236,y+210,102,32)}
        self._cards = []
        for rect in (self.card,self.history):
            layer = pygame.Surface(rect.size,pygame.SRCALPHA)
            layer.fill((20,26,31,205))
            pygame.draw.rect(layer,(143,139,113,180),layer.get_rect(),1,border_radius=8)
            self._cards.append((rect,layer))

    def contains(self, position):
        """Consume the full HUD surface, including labels and gaps between buttons."""
        return self.card.collidepoint(position) or self.history.collidepoint(position)

    def hit_test(self, position):
        return next((action for action,rect in self._buttons.items() if rect.collidepoint(position)),None)

    def _text(self,surface,value,position,width,font=None,color=(226,226,211)):
        font = self.small_font if font is None else font
        while value and font.size(value)[0] > width:
            value = value[:-1]
        surface.blit(font.render(value,True,color),position)

    def draw(self,surface,view):
        for rect,layer in self._cards:
            surface.blit(layer,rect)
        x,y = self.card.x+14,self.card.y+10
        cn = self.chinese
        actor = view.active
        title = ("第 {} 回合" if cn else "ROUND {}").format(view.round_number)
        self._text(surface,title,(x,y),320,self.title_font,(240,211,148))
        if view.finished:
            winner = {"ally":"蓝方获胜","enemy":"红方获胜","draw":"平局"}.get(view.winner,view.winner)
            state = "战斗结束 · " + winner if cn else "FINISHED / {} wins".format(view.winner)
        else:
            name = actor.name if cn else actor.uid
            phase = {"move":"移动","attack":"攻击","resolving":"结算中"}[view.phase] if cn else view.phase
            state = ("行动：{} [{}] · {}" if cn else "Active: {} [{}] / {}").format(name,actor.uid,phase)
        self._text(surface,state,(x,y+36),320,self.font)
        unit = view.selected
        if unit:
            name = unit.name if cn else unit.uid
            self._text(surface,("查看：{} [{}]" if cn else "Inspect: {} [{}]").format(name,unit.uid),(x,y+68),320,self.font)
            stats = (("生命" if cn else "HP","{}/{}".format(unit.health,unit.max_health)),
                     ("攻击" if cn else "ATK",unit.attack),("防御" if cn else "DEF",unit.defense),
                     ("速度" if cn else "SPD",unit.speed),("移动" if cn else "MOVE",unit.movement),
                     ("范围" if cn else "RANGE",1))
            for index,(label,value) in enumerate(stats):
                self._text(surface,"{}: {}".format(label,value),(x+(index%2)*170,y+100+(index//2)*25),160,self.font)
        hint = "结算中，请稍候" if cn and view.input_locked else "鼠标选择/行动 · F3 网格" if cn else "Click to inspect/act / F3 grid"
        self._text(surface,hint,(x,y+178),320,color=(163,194,183))
        enabled = {UIAction.UNDO:view.can_undo,UIAction.SKIP_PHASE:view.can_skip,UIAction.END_TURN:view.can_end_turn}
        labels = {UIAction.UNDO:"回溯 [退格]" if cn else "Undo [Bksp]",
                  UIAction.SKIP_PHASE:"跳过 [空格]" if cn else "Skip [Space]",
                  UIAction.END_TURN:"结束 [回车]" if cn else "End [Enter]"}
        for action,rect in self._buttons.items():
            pygame.draw.rect(surface,(65,77,75) if enabled[action] else (40,44,45),rect,border_radius=4)
            label = self.small_font.render(labels[action],True,(241,224,188) if enabled[action] else (110,117,116))
            surface.blit(label,label.get_rect(center=rect.center))
        hx,hy = self.history.x+12,self.history.y+10
        order = " → ".join("{}({})".format(u.uid,u.speed) for u in view.order)
        self._text(surface,("顺序：" if cn else "Order: ")+order,(hx,hy),466,color=(233,202,144))
        for index,message in enumerate(view.log[-3:]):
            self._text(surface,message[0 if cn else 1],(hx,hy+27+index*22),466)
```

## tactics/settings.py

```python
"""Presentation defaults only; logical board dimensions come from the scenario."""

CELL_SIZE = 64
PANEL_WIDTH = 384
MIN_WINDOW_HEIGHT = 512
FPS = 60
```

## tactics/view_models.py

```python
"""Detached, immutable values shared by the application and presentation layers."""

from dataclasses import dataclass
from typing import FrozenSet, Optional, Tuple

from .models import AttackResult, Cell


@dataclass(frozen=True)
class BoardUnitView:
    uid: str
    team: str
    cell: Cell
    health: int
    max_health: int
    definition_id: str = ""


@dataclass(frozen=True)
class BoardView:
    cols: int
    rows: int
    obstacles: FrozenSet[Cell]
    units: Tuple[BoardUnitView, ...]
    active_uid: Optional[str]
    selected_uid: Optional[str]
    move_cells: FrozenSet[Cell]
    attack_cells: FrozenSet[Cell]
    target_cells: FrozenSet[Cell]


@dataclass(frozen=True)
class UnitView:
    uid: str
    name: str
    team: str
    role: str
    cell: Cell
    health: int
    max_health: int
    attack: int
    defense: int
    speed: int
    movement: int
    definition_id: str = ""

    @property
    def alive(self):
        return self.health > 0


@dataclass(frozen=True)
class BattleView:
    board: BoardView
    units: Tuple[UnitView, ...]
    active: Optional[UnitView]
    selected: Optional[UnitView]
    phase: str
    round_number: int
    winner: Optional[str]
    order: Tuple[UnitView, ...]
    log: Tuple[Tuple[str, str], ...]
    can_undo: bool
    can_skip: bool
    can_end_turn: bool
    input_locked: bool
    presentation_generation: int
    pending_resolution: Optional["ResolutionToken"]

    @property
    def finished(self):
        return self.winner is not None


@dataclass(frozen=True)
class ResolutionToken:
    """Identity of one blocking presentation in one controller generation."""

    generation: int
    resolution_id: int


@dataclass(frozen=True)
class AttackPresentation:
    token: ResolutionToken
    result: AttackResult


def build_board_view(board, battle, selected):
    """Project existing legal queries into values; never expose live Unit objects."""
    active = battle.active_unit
    move_cells = attack_cells = target_cells = frozenset()
    if active is not None and selected is active:
        if battle.phase == "move":
            move_cells = frozenset(battle.movement_range())
        elif battle.phase == "attack":
            attack_cells = frozenset(board.neighbors(active.cell)) - board.obstacles
            target_cells = frozenset(unit.cell for unit in battle.attack_targets())
    return BoardView(
        board.cols, board.rows, frozenset(board.obstacles),
        tuple(BoardUnitView(unit.uid, unit.team, tuple(unit.cell), unit.health, unit.max_health, unit.definition_id)
              for unit in board.living_units),
        active.uid if active is not None else None,
        selected.uid if selected is not None else None,
        move_cells, attack_cells, target_cells,
    )


def build_battle_view(board, battle, selected, presentation_generation, pending_resolution):
    """Build one consistent snapshot, including units that a later undo may revive."""
    units = tuple(UnitView(
        unit.uid, unit.name, unit.team, unit.role, tuple(unit.cell),
        unit.health, unit.max_health, unit.attack, unit.defense, unit.speed, unit.movement,
        unit.definition_id,
    ) for unit in board.units)
    by_uid = {unit.uid: unit for unit in units}
    actor = battle.active_unit
    can_act = battle.phase in ("move", "attack")
    return BattleView(
        build_board_view(board, battle, selected), units,
        by_uid[actor.uid] if actor is not None else None,
        by_uid[selected.uid] if selected is not None else None,
        battle.phase, battle.round_number, battle.winner,
        tuple(by_uid[unit.uid] for unit in battle.order),
        tuple(tuple(message) for message in battle.log),
        battle.can_undo, can_act, can_act, battle.phase == "resolving",
        presentation_generation, pending_resolution,
    )
```

## tests/test_assets.py

```python
"""Real PNG cache, fallback, layering and M3 animation handoff checks."""

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

from tactics.assets import AssetManager
from tactics.content import load_content
from tactics.data_files import DataError
from tactics.game import Game
from tactics.scenario import Scenario, UnitSpawn, default_scenario


class AssetChecks(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_mode((128, 128))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(pygame.quit)
        self.root = Path(self.temp.name)
        for name, color in (("one", (0, 200, 210)), ("two", (205, 40, 180)), ("floor", (18, 34, 58))):
            image = pygame.Surface((8, 12), pygame.SRCALPHA)
            image.fill(color if name == "floor" else (0, 0, 0, 0))
            if name != "floor":pygame.draw.rect(image, color, (1, 2, 6, 10))
            pygame.image.save(image, str(self.root / (name + ".png")))
        self.data = {
            "schema_version":1,
            "images":{key:{"path":path, "display_size":size, "pivot":[.5, 1] if key != "floor" else [.5,.5],
                           "optional":True}
                      for key, path, size in (("idle0","one.png",[64,96]), ("idle1","two.png",[64,96]),
                                               ("floor","floor.png",[64,64]), ("alias","one.png",[64,96]))},
            "animations":{
                "idle":{"frames":["idle0","idle1"], "fps":2, "loop":True},
                "attack":{"frames":["idle0","idle1"], "fps":4, "loop":False},
                "death":{"frames":["idle1","idle0"], "fps":2, "loop":False}},
            "visuals":{"unit.scout":{"idle":"idle", "attack":"attack", "death":"death"},
                       "unit.vanguard":{}, "unit.guard":{}, "unit.dummy":{}},
            "board":{"floor":"floor"}}
        self.write()

    def write(self):
        (self.root / "manifest.json").write_text(json.dumps(self.data), encoding="utf-8")

    def manager(self):
        self.write()
        return AssetManager(self.root, load_content().definitions)

    def game(self, scenario=None, **kwargs):
        self.write()
        return Game(scenario, asset_root=self.root, **kwargs)

    def test_original_and_scaled_images_are_cached_across_aliases_and_sizes(self):
        with patch("tactics.assets.pygame.image.load", wraps=pygame.image.load) as load, \
             patch("tactics.assets.pygame.transform.smoothscale", wraps=pygame.transform.smoothscale) as scale:
            manager = self.manager()
            first = manager.get_image("idle0")
            self.assertIs(first.surface, manager.get_image("alias").surface)
            count = scale.call_count
            half = manager.get_image("idle0", .5)
            self.assertEqual(half.surface.get_size(), (32, 48))
            self.assertIs(half, manager.get_image("idle0", .5))
            self.assertEqual(scale.call_count, count + 1)
            self.assertEqual(sum(Path(call.args[0]).name == "one.png" for call in load.call_args_list), 1)

    def test_optional_missing_is_negative_cached_reported_once_and_reload_is_explicit(self):
        (self.root / "one.png").unlink()
        with self.assertLogs("tactics.assets", level="WARNING"):
            manager = self.manager()
        issues = manager.issues
        with patch("tactics.assets.pygame.image.load", side_effect=AssertionError("retried missing file")):
            self.assertIsNone(manager.get_image("idle0", .5))
            self.assertIsNone(manager.get_clip("attack"))
        self.assertEqual(manager.issues, issues)
        image = pygame.Surface((8, 12), pygame.SRCALPHA)
        pygame.image.save(image, str(self.root / "one.png"))
        self.assertIsNone(manager.get_image("idle0"))
        manager.clear_cache()
        manager.preload()
        self.assertIsNotNone(manager.get_image("idle0"))

    def test_corrupt_optional_image_falls_back_and_required_image_fails_at_startup(self):
        (self.root / "one.png").write_bytes(b"broken PNG")
        with self.assertLogs("tactics.assets", level="WARNING"):
            self.assertIsNone(self.manager().visual("scout", "idle"))
        self.data["images"]["idle0"]["optional"] = False
        self.write()
        with self.assertRaisesRegex(DataError, "required image unavailable.*idle0"):
            Game(asset_root=self.root)
        self.assertFalse(pygame.display.get_init())

    def test_unused_required_entry_is_validated_even_after_optional_alias_failed(self):
        self.data["images"]["optional"] = dict(self.data["images"]["idle0"], path="missing.png")
        self.data["images"]["required"] = dict(self.data["images"]["optional"], optional=False)
        with self.assertLogs("tactics.assets", level="WARNING"), \
             self.assertRaisesRegex(DataError, "required image unavailable.*required"):
            self.manager()

    def test_unknown_visual_binding_is_a_clear_initialization_error(self):
        content = load_content()
        definitions = (replace(content.definitions[0], visual_id="unknown"),)
        with self.assertRaisesRegex(DataError, "vanguard.*unknown visual"):
            AssetManager(self.root, definitions)

    def test_asset_loading_requires_initialized_display(self):
        pygame.quit()
        with self.assertRaisesRegex(DataError, "initialized display"):
            self.manager()

    def test_frame_selection_loop_and_completion_are_independent_of_global_busy(self):
        manager = self.manager()
        idle = manager.visual("scout", "idle")
        self.assertIs(idle.frame_at(0), idle.frame_at(1))
        self.assertIsNot(idle.frame_at(0), idle.frame_at(.5))
        self.assertFalse(idle.finished(1000))
        attack = manager.visual("scout", "attack")
        self.assertFalse(attack.finished(.49))
        self.assertTrue(attack.finished(.5))
        self.assertIs(attack.frame_at(100), attack.frames[-1])
        self.assertIsNone(manager.visual("unknown", "idle"))

    def test_pivot_transparency_and_requested_sizes_are_preserved(self):
        sprite = self.manager().get_image("idle0")
        surface = pygame.Surface((100, 120))
        surface.fill("white")
        sprite.blit(surface, (50, 110))
        self.assertEqual(tuple(surface.get_at((18, 14)))[:3], (255, 255, 255))
        self.assertEqual(tuple(surface.get_at((50, 80)))[:3], (0, 200, 210))
        self.assertEqual(sprite.surface.get_at((0, 0)).a, 0)
        for value in (True, 0, -1, float("nan")):
            with self.subTest(value=value), self.assertRaises(DataError):
                self.manager().get_clip("attack", value)

    def test_game_default_render_chain_uses_supplied_floor_and_unit_images(self):
        game = self.game()
        game.draw()
        self.assertEqual(tuple(game.screen.get_at((470, 470)))[:3], (18, 34, 58))
        self.assertEqual(tuple(game.screen.get_at((85, 185)))[:3], (0, 200, 210))
        self.assertEqual(game.geometry.cell_at((85, 185)), (1, 2))  # Tall art does not move the unit.
        self.assertEqual(game.controller.get_view_state().active.cell, (1, 3))

    def test_repeated_draws_and_idle_updates_do_not_load_scale_or_change_rule_state(self):
        game = self.game()
        before = game.controller.get_view_state()
        with patch("tactics.assets.pygame.image.load", side_effect=AssertionError("per-frame load")), \
             patch("tactics.assets.pygame.transform.smoothscale", side_effect=AssertionError("per-frame scale")):
            for _ in range(5):
                game.update(.5)
                game.draw()
            self.assertEqual(game.controller.get_view_state(), before)
            game.controller.move_to((4, 4))
            game.controller.attack("D2")
            self.assertEqual(tuple(body.uid for body in game.effects.body_views()), ("A2",))
            game.update(.1)
            game.draw()
            game.update(.81)
            self.assertEqual(game.controller.get_view_state().active.uid, "A1")

    def test_geometry_and_images_produce_identical_move_attack_and_undo_state(self):
        views = []
        for geometric in (True, False):
            game = self.game(geometric=geometric)
            game.controller.move_to((4, 4))
            game.controller.attack("D2")
            game.update(2)
            after = game.controller.get_view_state()
            game.controller.undo()
            views.append((after, game.controller.get_view_state()))
        self.assertEqual(*views)

    def test_sprite_death_waits_hides_and_undo_restores_without_old_callback(self):
        scenario = Scenario("death", 3, 3, (
            UnitSpawn("blue", "Blue", "ally", "test", (0, 1), speed=20, definition_id="vanguard"),
            UnitSpawn("red", "Red", "enemy", "test", (2, 1), health=5, definition_id="scout")))
        game = self.game(scenario)
        game.controller.move_to((1, 1))
        game.controller.attack("red")
        token = game.controller.get_view_state().pending_resolution
        self.assertEqual(tuple(body.uid for body in game.effects.body_views()), ("red",))
        game.update(.91)
        self.assertTrue(game.controller.get_view_state().input_locked)
        game.draw()
        game.update(.1)
        self.assertFalse(game.effects.body_views())
        self.assertEqual(game.controller.get_view_state().winner, "ally")
        self.assertFalse(game.controller.complete_presentation(token))
        game.draw()
        self.assertEqual(tuple(game.screen.get_at(game.geometry.cell_center((2, 1))))[:3], (18, 34, 58))
        game.controller.undo()
        self.assertFalse(game.effects.busy)
        self.assertFalse(game.controller.complete_presentation(token))
        self.assertEqual(len(game.controller.get_view_state().board.units), 2)
        game.draw()

    def test_missing_all_optional_pngs_matches_geometry_pixels_and_attack_fallback(self):
        for path in self.root.glob("*.png"):path.unlink()
        with self.assertLogs("tactics.assets", level="WARNING"):
            game = self.game()
        game.draw()
        image = pygame.image.tostring(game.screen, "RGBA")
        game.controller.move_to((4, 4))
        game.controller.attack("D2")
        self.assertFalse(game.effects.sprites)
        game.update(1)
        self.assertEqual(game.controller.get_view_state().active.uid, "A1")
        geometric = self.game(geometric=True)
        geometric.draw()
        self.assertEqual(image, pygame.image.tostring(geometric.screen, "RGBA"))
        scenario = Scenario("fallback_death", 3, 3, (
            UnitSpawn("blue", "Blue", "ally", "test", (2, 1), health=5, speed=5, definition_id="scout"),
            UnitSpawn("red", "Red", "enemy", "test", (0, 1), speed=20, definition_id="dummy")))
        with self.assertLogs("tactics.assets", level="WARNING"):
            death = self.game(scenario)
        death.controller.move_to((1, 1))
        death.controller.attack("blue")
        self.assertEqual(len(death.effects.deaths), 1)
        self.assertFalse(death.effects.sprites)
        death.update(1)
        self.assertEqual(death.controller.get_view_state().winner, "enemy")
        self.assertTrue(death.controller.undo())

    def test_manifest_only_replacement_changes_art_without_changing_rule_values(self):
        game = self.game()
        game.draw()
        pixel = tuple(game.screen.get_at((85, 185)))
        before = game.controller.get_view_state()
        self.data["visuals"]["unit.scout"]["idle"] = "idle1"
        replacement = self.game()
        replacement.draw()
        self.assertNotEqual(tuple(replacement.screen.get_at((85, 185))), pixel)
        self.assertEqual(replacement.controller.get_view_state(), before)

    def test_all_overlays_remain_above_tall_sprites_and_clip_is_restored(self):
        scenario = Scenario("layers", 3, 3, (
            UnitSpawn("blue", "Blue", "ally", "test", (1, 1), speed=20, definition_id="vanguard"),
            UnitSpawn("red", "Red", "enemy", "test", (1, 2), definition_id="scout")))
        game = self.game(scenario)
        game.draw()
        self.assertEqual(tuple(game.screen.get_at((76, 122)))[:3], (105, 218, 153))
        surface = pygame.Surface((250, 250))
        surface.fill("magenta")
        surface.set_clip((10, 10, 220, 220))
        before = surface.get_clip()
        game.renderer.draw(surface, game.controller.get_view_state().board)
        self.assertEqual(surface.get_clip(), before)
        self.assertEqual(tuple(surface.get_at((200, 200)))[:3], (255, 0, 255))

    def test_geometric_mode_does_not_need_manifest_or_image_directory(self):
        game = Game(asset_root=self.root / "absent", geometric=True)
        self.assertIsNone(game.assets)
        game.draw()


if __name__ == "__main__":
    unittest.main()
```

## tests/test_battle.py

```python
"""Rule checks without a window: speed order, paths, turn limits, damage."""

import unittest

from tactics.battle import Battle
from tactics.board import Board
from tactics.scenario import default_scenario


class BattleChecks(unittest.TestCase):
    def setUp(self):
        self.board = Board(default_scenario())
        self.battle = Battle(self.board)
        self.actor = self.battle.active_unit

    def test_speed_order_includes_both_teams(self):
        self.assertEqual([unit.uid for unit in self.battle.order],
                         ["A2", "A1", "D1", "A3", "D2", "D3"])
        self.assertEqual(self.battle.round_number, 1)
        self.assertEqual(self.battle.phase, "move")

    def test_tied_speed_preserves_entry_order(self):
        for unit in self.board.units:
            unit.speed = 10
        self.assertEqual(Battle(self.board).order, self.board.units)

    def test_movement_counts_real_path_around_wall(self):
        reachable = self.battle.movement_range()
        self.assertIn((4, 4), reachable)  # Four actual steps around the wall.
        self.assertNotIn((4, 3), reachable)  # Manhattan distance 3, real path 5.
        self.assertNotIn((3, 3), reachable)  # Obstacle.
        self.assertNotIn((1, 1), reachable)  # Ally.
        self.assertNotIn((5, 4), reachable)  # Enemy.
        self.assertNotIn(self.actor.cell, reachable)

    def test_open_board_range_is_orthogonal_and_bounded(self):
        self.board.units = (self.actor,)
        self.board.obstacles = frozenset()
        self.actor.cell = (3, 3)
        self.actor.movement = 2
        expected = {(x, y) for x in range(8) for y in range(8)
                    if 0 < abs(x - 3) + abs(y - 3) <= 2}
        self.assertEqual(self.board.reachable_cells(self.actor), expected)
        self.actor.cell = (0, 0)
        self.assertEqual(self.board.reachable_cells(self.actor),
                         {(1, 0), (0, 1), (2, 0), (1, 1), (0, 2)})

    def test_all_occupied_cells_block_paths(self):
        self.actor.cell = (0, 0)
        self.actor.movement = 10
        self.board.allies[0].cell = (1, 0)
        self.board.enemies[0].cell = (0, 1)
        self.board.obstacles = frozenset()
        self.assertEqual(self.battle.movement_range(), set())

    def test_zero_movement_still_allows_skipping_to_attack(self):
        self.actor.movement = 0
        self.assertEqual(self.battle.movement_range(), set())
        self.battle.skip_phase()
        self.assertEqual(self.battle.phase, "attack")
        self.assertIs(self.battle.active_unit, self.actor)

    def test_move_is_once_per_turn_and_rejects_illegal_destinations(self):
        start = self.actor.cell
        for cell in ((-1, 3), (8, 3), (7, 7), (3, 3), (1, 1), start, None):
            self.assertFalse(self.battle.move(cell))
            self.assertEqual(self.actor.cell, start)
            self.assertEqual(self.battle.phase, "move")
        self.assertTrue(self.battle.move((2, 3)))
        self.assertEqual(self.actor.cell, (2, 3))
        self.assertEqual(self.battle.phase, "attack")
        self.assertFalse(self.battle.move((2, 4)))
        self.assertEqual(self.actor.cell, (2, 3))

    def test_attacks_require_attack_phase_and_adjacent_enemy(self):
        target, diagonal, distant = self.board.enemies
        target.cell = (2, 3)
        diagonal.cell = (2, 4)
        friend = self.board.allies[0]
        friend.cell = (1, 2)
        self.assertFalse(self.battle.attack(target))
        self.battle.skip_phase()
        self.assertEqual(self.battle.attack_targets(), (target,))
        for invalid in (self.actor, friend, diagonal, distant, None):
            self.assertFalse(self.battle.attack(invalid))
            self.assertIs(self.battle.active_unit, self.actor)

    def test_damage_equals_attack_ignores_defense_and_hands_off_after_effects(self):
        target = self.board.enemies[1]
        health = target.health
        self.actor.attack = 37
        target.defense = 9999
        self.assertTrue(self.battle.move((4, 4)))
        self.assertIn(target, self.battle.attack_targets())
        self.assertTrue(self.battle.attack(target))
        self.assertEqual(target.health, health - 37)
        self.assertEqual(self.battle.log[-1][1], "A2 attacked D2 for 37 damage.")
        self.assertEqual(self.battle.phase, "resolving")
        self.assertIs(self.battle.active_unit, self.actor)
        self.assertEqual(self.battle.pending_attack.damage, 37)
        resolution_id = self.battle.pending_attack.resolution_id
        self.assertTrue(self.battle.finish_attack(resolution_id))
        self.assertIs(self.battle.active_unit, self.board.allies[0])
        self.assertEqual(self.battle.phase, "move")
        self.assertFalse(self.battle.attack(target))
        self.assertFalse(self.battle.finish_attack(resolution_id))

    def test_skips_and_round_reset(self):
        self.battle.skip_phase()
        self.assertIs(self.battle.active_unit, self.actor)
        self.battle.skip_phase()
        self.assertEqual(self.battle.index, 1)
        self.assertEqual(self.battle.phase, "move")
        for _ in range(5):
            self.battle.end_turn()
        self.assertEqual(self.battle.round_number, 2)
        self.assertIs(self.battle.active_unit, self.actor)
        self.assertEqual(self.battle.phase, "move")
        self.assertTrue(self.battle.move((2, 3)))

    def test_enemy_turn_can_move_and_attack_manually(self):
        self.battle.end_turn()
        self.battle.end_turn()
        enemy = self.battle.active_unit
        self.assertEqual(enemy.team, "enemy")
        target = self.board.allies[0]
        target.cell = (4, 1)
        self.assertTrue(self.battle.move((5, 1)))
        health = target.health
        self.assertTrue(self.battle.attack(target))
        self.assertEqual(target.health, health - enemy.attack)
        self.battle.finish_attack(self.battle.pending_attack.resolution_id)
        self.assertEqual(self.battle.index, 3)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_calibration.py

```python
"""Observation integrity and independent error metrics; no Pygame required."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.calibrate_board import DEFAULT, inspect_extent, load_observations, measure
from tactics.data_files import DataError
from tactics.perspective_geometry import PerspectiveBoardGeometry
from scripts.fit_board import load_map, measure_map, check_presentation


class CalibrationChecks(unittest.TestCase):
    def setUp(self):
        self.data,self.geometry = load_observations(DEFAULT)

    def test_measured_strip_is_not_claimed_as_eight_by_eight(self):
        report = measure(self.data,self.geometry)
        self.assertEqual(report['measured_physical_span'],[2,6])
        self.assertEqual(report['interior']['count'],5)
        self.assertAlmostEqual(report['interior']['mean_px'],5.555742450788599)
        self.assertAlmostEqual(report['interior']['max_px'],11.713753031428595)
        self.assertTrue(report['local_threshold_met'])
        self.assertFalse(report['requested_8x8_verified'])

    def test_metric_uses_holdout_points_excludes_fitted_corners(self):
        geometry = PerspectiveBoardGeometry(4,4,((0,0),(400,0),(400,400),(0,400)),(400,400),(400,400))
        data = {'sha256':'test','physical_span':[4,4], 'samples':[
            {'node':[1,1],'image':[102,100],'band':'far'},
            {'node':[2,2],'image':[210,200],'band':'near'}]}
        report = measure(data,geometry)
        self.assertEqual(report['interior'],{'count':2,'mean_px':6.0,'max_px':10.0})
        data['samples'][1]['image']=[214,200]
        self.assertFalse(measure(data,geometry)['local_threshold_met'])

    def test_scaled_viewport_metrics_scale_with_background(self):
        from dataclasses import replace
        original = measure(self.data,self.geometry)
        small = measure(self.data,replace(self.geometry,viewport_size=(640,360)))
        self.assertAlmostEqual(small['interior']['mean_px'],original['interior']['mean_px']/2)
        self.assertAlmostEqual(small['interior']['max_px'],original['interior']['max_px']/2)

    def test_invalid_source_digest_duplicate_sample_and_placeholder_rejected(self):
        variations = []
        changed=deepcopy(self.data); changed['sha256']='0'*64; variations.append(changed)
        changed=deepcopy(self.data); changed['samples'].append(changed['samples'][0]); variations.append(changed)
        changed=deepcopy(self.data); changed['corners']={k:[0,0] for k in changed['corners']}; variations.append(changed)
        changed=deepcopy(self.data); changed['samples'][0]['node']=[0,1]; variations.append(changed)
        changed=deepcopy(self.data); changed['physical_span']=[True,6]; variations.append(changed)
        changed=deepcopy(self.data); changed['image']='../../escape.png'; variations.append(changed)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'observations.json'
            for data in variations:
                with self.subTest(data=data):
                    path.write_text(json.dumps(data),encoding='utf-8')
                    with self.assertRaises(DataError): load_observations(path)

    def test_extent_candidates_are_explicitly_extrapolation_not_observations(self):
        data=deepcopy(self.data)
        result=inspect_extent(self.geometry)
        self.assertIn('EXTRAPOLATION ONLY',result['warning'])
        self.assertTrue(result['candidates_inside_png'])
        self.assertEqual(result['candidates_above_loose_paving_bound'],0)
        self.assertEqual(self.data,data)

    def test_source_points_are_native_coordinates_and_interior_picks_roundtrip(self):
        self.assertEqual(self.geometry.reference_size,(1672,941))
        for sample in self.data['samples']:
            self.assertEqual(self.geometry.cell_at(self.geometry.cell_center((0,sample['node'][1]-1))),
                             (0,sample['node'][1]-1))
            native=self.geometry.fit.to_image(self.geometry.fit.to_screen(sample['image']))
            for a,b in zip(native,sample['image']): self.assertAlmostEqual(a,b)

    def test_irregular_map_holdouts_meet_target_and_runtime_matches_fit(self):
        data,geometry=load_map()
        report=measure_map(data,geometry)
        self.assertTrue(report['threshold_met'])
        self.assertFalse(report['full_rectangular_8x8'])
        self.assertEqual(report['playable_cells'],28)
        self.assertEqual(report['independent_validation']['count'],20)
        self.assertAlmostEqual(report['independent_validation']['mean_px'],5.567315763585733)
        self.assertAlmostEqual(report['independent_validation']['max_px'],11.41999211967498)
        self.assertEqual(report['independent_interior']['count'],9)
        self.assertGreater(report['four_observed_corners_baseline']['max_px'],12)
        # These four reference corners are held out, not falsely reported as zero-error fits.
        for node in ((1,3),(7,3),(7,7),(1,7)):
            self.assertEqual(next(p['role'] for p in data['observations'] if tuple(p['node'])==node),'validation')
        check_presentation(data,geometry)

    def test_map_validation_points_cannot_influence_homography(self):
        from scripts.fit_board import fit_corners
        data,geometry=load_map()
        changed=deepcopy(data)
        for item in changed['observations']:
            if item['role']=='validation': item['image'][0]+=30
        self.assertEqual(fit_corners(changed),fit_corners(data))
        self.assertFalse(measure_map(changed,geometry)['threshold_met'])

    def test_map_missing_duplicate_and_unusable_observations_rejected(self):
        data,_=load_map()
        variations=[]
        changed=deepcopy(data); changed['observations'].pop(); variations.append(changed)
        changed=deepcopy(data); changed['observations'].append(changed['observations'][0]); variations.append(changed)
        changed=deepcopy(data); changed['sha256']='0'*64; variations.append(changed)
        changed=deepcopy(data)
        for item in changed['observations']: item['role']='calibration'
        variations.append(changed)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'map.json'
            for changed in variations:
                path.write_text(json.dumps(changed),encoding='utf-8')
                with self.subTest(changed=changed),self.assertRaises(DataError): load_map(path)
```

## tests/test_content.py

```python
"""M4 file formats and portable paths, runnable before installing Pygame."""

from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tactics.asset_manifest import load_manifest
from tactics.content import load_content
from tactics.data_files import DataError, PROJECT_ROOT, rooted_path
from tactics.scenario import default_scenario


class ContentChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scenarios").mkdir()
        self.units = json.loads((PROJECT_ROOT / "content/units.json").read_text(encoding="utf-8"))
        self.scene = json.loads((PROJECT_ROOT / "content/scenarios/training_ground.json").read_text(encoding="utf-8"))

    def write(self):
        (self.root / "units.json").write_text(json.dumps(self.units), encoding="utf-8")
        (self.root / "scenarios/training_ground.json").write_text(json.dumps(self.scene), encoding="utf-8")

    def test_default_json_preserves_scenario_and_definition_identity(self):
        content = load_content()
        self.assertEqual(content.scenario, default_scenario())
        self.assertEqual(tuple(unit.definition_id for unit in content.scenario.units),
                         ("vanguard", "scout", "guard", "dummy", "dummy", "dummy"))
        self.assertEqual(content.definitions[1].visual_id, "unit.scout")
        self.assertEqual(content.scenario.units[1].health, 80)
        self.assertEqual(content.scenario.units[-1].speed, 8)

    def test_alternate_scenario_uses_same_definitions_without_rule_changes(self):
        self.scene.update(id="small", cols=5, rows=4, obstacles=[[1, 0]], spawns=[
            {"uid":"blue", "definition_id":"scout", "team":"ally", "cell":[0,0]},
            {"uid":"red", "definition_id":"dummy", "team":"enemy", "cell":[3,0],
             "overrides":{"max_health":50, "attack":17}},
        ])
        self.write()
        content = load_content(self.root)
        self.assertEqual((content.scenario.cols, content.scenario.rows), (5, 4))
        self.assertEqual((content.scenario.units[-1].health, content.scenario.units[-1].max_health), (50, 50))
        from tactics.controller import Controller
        controller = Controller(content.scenario)
        self.assertTrue(controller.move_to((2, 0)))
        self.assertTrue(controller.attack("red"))
        controller.update(0)
        self.assertTrue(controller.undo())
        self.assertEqual(controller.get_view_state().active.definition_id, "scout")

    def test_unknown_definition_and_unknown_fields_are_located(self):
        for change, expected in (({"definition_id":"missing"}, "unknown definition"),
                                 ({"typo":1}, "unknown")):
            with self.subTest(change=change):
                record = dict(self.scene["spawns"][0])
                self.scene["spawns"][0].update(change)
                self.write()
                with self.assertRaisesRegex(DataError, expected):
                    load_content(self.root)
                self.scene["spawns"][0] = record

    def test_duplicate_definition_ids_and_json_keys_are_rejected(self):
        self.units["units"].append(self.units["units"][0])
        self.write()
        with self.assertRaisesRegex(DataError, "duplicate definition"):
            load_content(self.root)
        (self.root / "units.json").write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        with self.assertRaisesRegex(DataError, "units.json.*duplicate key"):
            load_content(self.root)

    def test_definition_numbers_and_versions_are_strict(self):
        for key, value in (("speed", True), ("movement", -1), ("attack", 1.5), ("max_health", 0),
                           ("defense", float("nan"))):
            with self.subTest(key=key):
                old = self.units["units"][0][key]
                self.units["units"][0][key] = value
                self.write()
                with self.assertRaises(DataError):load_content(self.root)
                self.units["units"][0][key] = old
        self.units["schema_version"] = True
        self.write()
        with self.assertRaisesRegex(DataError, "schema_version"):
            load_content(self.root)

    def test_invalid_spawn_configuration_is_rejected_by_existing_scenario_validator(self):
        for changes in ({"cell":[8, 0]}, {"cell":[3, 1]}, {"uid":"D1"},
                        {"team":"other"}, {"overrides":{"health":0}}, {"overrides":{"health":101}}):
            old = dict(self.scene["spawns"][0])
            self.scene["spawns"][0].update(changes)
            self.write()
            with self.subTest(changes=changes), self.assertRaises(DataError):
                load_content(self.root)
            self.scene["spawns"][0] = old

    def test_rooted_paths_reject_absolute_windows_and_traversal_inputs(self):
        for value in ("../outside.png", "/outside.png", "C:/outside.png", "C:outside.png",
                      "\\\\server\\file.png", "units\\file.png"):
            with self.subTest(value=value), self.assertRaises(DataError):
                rooted_path(self.root, value, "asset")
        self.assertEqual(rooted_path(self.root, "units/../ok.png", "asset"), (self.root / "ok.png").resolve())

    def test_symlink_escape_is_rejected_when_os_permits_symlinks(self):
        with tempfile.TemporaryDirectory() as outside:
            try:
                (self.root / "escape").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("OS does not permit creating symlinks")
            with self.assertRaisesRegex(DataError, "escapes root"):
                rooted_path(self.root, "escape/file.png", "asset")

    def test_missing_and_malformed_json_have_file_context(self):
        with self.assertRaisesRegex(DataError, "units.json"):
            load_content(self.root)
        (self.root / "units.json").write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(DataError, "units.json"):
            load_content(self.root)

    def test_content_and_manifest_work_from_other_cwd_with_pygame_blocked(self):
        script = """
import importlib.abc,sys
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if fullname == 'pygame' or fullname.startswith('pygame.'):
   raise AssertionError('Pygame import in data loader')
sys.meta_path.insert(0,Block())
from tactics.content import load_content
from tactics.asset_manifest import load_manifest
from tactics.data_files import PROJECT_ROOT
from tactics.controller import Controller
content=load_content()
manifest=load_manifest(PROJECT_ROOT/'assets')
controller=Controller(content.scenario)
assert controller.move_to((4,4)) and controller.attack('D2')
controller.update(0)
assert controller.undo()
assert controller.get_view_state().active.definition_id=='scout'
assert len(manifest.images)==9 and 'pygame' not in sys.modules
"""
        result = subprocess.run([sys.executable, "-S", "-c", script], cwd=self.root,
                                env={**os.environ, "PYTHONPATH":str(PROJECT_ROOT)},
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ManifestChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = json.loads((PROJECT_ROOT / "assets/manifest.json").read_text(encoding="utf-8"))

    def load(self):
        (self.root / "manifest.json").write_text(json.dumps(self.data), encoding="utf-8")
        return load_manifest(self.root)

    def test_dimensions_pivots_paths_and_boolean_fields_are_validated(self):
        for changes in ({"display_size":[0, 64]}, {"display_size":[True, 64]}, {"pivot":[1.1, 0]},
                        {"pivot":[float("nan"), 0]}, {"optional":"yes"}, {"path":"../x.png"},
                        {"path":"tile.jpg"}, {"typo":0}):
            old = dict(self.data["images"]["tile.floor"])
            self.data["images"]["tile.floor"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(DataError):self.load()
            self.data["images"]["tile.floor"] = old

    def test_animation_references_rates_and_loop_policies_are_validated(self):
        for changes in ({"frames":[]}, {"frames":["unknown"]}, {"fps":0}, {"fps":float("inf")},
                        {"loop":True}, {"loop":1}):
            old = dict(self.data["animations"]["scout.attack"])
            self.data["animations"]["scout.attack"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(DataError):self.load()
            self.data["animations"]["scout.attack"] = old

    def test_visual_board_and_duplicate_cross_kind_references_are_rejected(self):
        self.data["visuals"]["unit.scout"]["idle"] = "unknown"
        with self.assertRaises(DataError):self.load()
        self.data["visuals"]["unit.scout"] = {}
        self.data["board"]["floor"] = "unknown"
        with self.assertRaises(DataError):self.load()
        self.data["board"] = {}
        self.data["animations"]["tile.floor"] = self.data["animations"]["scout.attack"]
        with self.assertRaisesRegex(DataError, "also used"):
            self.load()


if __name__ == "__main__":
    unittest.main()
```

## tests/test_controller.py

```python
"""Application contracts; run with python -S, without Pygame or a display."""

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
import ast
from pathlib import Path
import unittest

from tactics.actions import UIAction
from tactics.controller import Controller
from tactics.scenario import default_scenario


class HeldPresentation:
    """Test-controlled completion: advancing time alone does not finish an attack."""

    def __init__(self):
        self.busy = False
        self.results = []
        self.elapsed = []
        self.clears = 0
        self.pending = None

    def play_attack(self, result):
        self.results.append(result)
        self.pending = result.token
        self.busy = True

    def update(self, elapsed):
        self.elapsed.append(elapsed)
        if not self.busy and self.pending is not None:
            token, self.pending = self.pending, None
            return (token,)
        return ()

    def clear(self):
        self.clears += 1
        self.busy = False
        self.pending = None


def changed_scenario(**changes):
    scenario = default_scenario()
    return replace(scenario, units=tuple(
        replace(unit, **changes.get(unit.uid, {})) for unit in scenario.units))


class ControllerChecks(unittest.TestCase):
    def setUp(self):
        self.presentation = HeldPresentation()
        self.controller = Controller(default_scenario(), self.presentation)

    @property
    def view(self):
        return self.controller.get_view_state()

    def unit(self, uid):
        return next(unit for unit in self.view.units if unit.uid == uid)

    def start_attack(self):
        self.assertTrue(self.controller.move_to((4, 4)))
        self.assertTrue(self.controller.attack("D2"))

    def finish(self):
        self.presentation.busy = False
        self.controller.update(0)

    def test_initial_view_contains_complete_stats_order_log_ranges_and_buttons(self):
        view = self.view
        self.assertEqual(view.active, view.selected)
        self.assertEqual((view.active.uid, view.active.health, view.active.max_health,
                          view.active.attack, view.active.defense, view.active.speed,
                          view.active.movement, view.active.role),
                         ("A2", 80, 100, 10, 5, 14, 4, "侦察"))
        self.assertEqual(tuple(unit.uid for unit in view.order), ("A2", "A1", "D1", "A3", "D2", "D3"))
        self.assertEqual(view.board.active_uid, view.active.uid)
        self.assertEqual(view.board.selected_uid, view.selected.uid)
        self.assertTrue(view.can_skip and view.can_end_turn and view.board.move_cells and view.log)
        self.assertFalse(view.can_undo or view.input_locked or view.finished)

    def test_full_view_has_only_deeply_immutable_values(self):
        def check(value):
            if is_dataclass(value):
                self.assertTrue(value.__dataclass_params__.frozen)
                for field in fields(value):
                    check(getattr(value, field.name))
            elif isinstance(value, (tuple, frozenset)):
                for child in value:
                    check(child)
            else:
                self.assertIs(type(value) in (str, int, bool, type(None)), True)
        check(self.view)
        with self.assertRaises(FrozenInstanceError):
            self.view.selected.health = 0
        with self.assertRaises(FrozenInstanceError):
            self.view.can_undo = True
        with self.assertRaises(AttributeError):
            self.view.board.move_cells.add((7, 7))

    def test_old_views_remain_detached_after_move_damage_handoff_and_undo(self):
        before = self.view
        self.start_attack()
        resolving = self.view
        self.finish()
        self.controller.undo()
        self.assertEqual(replace(self.view, presentation_generation=before.presentation_generation), before)
        self.assertEqual(before.active.cell, (1, 3))
        self.assertEqual(next(unit.health for unit in before.units if unit.uid == "D2"), 100)
        self.assertEqual(resolving.active.cell, (4, 4))
        self.assertEqual(next(unit.health for unit in resolving.units if unit.uid == "D2"), 90)
        self.assertTrue(resolving.input_locked)

    def test_click_inspection_hides_ranges_and_requires_reselecting_actor(self):
        self.assertTrue(self.controller.click_cell((1, 1)))
        self.assertEqual(self.view.selected.uid, "A1")
        self.assertEqual(self.view.active.uid, "A2")
        self.assertFalse(self.view.board.move_cells)
        before = self.view
        self.assertFalse(self.controller.click_cell((4, 4)))
        self.assertEqual(self.view, before)
        self.controller.click_cell((1, 3))
        self.controller.click_cell((4, 4))
        self.assertEqual((self.view.phase, self.view.active.cell), ("attack", (4, 4)))

    def test_invalid_clicks_and_selection_do_not_change_any_view_state(self):
        before = self.view
        for cell in (None, (-1, 0), (8, 0), (7, 7), (3, 1)):
            result = self.controller.click_cell(cell)
            self.assertFalse(result)
            self.assertTrue(result.reason)
            self.assertEqual(self.view, before)
        self.assertFalse(self.controller.select("missing"))
        self.assertEqual(self.view, before)
        self.assertFalse(self.presentation.results)

    def test_explicit_commands_act_on_active_actor_and_validate_once_in_rules(self):
        self.controller.select("D1")
        self.assertTrue(self.controller.move_to((4, 4)))
        self.assertEqual(self.view.selected.uid, "A2")
        before = self.view
        self.assertFalse(self.controller.move_to((4, 3)))
        self.assertEqual(self.view, before)
        self.assertTrue(self.controller.attack("D2"))
        self.assertEqual(self.unit("D2").health, 90)

    def test_illegal_attacks_return_failure_without_changing_state_or_playing_effects(self):
        self.assertFalse(self.controller.attack("D2"))  # Before moving/skipping.
        self.controller.move_to((4, 4))
        before = self.view
        for uid in ("missing", "A2", "A1", "D1"):
            result = self.controller.attack(uid)
            self.assertFalse(result)
            self.assertEqual(result.reason, "illegal_target")
            self.assertEqual(self.view, before)
        self.assertFalse(self.presentation.results)

    def test_all_application_inputs_are_locked_while_resolving(self):
        self.start_attack()
        before = self.view
        self.assertTrue(before.input_locked)
        self.assertFalse(before.can_skip or before.can_end_turn or before.can_undo)
        attempts = [lambda: self.controller.select("D1"),
                    lambda: self.controller.click_cell((6, 1)),
                    lambda: self.controller.move_to((4, 3)),
                    lambda: self.controller.attack("D2"), self.controller.undo]
        attempts += [lambda action=action: self.controller.handle_action(action) for action in UIAction]
        for attempt in attempts:
            self.assertFalse(attempt())
            self.assertEqual(self.view, before)
        self.assertEqual(len(self.presentation.results), 1)
        self.assertEqual(self.presentation.clears, 0)

    def test_completion_waits_for_presentation_and_hands_off_only_once(self):
        self.start_attack()
        self.controller.update(100)
        self.assertEqual(self.view.phase, "resolving")
        self.controller.update(-1)
        self.assertEqual(self.presentation.elapsed[-1], 0)
        self.finish()
        handoff = self.view
        self.assertEqual(handoff.active.uid, "A1")
        self.assertEqual(handoff.selected, handoff.active)
        self.assertFalse(handoff.input_locked)
        for _ in range(3):
            self.controller.update(1)
            self.assertEqual(self.view, handoff)

    def test_without_presentation_attack_completes_on_next_update(self):
        self.controller = Controller(default_scenario())
        self.start_attack()
        self.assertEqual(self.view.phase, "resolving")
        self.controller.update(0)
        self.assertEqual(self.view.active.uid, "A1")
        self.assertTrue(self.controller.undo())
        self.assertEqual(self.unit("D2").health, 100)

    def test_undo_clears_effects_restores_previous_turn_and_discards_partial_move(self):
        before = self.view
        self.assertFalse(self.controller.undo())
        self.assertEqual(self.presentation.clears, 0)
        self.start_attack()
        self.finish()
        self.controller.move_to((0, 1))
        self.assertTrue(self.controller.handle_action(UIAction.UNDO))
        self.assertEqual(replace(self.view, presentation_generation=before.presentation_generation), before)
        self.assertEqual(self.presentation.clears, 1)
        self.assertFalse(self.presentation.busy)
        self.assertFalse(self.controller.undo())

    def test_final_kill_waits_then_finishes_and_undo_revives_target(self):
        scenario = changed_scenario(D2={"health": 5})
        scenario = replace(scenario, units=tuple(unit for unit in scenario.units if unit.uid in ("A2", "D2")))
        self.controller = Controller(scenario, self.presentation)
        self.start_attack()
        self.assertFalse(self.view.finished)
        self.assertFalse(self.controller.select("D2"))
        self.assertNotIn("D2", tuple(unit.uid for unit in self.view.board.units))
        self.finish()
        self.assertEqual((self.view.phase, self.view.winner, self.view.active, self.view.selected),
                         ("finished", "ally", None, None))
        before = self.view
        self.assertFalse(self.controller.handle_action(UIAction.END_TURN))
        self.assertFalse(self.controller.handle_action(UIAction.SKIP_PHASE))
        self.assertEqual(self.view, before)
        self.assertTrue(self.controller.select("A2"))  # Inspection remains available.
        self.assertTrue(self.controller.undo())
        self.assertEqual((self.view.active.uid, self.unit("D2").health), ("A2", 5))
        self.assertEqual(len(self.view.board.units), 2)
        self.assertFalse(self.view.finished)

    def test_semantic_actions_work_for_both_teams_and_round_wrap(self):
        for uid in ("A2", "A1", "D1", "A3", "D2", "D3"):
            self.assertEqual(self.view.active.uid, uid)
            self.assertTrue(self.controller.handle_action(UIAction.SKIP_PHASE))
            self.assertEqual(self.view.phase, "attack")
            self.assertTrue(self.controller.handle_action(UIAction.SKIP_PHASE))
            self.assertEqual(self.view.selected, self.view.active)
        self.assertEqual((self.view.round_number, self.view.active.uid), (2, "A2"))
        self.assertTrue(self.controller.undo())
        self.assertEqual((self.view.round_number, self.view.active.uid), (1, "D3"))

    def test_zero_movement_and_invalid_action_do_not_need_presentation(self):
        self.controller = Controller(changed_scenario(A2={"movement": 0}), self.presentation)
        before = self.view
        self.assertFalse(before.board.move_cells)
        self.assertFalse(self.controller.handle_action("end_turn"))
        self.assertEqual(self.view, before)
        self.assertTrue(self.controller.handle_action(UIAction.SKIP_PHASE))
        self.assertEqual(self.view.phase, "attack")
        self.assertFalse(self.presentation.results)

    def test_effect_result_is_detached_and_read_only_even_after_undo(self):
        self.start_attack()
        result = self.presentation.results[0].result
        self.assertEqual((result.actor_uid, result.target_uid, result.target_cell,
                          result.target_team, result.damage, result.killed),
                         ("A2", "D2", (5, 4), "enemy", 10, False))
        self.assertFalse(hasattr(result, "target") or hasattr(result, "actor"))
        with self.assertRaises(FrozenInstanceError):
            result.damage = 0
        self.finish()
        self.controller.undo()
        self.assertEqual((result.target_cell, result.damage), ((5, 4), 10))

    def test_presentation_and_game_do_not_import_mutable_rule_objects(self):
        root = Path(__file__).resolve().parents[1] / "tactics"
        for name in ("game", "panel", "effects", "board_renderer"):
            tree = ast.parse((root / (name + ".py")).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, ("board", "battle", "models",
                                                  "tactics.board", "tactics.battle", "tactics.models"), name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name, ("tactics.board", "tactics.battle", "tactics.models"), name)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_core.py

```python
"""M1 contracts; runnable with python -S and no third-party packages installed."""

from dataclasses import FrozenInstanceError, replace
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tactics.battle import Battle
from tactics.board import Board
from tactics.geometry import BoardGeometry
from tactics.scenario import Scenario, UnitSpawn, default_scenario


def alternate_scenario():
    return Scenario("detour", 5, 4, (
        UnitSpawn("blue", "Blue", "ally", "test", (0, 0), speed=20, movement=4, attack=17),
        UnitSpawn("red", "Red", "enemy", "test", (3, 0), health=50, speed=5),
    ), frozenset(((1, 0),)))


class ScenarioChecks(unittest.TestCase):
    def test_default_layout_and_stats_match_original(self):
        scenario = default_scenario()
        self.assertEqual((scenario.cols, scenario.rows), (8, 8))
        board = Board(scenario)
        self.assertEqual([(unit.uid, unit.cell, unit.health, unit.max_health, unit.speed, unit.movement)
                          for unit in board.units], [
            ("A1", (1, 1), 100, 100, 12, 3), ("A2", (1, 3), 80, 100, 14, 4),
            ("A3", (2, 6), 120, 120, 10, 2), ("D1", (6, 1), 100, 100, 11, 3),
            ("D2", (5, 4), 100, 100, 9, 3), ("D3", (6, 6), 100, 100, 8, 3),
        ])
        self.assertEqual(board.obstacles, {(3, 1), (3, 2), (3, 3), (4, 5), (4, 6)})
        self.assertTrue(all(unit.attack == 10 and unit.defense == 5 for unit in board.units))

    def test_reused_scenario_does_not_share_runtime_units(self):
        scenario = default_scenario()
        first, second = Board(scenario), Board(scenario)
        first.units[0].health = 1
        first.units[0].cell = (0, 0)
        self.assertEqual(second.units[0].health, 100)
        self.assertEqual(scenario.units[0].cell, (1, 1))
        self.assertIsNot(first.units[0], second.units[0])

    def test_immutable_configuration_normalizes_mutable_inputs(self):
        source = list(alternate_scenario().units)
        obstacles = [[1, 0]]
        scenario = Scenario("copied", 5, 4, source, obstacles)
        source.clear()
        obstacles[0][0] = 4
        self.assertEqual(len(scenario.units), 2)
        self.assertEqual(scenario.obstacles, {(1, 0)})
        with self.assertRaises(FrozenInstanceError):
            scenario.units[0].health = 1

    def test_alternate_board_runs_path_attack_handoff_and_undo(self):
        board = Board(alternate_scenario())
        battle = Battle(board)
        actor, target = board.units
        self.assertEqual(board.neighbors((4, 3)), ((3, 3), (4, 2)))
        self.assertIn((2, 0), battle.movement_range())
        self.assertNotIn((1, 0), battle.movement_range())
        self.assertNotIn((4, 0), battle.movement_range())
        self.assertTrue(battle.move((2, 0)))
        self.assertTrue(battle.attack(target))
        self.assertEqual(target.health, 33)
        battle.finish_attack(battle.pending_attack.resolution_id)
        self.assertIs(battle.active_unit, target)
        self.assertTrue(battle.undo())
        self.assertEqual(battle.active_unit.uid, actor.uid)
        self.assertIsNot(battle.active_unit, actor)
        self.assertEqual(battle.active_unit.cell, (0, 0))
        self.assertEqual(board.units[1].health, 50)

    def test_rejects_invalid_dimensions_empty_or_one_sided_scenarios(self):
        source = alternate_scenario()
        for changes in ({"cols": 0}, {"rows": -1}, {"cols": True}, {"rows": 3.5},
                        {"scenario_id": ""}, {"units": ()}, {"units": source.units[:1]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(source, **changes)

    def test_rejects_bad_spawn_coordinates_collisions_and_duplicate_ids(self):
        source = alternate_scenario()
        for changes in ({"cell": (5, 0)}, {"cell": (-1, 0)}, {"cell": (1, 0)},
                        {"cell": (3, 0)}, {"cell": (True, 0)}, {"cell": (0.5, 0)}, {"uid": "red"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(source, units=(replace(source.units[0], **changes), source.units[1]))
        for obstacles in ([(5, 0)], [(1,)], [(1, False)]):
            with self.subTest(obstacles=obstacles), self.assertRaises(ValueError):
                replace(source, obstacles=obstacles)

    def test_rejects_invalid_teams_attributes_and_initially_dead_units(self):
        source = alternate_scenario()
        for changes in ({"health": 0}, {"health": 101}, {"max_health": 0}, {"team": "unknown"},
                        {"attack": -1}, {"defense": -1}, {"speed": -1}, {"movement": -1},
                        {"movement": 1.5}, {"speed": True}, {"uid": ""}, {"role": ""}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(source, units=(replace(source.units[0], **changes), source.units[1]))


class GeometryChecks(unittest.TestCase):
    def test_nonzero_origin_and_odd_cell_size_roundtrip(self):
        geometry = BoardGeometry(5, 3, 31, (17, 29))
        self.assertEqual(geometry.bounds, (17, 29, 155, 93))
        self.assertEqual(geometry.cell_rect((1, 1)), (48, 60, 31, 31))
        for row in range(3):
            for col in range(5):
                self.assertEqual(geometry.cell_at(geometry.cell_center((col, row))), (col, row))

    def test_half_open_pixel_edges_and_sidebar(self):
        geometry = BoardGeometry(8, 8, 64)
        self.assertEqual(geometry.cell_at((0, 0)), (0, 0))
        self.assertEqual(geometry.cell_at((511, 511)), (7, 7))
        for pixel in ((512, 0), (0, 512), (-1, 0), (0, -1), (799, 511)):
            self.assertIsNone(geometry.cell_at(pixel))
        offset = BoardGeometry(2, 2, 32, (10, 20))
        self.assertIsNone(offset.cell_at((9, 20)))
        self.assertEqual(offset.cell_at((73, 83)), (1, 1))
        self.assertIsNone(offset.cell_at((74, 84)))

    def test_invalid_geometry_and_cells_are_rejected(self):
        for args in ((0, 8, 64), (8, -1, 64), (8, 8, 0), (True, 8, 64), (8, 8, 32.5)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                BoardGeometry(*args)
        with self.assertRaises(ValueError):
            BoardGeometry(8, 8, 64, (0.5, 0))
        for cell in ((8, 0), (-1, 0), (0, 8), (False, 0), (0.5, 0)):
            with self.subTest(cell=cell), self.assertRaises(ValueError):
                BoardGeometry(8, 8, 64).cell_rect(cell)


class CoreBoundaryChecks(unittest.TestCase):
    def test_board_has_no_pixel_or_rendering_entrypoints(self):
        board = Board(default_scenario())
        for name in ("draw", "rect", "cell_at", "label_font"):
            self.assertFalse(hasattr(board, name), name)

    def test_full_rule_flow_without_site_packages_and_with_pygame_blocked(self):
        root = Path(__file__).resolve().parents[1]
        script = """
import importlib.abc
import importlib.util
from dataclasses import asdict
import json
import sys
assert importlib.util.find_spec('pygame') is None
class NoPygame(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'pygame' or fullname.startswith('pygame.'):
            raise AssertionError('Core imported Pygame: ' + fullname)
sys.meta_path.insert(0, NoPygame())
from tactics.board import Board
from tactics.battle import Battle
from tactics.scenario import default_scenario
from tactics.geometry import BoardGeometry
from tactics.view_models import build_board_view
from tactics.controller import Controller
from tactics.actions import UIAction
board = Board(default_scenario())
battle = Battle(board)
assert battle.move((4, 4))
assert battle.attack(board.enemies[1])
assert board.enemies[1].health == 90
battle.finish_attack(battle.pending_attack.resolution_id)
assert battle.undo()
assert board.enemies[1].health == 100
assert build_board_view(board, battle, battle.active_unit).active_uid == 'A2'
assert BoardGeometry(8, 8, 64).cell_at((511, 511)) == (7, 7)
controller = Controller(default_scenario())
assert controller.move_to((4, 4))
assert controller.attack('D2')
assert controller.get_view_state().input_locked
token = controller.get_view_state().pending_resolution
assert not controller.complete_presentation(None)
controller.update(0)
assert controller.get_view_state().active.uid == 'A1'
assert not controller.complete_presentation(token)
assert controller.handle_action(UIAction.UNDO)
assert controller.get_view_state().active.cell == (1, 3)
assert controller.get_view_state().presentation_generation == 1
json.dumps(asdict(battle.history[0]))
assert 'pygame' not in sys.modules
print('core-without-pygame: OK')
"""
        result = subprocess.run([sys.executable, "-S", "-c", script], cwd=str(root),
                                env={**os.environ, "PYTHONPATH": str(root)},
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("core-without-pygame: OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_effects.py

```python
"""Actual window rendering, animation lifecycle, input lock and rewind controls."""

from dataclasses import replace
import unittest
from unittest.mock import patch

import pygame

from tactics.scenario import default_scenario
from tactics.game import Game


class CombatInteractionChecks(unittest.TestCase):
    def setUp(self):
        self.game = Game(geometric=True)

    @property
    def view(self):
        return self.game.controller.get_view_state()

    @property
    def actor(self):
        return next(unit for unit in self.view.units if unit.uid == "A2")

    @property
    def target(self):
        return next(unit for unit in self.view.units if unit.uid == "D2")

    def tearDown(self):
        pygame.quit()

    def click(self, position):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    def start_attack(self, lethal=False, final=False):
        if lethal:
            scenario = default_scenario()
            units = tuple(replace(unit, health=5) if unit.uid == "D2" else unit
                          for unit in scenario.units)
            if final:
                units = tuple(unit for unit in units if unit.uid in ("A2", "D2"))
            self.game = Game(replace(scenario, units=units), geometric=True)
        self.click(self.game.geometry.cell_center((4, 4)))
        self.click(self.game.geometry.cell_center(self.target.cell))

    def test_damage_popup_and_controls_are_locked_until_effect_finishes(self):
        self.start_attack()
        self.assertEqual(self.game.effects.damage_texts[0].amount, self.actor.attack)
        self.game.update(0.2)
        self.assertAlmostEqual(self.game.effects.damage_texts[0].age, 0.2)
        self.game.draw()
        for key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
            self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        for position in ((617, 303), (791, 303), (796, 30)):
            self.click(position)
        self.click(self.game.geometry.cell_center(self.target.cell))
        self.assertEqual(self.target.health, self.target.max_health - self.actor.attack)
        self.assertEqual(self.view.active, self.actor)
        self.assertEqual(self.view.phase, "resolving")
        self.game.update(1.0)
        self.assertFalse(self.game.effects.busy)
        self.assertEqual(self.view.phase, "move")
        self.assertEqual(self.view.active.uid, "A1")

    def test_defeated_body_animates_then_disappears_from_actual_surface(self):
        self.start_attack(lethal=True)
        self.assertEqual(len(self.game.effects.deaths), 1)
        self.assertFalse(self.target.alive)
        self.game.draw()
        center = self.game.geometry.cell_center(self.target.cell)
        background = (42, 55, 70)
        self.assertNotEqual(tuple(self.game.screen.get_at(center))[:3], background)
        self.game.update(0.4)
        self.assertEqual(len(self.game.effects.deaths), 1)
        self.game.draw()
        self.game.update(0.3)
        self.assertEqual(len(self.game.effects.deaths), 0)
        self.assertTrue(self.game.effects.busy)  # Floating damage text finishes later.
        self.game.draw()
        self.assertEqual(tuple(self.game.screen.get_at(center))[:3], background)
        self.game.update(0.3)
        self.assertFalse(self.game.effects.busy)

    def test_sidebar_undo_revives_target_and_clears_visual_state(self):
        self.start_attack(lethal=True)
        self.game.update(1.0)
        self.click((self.game.geometry.width + 284, 30))
        self.assertEqual(self.target.health, 5)
        self.assertIn(self.target.uid, tuple(unit.uid for unit in self.view.board.units))
        self.assertEqual(self.view.active, self.actor)
        self.assertEqual(self.view.selected, self.actor)
        self.assertEqual(self.actor.cell, (1, 3))
        self.assertFalse(self.game.effects.busy)
        self.game.draw()

    def test_backspace_rewinds_previous_turn_and_discards_partial_current_move(self):
        self.start_attack()
        self.game.update(1.0)
        self.click(self.game.geometry.cell_center((0, 1)))
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        self.assertEqual(self.view.active.uid, "A2")
        self.assertEqual(self.target.health, self.target.max_health)
        self.assertEqual(next(unit.cell for unit in self.view.units if unit.uid == "A1"), (1, 1))
        self.assertEqual(self.view.phase, "move")

    def test_finished_battle_is_renderable_and_can_be_undone(self):
        self.start_attack(lethal=True, final=True)
        self.game.update(1.0)
        self.assertTrue(self.view.finished)
        self.game.draw()
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertTrue(self.view.finished)
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        self.assertFalse(self.view.finished)
        self.assertTrue(self.target.alive)
        self.game.draw()

    def test_health_panel_shows_current_and_maximum(self):
        scenario = default_scenario()
        self.game = Game(replace(scenario, units=tuple(
            replace(unit, health=800, max_health=1000) if unit.uid == "A2" else unit
            for unit in scenario.units)), geometric=True)
        with patch.object(self.game.panel, "text", wraps=self.game.panel.text) as draw_text:
            self.game.draw()
        expected = "生命: 800/1000" if self.game.panel.chinese else "HP: 800/1000"
        self.assertTrue(any(call.args[1] == expected for call in draw_text.call_args_list))

    def test_close_event_still_works_during_attack_animation(self):
        self.start_attack(lethal=True)
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.game.run()
        self.assertFalse(pygame.display.get_init())
        self.assertFalse(pygame.font.get_init())

    def test_real_effect_adapter_emits_matching_completion_only_once(self):
        self.start_attack()
        token = self.view.pending_resolution
        self.assertEqual(self.game.effects.update(0.2), ())
        self.assertEqual(self.game.effects.update(0.71), (token,))
        self.assertEqual(self.game.effects.update(10), ())
        self.assertEqual(self.view.phase, "resolving")  # Effects cannot mutate the battle.
        self.assertTrue(self.game.controller.complete_presentation(token))
        after = self.view
        self.assertFalse(self.game.controller.complete_presentation(token))
        self.assertEqual(self.view, after)

    def test_death_completion_waits_for_longer_damage_popup(self):
        self.start_attack(lethal=True)
        token = self.view.pending_resolution
        self.assertEqual(self.game.effects.update(0.7), ())
        self.assertFalse(self.game.effects.deaths)
        self.assertTrue(self.game.effects.damage_texts)
        self.assertEqual(self.view.phase, "resolving")
        self.assertEqual(self.game.effects.update(0.21), (token,))
        self.assertFalse(self.game.effects.busy)
        self.assertEqual(self.game.effects.update(1), ())

    def test_repeated_kill_undo_and_restart_leave_no_duplicate_visuals_or_notifications(self):
        self.start_attack(lethal=True)
        for _ in range(2):
            token = self.view.pending_resolution
            self.assertEqual((len(self.game.effects.deaths), len(self.game.effects.damage_texts)), (1, 1))
            self.game.update(1)
            self.assertTrue(self.game.controller.undo())
            self.assertFalse(self.game.effects.busy)
            self.assertEqual(self.game.effects.update(1), ())
            self.assertFalse(self.game.controller.complete_presentation(token))
            self.assertEqual(self.target.health, 5)
            self.click(self.game.geometry.cell_center((4, 4)))
            self.click(self.game.geometry.cell_center((5, 4)))
        old = self.view.pending_resolution
        self.game.controller.restart()
        self.assertFalse(self.game.effects.busy)
        self.assertEqual(self.game.effects.update(1), ())
        self.assertFalse(self.game.controller.complete_presentation(old))
        self.assertEqual((self.actor.cell, self.target.health), ((1, 3), 5))
        self.game.draw()


if __name__ == "__main__":
    unittest.main()
```

## tests/test_game.py

```python
"""Window input adapters and retained font regression checks."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from tactics.actions import UIAction
from tactics.game import Game
from tactics.panel import InfoPanel
from tactics.settings import CELL_SIZE


class GameChecks(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    @property
    def view(self):
        return self.game.controller.get_view_state()

    def unit(self, uid):
        return next(unit for unit in self.view.units if unit.uid == uid)

    def click(self, position, button=1):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=position, button=button))

    def test_layout_and_initial_scenario(self):
        for name in ("board", "battle", "selected"):
            self.assertFalse(hasattr(self.game, name), name)
        self.assertEqual(self.game.screen.get_size(), (896, 512))
        self.assertEqual(CELL_SIZE, 64)
        self.assertEqual((self.game.geometry.width, self.game.geometry.height), (512, 512))
        cells = [unit.cell for unit in self.view.units] + list(self.view.board.obstacles)
        self.assertEqual(sum(unit.team == "ally" for unit in self.view.units), 3)
        self.assertEqual(sum(unit.team == "enemy" for unit in self.view.units), 3)
        self.assertTrue(self.view.board.obstacles)
        self.assertEqual(len(cells), len(set(cells)))
        self.assertTrue(all(0 <= col < 8 and 0 <= row < 8 for col, row in cells))

    def test_inspect_each_unit_without_changing_turn(self):
        actor = self.view.active
        for unit in self.view.units:
            self.click(self.game.geometry.cell_center(unit.cell))
            self.assertEqual(self.view.selected, unit)
            self.assertEqual(self.view.active, actor)
            self.game.draw()

    def test_invalid_terrain_and_outside_clicks_do_not_consume_action(self):
        before = self.view
        positions = [(511, 511), (530, 20), (-1, 0), (0, 512)]
        positions += [self.game.geometry.cell_center(cell) for cell in self.view.board.obstacles]
        for position in positions:
            self.click(position)
            self.assertEqual(self.view, before)
        self.assertEqual(self.game.geometry.cell_at((511, 511)), (7, 7))

    def test_right_click_does_not_change_selection_or_scenario(self):
        before = self.view
        self.click(self.game.geometry.cell_center((4, 4)), button=3)
        self.assertEqual(self.view, before)

    def test_mouse_move_attack_and_turn_handoff(self):
        actor = self.view.active
        target = self.unit("D2")
        self.click(self.game.geometry.cell_center((4, 4)))
        self.assertEqual(self.view.active.cell, (4, 4))
        self.assertEqual(self.view.phase, "attack")
        self.game.draw()
        self.click(self.game.geometry.cell_center(target.cell))
        self.assertEqual(self.unit("D2").health, target.health - actor.attack)
        self.assertEqual(self.view.phase, "resolving")
        self.assertTrue(self.game.effects.busy)
        self.game.draw()
        self.game.update(1.0)
        self.assertEqual(self.view.selected, self.view.active)
        self.assertNotEqual(self.view.selected.uid, actor.uid)
        self.game.draw()

    def test_inspection_cannot_move_a_unit_out_of_turn(self):
        actor = self.view.active
        other = self.unit("A1")
        self.click(self.game.geometry.cell_center(other.cell))
        self.click(self.game.geometry.cell_center((4, 4)))
        self.assertEqual(self.view.active, actor)
        self.assertEqual(self.unit("A1"), other)
        self.click(self.game.geometry.cell_center(actor.cell))
        self.click(self.game.geometry.cell_center((4, 4)))
        self.assertEqual(self.view.active.cell, (4, 4))

    def test_keyboard_and_sidebar_skip_controls(self):
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.assertEqual(self.view.phase, "attack")
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.view.active.uid, "A1")
        # Exercise public input and semantic hit testing, without reading panel rectangles.
        skip = (self.game.geometry.width + 105, 303)
        end = (self.game.geometry.width + 279, 303)
        self.assertIs(self.game.panel.hit_test(skip), UIAction.SKIP_PHASE)
        self.assertIs(self.game.panel.hit_test(end), UIAction.END_TURN)
        self.click(skip)
        self.assertEqual(self.view.phase, "attack")
        self.click(end)
        self.assertEqual(self.view.active.uid, "D1")
        self.assertEqual(self.view.active.team, "enemy")
        self.assertEqual(self.view.selected, self.view.active)
        self.game.draw()

    def test_window_quit_event_exits_main_loop(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.game.run()
        self.assertFalse(self.game.running)
        self.assertFalse(pygame.display.get_init())
        self.assertFalse(pygame.font.get_init())


class FontChecks(unittest.TestCase):
    def setUp(self):
        pygame.font.init()

    def tearDown(self):
        pygame.quit()

    def test_known_windows_font_bypasses_registry_scan(self):
        font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        if not (font_dir / "msyh.ttc").is_file():
            self.skipTest("Microsoft YaHei is not installed on this machine")
        with patch("tactics.panel.pygame.font.match_font", side_effect=TypeError("non-string entry")) as scan:
            panel = InfoPanel()
        self.assertTrue(panel.chinese)
        scan.assert_not_called()

    def test_registry_errors_still_allow_window_render_and_quit(self):
        errors = (TypeError("non-string entry"), OSError("registry unavailable"),
                  ValueError("invalid font"), pygame.error("font discovery failed"))
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with patch("tactics.panel.Path.is_file", return_value=False), \
                     patch("tactics.panel.pygame.font.match_font", side_effect=error):
                    game = Game()
                self.assertFalse(game.panel.chinese)
                game.draw()
                game.controller.select("A1")
                game.draw()
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                game.run()
                self.assertFalse(pygame.display.get_init())

    def test_missing_chinese_font_uses_builtin_font(self):
        with patch("tactics.panel.Path.is_file", return_value=False), \
             patch("tactics.panel.pygame.font.match_font", return_value=None):
            panel = InfoPanel()
        self.assertFalse(panel.chinese)
        self.assertGreater(panel.font.render("No selection", True, "white").get_width(), 0)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_milestone.py

```python
"""M5 extension acceptance using shipped content and public application operations."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pygame

from tactics.content import load_content
from tactics.game import Game

ROOT = Path(__file__).resolve().parents[1]
MODES = ("geometry", "classic", "dusk")


def make_game(scene, mode):
    return Game(scenario_file="scenarios/{}.json".format(scene),
                geometric=mode == "geometry",
                asset_root=ROOT / "assets/skins/dusk" if mode == "dusk" else None)


def exercise(check, game, scene, capture=None):
    """Same inputs and observations for every skin; also used for window captures."""
    trace = []

    def observe(name):
        game.draw()
        trace.append(game.controller.get_view_state())
        if capture:
            capture(name, game)
        return trace[-1]

    def click(cell):
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                           pos=game.geometry.cell_center(cell)))

    def key(value):
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=value))

    def unit(uid):
        return next(u for u in game.controller.get_view_state().units if u.uid == uid)

    initial = observe("initial")
    check.assertEqual(initial.active.uid, "A2")
    check.assertEqual((initial.active.health, initial.active.max_health), (80, 100))
    river = scene == "river_crossing"
    target = "R1" if river else "D2"
    click((3, 2) if river else (4, 4))
    observe("moved")
    click(unit(target).cell)
    resolving = observe("attack")
    token = resolving.pending_resolution
    check.assertTrue(resolving.input_locked)
    check.assertEqual(unit(target).health, 0 if river else 90)
    check.assertEqual(game.effects.damage_texts[0].amount, 10)
    if river:
        check.assertNotIn(target, [u.uid for u in resolving.board.units])
        check.assertTrue(game.effects.deaths or game.effects.body_views())
    for value in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
        key(value)
    click(initial.active.cell)
    check.assertEqual(game.controller.get_view_state(), resolving)
    game.update(0.2)
    observe("death" if river else "damage")
    game.update(2.0)
    after = observe("handoff")
    check.assertEqual(after.active.uid, "A1")
    check.assertFalse(game.effects.busy)
    check.assertFalse(game.effects.body_views())
    check.assertFalse(game.controller.complete_presentation(token))
    check.assertEqual(game.controller.get_view_state(), after)

    if river:
        key(pygame.K_RETURN)
        check.assertEqual(observe("enemy").active.uid, "R2")
        key(pygame.K_RETURN)
        round_two = observe("round_two")
        check.assertEqual((round_two.round_number, round_two.active.uid), (2, "A2"))
        click((5, 3))
        check.assertEqual(game.controller.get_view_state().active.cell, (5, 3))
        click(unit("R2").cell)
        second_token = observe("final_attack").pending_resolution
        game.update(2.0)
        finished = observe("finished")
        check.assertEqual((finished.phase, finished.winner), ("finished", "ally"))
        for name in ("undo_win", "undo_round", "undo_enemy", "revived"):
            key(pygame.K_BACKSPACE)
            observe(name)
        check.assertEqual(unit("R1").health, 5)
        check.assertEqual(unit("R2").health, 10)
        check.assertEqual(game.controller.get_view_state().round_number, 1)
        check.assertFalse(game.controller.complete_presentation(second_token))
    else:
        key(pygame.K_RETURN)
        check.assertEqual(observe("enemy").active.uid, "D1")
        key(pygame.K_BACKSPACE)
        observe("undo_enemy")
        key(pygame.K_BACKSPACE)
        observe("revived")
        check.assertEqual(unit(target).health, 100)

    restored = game.controller.get_view_state()
    check.assertEqual(restored.active, initial.active)
    check.assertEqual(restored.units, initial.units)
    check.assertEqual(restored.board, initial.board)
    check.assertFalse(game.effects.busy)
    check.assertFalse(game.controller.complete_presentation(token))
    check.assertEqual(game.controller.get_view_state(), restored)
    return tuple(trace)


class ExtensionAcceptance(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_second_scene_reuses_definitions_with_different_layout(self):
        original = load_content()
        river = load_content(scenario_file="scenarios/river_crossing.json")
        self.assertEqual(original.definitions, river.definitions)
        self.assertEqual((river.scenario.cols, river.scenario.rows), (6, 5))
        self.assertNotEqual(original.scenario.obstacles, river.scenario.obstacles)
        self.assertEqual(len(river.scenario.units), 4)

    def test_both_shipped_skins_load_without_fallback_issues(self):
        frames = []
        for mode in ("classic", "dusk"):
            game = make_game("river_crossing", mode)
            self.assertFalse(game.assets.issues)
            game.draw()
            frames.append(pygame.image.tostring(game.screen, "RGB"))
            pygame.quit()
        self.assertNotEqual(*frames)

    def compare_modes(self, scene):
        traces = []
        for mode in MODES:
            with self.subTest(mode=mode):
                game = make_game(scene, mode)
                traces.append(exercise(self, game, scene))
                pygame.quit()
        self.assertEqual(traces[0], traces[1])
        self.assertEqual(traces[0], traces[2])

    def test_default_scene_identical_rules_in_three_modes(self):
        self.compare_modes("training_ground")

    def test_river_kills_rounds_and_rewinds_identical_in_three_modes(self):
        self.compare_modes("river_crossing")

    def test_font_registry_fallback_and_quit_while_resolving(self):
        for mode in MODES:
            with self.subTest(mode=mode), \
                 patch("tactics.panel.Path.is_file", return_value=False), \
                 patch("tactics.panel.pygame.font.match_font", side_effect=TypeError("bad registry")):
                game = make_game("river_crossing", mode)
                self.assertFalse(game.panel.chinese)
                self.assertTrue(game.controller.move_to((3, 2)))
                self.assertTrue(game.controller.attack("R1"))
                game.draw()
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                game.run()
                self.assertFalse(game.running)
                self.assertFalse(pygame.display.get_init())
                self.assertFalse(pygame.font.get_init())

    def test_real_cli_from_foreign_directory_with_dusk(self):
        # Execute the actual argparse/main entry, then inject a close event into its loop.
        script = """
import runpy, sys
from pathlib import Path
import pygame
from tactics.game import Game
original_run = Game.run
def run(self):
    assert self.screen.get_size() == (768, 512)
    assert self.controller.get_view_state().active.uid == 'A2'
    assert not self.assets.issues
    self.draw()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    original_run(self)
    assert not pygame.display.get_init()
    print('CLI_WINDOW_QUIT_OK')
Game.run = run
root = Path(sys.argv[1])
sys.argv = [str(root / 'main.py'), '--scenario', 'scenarios/river_crossing.json',
            '--assets', str(root / 'assets/skins/dusk')]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        env = dict(os.environ, PYTHONPATH=str(ROOT), PYGAME_HIDE_SUPPORT_PROMPT="1")
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, "-c", script, str(ROOT)], cwd=folder,
                                    env=env, capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CLI_WINDOW_QUIT_OK", result.stdout)
```

## tests/test_perspective_geometry.py

```python
"""Pure homography acceptance, including ownership of shared boundaries."""

from dataclasses import replace
import math
import unittest

from tactics.perspective_geometry import BackgroundFit, PerspectiveBoardGeometry, transform


class PerspectiveGeometryChecks(unittest.TestCase):
    def setUp(self):
        self.geometry = PerspectiveBoardGeometry(8, 8, ((600,100),(950,350),(550,650),(150,400)), (1100,700))

    def test_four_logical_outer_corners(self):
        for point, corner in zip(((0,0),(8,0),(8,8),(0,8)), self.geometry.corners):
            actual = self.geometry.project(point)
            expected = self.geometry.fit.to_screen(corner)
            for a, b in zip(actual, expected):
                self.assertAlmostEqual(a, b)

    def test_all_centers_and_interior_points_pick_their_own_cell(self):
        for row in range(8):
            for col in range(8):
                cell = (col,row)
                self.assertEqual(self.geometry.cell_at(self.geometry.cell_center(cell)), cell)
                for dx,dy in ((.05,.05),(.95,.95),(.1,.9),(.9,.1)):
                    self.assertEqual(self.geometry.cell_at(self.geometry.project((col+dx,row+dy))), cell)
                self.assertEqual(self.geometry.cell_at(self.geometry.cell_anchor(cell)), cell)
                x,y,w,h = self.geometry.body_rect(cell)
                ax,ay = self.geometry.cell_anchor(cell)
                self.assertLessEqual(abs(x+w/2-ax),1)
                self.assertLessEqual(abs(y+h-ay),1)
                self.assertEqual(self.geometry.depth_at(cell), self.geometry.cell_anchor(cell)[1])

    def test_polygons_share_exact_edges_and_consistent_winding(self):
        for row in range(8):
            for col in range(8):
                a,b,c,d = self.geometry.cell_polygon((col,row))
                self.assertGreater((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]),0)
                if col < 7:
                    adjacent = self.geometry.cell_polygon((col+1,row))
                    self.assertEqual((b,c),(adjacent[0],adjacent[3]))
                if row < 7:
                    adjacent = self.geometry.cell_polygon((col,row+1))
                    self.assertEqual((d,c),(adjacent[0],adjacent[1]))

    def test_half_open_shared_edges_and_outer_boundaries(self):
        for index in range(1,8):
            self.assertEqual(self.geometry.cell_at(self.geometry.project((index,2.5))), (index,2))
            self.assertEqual(self.geometry.cell_at(self.geometry.project((2.5,index))), (2,index))
        self.assertEqual(self.geometry.cell_at(self.geometry.project((0,0))), (0,0))
        for point in ((8,2),(2,8),(-.001,2),(2,-.001),(8,8)):
            self.assertIsNone(self.geometry.cell_at(self.geometry.project(point)))

    def test_contain_letterbox_and_nonfinite_input(self):
        geometry = replace(self.geometry, viewport_size=(1600,700))
        self.assertIsNone(geometry.cell_at((10,350)))
        for cell in ((0,0),(3,6),(7,7)):
            self.assertEqual(geometry.cell_at(geometry.cell_center(cell)),cell)
        for position in ((math.nan,0),(0,math.inf),None,(0,),('x',1)):
            self.assertIsNone(geometry.cell_at(position))
        with self.assertRaisesRegex(ValueError,'horizon'):
            transform((1,0,0,0,1,0,1,0,-1),(1,0))

    def test_degenerate_crossed_reversed_and_invalid_configurations(self):
        for corners in (((0,0),)*4, ((0,0),(100,0),(200,0),(0,100)),
                        ((0,0),(100,100),(100,0),(0,100)), tuple(reversed(self.geometry.corners)),
                        ((math.nan,0),(100,0),(100,100),(0,100))):
            with self.subTest(corners=corners), self.assertRaises(ValueError):
                replace(self.geometry,corners=corners)
        for cell in ((8,0),(-1,0),(True,0),(1.0,2)):
            with self.assertRaises(ValueError):
                self.geometry.cell_polygon(cell)
        with self.assertRaises(ValueError):
            BackgroundFit((0,10),(100,100))

    def test_affine_rectangle_and_axis_orientation(self):
        geometry = PerspectiveBoardGeometry(8,8,((0,0),(800,0),(800,800),(0,800)),(800,800),(800,800))
        self.assertEqual(geometry.cell_center((2,5)),(250.0,550.0))
        self.assertEqual(geometry.cell_at((350,250)),(3,2))

    def test_irregular_mask_reference_rectangle_and_shared_edge_ownership(self):
        geometry = PerspectiveBoardGeometry(8,8,((100,100),(400,100),(400,400),(100,400)),
            (800,800),(800,800),(1,2,3,3),((1,2),(2,2),(2,3)))
        self.assertEqual(geometry.cell_center((2,3)),(250,250))
        self.assertIsNone(geometry.cell_at(geometry.project((1.5,3.5))))
        self.assertEqual(geometry.cell_at(geometry.project((2,2.5))),(2,2))
        self.assertIsNone(geometry.cell_at(geometry.project((3,2.5))))
        self.assertEqual(geometry.cell_at(geometry.project((2.5,3))),(2,3))
        for cell in geometry.cells:
            self.assertEqual(geometry.cell_at(geometry.cell_center(cell)),cell)
        with self.assertRaises(ValueError): geometry.cell_anchor((1,3))
        for changes in ({'cells':[]},{'cells':[(1,2),(1,2)]},{'cells':[(True,2)]},
                        {'reference_region':[]},{'reference_region':[1,2,8,8]}):
            with self.subTest(changes=changes),self.assertRaises(ValueError): replace(geometry,**changes)
```

## tests/test_perspective_rendering.py

```python
"""Public-input acceptance for projected combat, UI, resources and real CLI."""

from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pygame

from tactics.actions import UIAction
from tactics.assets import Sprite
from tactics.content import load_content
from tactics.data_files import DataError
from tactics.game import Game
from tactics.presentation_layout import load_presentation

ROOT = Path(__file__).resolve().parents[1]
PRESENTATION = "presentations/war_torn_8x8.json"


def combat_trace(check, game, capture=None):
    trace = []

    def observe(name):
        game.draw()
        trace.append(game.controller.get_view_state())
        if capture: capture(name,game)
        return trace[-1]

    def click(cell):
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=game.geometry.cell_center(cell)))

    def key(value):
        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=value))

    initial = observe('initial')
    # Inspection and reselection use reverse picking, including near/far cells.
    for uid in ('D2','A1','A2'):
        unit = next(u for u in initial.units if u.uid==uid)
        click(unit.cell)
        check.assertEqual(game.controller.get_view_state().selected.uid,uid)
    token = None
    for index,(move,target) in enumerate((((4,3),(5,3)),((5,2),(6,2)),((6,4),(6,5)))):
        click(move)
        check.assertEqual(observe('move'+str(index)).active.cell,move)
        click(target)
        resolving = observe('attack'+str(index))
        check.assertEqual(resolving.phase,'resolving')
        if token is None: token = resolving.pending_resolution
        for value in (pygame.K_BACKSPACE,pygame.K_RETURN,pygame.K_SPACE): key(value)
        check.assertEqual(game.controller.get_view_state(),resolving)
        game.update(.2)
        observe('death'+str(index))
        game.update(1)
        state = observe('handoff'+str(index))
        check.assertFalse(game.effects.busy)
        if index < 2:
            while state.active.uid!='A2':
                key(pygame.K_RETURN)
                state=observe('skip')
            check.assertEqual(state.round_number,index+2)
    check.assertEqual((state.phase,state.winner),('finished','ally'))
    observe('finished')
    while game.controller.get_view_state().can_undo:
        key(pygame.K_BACKSPACE)
        observe('undo')
    restored = observe('revived')
    check.assertEqual(restored.units,initial.units)
    check.assertEqual(restored.board,initial.board)
    check.assertFalse(game.controller.complete_presentation(token))
    check.assertEqual(game.controller.get_view_state(),restored)
    return tuple(trace)


class PerspectiveRenderingChecks(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_calibration_picker_undo_preview_and_save_raw_draft(self):
        from scripts.calibrate_board import DEFAULT, load_observations, pick
        data,geometry=load_observations(DEFAULT)
        points=list(data['corners'].values())+[s['image'] for s in data['samples']]
        events=[]
        # Mark then undo a duplicate corner; saved points must be actual clicks only.
        for index,point in enumerate(points):
            position=geometry.fit.to_screen(point)
            click=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=position)
            events.append(click)
            if index==1:
                events.extend((pygame.event.Event(pygame.KEYDOWN,key=pygame.K_BACKSPACE),click))
        events.extend(pygame.event.Event(pygame.KEYDOWN,key=key) for key in (pygame.K_p,pygame.K_s))
        events.append(pygame.event.Event(pygame.QUIT))
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'draft.json'
            with patch('pygame.event.get',return_value=events):
                pick(ROOT/data['image'],2,6,output)
            saved=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(saved['status'],'draft')
            self.assertEqual(list(saved['corners'].values()),points[:4])
            self.assertEqual([s['image'] for s in saved['samples']],points[4:])
            self.assertFalse(pygame.display.get_init())

    def test_same_full_combat_trace_as_rectangular_mode(self):
        original=load_content(scenario_file='scenarios/war_torn.json').scenario
        scenario=replace(original,units=tuple(replace(u,health=5) if u.team=='enemy' else u for u in original.units))
        rectangle=Game(scenario,geometric=True)
        expected=combat_trace(self,rectangle)
        pygame.quit()
        perspective=Game(scenario,presentation_file=PRESENTATION)
        actual=combat_trace(self,perspective)
        self.assertEqual(actual,expected)

    def test_hud_consumes_cards_and_buttons_use_controller_actions(self):
        game=Game(presentation_file=PRESENTATION)
        initial=game.controller.get_view_state()
        for unit in initial.units:
            rect=pygame.Rect(game.geometry.body_rect(unit.cell))
            self.assertEqual(game.renderer.cell_at(rect.center,initial.board),unit.cell)
        for position in ((30,30),(40,180),(410,60)):
            self.assertTrue(game.panel.contains(position))
            game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=position))
            self.assertEqual(game.controller.get_view_state(),initial)
        skip=(200,250)
        self.assertIs(game.panel.hit_test(skip),UIAction.SKIP_PHASE)
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=skip))
        self.assertEqual(game.controller.get_view_state().phase,'attack')
        self.assertTrue(game.controller.handle_action(UIAction.END_TURN))
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(65,250)))
        self.assertEqual(game.controller.get_view_state().units,initial.units)
        self.assertEqual(game.controller.get_view_state().active,initial.active)

    def test_background_and_debug_are_cached_and_translucent(self):
        game=Game(presentation_file=PRESENTATION,debug_grid=True)
        before=game.controller.get_view_state()
        with patch('pygame.image.load',side_effect=AssertionError('frame disk IO')), \
             patch('pygame.transform.smoothscale',side_effect=AssertionError('frame scaling')):
            for _ in range(3):
                game.update(.02)
                game.draw()
            game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F3))
            game.draw()
        self.assertFalse(any(game.renderer.debug.values()))
        self.assertEqual(game.controller.get_view_state(),before)
        # Uncovered sky is the original contain-fitted background, not repeated floor tiles.
        expected=pygame.Surface(game.screen.get_size())
        expected.fill((21,30,42))
        game.renderer.background.blit(expected,game.geometry.fit.offset)
        self.assertEqual(game.screen.get_at((1100,140)),expected.get_at((1100,140)))
        center=tuple(round(v) for v in game.geometry.cell_center((2,4)))
        pixel=game.screen.get_at(center)
        self.assertNotEqual(pixel[:3],(76,139,137))  # Range fill preserves image texture via alpha.

    def test_irregular_voids_body_picking_ranges_and_foot_anchored_obstacle(self):
        original=load_content(scenario_file='scenarios/war_torn.json').scenario
        scenario=replace(original,obstacles=frozenset(original.obstacles)|{(3,6)})
        game=Game(scenario,presentation_file=PRESENTATION,debug_grid=True)
        initial=game.controller.get_view_state()
        cells=frozenset(game.geometry.cells)
        self.assertTrue(initial.board.move_cells<=cells)
        self.assertEqual(tuple((u.uid,u.cell) for u in initial.units),tuple((u.uid,u.cell) for u in original.units))
        for uid in ('D2','D1','A1','A2'):
            unit=next(u for u in initial.units if u.uid==uid)
            body=pygame.Rect(game.geometry.body_rect(unit.cell))
            game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=body.center))
            self.assertEqual(game.controller.get_view_state().selected.uid,uid)
        # Ground hits are tested independently of body-selection priority, across all 28 tiles.
        for cell in cells:
            self.assertEqual(game.geometry.cell_at(game.geometry.cell_center(cell)),cell)
        for cell in original.obstacles:
            self.assertIsNone(game.geometry.cell_at(game.geometry.project((cell[0]+.5,cell[1]+.5))))
        rectangles=[]
        draw_rect=pygame.draw.rect
        def record(surface,color,rect,*args,**kwargs):
            if color==(92,89,84): rectangles.append(pygame.Rect(rect))
            return draw_rect(surface,color,rect,*args,**kwargs)
        with patch('pygame.draw.rect',side_effect=record): game.draw()
        self.assertEqual(len(rectangles),1)
        anchor=game.geometry.cell_anchor((3,6))
        self.assertEqual(rectangles[0].midbottom,tuple(round(v) for v in anchor))
        self.assertTrue(game.controller.move_to((4,3)))
        self.assertTrue(game.controller.attack('D1'))
        game.update(.2)
        death=next(body for body in game.effects.body_views() if body.uid=='D1')
        self.assertEqual(death.sprite.pivot,(.5,1))
        anchors=[]
        blit=Sprite.blit
        def record_body(sprite,surface,position):
            if sprite is not game.renderer.background: anchors.append(position)
            return blit(sprite,surface,position)
        with patch.object(Sprite,'blit',record_body): game.draw()
        self.assertEqual(anchors,[game.geometry.cell_anchor(death.cell)])  # One depth-sorted defeat body.
        broken=replace(original,obstacles=frozenset())
        with self.assertRaisesRegex(DataError,'void'): Game(broken,presentation_file=PRESENTATION)

    def test_missing_corrupt_and_wrong_sized_background_fail_cleanly(self):
        layout=load_presentation(PRESENTATION)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'backgrounds').mkdir()
            shutil.copyfile(ROOT/'assets/skins/war_torn/manifest.json',root/'manifest.json')
            for kind in ('missing','corrupt','size'):
                with self.subTest(kind=kind):
                    image=root/'backgrounds/battlefield.png'
                    if kind=='corrupt': image.write_bytes(b'not a PNG')
                    elif kind=='size': pygame.image.save(pygame.Surface((20,20)),str(image))
                    with patch('tactics.game.load_presentation',return_value=replace(layout,asset_root=root)):
                        with self.assertRaisesRegex(DataError,'background|battlefield'):
                            Game(presentation_file=PRESENTATION)
                    self.assertFalse(pygame.display.get_init())

    def test_existing_sprite_clips_depth_order_and_no_frame_rescaling(self):
        layout=load_presentation(PRESENTATION)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'skin'
            shutil.copytree(ROOT/'assets/skins/dusk',root)
            (root/'backgrounds').mkdir()
            shutil.copyfile(ROOT/'assets/skins/war_torn/backgrounds/battlefield.png',root/'backgrounds/battlefield.png')
            data=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
            data['images']['battlefield']={'path':'backgrounds/battlefield.png','display_size':[1672,941],'pivot':[0,0],'optional':False}
            data['board']['background']='battlefield'
            (root/'manifest.json').write_text(json.dumps(data),encoding='utf-8')
            with patch('tactics.game.load_presentation',return_value=replace(layout,asset_root=root)):
                game=Game(presentation_file=PRESENTATION)
            calls=[]
            original=Sprite.blit
            def record(sprite,target,anchor):
                if sprite is not game.renderer.background: calls.append(anchor)
                return original(sprite,target,anchor)
            with patch.object(Sprite,'blit',record), \
                 patch('pygame.image.load',side_effect=AssertionError('frame disk IO')), \
                 patch('pygame.transform.smoothscale',side_effect=AssertionError('frame scaling')):
                game.draw()
                self.assertEqual([p[1] for p in calls],sorted(p[1] for p in calls))
                self.assertTrue(game.controller.move_to((4,3)))
                self.assertTrue(game.controller.attack('D1'))
                self.assertTrue(game.effects.body_views())
                self.assertFalse(game.effects.deaths)  # The target uses the cached PNG death clip.
                game.update(.2)
                game.draw()
                game.update(1)
                self.assertTrue(game.controller.undo())
                self.assertFalse(game.effects.body_views())
                game.draw()

    def test_mixed_flags_dimensions_and_font_fallback(self):
        for kwargs in ({'geometric':True},{'scenario_file':'scenarios/training_ground.json'},
                       {'asset_root':ROOT/'assets'},{'content_root':ROOT/'content'}):
            with self.subTest(kwargs=kwargs),self.assertRaisesRegex(DataError,'cannot be combined'):
                Game(presentation_file=PRESENTATION,**kwargs)
        with self.assertRaisesRegex(DataError,'needs --presentation'): Game(debug_grid=True)
        with self.assertRaisesRegex(DataError,'dimensions'):
            Game(load_content(scenario_file='scenarios/river_crossing.json').scenario,presentation_file=PRESENTATION)
        with patch('tactics.panel.Path.is_file',return_value=False), \
             patch('tactics.panel.pygame.font.match_font',side_effect=TypeError('bad registry')):
            game=Game(presentation_file=PRESENTATION)
        self.assertFalse(game.panel.chinese)
        self.assertTrue(game.controller.move_to((4,3)))
        self.assertTrue(game.controller.attack('D1'))
        game.draw()
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        game.run()
        self.assertFalse(pygame.display.get_init())

    def test_real_cli_and_relative_presentation_from_foreign_cwd(self):
        script="""
import runpy,sys,pygame
from tactics.game import Game
original=Game.run
def run(self):
    assert self.screen.get_size()==(1280,720)
    assert all(self.renderer.debug.values())
    self.draw()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    original(self)
    assert not pygame.display.get_init()
    print('PERSPECTIVE_CLI_QUIT_OK')
Game.run=run
sys.argv=[sys.argv[1], '--presentation','presentations/war_torn_8x8.json','--debug-grid']
runpy.run_path(sys.argv[0],run_name='__main__')
"""
        env=dict(os.environ,PYTHONPATH=str(ROOT),PYGAME_HIDE_SUPPORT_PROMPT='1')
        with tempfile.TemporaryDirectory() as folder:
            result=subprocess.run([sys.executable,'-c',script,str(ROOT/'main.py')],env=env,cwd=folder,
                                  text=True,capture_output=True,timeout=45)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('PERSPECTIVE_CLI_QUIT_OK',result.stdout)
```

## tests/test_presentation_layout.py

```python
"""Pure, strict presentation and background manifest checks."""

import json
from pathlib import Path
import tempfile
import unittest

from tactics.asset_manifest import load_manifest
from tactics.data_files import DataError
from tactics.presentation_layout import load_presentation

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "presentations/war_torn_8x8.json"


class PresentationLayoutChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'presentations').mkdir()
        self.data = json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))

    def load(self):
        (self.root/CONFIG).write_text(json.dumps(self.data),encoding='utf-8')
        return load_presentation(CONFIG,self.root)

    def test_shipped_layout_and_compatible_manifests(self):
        layout = load_presentation(CONFIG)
        self.assertEqual(layout.geometry.reference_size,(1672,941))
        for folder in ('assets','assets/skins/dusk','assets/skins/war_torn'):
            self.assertTrue(load_manifest(ROOT/folder).visuals)
        self.assertEqual(len(layout.geometry.cells),28)
        self.assertEqual(layout.geometry.cell_at(layout.geometry.cell_center((6,5))),(6,5))
        self.assertIsNone(layout.geometry.cell_at(layout.geometry.project((7.5,7.5))))

    def test_legacy_full_rectangular_presentation_remains_supported(self):
        self.data['board'].pop('reference_region')
        self.data['board'].pop('cells')
        geometry=self.load().geometry
        self.assertEqual(len(geometry.cells),64)
        self.assertEqual(geometry.cell_at(geometry.cell_center((7,7))),(7,7))

    def test_unknown_fields_versions_modes_and_placeholder_corners(self):
        for key,value in (('schema_version',2),('mode','unknown'),('unexpected',1)):
            with self.subTest(key=key):
                original = dict(self.data)
                self.data[key]=value
                with self.assertRaises(DataError): self.load()
                self.data=original
        self.data['board']['corners']={k:[0,0] for k in ('p00','p10','p11','p01')}
        with self.assertRaisesRegex(DataError,'corners'): self.load()

    def test_paths_must_stay_in_project_or_content_root(self):
        for key in ('scenario_file','asset_root'):
            for value in ('../../escape','C:/absolute','/absolute','..\\escape'):
                with self.subTest(key=key,value=value):
                    original=self.data[key]
                    self.data[key]=value
                    with self.assertRaises(DataError): self.load()
                    self.data[key]=original
        with self.assertRaises(DataError): load_presentation('../escape',self.root)

    def test_invalid_viewport_hud_and_debug_are_rejected(self):
        for section,key,value in (('viewport','background_fit','stretch'),('viewport','reference_size',[0,720]),
                                  ('hud','safe_margin',999),('hud','layout','sidebar'),
                                  ('debug','show_grid',1),('board','cols',True)):
            with self.subTest(section=section,key=key):
                original=self.data[section][key]
                self.data[section][key]=value
                with self.assertRaises(DataError): self.load()
                self.data[section][key]=original

    def test_background_reference_and_required_flag_are_validated(self):
        data=json.loads((ROOT/'assets/skins/war_torn/manifest.json').read_text(encoding='utf-8'))
        for bad in ('unknown','optional'):
            if bad=='unknown': data['board']['background']='missing'
            else:
                data['board']['background']='battlefield'
                data['images']['battlefield']['optional']=True
            (self.root/'manifest.json').write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaisesRegex(DataError,'background|unknown image'): load_manifest(self.root)
```

## tests/test_release.py

```python
"""Reject unusable delivery artifacts before executing extracted source."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.verify_release import verify


class ReleaseIntegrityChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "release.zip"
        self.commit = "a" * 40

    def write_archive(self, version="0.2.0", extra=None):
        with zipfile.ZipFile(self.archive, "w") as package:
            package.comment = json.dumps({"format": "chrono-tactics-source-v1", "version": "0.2.0",
                                          "commit": self.commit}).encode("ascii")
            package.writestr("chrono-tactics-pygame-0.2.0/VERSION.txt", version)
            if extra:
                package.writestr(extra, "unwanted")
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.archive.with_suffix(".zip.sha256").write_text(digest + "  release.zip\n", encoding="ascii")

    def reject(self, message, expected=None):
        with patch("scripts.verify_release.subprocess.run") as execute:
            with self.assertRaisesRegex(ValueError, message):
                verify(self.archive, expected)
            execute.assert_not_called()

    def test_changed_archive_fails_checksum_before_execution(self):
        self.write_archive()
        with self.archive.open("ab") as output:
            output.write(b"tampered")
        self.reject("SHA256")

    def test_wrong_source_commit_is_rejected(self):
        self.write_archive()
        self.reject("Unexpected source commit", "b" * 40)

    def test_version_file_must_match_metadata(self):
        self.write_archive(version="9.9.9")
        self.reject("Source version")

    def test_unsafe_paths_and_workspace_artifacts_are_rejected(self):
        for extra in ("chrono-tactics-pygame-0.2.0/../../escape", "/absolute",
                      "chrono-tactics-pygame-0.2.0/.venv/python.exe",
                      "chrono-tactics-pygame-0.2.0/.git/config",
                      "chrono-tactics-pygame-0.2.0/dist/old.zip",
                      "chrono-tactics-pygame-0.2.0/C:/escape"):
            with self.subTest(extra=extra):
                self.write_archive(extra=extra)
                self.reject("Unsafe or unwanted")
```

## tests/test_rendering.py

```python
"""M1 renderer/view contracts, separate from the retained gameplay checks."""

from dataclasses import FrozenInstanceError, asdict, replace
import unittest
from unittest.mock import patch

import pygame

from tactics.actions import UIAction
from tactics.battle import Battle
from tactics.controller import Controller
from tactics.board import Board
from tactics.board_renderer import BoardRenderer
from tactics.game import Game
from tactics.geometry import BoardGeometry
from tactics.panel import InfoPanel
from tactics.scenario import Scenario, UnitSpawn, default_scenario
from tactics.view_models import build_board_view


class RenderBoundaryChecks(unittest.TestCase):
    def setUp(self):
        pygame.font.init()
        self.board = Board(default_scenario())
        self.battle = Battle(self.board)
        self.actor = self.battle.active_unit

    def tearDown(self):
        pygame.quit()

    def test_view_is_detached_and_deeply_read_only(self):
        view = build_board_view(self.board, self.battle, self.actor)
        unit_view = next(unit for unit in view.units if unit.uid == self.actor.uid)
        self.actor.health = 1
        self.actor.cell = (0, 0)
        self.assertEqual((unit_view.health, unit_view.cell), (80, (1, 3)))
        self.assertIsInstance(view.move_cells, frozenset)
        self.assertIsInstance(view.units, tuple)
        with self.assertRaises(FrozenInstanceError):
            unit_view.health = 0
        with self.assertRaises(FrozenInstanceError):
            view.active_uid = "D1"

    def test_ranges_follow_selection_phase_and_legal_queries(self):
        view = build_board_view(self.board, self.battle, self.actor)
        self.assertEqual(view.move_cells, self.battle.movement_range())
        self.assertFalse(view.attack_cells)
        hidden = build_board_view(self.board, self.battle, self.board.enemies[0])
        self.assertFalse(hidden.move_cells or hidden.attack_cells or hidden.target_cells)
        self.battle.move((4, 4))
        view = build_board_view(self.board, self.battle, self.actor)
        self.assertFalse(view.move_cells)
        self.assertEqual(view.attack_cells, {(4, 3), (3, 4), (5, 4)})
        self.assertEqual(view.target_cells, {(5, 4)})
        self.battle.attack(self.board.enemies[1])
        resolving = build_board_view(self.board, self.battle, self.actor)
        self.assertFalse(resolving.move_cells or resolving.attack_cells or resolving.target_cells)

    def test_renderer_needs_only_values_and_preserves_state_and_surface_clip(self):
        view = build_board_view(self.board, self.battle, self.actor)
        before = [asdict(unit) for unit in self.board.units]
        geometry = BoardGeometry(8, 8, 32, (11, 13))
        surface = pygame.Surface((300, 300))
        surface.fill("magenta")
        surface.set_clip((5, 5, 280, 280))
        clip = surface.get_clip()
        with patch.object(self.battle, "movement_range", side_effect=AssertionError("renderer queried rules")), \
             patch.object(self.battle, "attack_targets", side_effect=AssertionError("renderer queried targets")):
            BoardRenderer(geometry).draw(surface, view)
        self.assertEqual([asdict(unit) for unit in self.board.units], before)
        self.assertEqual(surface.get_clip(), clip)
        self.assertEqual(tuple(surface.get_at((10, 13)))[:3], (255, 0, 255))
        self.assertNotEqual(tuple(surface.get_at((11, 13)))[:3], (255, 0, 255))
        with self.assertRaises(ValueError):
            BoardRenderer(geometry).draw(surface, replace(view, cols=5))

    def test_injected_scenario_uses_its_dimensions_for_window_clicks_and_effects(self):
        scenario = Scenario("small", 5, 4, (
            UnitSpawn("blue", "Blue", "ally", "test", (0, 0), speed=20, movement=4, attack=17),
            UnitSpawn("red", "Red", "enemy", "test", (3, 0), health=50, speed=5),
        ), frozenset(((1, 0),)))
        game = Game(scenario)
        self.assertEqual(game.geometry.bounds, (0, 0, 320, 256))
        self.assertEqual(game.screen.get_size(), (704, 512))
        self.assertIs(game.panel.hit_test((344, 284)), UIAction.SKIP_PHASE)
        self.assertIs(game.effects.geometry, game.geometry)
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                            pos=game.geometry.cell_center((2, 0))))
        self.assertEqual(game.controller.get_view_state().phase, "attack")
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                            pos=game.geometry.cell_center((3, 0))))
        self.assertEqual(next(unit.health for unit in game.controller.get_view_state().units if unit.uid == "red"), 33)
        self.assertEqual(game.effects.damage_texts[0].cell, (3, 0))
        game.draw()
        game.update(1)
        game.controller.undo()
        self.assertEqual(next(unit.health for unit in game.controller.get_view_state().units if unit.uid == "red"), 50)
        game.draw()

    def test_panel_hit_test_returns_intent_with_half_open_bounds_at_custom_width(self):
        panel = InfoPanel(320)
        for position, expected in (
            ((344, 284), UIAction.SKIP_PHASE), ((505, 321), UIAction.SKIP_PHASE),
            ((518, 284), UIAction.END_TURN), ((679, 321), UIAction.END_TURN),
            ((528, 14), UIAction.UNDO), ((679, 45), UIAction.UNDO),
            ((343, 284), None), ((506, 303), None), ((344, 322), None),
            ((680, 30), None), ((528, 46), None), ((0, 0), None),
        ):
            with self.subTest(position=position):
                self.assertIs(panel.hit_test(position), expected)
        for name in ("undo_button", "skip_button", "end_button"):
            self.assertFalse(hasattr(panel, name), name)

    def test_panel_draws_saved_view_without_access_to_controller_or_rules(self):
        controller = Controller(default_scenario())
        saved = controller.get_view_state()
        controller.handle_action(UIAction.END_TURN)
        panel = InfoPanel()
        surface = pygame.Surface((896, 512))
        with patch.object(panel, "text", wraps=panel.text) as text:
            panel.draw(surface, saved)
        expected = "当前行动：斥候 [A2]" if panel.chinese else "Active: A2 [A2]"
        self.assertTrue(any(call.args[1] == expected for call in text.call_args_list))
        self.assertEqual(saved.active.uid, "A2")
        self.assertEqual(controller.get_view_state().active.uid, "A1")


if __name__ == "__main__":
    unittest.main()
```

## tests/test_resolution.py

```python
"""M3 snapshot and completion contracts, runnable with python -S."""

from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
import json
import unittest

from tactics.actions import UIAction
from tactics.battle import Battle
from tactics.board import Board
from tactics.controller import Controller
from tactics.models import Unit, UnitSnapshot
from tactics.scenario import default_scenario
from tactics.view_models import ResolutionToken


def scenario_with(**changes):
    scenario = default_scenario()
    return replace(scenario, units=tuple(
        replace(unit, **changes.get(unit.uid, {})) for unit in scenario.units))


def assert_pure(test, value):
    if is_dataclass(value):
        test.assertTrue(value.__dataclass_params__.frozen)
        for field in fields(value):
            assert_pure(test, getattr(value, field.name))
    elif isinstance(value, tuple):
        for child in value:
            assert_pure(test, child)
    else:
        test.assertIn(type(value), (str, int, bool, type(None)))


class SnapshotAndResultChecks(unittest.TestCase):
    def setUp(self):
        self.board = Board(default_scenario())
        self.battle = Battle(self.board)

    def attack(self):
        self.assertTrue(self.battle.move((4, 4)))
        self.assertTrue(self.battle.attack(next(unit for unit in self.board.units if unit.uid == "D2")))
        return self.battle.pending_attack

    def test_snapshots_are_deeply_immutable_values_covering_every_unit_field(self):
        snapshot = self.battle.history[0]
        self.assertEqual({field.name for field in fields(UnitSnapshot)},
                         {field.name for field in fields(Unit)})
        assert_pure(self, snapshot)
        self.assertEqual(snapshot.order_uids, ("A2", "A1", "D1", "A3", "D2", "D3"))
        with self.assertRaises(FrozenInstanceError):
            snapshot.units[0].health = 0
        with self.assertRaises(FrozenInstanceError):
            snapshot.index = 2
        self.assertIsInstance(json.loads(json.dumps(asdict(snapshot)))["units"], list)
        self.assertFalse(hasattr(snapshot, "_next_resolution_id"))

    def test_saved_values_do_not_change_with_runtime_damage_attributes_or_logs(self):
        snapshot = self.battle.history[0]
        before = asdict(snapshot)
        self.attack()
        for unit in self.board.units:
            unit.health = 1
            unit.attack = 999
            unit.cell = (0, 0)
            unit.name = "Changed"
        self.battle.notify("changed", "changed")
        self.assertEqual(asdict(snapshot), before)

    def test_undo_recreates_all_attributes_and_canonical_slots_by_uid(self):
        self.board = Board(scenario_with(A2={"health": 800, "max_health": 1000, "attack": 300},
                                         D2={"health": 5}))
        self.battle = Battle(self.board)
        original_units = self.board.units
        before = self.battle.history[0]
        result = self.attack()
        self.battle.finish_attack(result.resolution_id)
        self.battle.move((0, 1))
        for unit in self.board.units:
            unit.name, unit.role, unit.defense = "Changed", "Other", 999
            unit.speed, unit.movement, unit.max_health, unit.health = 1, 0, 1, 1
        self.assertTrue(self.battle.undo())
        self.assertEqual(self.battle._snapshot(), before)
        for old, current in zip(original_units, self.board.units):
            self.assertIsNot(old, current)
        by_uid = {unit.uid: unit for unit in self.board.units}
        self.assertTrue(all(unit is by_uid[unit.uid] for unit in self.battle.entry_order))
        self.assertEqual((by_uid["D2"].health, by_uid["A2"].health, by_uid["A2"].max_health), (5, 800, 1000))
        self.battle.move((4, 4))
        self.assertFalse(self.battle.attack(original_units[4]))  # Stale object identity is not a target.
        self.assertTrue(self.battle.attack(by_uid["D2"]))

    def test_dead_state_and_round_are_restored_through_multiple_undos(self):
        self.board = Board(scenario_with(D2={"health": 5}))
        self.battle = Battle(self.board)
        result = self.attack()
        self.battle.finish_attack(result.resolution_id)
        after_kill = self.battle.history[-1]
        for _ in range(4):
            self.battle.end_turn()
        self.assertEqual((self.battle.round_number, self.battle.active_unit.uid), (2, "A2"))
        for _ in range(4):
            self.assertTrue(self.battle.undo())
        self.assertEqual(self.battle._snapshot(), after_kill)
        self.assertEqual(next(unit.health for unit in self.board.units if unit.uid == "D2"), 0)
        self.assertNotIn("D2", tuple(unit.uid for unit in self.battle.order))
        self.assertTrue(self.battle.undo())
        self.assertEqual(next(unit.health for unit in self.board.units if unit.uid == "D2"), 5)
        self.assertIn("D2", tuple(unit.uid for unit in self.battle.order))

    def test_rule_completion_requires_matching_id_and_ids_do_not_rewind(self):
        self.assertFalse(self.battle.attack(self.board.enemies[1]))
        first = self.attack()
        self.assertEqual(first.resolution_id, 1)
        before = self.battle._snapshot()
        self.assertFalse(self.battle.finish_attack(first.resolution_id + 1))
        self.assertEqual(self.battle._snapshot(), before)
        self.assertTrue(self.battle.finish_attack(first.resolution_id))
        self.assertFalse(self.battle.finish_attack(first.resolution_id))
        self.battle.undo()
        second = self.attack()
        self.assertGreater(second.resolution_id, first.resolution_id)
        self.assertFalse(self.battle.finish_attack(first.resolution_id))
        self.assertEqual(self.battle.phase, "resolving")
        self.assertTrue(self.battle.finish_attack(second.resolution_id))

    def test_attack_results_capture_ids_location_full_damage_and_hp_change(self):
        for attack, health, expected_hp, killed in ((10, 100, 90, False), (300, 7, 0, True), (0, 7, 7, False)):
            with self.subTest(attack=attack):
                self.board = Board(scenario_with(A2={"attack": attack}, D2={"health": health}))
                self.battle = Battle(self.board)
                result = self.attack()
                assert_pure(self, result)
                self.assertEqual((result.actor_uid, result.target_uid, result.target_team,
                                  result.target_cell, result.damage, result.previous_hp,
                                  result.current_hp, result.killed),
                                 ("A2", "D2", "enemy", (5, 4), attack, health, expected_hp, killed))
                with self.assertRaises(FrozenInstanceError):
                    result.current_hp = 100
                self.board.enemies[1].cell = (7, 7)
                self.board.enemies[1].health = 1
                self.assertEqual((result.target_cell, result.current_hp), ((5, 4), expected_hp))


class DelayedPresentation:
    """Can deliver in-flight notifications even after clear; controller must reject them."""

    def __init__(self):
        self.events = []
        self.completions = []
        self.clears = 0
        self.busy = False
        self.on_clear = None

    def play_attack(self, event):
        self.events.append(event)

    def update(self, elapsed):
        completed, self.completions = tuple(self.completions), []
        return completed

    def clear(self):
        self.clears += 1
        if self.on_clear is not None:
            self.on_clear()


class CompletionContractChecks(unittest.TestCase):
    def setUp(self):
        self.presentation = DelayedPresentation()
        self.controller = Controller(default_scenario(), self.presentation)

    @property
    def view(self):
        return self.controller.get_view_state()

    def attack(self):
        self.assertTrue(self.controller.move_to((4, 4)))
        self.assertTrue(self.controller.attack("D2"))
        return self.presentation.events[-1].token

    def test_matching_completion_is_accepted_only_once(self):
        token = self.attack()
        self.assertEqual(self.view.pending_resolution, token)
        assert_pure(self, self.presentation.events[-1])
        self.assertTrue(self.controller.complete_presentation(token))
        after = self.view
        self.assertEqual(after.active.uid, "A1")
        self.assertIsNone(after.pending_resolution)
        self.assertFalse(self.controller.complete_presentation(token))
        self.assertEqual(self.view, after)

    def test_wrong_generation_or_resolution_is_rejected_without_side_effects(self):
        token = self.attack()
        before = self.view
        for wrong in (replace(token, generation=token.generation + 1),
                      replace(token, resolution_id=token.resolution_id + 1), None):
            self.assertFalse(self.controller.complete_presentation(wrong))
            self.assertEqual(self.view, before)
        self.assertTrue(self.controller.complete_presentation(token))

    def test_busy_false_without_completion_cannot_handoff(self):
        self.attack()
        self.assertFalse(self.presentation.busy)
        before = self.view
        self.controller.update(10000)
        self.assertEqual(self.view, before)

    def test_background_busy_does_not_block_explicit_attack_completion(self):
        token = self.attack()
        self.presentation.busy = True  # Future ambient/idle animation may continue forever.
        self.presentation.completions.append(token)
        self.controller.update(0)
        self.assertEqual((self.view.active.uid, self.view.phase), ("A1", "move"))

    def test_undo_replay_rejects_old_completion_before_and_during_new_attack(self):
        old = self.attack()
        self.controller.complete_presentation(old)
        self.controller.undo()
        self.assertEqual(self.view.presentation_generation, old.generation + 1)
        self.assertFalse(self.controller.complete_presentation(old))
        current = self.attack()
        self.assertGreater(current.resolution_id, old.resolution_id)
        before = self.view
        self.assertFalse(self.controller.complete_presentation(old))
        self.assertEqual(self.view, before)
        self.assertTrue(self.controller.complete_presentation(current))

    def test_restart_during_attack_cancels_old_generation_even_when_ids_repeat(self):
        old = self.attack()
        self.assertTrue(self.controller.restart())
        self.assertEqual((self.view.presentation_generation, self.view.active.cell), (1, (1, 3)))
        self.assertEqual(next(unit.health for unit in self.view.units if unit.uid == "D2"), 100)
        self.assertFalse(self.view.can_undo)
        current = self.attack()
        self.assertEqual(old.resolution_id, current.resolution_id)
        self.assertNotEqual(old.generation, current.generation)
        self.assertFalse(self.controller.complete_presentation(old))
        self.assertEqual(self.view.pending_resolution, current)
        self.assertTrue(self.controller.complete_presentation(current))

    def test_generation_is_invalidated_before_clear_can_deliver_late_callback(self):
        old = self.attack()
        results = []

        def late_callback():
            self.assertEqual(self.view.presentation_generation, old.generation + 1)
            self.assertIsNone(self.view.pending_resolution)
            results.append(self.controller.complete_presentation(old))

        self.presentation.on_clear = late_callback
        self.controller.restart()  # Old token was valid and resolving immediately before clear.
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0])
        self.assertEqual((self.view.active.uid, self.view.phase), ("A2", "move"))
        self.assertEqual(self.presentation.clears, 1)

    def test_failed_undo_does_not_advance_generation_or_clear_current_presentation(self):
        before = self.view
        self.assertFalse(self.controller.undo())
        self.assertEqual(self.view, before)
        self.controller.handle_action(UIAction.END_TURN)
        self.controller.undo()
        self.attack()
        before = self.view
        clears = self.presentation.clears
        self.assertFalse(self.controller.undo())
        self.assertEqual(self.view, before)
        self.assertEqual(self.presentation.clears, clears)

    def test_batch_of_late_duplicate_and_current_notifications_hands_off_once(self):
        old = self.attack()
        self.controller.complete_presentation(old)
        self.presentation.completions.append(old)
        self.controller.undo()  # In-flight notification survives adapter.clear().
        current = self.attack()
        self.presentation.completions += [current, current, old]
        self.controller.update(0)
        after = self.view
        self.assertEqual((after.active.uid, after.round_number), ("A1", 1))
        self.controller.update(1)
        self.assertEqual(self.view, after)

    def test_final_kill_completion_cannot_repeat_after_finish_or_undo(self):
        scenario = scenario_with(D2={"health": 5})
        scenario = replace(scenario, units=tuple(unit for unit in scenario.units if unit.uid in ("A2", "D2")))
        self.controller = Controller(scenario, self.presentation)
        token = self.attack()
        self.assertFalse(self.view.finished)
        self.controller.complete_presentation(token)
        self.assertEqual(self.view.winner, "ally")
        after = self.view
        self.assertFalse(self.controller.complete_presentation(token))
        self.assertEqual(self.view, after)
        self.controller.undo()
        self.assertFalse(self.controller.complete_presentation(token))
        self.assertEqual(next(unit.health for unit in self.view.units if unit.uid == "D2"), 5)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_rewind.py

```python
"""Whole-turn rewind, defeated-unit restoration and stable initiative slots."""

from dataclasses import asdict
import unittest

from tactics.battle import Battle
from tactics.board import Board
from tactics.scenario import default_scenario


class RewindAndDefeatChecks(unittest.TestCase):
    def setUp(self):
        self.board = Board(default_scenario())
        self.battle = Battle(self.board)

    @property
    def actor(self):
        return next(unit for unit in self.board.units if unit.uid == "A2")

    @property
    def target(self):
        return next(unit for unit in self.board.units if unit.uid == "D2")

    def test_first_turn_has_no_previous_turn_even_after_moving(self):
        self.assertFalse(self.battle.can_undo)
        self.assertFalse(self.battle.undo())
        self.battle.move((4, 4))
        self.assertFalse(self.battle.undo())
        self.assertEqual(self.actor.cell, (4, 4))

    def test_undo_restores_full_previous_turn_and_discards_partial_current_turn(self):
        before = [asdict(unit) for unit in self.board.units]
        log = list(self.battle.log)
        self.battle.move((4, 4))
        self.battle.attack(self.target)
        self.battle.finish_attack(self.battle.pending_attack.resolution_id)
        self.assertTrue(self.battle.move((0, 1)))
        self.assertTrue(self.battle.undo())
        self.assertEqual([asdict(unit) for unit in self.board.units], before)
        self.assertIs(self.battle.active_unit, self.actor)
        self.assertEqual(self.battle.phase, "move")
        self.assertEqual(self.battle.log, log)
        self.assertIsNone(self.battle.pending_attack)
        self.assertFalse(self.battle.undo())

    def test_resolving_attack_locks_turn_changes_and_undo(self):
        self.battle.end_turn()
        self.board.enemies[0].cell = (2, 1)
        self.battle.skip_phase()
        self.battle.attack(self.board.enemies[0])
        self.assertGreater(len(self.battle.history), 1)
        self.assertFalse(self.battle.can_undo)
        self.assertFalse(self.battle.undo())
        self.assertFalse(self.battle.end_turn())
        self.battle.skip_phase()
        self.assertEqual(self.battle.index, 1)
        self.assertEqual(self.battle.phase, "resolving")

    def test_multiple_undos_cross_round_boundary(self):
        for _ in range(8):
            self.battle.end_turn()
        self.assertEqual((self.battle.round_number, self.battle.index), (2, 2))
        for expected in ((2, 1), (2, 0), (1, 5)):
            self.assertTrue(self.battle.undo())
            self.assertEqual((self.battle.round_number, self.battle.index), expected)

    def test_new_branch_discards_abandoned_future(self):
        self.battle.end_turn()
        self.battle.end_turn()
        self.battle.undo()
        self.assertTrue(self.battle.move((0, 1)))
        self.battle.end_turn()
        self.assertTrue(self.battle.undo())
        self.assertEqual(self.battle.active_unit.uid, "A1")
        self.assertEqual(self.battle.active_unit.cell, (1, 1))
        self.assertEqual(len(self.battle.history), 2)

    def test_defeated_units_leave_targets_collision_and_queue(self):
        self.target.health = 5
        self.battle.move((4, 4))
        self.assertTrue(self.battle.attack(self.target))
        self.assertEqual(self.target.health, 0)
        self.assertTrue(self.battle.pending_attack.killed)
        self.assertNotIn(self.target, self.battle.order)
        self.assertIsNone(self.board.unit_at(self.target.cell))
        self.assertIn(self.target.cell, self.board.reachable_cells(self.actor))
        self.assertIn(self.target, self.board.units)  # Roster is retained for undo.

    def test_overkill_clamps_health_and_preserves_full_damage_amount(self):
        self.target.health = 7
        self.actor.attack = 300
        self.battle.move((4, 4))
        self.battle.attack(self.target)
        self.assertEqual(self.target.health, 0)
        self.assertEqual(self.battle.pending_attack.damage, 300)
        self.assertFalse(self.battle.attack(self.target))

    def test_killing_earlier_slot_does_not_shift_next_actor(self):
        ally = self.board.allies[0]
        ally.cell = (5, 1)
        ally.health = 5
        self.battle.end_turn()
        self.battle.end_turn()
        self.assertEqual(self.battle.active_unit.uid, "D1")
        self.battle.skip_phase()
        self.battle.attack(ally)
        self.battle.finish_attack(self.battle.pending_attack.resolution_id)
        self.assertEqual(self.battle.active_unit.uid, "A3")

    def test_killing_next_actor_skips_the_dead_slot(self):
        enemy = self.board.enemies[0]
        enemy.cell = (2, 1)
        enemy.health = 5
        self.battle.end_turn()
        self.battle.skip_phase()
        self.battle.attack(enemy)
        self.battle.finish_attack(self.battle.pending_attack.resolution_id)
        self.assertEqual(self.battle.active_unit.uid, "A3")

    def test_round_wrap_can_skip_a_dead_first_slot(self):
        self.actor.cell = (6, 5)
        self.actor.health = 5
        for _ in range(5):
            self.battle.end_turn()
        self.assertEqual(self.battle.active_unit.uid, "D3")
        self.battle.skip_phase()
        self.battle.attack(self.actor)
        self.battle.finish_attack(self.battle.pending_attack.resolution_id)
        self.assertEqual(self.battle.active_unit.uid, "A1")
        self.assertEqual(self.battle.round_number, 2)

    def test_final_kill_finishes_after_effects_and_undo_revives_enemy(self):
        self.board.units = (self.actor, self.target)
        self.target.health = 5
        battle = Battle(self.board)
        battle.move((4, 4))
        battle.attack(self.target)
        self.assertFalse(battle.finished)
        battle.finish_attack(battle.pending_attack.resolution_id)
        self.assertEqual(battle.winner, "ally")
        self.assertIsNone(battle.active_unit)
        self.assertFalse(battle.end_turn())
        self.assertTrue(battle.undo())
        self.assertEqual(self.target.health, 5)
        self.assertIn(self.target, battle.order)
        self.assertIs(self.board.unit_at(self.target.cell), self.target)
        self.assertIsNone(battle.winner)
        self.assertEqual(battle.phase, "move")

    def test_undo_restores_killed_unit_and_allows_same_action_again(self):
        self.actor.attack = 300
        self.actor.max_health = 1000
        self.actor.health = 800
        battle = Battle(self.board)
        original_order = tuple(unit.uid for unit in battle.order)
        for _ in range(2):
            self.assertTrue(battle.move((4, 4)))
            self.assertTrue(battle.attack(self.target))
            battle.finish_attack(battle.pending_attack.resolution_id)
            self.assertFalse(self.target.alive)
            self.assertTrue(battle.undo())
            self.assertTrue(self.target.alive)
            self.assertEqual(self.target.health, self.target.max_health)
            self.assertEqual((self.actor.health, self.actor.max_health), (800, 1000))
            self.assertEqual(tuple(unit.uid for unit in battle.order), original_order)
            self.assertEqual(self.actor.cell, (1, 3))


if __name__ == "__main__":
    unittest.main()
```
