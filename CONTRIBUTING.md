# 贡献与发布

## 开发

本项目是单文件标准库工具。`generate_roll_ramps.py` 是应用源码，`tests/` 检查生成行为，`scripts/release.py` 检查发布元数据并打包。
生成的 FDS 输入、缓存、日志、本地配置和构建结果不提交。没有第三方 Python 依赖，因此不维护依赖锁文件。

```bash
python -m unittest discover -s tests -v
python scripts/release.py
```

有图形桌面时，可设置环境变量 `FDS_GUI_TEST=1` 再执行测试，以检查完整文本、初始滚动位置和复制功能。没有图形桌面的 CI 默认跳过此项。
本工具没有参数式 CLI，导入及短时间代码生成是对应的无配置冒烟测试。

## 变更管理

先在 Issue 中说明背景、期望结果、验收标准和范围；小型更正可直接在 PR 中记录。
使用短生命周期分支，如 `fix/12-endpoint` 或 `feature/13-preview`，提交使用 `feat:`、`fix:`、`docs:`、`test:`、`chore:`。
PR 说明测试结果、用户可感知变化、兼容性和回滚方式；界面变化附截图或实际 UI 检查记录。
默认通过 Squash merge 合并。

## 分支与发布治理

- `main` 通过 PR 合并，要求 `CI Gate` 成功并解决全部审查讨论；禁止强制推送和删除。
- 单维护者初始阶段设置 0 个人工批准，维护者负责检查 PR 和 CI；这是一项明确的治理例外，增加维护者后应改为至少 1 个批准。
- 默认分支规则不设置管理员绕过。`v*` 标签禁止更新和删除；仅仓库管理员可创建发布标签。
- `VERSION` 是唯一版本事实来源；应用不另设版本常量，README 静态徽章、CHANGELOG 和发布说明必须匹配。
- 工作流只有 `contents: read` 权限；Dependabot 每周检查 GitHub Actions 更新。
- 已发布的标签、资产和版本不覆盖；修复使用新版本。

## 发布步骤

1. 创建 `release/vX.Y.Z` 分支，更新 `VERSION`、README 徽章、CHANGELOG 和 `docs/releases/vX.Y.Z.md`。
2. 运行上述验证及 `python scripts/release.py --build`，检查源码包与 SHA256；在仓库外执行本地路径复扫。
3. 推送分支并创建发布 PR，等待 CI 通过，再 Squash merge。
4. 同步 `main` 并等待该提交 CI 全绿；从该提交创建附注标签 `vX.Y.Z`，推送并等待标签 CI 全绿。
5. 在干净的 `main` 上重新执行 `python scripts/release.py --build`，创建 Release，上传 ZIP 和 SHA256 文件。Release 正文使用 `docs/releases/vX.Y.Z.md`。
6. 从 GitHub 重新读取 README、标签并下载 Release 资产，复核哈希、清单和敏感信息。

本项目只通过 GitHub 分发源码，不发布 PyPI/npm 包。首次初始化提交只建立仓库骨架，首个应用版本经发布 PR 合并。
