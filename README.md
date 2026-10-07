<div align="center">

# TieBaAutoSign

基于 GitHub Actions 的百度贴吧自动签到工具。

[![Baidu Tieba Auto Sign](https://github.com/AullChen/TieBaAutoSign/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/AullChen/TieBaAutoSign/actions/workflows/main.yml)

</div>

## 功能

- GitHub Actions 定时执行，无需常驻服务器。
- 支持单个或多个百度账号。
- 默认每天执行两次签到。
- 正常运行不写入 Git 历史；仅在出现错误时更新 `run.log`。
- 失败日志由 `github-actions[bot]` 提交，不计入个人贡献。
- 单独的月度 keepalive workflow 用于低频刷新仓库活动。
- 日志输出会主动隐藏已配置的 BDUSS、邮箱认证信息等敏感值。

## 快速开始

### 1. 准备仓库

Fork 或复制本仓库到自己的 GitHub 账户，并在仓库的 **Actions** 页面启用 GitHub Actions。

> 如果你使用的是 private repository，Actions 状态徽章只对有权限访问该仓库的用户可见。

### 2. 配置 BDUSS

进入：

`Settings → Secrets and variables → Actions → New repository secret`

创建：

| Name | 必需 | 说明 |
| --- | --- | --- |
| `BDUSS` | 是 | 百度登录会话中的 BDUSS。多个账号使用 `#` 分隔。 |

例如，多账号的值形式为：

`BDUSS_ACCOUNT_1#BDUSS_ACCOUNT_2`

BDUSS 等同于登录凭据的一部分，请始终保存为 GitHub Secret，不要写进 README、Issue、代码或普通配置文件。

### 3. 测试运行

进入 **Actions → Baidu Tieba Auto Sign → Run workflow** 手动执行一次。

执行成功后，之后会按计划自动运行。

## 运行计划

签到 workflow 使用：

`5 16,22 * * *`

GitHub Actions cron 使用 UTC，因此在 UTC+8 时区通常对应每天约 **00:05** 和 **06:05**。scheduled workflow 可能存在数分钟延迟。

月度维护 workflow 使用：

`37 20 1 * *`

它只更新 `.github/.keepalive`，提交者为 `github-actions[bot]`。该任务与签到状态分离，不会影响上方签到状态徽章。

## 日志与故障排查

### 正常运行

正常签到不会修改 `run.log`，也不会产生自动日志提交。详细输出可直接在对应的 GitHub Actions run 中查看。

### 失败运行

程序只把 `ERROR` / `CRITICAL` 级别信息写入 `run.log`。如果文件发生变化，workflow 会使用 `github-actions[bot]` 创建：

`chore(log): record failed sign-in`

因此 Git 历史中只会保留真正需要排查的异常记录。

常见排查顺序：

1. 打开 Actions 中失败的 `Baidu Tieba Auto Sign` run。
2. 查看 `Start Sign` 步骤的输出。
3. 查看仓库中的 `run.log`。
4. 如果提示 BDUSS 无效或登录状态失效，重新获取会话并更新 Secret。
5. 若百度接口出现临时网络错误，可等待下一次计划任务或手动重试。

## 安全说明

- 不要在任何公开位置提交 BDUSS。
- 不要把 BDUSS 放在 workflow YAML、README 或普通环境配置文件中。
- 本项目会对控制台和持久化错误日志中的已配置凭据做基础脱敏。
- 如果怀疑 BDUSS 已泄露，请立即在百度侧刷新登录状态并更新 GitHub Secret。
- 详细建议见 [SECURITY.md](SECURITY.md)。

## 项目结构

```text
.
├── .github/
│   └── workflows/
│       ├── main.yml
│       └── keepalive.yml
├── img/
├── main.py
├── requirements.txt
├── run.log
├── README.md
├── SECURITY.md
├── LICENSE
└── NOTICE
```

## 来源与许可

本项目基于 [gwtak/TieBaSign](https://github.com/gwtak/TieBaSign) 演进而来。

原始仓库在本次整理时没有声明开源许可证，因此本仓库不能将第三方原始代码重新授权为 MIT。由本仓库维护者独立新增或修改、且不受第三方权利限制的部分采用 MIT License；具体边界与来源说明见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。

## 免责声明

本项目仅用于个人自动化与学习。请自行确保使用方式符合百度贴吧、GitHub Actions 以及你所在地区适用的规则与条款。接口、登录策略或平台限制变化都可能导致自动签到失效。
