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

校验器检查 SHA256、ZIP CRC、路径、版本与指定提交，然后在临时目录解压，使用调用者已有 Python/Pygame 离线执行 SOURCE 一致性、`main.py --help`、六项 M5 与七项透视集成验收。通过不代表安装了独立运行时，也不代表人工点击验收；完整回归在打包前执行。已发布 v0.2.0 保留其原始六项验收脚本；未发布透视扩展在当前提交中另纳入新验收，不覆盖已发布附件。

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
