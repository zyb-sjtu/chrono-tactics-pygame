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
