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
