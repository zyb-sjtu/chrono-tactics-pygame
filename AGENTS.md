# 项目维护与后续开发约定

## 先确认实际状态

- 最近发布版本是 v0.1.0，开发代码已完成 M1、M2：场景注入、纯逻辑地图、独立渲染、Controller、完整只读视图与 UIAction。M3–M5 尚未实施；以 `TASKS.md` 区分现有能力和规划。
- 修改玩法、结构或资源入口前，阅读 [整体架构](docs/ARCHITECTURE.md)、[实施路线](docs/ROADMAP.md) 与 [功能开发规范](docs/FEATURE_DEVELOPMENT.md)。接入美术时同时遵守 [资源规范](docs/ASSET_GUIDE.md)。用户提供的原始报告是评审材料，当前开发决策以这些评审后文档为准。

## 开发边界

- 这是离线 Python/Pygame 战棋原型。保留几何绘制作为无素材时的默认回退，后续美术通过统一资源与渲染层接入；具体玩法按用户需求推进。
- 业务规则放在 `tactics/battle.py`，空间与路径规则放在 `tactics/board.py`。Board 显式接收 Scenario，不恢复像素坐标或绘图入口；坐标由 Geometry 转换，绘制由 BoardRenderer 读取 BoardView 完成。
- 应用操作统一经过 `Controller`，通过 `get_view_state()` 查询独立的 BattleView；不向 Game、Panel、Renderer、Effects 暴露活动 Unit/Board/Battle。Game 只做组装、输入适配、循环与清理；Panel 用 `hit_test(position)` 返回 UIAction，按钮矩形保持内部实现。
- `move_to/attack` 对当前行动者提交指令，与查看谁的属性无关；鼠标通过 `click_cell` 保留“先选回行动者再操作”的交互。不要让未来 AI 模拟像素点击，也不以重建 Game 内部字段作为测试夹具；用 Scenario 构建局面。
- M2 使用小型表现接口（play_attack/update/busy/clear）和独立 AttackPresentation；规则内部结果与快照的实体引用、结算编号和表现代次仍待 M3，资源加载待 M4。
- 后续功能必须建立在可扩展边界上：先明确规则入口、数据归属、回溯策略、表现/资源接入和验收证据。前置能力缺失时先补齐最小必要部分，与需求一并交付；不能以架构未完成为由无限延后任务，也不为每个小改动制造额外批准流程。
- 新增规则代码不依赖 Pygame；渲染、UI、动画和未来 AI 不直接改战斗状态。UI/AI 共用合法性校验和指令入口，避免复制规则。
- 新增运行状态必须明确快照与恢复行为；新增资源、图片、字体、动画进度不得进入规则快照。对外视图和结算结果使用独立数据与稳定 ID，不向表现层泄露可变实体。
- 图片集中加载和缓存，不在每帧读盘；路径相对资源根解析。替换美术不能改变占格、移动、攻击或回溯语义。
- 抽象和模块必须有实际调用方。不提前创建空的插件、ECS、通用注册中心或未使用扩展层。结构性整改使用专用分支、分阶段验证与审查差异。

## 验证和维护

- 修改代码、测试或配置时，同步维护 `TASKS.md` 和 `CHANGELOG.md`；行为或操作变化同步到 `README.md`。
- 保留直接读取字体文件和字体扫描异常的回退逻辑，避免启动时再次因 Windows 字体注册表异常崩溃。
- 完成修改后运行 `python -m unittest discover -s tests -v`，并说明真实窗口与无窗口测试的验证边界。
- 修改规则、场景、几何或棋盘视图后，另运行 `python -S -m unittest discover -s tests -p test_core.py -v`，保证无第三方包时仍可运行。不要为兼容旧测试把 Pygame 加回核心。
- 修改协调、动作或完整视图后，另运行 `python -S -m unittest discover -s tests -p test_controller.py -v`。CI 在安装依赖前执行这两组检查。
- 保留原有行为覆盖；接口迁移时可调整测试夹具，不为保留旧字段访问而保留架构漏洞。新增架构边界在相应阶段就加入检查，不推迟到最终验收。
- 使用 `python scripts/export_source.py` 更新 `SOURCE.md`，再用 `python scripts/export_source.py --check` 检查一致性。
- 不提交虚拟环境、缓存、安装器、凭据或 `dist/`、`.delivery/` 中的生成文件。`artifacts/*.png` 是随文档交付的运行截图。
