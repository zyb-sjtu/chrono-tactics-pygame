# 完整项目源码

本文件由 `python scripts/export_source.py` 生成。包含项目全部文本源码、配置和文档；不包含自身、截图、虚拟环境、缓存及压缩包。

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
      - name: Install dependencies
        run: python -m pip install -r requirements.txt
      - name: Check source bundle
        run: python scripts/export_source.py --check
      - name: Run regression tests
        run: python -m unittest discover -s tests -v
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
# 项目维护约定

- 这是离线 Python/Pygame 战棋原型。保留无外部美术资源的绘制方式；新增玩法按用户需求推进。
- 业务规则放在 `tactics/battle.py`，空间与路径规则放在 `tactics/board.py`，动画放在 `tactics/effects.py`；避免将规则塞进主循环。
- 修改代码、测试或配置时，同步维护 `TASKS.md` 和 `CHANGELOG.md`；行为或操作变化同步到 `README.md`。
- 保留直接读取字体文件和字体扫描异常的回退逻辑，避免启动时再次因 Windows 字体注册表异常崩溃。
- 完成修改后运行 `python -m unittest discover -s tests -v`，并说明真实窗口与无窗口测试的验证边界。
- 使用 `python scripts/export_source.py` 更新 `SOURCE.md`，再用 `python scripts/export_source.py --check` 检查一致性。
- 不提交虚拟环境、缓存、安装器、凭据或 `dist/`、`.delivery/` 中的生成文件。`artifacts/*.png` 是随文档交付的运行截图。
````

## CHANGELOG.md

````markdown
# 更新记录

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

仓库名称：`chrono-tactics-pygame`，当前版本：`0.1.0`。

项目仓库：[zyb-sjtu/chrono-tactics-pygame](https://github.com/zyb-sjtu/chrono-tactics-pygame)。这是私有仓库，需要登录有权限的 GitHub 账号访问。

使用 Python 和 Pygame 绘制，运行时不访问网络，不需要外部美术资源。棋盘保持 8×8，每格 64×64 像素；为展示属性和回合信息，侧栏扩为 384 像素，窗口为 896×512。

## 运行

当前机器已经配置好独立环境，无需激活或重新安装：

```powershell
cd E:\gamedesign
.\.venv\Scripts\python.exe main.py
```

如果旧版窗口还开着，请先关闭，再执行以上命令。

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

- 3 个蓝色圆形友方与 3 个红色方形木桩均为单位，具有当前生命、最大生命、攻击、防御、速度、移动力。侧栏显示 `生命: 80/100` 这样的当前值/上限格式，棋盘单位下方显示血条。数值在 `tactics/models.py` 中配置，暂为功能演示占位值。
- 入场时将双方单位按速度从高到低排序，同速按入场顺序排列。每轮各行动一次，全部行动后进入下一轮，按相同顺序继续。
- 每次行动分为**一次移动 → 一次攻击**。可以跳过移动、跳过攻击，或直接结束行动；成功攻击后，动画播放完毕再交接给下一位。
- 移动和攻击均按上下左右四方向计算，不允许斜走或斜向攻击。
- 移动目的地可以是移动力步数内的任意可达空格，按实际通路步数计算。障碍、友方和敌方单位均不能穿过或重叠。即使没有用满步数，也消耗本次移动机会，不能分段多次移动。
- 攻击仅能锁定距离 1 格的敌方单位，不能攻击自己、同阵营、斜向或更远的单位。必须先完成或跳过移动，才能攻击。
- 伤害为**攻击属性的 100%**，当前防御属性不减伤。例如攻击 10 对生命 100/100 的目标造成 10 点伤害，生命变为 90/100。伤害跳字显示攻击结算值，持续约 0.9 秒并向上浮动淡出；过量伤害下生命最低为 0。
- 生命归零即被击杀：播放约 0.65 秒的闪烁、缩小、碎点扩散和淡出动画，然后在棋盘消失。被击杀单位不再阻挡路径、不能被选为目标，也不会再次行动。
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
├── tactics\
│   ├── __init__.py
│   ├── settings.py          # 棋盘和窗口尺寸
│   ├── models.py            # 双方单位属性、初始位置、障碍
│   ├── board.py             # 格子几何、BFS 可达范围、绘制
│   ├── battle.py            # 伤害、击杀、速度队列、回合快照与回溯
│   ├── effects.py           # 伤害跳字、几何击杀动画、逐帧更新
│   ├── panel.py             # 字体回退、属性栏、按钮、日志和队列
│   └── game.py              # 鼠标/键盘事件、主循环、退出清理
├── tests\
│   ├── test_battle.py       # 11 项战斗规则检查，无需创建窗口
│   ├── test_game.py         # 11 项窗口交互、绘制与字体检查
│   ├── test_effects.py      # 7 项动画、按键、血量显示和退出检查
│   └── test_rewind.py       # 12 项回溯、击杀及行动顺序检查
├── artifacts\               # 实际运行截图，不是游戏资源
│   ├── initial.png          # 开局移动范围
│   ├── selected.png         # 移动后可攻击目标
│   ├── damage_popup.png     # 实际攻击 10 的跳字
│   ├── after_attack.png     # 木桩生命 90/100
│   ├── enemy_turn.png       # 红方手动回合
│   ├── rewind.png           # 回溯后恢复位置和血量
│   ├── defeat.png           # 击杀动画中间帧
│   ├── defeat_disappeared.png # 击杀动画后消失
│   ├── defeat_result.png    # 击杀后交接回合
│   └── defeat_rewind.png    # 回溯恢复被击杀单位
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
New-Item -ItemType Directory -Force dist
git archive --format=zip --prefix=chrono-tactics-pygame/ --output=dist/chrono-tactics-pygame-v0.1.0.zip HEAD
```

源码包包含运行代码、测试、文档、配置和截图，不包含 `.venv`、缓存或凭据；解压后按上面的新机器安装步骤创建环境。这是 Python 源码包，未构建独立 EXE。

## 验证记录

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

2026-10-22，本机 Python 3.9.1 / Pygame 2.6.1 / SDL 2.28.4 实测 **41 项检查全部通过，退出码 0**。覆盖速度和同速顺序、四方向范围、路径阻挡、移动次数、敌我与攻击距离限制、攻击 100% 结算及忽略防御、过量伤害归零、跳字生命周期、动画期间锁定操作及正常关闭、实际画面中击杀形体消失、死亡后的行动顺序、连续和跨轮回溯、回溯恢复已死单位与当前/最大生命、回溯战斗结束状态，以及原有窗口和字体回退。

另外通过 `main.py` 实际入口创建窗口，使用 `windows` 显示驱动向事件队列投递鼠标和键盘事件，验证了两条完整流程，均退出码 0：默认配置下“移动 → 攻击 10 → 跳字 → 查看 90/100 → 红方回合 → 连续回溯”；测试场景下“攻击生命 5 的目标 → 击杀动画 → 形体消失 → 下一回合 → 回溯复活”。击杀场景仅在验证进程中设置目标生命为 5，没有改动游戏默认初始数据。已保存截图并查看跳字、扣血、击杀动画、消失和复活的实际画面。这是自动投递事件验证，并非人工鼠标逐次操作；其他系统尚未实测。

保留字体问题修复：优先直接加载 Windows 字体文件，失败后再扫描系统字体；扫描抛出 TypeError、OSError、ValueError 或 pygame.error 时，回退到 Pygame 内置字体与英文界面。不修改系统字体或注册表。

自动测试配置位于 [.github/workflows/ci.yml](.github/workflows/ci.yml)，使用虚拟显示驱动执行回归检查；它不能替代实际窗口的显示效果检查。远程运行结果见仓库 Actions 页面。CI 使用的动作版本参照 [checkout](https://github.com/actions/checkout) 和 [setup-python](https://github.com/actions/setup-python) 官方用法。

![伤害跳字](artifacts/damage_popup.png)

![实际扣血和当前/最大生命](artifacts/after_attack.png)

![击杀动画中间帧](artifacts/defeat.png)
````

## TASKS.md

````markdown
# 项目进度

当前版本：`0.1.0`。仅记录已经实现的内容；后续功能在收到需求后增加。

| ID | 状态 | 内容 |
| --- | --- | --- |
| BOARD-01 | 已完成 | 8×8 棋盘，每格 64×64，无外部美术资源 |
| UNIT-01 | 已完成 | 双方各 3 个单位、固定障碍、点击查看属性 |
| TURN-01 | 已完成 | 速度排序、四方向移动、相邻攻击、手动操作双方、跳过与交接 |
| COMBAT-01 | 已完成 | 当前/最大生命与血条，攻击力 100% 伤害，伤害跳字 |
| COMBAT-02 | 已完成 | 击杀动画、消失、死亡单位退出队列、一方全灭结束战斗 |
| REWIND-01 | 已完成 | 回溯上一单位行动开始前、连续回溯、恢复死亡单位和战斗状态 |
| FIX-01 | 已完成 | Windows 系统字体扫描异常回退，保留英文降级界面 |
| QA-01 | 已完成 | 41 项回归检查、Windows 实际窗口流程验证与截图 |
| DELIVERY-01 | 已完成 | 运行文档、源码汇总生成脚本、忽略规则和自动测试配置 |

CI 配置覆盖 Windows / Linux 与 Python 3.9 / 3.12。远程执行结果以 GitHub Actions 为准，配置存在不代表运行已通过。

当前没有 AI、网络、存档或独立 EXE。数值仍为演示占位值，防御暂不参与伤害计算。
````

## main.py

```python
"""Run the offline tactics prototype."""

from tactics.game import Game


if __name__ == "__main__":
    Game().run()
```

## requirements.txt

```text
pygame==2.6.1
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
    for folder in ("tactics", "tests", "scripts", ".github"):
        files.update(path for path in (ROOT / folder).rglob("*")
                     if path.is_file() and path.suffix in SUFFIXES)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def render():
    parts = ["# 完整项目源码\n\n本文件由 `python scripts/export_source.py` 生成。包含项目全部文本源码、配置和文档；不包含自身、截图、虚拟环境、缓存及压缩包。\n"]
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

## tactics/__init__.py

```python
"""Offline tactics prototype with manually controlled battle turns."""
```

## tactics/battle.py

```python
"""Speed order and one move / one adjacent attack per turn; no AI."""

from dataclasses import asdict, dataclass
from typing import Optional

from .models import Unit


@dataclass(frozen=True)
class AttackResult:
    actor: Unit
    target: Unit
    damage: int
    killed: bool


@dataclass(frozen=True)
class TurnSnapshot:
    units: tuple
    order: tuple
    index: int
    round_number: int
    phase: str
    log: tuple
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
        return TurnSnapshot(tuple((unit, asdict(unit)) for unit in self.board.units),
                            self.entry_order, self.index, self.round_number,
                            self.phase, tuple(self.log), self.winner)

    def undo(self):
        """Restore the previous unit turn's start, discarding this turn as well."""
        if not self.can_undo:
            return False
        self.history.pop()
        snapshot = self.history[-1]
        self.board.units = tuple(unit for unit, _ in snapshot.units)
        for unit, values in snapshot.units:
            for name, value in values.items():
                setattr(unit, name, value)
        self.entry_order = snapshot.order
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
        target.health = max(0, target.health - damage)
        self.pending_attack = AttackResult(actor, target, damage, not target.alive)
        self.phase = "resolving"
        self.notify("{} 攻击 {}，造成 {} 点伤害".format(actor.name, target.name, damage),
                    "{} attacked {} for {} damage.".format(actor.uid, target.uid, damage))
        if not target.alive:
            self.notify("{} 被击杀".format(target.name), "{} was defeated.".format(target.uid))
        return True

    def finish_attack(self):
        """Called once the presentation has finished its attack/death effects."""
        if self.phase != "resolving":
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
"""Board geometry, blocked-path movement range, and rendering."""

from collections import deque

import pygame

from .models import OBSTACLES, create_allies, create_enemies
from .settings import BOARD_HEIGHT, BOARD_WIDTH, CELL_SIZE, COLS, ROWS


class Board:
    def __init__(self):
        self.allies = create_allies()
        self.enemies = create_enemies()
        self.units = self.allies + self.enemies
        self.obstacles = OBSTACLES
        self.label_font = None

    @staticmethod
    def cell_at(position):
        x, y = position
        if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
            return x // CELL_SIZE, y // CELL_SIZE
        return None

    def unit_at(self, cell):
        return next((unit for unit in self.living_units if unit.cell == cell), None)

    @property
    def living_units(self):
        # Keep the complete roster for undo; defeated units leave play immediately.
        return tuple(unit for unit in self.units if unit.alive)

    @staticmethod
    def neighbors(cell):
        col, row = cell
        return tuple((x, y) for x, y in ((col - 1, row), (col + 1, row),
                                        (col, row - 1), (col, row + 1))
                     if 0 <= x < COLS and 0 <= y < ROWS)

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

    @staticmethod
    def rect(cell):
        col, row = cell
        return pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    def draw(self, surface, selected, battle):
        if self.label_font is None:
            self.label_font = pygame.font.Font(None, 20)
        for row in range(ROWS):
            for col in range(COLS):
                color = (42, 55, 70) if (row + col) % 2 else (48, 63, 79)
                rect = self.rect((col, row))
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (66, 81, 97), rect, 1)

        active = battle.active_unit
        if active is not None and selected is active and battle.phase in ("move", "attack"):
            cells = battle.movement_range() if battle.phase == "move" else self.neighbors(active.cell)
            color = (54, 109, 103) if battle.phase == "move" else (125, 65, 74)
            for cell in cells:
                if cell not in self.obstacles:
                    pygame.draw.rect(surface, color, self.rect(cell).inflate(-4, -4), border_radius=4)
            for target in battle.attack_targets():
                pygame.draw.rect(surface, (255, 161, 128), self.rect(target.cell).inflate(-5, -5), 3)

        for cell in self.obstacles:
            block = self.rect(cell).inflate(-12, -12)
            pygame.draw.rect(surface, (111, 124, 135), block, border_radius=5)
            pygame.draw.line(surface, (146, 157, 166), block.topleft, block.bottomright, 2)
            pygame.draw.line(surface, (146, 157, 166), block.topright, block.bottomleft, 2)

        for unit in self.living_units:
            rect = self.rect(unit.cell)
            if unit.team == "ally":
                pygame.draw.circle(surface, (69, 156, 239), rect.center, 21)
                pygame.draw.circle(surface, (146, 207, 255), rect.center, 21, 2)
            else:
                block = rect.inflate(-24, -24)
                pygame.draw.rect(surface, (231, 88, 94), block, border_radius=3)
                pygame.draw.rect(surface, (255, 153, 146), block, 2, border_radius=3)
            label = self.label_font.render(unit.uid, True, (255, 255, 255))
            surface.blit(label, label.get_rect(center=rect.center))
            if unit is active:
                pygame.draw.rect(surface, (255, 219, 116), rect.inflate(-4, -4), 3)
            if unit is selected:
                pygame.draw.circle(surface, (246, 248, 252), rect.center, 27, 2)
            bar = pygame.Rect(rect.x + 10, rect.y + 58, 44, 4)
            pygame.draw.rect(surface, (26, 31, 39), bar)
            fill = bar.copy()
            fill.width = round(bar.width * min(1, unit.health / max(1, unit.max_health)))
            pygame.draw.rect(surface, (105, 218, 153), fill)
```

## tactics/effects.py

```python
"""Non-blocking damage popups and geometric defeat animations."""

import math
from dataclasses import dataclass

import pygame

from .settings import BOARD_HEIGHT, BOARD_WIDTH, CELL_SIZE

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


class CombatEffects:
    def __init__(self):
        self.damage_texts = []
        self.deaths = []
        self.damage_font = pygame.font.Font(None, 32)
        self.label_font = pygame.font.Font(None, 20)

    @property
    def busy(self):
        return bool(self.damage_texts or self.deaths)

    def play_attack(self, result):
        self.damage_texts.append(DamageText(result.target.cell, result.damage))
        if result.killed:
            self.deaths.append(DeathEffect(result.target.cell, result.target.team, result.target.uid))

    def clear(self):
        self.damage_texts.clear()
        self.deaths.clear()

    def update(self, elapsed):
        for effect in self.damage_texts + self.deaths:
            effect.age += max(0, elapsed)
        self.damage_texts = [effect for effect in self.damage_texts if effect.age < DAMAGE_DURATION]
        self.deaths = [effect for effect in self.deaths if effect.age < DEATH_DURATION]

    def draw(self, surface):
        old_clip = surface.get_clip()
        surface.set_clip((0, 0, BOARD_WIDTH, BOARD_HEIGHT))
        for effect in self.deaths:
            progress = effect.age / DEATH_DURATION
            layer = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            size = max(4, round(42 * (1 - progress * 0.6)))
            color = (69, 156, 239) if effect.team == "ally" else (231, 88, 94)
            if int(effect.age * 20) % 2 == 0:
                color = (255, 224, 192)
            center = (CELL_SIZE // 2, CELL_SIZE // 2)
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
                radius = 8 + 23 * progress
                point = (round(center[0] + math.cos(angle) * radius),
                         round(center[1] + math.sin(angle) * radius))
                pygame.draw.circle(layer, (255, 192, 132), point, max(1, round(3 * (1 - progress))))
            layer.set_alpha(round(255 * (1 - progress)))
            surface.blit(layer, (effect.cell[0] * CELL_SIZE, effect.cell[1] * CELL_SIZE))

        for effect in self.damage_texts:
            progress = effect.age / DAMAGE_DURATION
            text = "-{}".format(effect.amount)
            label = self.damage_font.render(text, True, (255, 217, 150))
            shadow = self.damage_font.render(text, True, (37, 21, 28))
            alpha = round(255 * min(1, (1 - progress) * 3))
            label.set_alpha(alpha)
            shadow.set_alpha(alpha)
            x = effect.cell[0] * CELL_SIZE + CELL_SIZE // 2
            y = max(5, effect.cell[1] * CELL_SIZE + 8 - round(progress * 30))
            rect = label.get_rect(midtop=(x, y))
            surface.blit(shadow, rect.move(2, 2))
            surface.blit(label, rect)
        surface.set_clip(old_clip)
```

## tactics/game.py

```python
"""Window lifecycle, input dispatch, and the main render loop."""

import pygame

from .board import Board
from .battle import Battle
from .effects import CombatEffects
from .panel import InfoPanel
from .settings import FPS, WINDOW_SIZE


class Game:
    def __init__(self):
        # The prototype needs only display and fonts, so do not initialize audio.
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Grid Tactics - Battle Prototype")
        self.clock = pygame.time.Clock()
        self.board = Board()
        self.battle = Battle(self.board)
        self.panel = InfoPanel()
        self.effects = CombatEffects()
        self.selected = self.battle.active_unit
        self.running = True

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif self.battle.phase == "resolving":
            return
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.undo()
            elif event.key == pygame.K_SPACE:
                self.battle.skip_phase()
                self.selected = self.battle.active_unit
            elif event.key == pygame.K_RETURN:
                self.battle.end_turn()
                self.selected = self.battle.active_unit
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.panel.undo_button.collidepoint(event.pos):
                self.undo()
            elif self.panel.skip_button.collidepoint(event.pos):
                self.battle.skip_phase()
                self.selected = self.battle.active_unit
            elif self.panel.end_button.collidepoint(event.pos):
                self.battle.end_turn()
                self.selected = self.battle.active_unit
            else:
                self.board_click(event.pos)

    def board_click(self, position):
        if self.battle.phase == "resolving":
            return
        cell = self.board.cell_at(position)
        if cell is None:
            return
        unit = self.board.unit_at(cell)
        if self.battle.active_unit is not None and self.selected is self.battle.active_unit:
            if self.battle.move(cell):
                return
            if unit is not None and self.battle.attack(unit):
                self.effects.play_attack(self.battle.pending_attack)
                return
        if unit is not None:
            self.selected = unit

    def undo(self):
        if not self.battle.undo():
            return False
        self.effects.clear()
        self.selected = self.battle.active_unit
        return True

    def update(self, elapsed):
        self.effects.update(elapsed)
        if self.battle.phase == "resolving" and not self.effects.busy:
            self.battle.finish_attack()
            self.selected = self.battle.active_unit

    def draw(self):
        self.board.draw(self.screen, self.selected, self.battle)
        self.effects.draw(self.screen)
        self.panel.draw(self.screen, self.selected, self.battle)
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

## tactics/models.py

```python
"""Unit attributes and the initial scenario. All numbers are placeholders."""

from dataclasses import dataclass
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

    @property
    def alive(self):
        return self.health > 0


def create_allies():
    return (
        Unit("A1", "先锋", "ally", "近卫", (1, 1), speed=12),
        Unit("A2", "斥候", "ally", "侦察", (1, 3), health=80, speed=14, movement=4),
        Unit("A3", "卫士", "ally", "守备", (2, 6), health=120, max_health=120, speed=10, movement=2),
    )


DUMMIES = ((6, 1), (5, 4), (6, 6))
OBSTACLES = frozenset(((3, 1), (3, 2), (3, 3), (4, 5), (4, 6)))


def create_enemies():
    return tuple(
        Unit("D{}".format(index), "木桩{}".format(index), "enemy", "训练木桩", cell, speed=speed)
        for index, (cell, speed) in enumerate(zip(DUMMIES, (11, 9, 8)), start=1)
    )
```

## tactics/panel.py

```python
"""System-font text and the selected-unit sidebar; no asset files required."""

import os
from pathlib import Path

import pygame

from .settings import BOARD_HEIGHT, BOARD_WIDTH, PANEL_WIDTH


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
    def __init__(self):
        fonts, self.chinese = load_fonts()
        self.title_font, self.font, self.small_font = fonts
        self.skip_button = pygame.Rect(BOARD_WIDTH + 24, 284, 162, 38)
        self.end_button = pygame.Rect(BOARD_WIDTH + 198, 284, 162, 38)
        self.undo_button = pygame.Rect(BOARD_WIDTH + 208, 14, 152, 32)

    def text(self, surface, value, y, color=(220, 230, 241), small=False, title=False, x=None, width=None):
        font = self.title_font if title else self.small_font if small else self.font
        x = BOARD_WIDTH + 24 if x is None else x
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

    def draw(self, surface, selected, battle):
        pygame.draw.rect(surface, (21, 30, 42), (BOARD_WIDTH, 0, PANEL_WIDTH, BOARD_HEIGHT))
        cn = self.chinese
        actor = battle.active_unit
        name = (actor.name if cn else actor.uid) if actor is not None else ""
        moving = battle.phase == "move"
        self.text(surface, ("第 {} 回合" if cn else "ROUND {:02d}").format(battle.round_number),
                  14, title=True, width=182)
        self.button(surface, self.undo_button, "回溯 [退格]" if cn else "Undo [Backspace]", battle.can_undo)
        if battle.finished:
            winners = {"ally": ("蓝方获胜", "BLUE WINS"), "enemy": ("红方获胜", "RED WINS"),
                       "draw": ("平局", "DRAW")}
            self.text(surface, winners[battle.winner][0 if cn else 1], 54, (255, 219, 116))
            status = "战斗结束 · 可以回溯最后一次行动" if cn else "Battle ended. Undo is available."
        else:
            self.text(surface, ("当前行动：{} [{}]" if cn else "Active: {} [{}]").format(name, actor.uid),
                      54, (255, 219, 116))
        if not battle.finished and cn:
            phase = {"move": "移动阶段", "attack": "攻击阶段", "resolving": "攻击结算中"}[battle.phase]
            team = "蓝方" if actor.team == "ally" else "红方"
            status = "{} · {} · 移动 {} / 攻击 {}".format(team, phase, int(moving), int(battle.phase != "resolving"))
        elif not battle.finished:
            status = "{} / {} / Move {} / Attack {}".format(actor.team.upper(), battle.phase.upper(),
                                                           int(moving), int(battle.phase != "resolving"))
        self.text(surface, status, 86, (132, 159, 185), small=True)
        pygame.draw.line(surface, (60, 77, 96), (BOARD_WIDTH + 24, 116), (BOARD_WIDTH + PANEL_WIDTH - 24, 116))
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
                x = BOARD_WIDTH + 24 + (index % 2) * 174
                self.text(surface, "{}: {}".format(chinese if cn else english, value),
                          192 + (index // 2) * 27, x=x, width=162)

        skip = ("跳过移动 [空格]" if moving else "跳过攻击 [空格]") if cn else (
            "Skip move [Space]" if moving else "Skip attack [Space]")
        enabled = battle.phase in ("move", "attack")
        self.button(surface, self.skip_button, skip, enabled)
        self.button(surface, self.end_button, "结束行动 [回车]" if cn else "End turn [Enter]", enabled)
        if battle.phase == "resolving":
            hint = "攻击动画播放中，结束后继续" if cn else "Resolving attack. Please wait."
        elif battle.finished:
            hint = "战斗结束，可回溯上一单位行动" if cn else "Battle ended. Undo the previous turn."
        elif selected is not actor:
            hint = "点击金框单位，继续当前行动" if cn else "Click the gold-frame unit to act."
        elif moving:
            hint = "绿色：可移动；点击高亮格确认" if cn else "Green cells: click once to move."
        else:
            hint = "红色：攻击范围；点击敌方攻击" if cn else "Red range: click an enemy to attack."
        self.text(surface, hint, 334, (166, 207, 191), small=True)
        self.text(surface, "伤害 = 攻击 × 100% · 退格回溯" if cn else "Damage = ATK x 100% / Backspace undo",
                  357, (132, 159, 185), small=True)
        for index, message in enumerate(battle.log):
            self.text(surface, message[0 if cn else 1], 385 + index * 21, small=True)

        self.text(surface, "行动顺序（速度↓，金色为当前）" if cn else "ORDER / SPD descending / gold = active",
                  433, (132, 159, 185), small=True)
        for index, unit in enumerate(battle.order):
            name = unit.name if cn else unit.uid
            color = (255, 219, 116) if unit is actor else (161, 178, 196)
            label = "{}.{}({})".format(index + 1, name, unit.speed)
            self.text(surface, label, 459 + (index // 3) * 25, color, small=True,
                      x=BOARD_WIDTH + 24 + (index % 3) * 114, width=108)
```

## tactics/settings.py

```python
"""Shared layout settings. Board coordinates are (column, row), zero based."""

COLS = 8
ROWS = 8
CELL_SIZE = 64
BOARD_WIDTH = COLS * CELL_SIZE
BOARD_HEIGHT = ROWS * CELL_SIZE
PANEL_WIDTH = 384
WINDOW_SIZE = (BOARD_WIDTH + PANEL_WIDTH, BOARD_HEIGHT)
FPS = 60
```

## tests/test_battle.py

```python
"""Rule checks without a window: speed order, paths, turn limits, damage."""

import unittest

from tactics.battle import Battle
from tactics.board import Board


class BattleChecks(unittest.TestCase):
    def setUp(self):
        self.board = Board()
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
        self.assertTrue(self.battle.finish_attack())
        self.assertIs(self.battle.active_unit, self.board.allies[0])
        self.assertEqual(self.battle.phase, "move")
        self.assertFalse(self.battle.attack(target))
        self.assertFalse(self.battle.finish_attack())

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
        self.battle.finish_attack()
        self.assertEqual(self.battle.index, 3)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_effects.py

```python
"""Actual window rendering, animation lifecycle, input lock and rewind controls."""

import unittest
from unittest.mock import patch

import pygame

from tactics.battle import Battle
from tactics.game import Game


class CombatInteractionChecks(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.actor = self.game.battle.active_unit
        self.target = self.game.board.enemies[1]

    def tearDown(self):
        pygame.quit()

    def click(self, position):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    def start_attack(self, lethal=False):
        if lethal:
            self.target.health = 5
            self.game.battle = Battle(self.game.board)
            self.game.selected = self.game.battle.active_unit
        self.click(self.game.board.rect((4, 4)).center)
        self.click(self.game.board.rect(self.target.cell).center)

    def test_damage_popup_and_controls_are_locked_until_effect_finishes(self):
        self.start_attack()
        self.assertEqual(self.game.effects.damage_texts[0].amount, self.actor.attack)
        self.game.update(0.2)
        self.assertAlmostEqual(self.game.effects.damage_texts[0].age, 0.2)
        self.game.draw()
        for key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
            self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        for rect in (self.game.panel.skip_button, self.game.panel.end_button, self.game.panel.undo_button):
            self.click(rect.center)
        self.click(self.game.board.rect(self.target.cell).center)
        self.assertEqual(self.target.health, self.target.max_health - self.actor.attack)
        self.assertIs(self.game.battle.active_unit, self.actor)
        self.assertEqual(self.game.battle.phase, "resolving")
        self.game.update(1.0)
        self.assertFalse(self.game.effects.busy)
        self.assertEqual(self.game.battle.phase, "move")
        self.assertEqual(self.game.battle.active_unit.uid, "A1")

    def test_defeated_body_animates_then_disappears_from_actual_surface(self):
        self.start_attack(lethal=True)
        self.assertEqual(len(self.game.effects.deaths), 1)
        self.assertFalse(self.target.alive)
        self.game.draw()
        center = self.game.board.rect(self.target.cell).center
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
        self.click(self.game.panel.undo_button.center)
        self.assertEqual(self.target.health, 5)
        self.assertIs(self.game.board.unit_at(self.target.cell), self.target)
        self.assertIs(self.game.battle.active_unit, self.actor)
        self.assertIs(self.game.selected, self.actor)
        self.assertEqual(self.actor.cell, (1, 3))
        self.assertFalse(self.game.effects.busy)
        self.game.draw()

    def test_backspace_rewinds_previous_turn_and_discards_partial_current_move(self):
        self.start_attack()
        self.game.update(1.0)
        self.click(self.game.board.rect((0, 1)).center)
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        self.assertEqual(self.game.battle.active_unit.uid, "A2")
        self.assertEqual(self.target.health, self.target.max_health)
        self.assertEqual(self.game.board.allies[0].cell, (1, 1))
        self.assertEqual(self.game.battle.phase, "move")

    def test_finished_battle_is_renderable_and_can_be_undone(self):
        self.game.board.units = (self.actor, self.target)
        self.start_attack(lethal=True)
        self.game.update(1.0)
        self.assertTrue(self.game.battle.finished)
        self.game.draw()
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertTrue(self.game.battle.finished)
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        self.assertFalse(self.game.battle.finished)
        self.assertTrue(self.target.alive)
        self.game.draw()

    def test_health_panel_shows_current_and_maximum(self):
        self.actor.health = 800
        self.actor.max_health = 1000
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


if __name__ == "__main__":
    unittest.main()
```

## tests/test_game.py

```python
"""Run with: python -m unittest discover -s tests -v"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from tactics.game import Game
from tactics.panel import InfoPanel
from tactics.settings import BOARD_HEIGHT, BOARD_WIDTH, CELL_SIZE, WINDOW_SIZE


class GameChecks(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    def click(self, position, button=1):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=position, button=button))

    def test_layout_and_initial_scenario(self):
        self.assertEqual(WINDOW_SIZE, (896, 512))
        self.assertEqual(CELL_SIZE, 64)
        self.assertEqual((BOARD_WIDTH, BOARD_HEIGHT), (512, 512))
        cells = [unit.cell for unit in self.game.board.units] + list(self.game.board.obstacles)
        self.assertEqual(len(self.game.board.allies), 3)
        self.assertEqual(len(self.game.board.enemies), 3)
        self.assertTrue(self.game.board.obstacles)
        self.assertEqual(len(cells), len(set(cells)))
        self.assertTrue(all(0 <= col < 8 and 0 <= row < 8 for col, row in cells))

    def test_inspect_each_unit_without_changing_turn(self):
        actor = self.game.battle.active_unit
        for unit in self.game.board.units:
            self.click(self.game.board.rect(unit.cell).center)
            self.assertIs(self.game.selected, unit)
            self.assertIs(self.game.battle.active_unit, actor)
            self.game.draw()

    def test_invalid_terrain_and_outside_clicks_do_not_consume_action(self):
        actor = self.game.battle.active_unit
        start = actor.cell
        positions = [(511, 511), (530, 20), (-1, 0), (0, 512)]
        positions += [self.game.board.rect(cell).center for cell in self.game.board.obstacles]
        for position in positions:
            self.click(position)
            self.assertEqual(actor.cell, start)
            self.assertEqual(self.game.battle.phase, "move")
        self.assertEqual(self.game.board.cell_at((511, 511)), (7, 7))

    def test_right_click_does_not_change_selection_or_scenario(self):
        before = tuple(unit.cell for unit in self.game.board.units)
        selected = self.game.selected
        self.click(self.game.board.rect((4, 4)).center, button=3)
        self.assertIs(self.game.selected, selected)
        self.assertEqual(tuple(unit.cell for unit in self.game.board.units), before)

    def test_mouse_move_attack_and_turn_handoff(self):
        actor = self.game.battle.active_unit
        target = self.game.board.enemies[1]
        health = target.health
        self.click(self.game.board.rect((4, 4)).center)
        self.assertEqual(actor.cell, (4, 4))
        self.assertEqual(self.game.battle.phase, "attack")
        self.game.draw()
        self.click(self.game.board.rect(target.cell).center)
        self.assertEqual(target.health, health - actor.attack)
        self.assertEqual(self.game.battle.phase, "resolving")
        self.assertTrue(self.game.effects.busy)
        self.game.draw()
        self.game.update(1.0)
        self.assertIs(self.game.selected, self.game.battle.active_unit)
        self.assertIsNot(self.game.selected, actor)
        self.game.draw()

    def test_inspection_cannot_move_a_unit_out_of_turn(self):
        actor = self.game.battle.active_unit
        start = actor.cell
        other = self.game.board.allies[0]
        self.click(self.game.board.rect(other.cell).center)
        self.click(self.game.board.rect((4, 4)).center)
        self.assertEqual(actor.cell, start)
        self.assertEqual(other.cell, (1, 1))
        self.click(self.game.board.rect(actor.cell).center)
        self.click(self.game.board.rect((4, 4)).center)
        self.assertEqual(actor.cell, (4, 4))

    def test_keyboard_and_sidebar_skip_controls(self):
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.assertEqual(self.game.battle.phase, "attack")
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.game.battle.index, 1)
        self.click(self.game.panel.skip_button.center)
        self.assertEqual(self.game.battle.phase, "attack")
        self.click(self.game.panel.end_button.center)
        self.assertEqual(self.game.battle.index, 2)
        self.assertEqual(self.game.battle.active_unit.team, "enemy")
        self.assertIs(self.game.selected, self.game.battle.active_unit)
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
                game.selected = game.board.allies[0]
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

## tests/test_rewind.py

```python
"""Whole-turn rewind, defeated-unit restoration and stable initiative slots."""

from dataclasses import asdict
import unittest

from tactics.battle import Battle
from tactics.board import Board


class RewindAndDefeatChecks(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.battle = Battle(self.board)
        self.actor = self.battle.active_unit
        self.target = self.board.enemies[1]

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
        self.battle.finish_attack()
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
        self.battle.finish_attack()
        self.assertEqual(self.battle.active_unit.uid, "A3")

    def test_killing_next_actor_skips_the_dead_slot(self):
        enemy = self.board.enemies[0]
        enemy.cell = (2, 1)
        enemy.health = 5
        self.battle.end_turn()
        self.battle.skip_phase()
        self.battle.attack(enemy)
        self.battle.finish_attack()
        self.assertEqual(self.battle.active_unit.uid, "A3")

    def test_round_wrap_can_skip_a_dead_first_slot(self):
        self.actor.cell = (6, 5)
        self.actor.health = 5
        for _ in range(5):
            self.battle.end_turn()
        self.assertEqual(self.battle.active_unit.uid, "D3")
        self.battle.skip_phase()
        self.battle.attack(self.actor)
        self.battle.finish_attack()
        self.assertEqual(self.battle.active_unit.uid, "A1")
        self.assertEqual(self.battle.round_number, 2)

    def test_final_kill_finishes_after_effects_and_undo_revives_enemy(self):
        self.board.units = (self.actor, self.target)
        self.target.health = 5
        battle = Battle(self.board)
        battle.move((4, 4))
        battle.attack(self.target)
        self.assertFalse(battle.finished)
        battle.finish_attack()
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
        original_order = battle.order
        for _ in range(2):
            self.assertTrue(battle.move((4, 4)))
            self.assertTrue(battle.attack(self.target))
            battle.finish_attack()
            self.assertFalse(self.target.alive)
            self.assertTrue(battle.undo())
            self.assertTrue(self.target.alive)
            self.assertEqual(self.target.health, self.target.max_health)
            self.assertEqual((self.actor.health, self.actor.max_health), (800, 1000))
            self.assertEqual(battle.order, original_order)
            self.assertEqual(self.actor.cell, (1, 3))


if __name__ == "__main__":
    unittest.main()
```
