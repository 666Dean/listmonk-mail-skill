# listmonk-mail：Codex 邮件管理 Skill

用自然语言管理 listmonk 名单、导入收件人、创建个性化邮件草稿、查询活动结果，配置阿里企业邮箱 SMTP 并排查 Windows 本地启动问题。

**MIT 开源，可使用、修改和分发。** 这是独立社区技能，与 listmonk、阿里云或 OpenAI 没有官方隶属关系。技能本身免费，不包含邮箱、服务器或邮件发送额度；第三方服务费用另计。

## 安装

克隆仓库，将 `skills/listmonk-mail` 整个目录复制到个人技能目录 `~/.codex/skills/listmonk-mail`（设置 CODEX_HOME 时使用该目录下的 skills）。如果使用其他技能加载器，请按其目录规范安装。

Windows PowerShell 示例，仓库克隆到你选择的工作目录后执行：

```powershell
$skillsRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex\skills' }
$targetSkill = Join-Path $skillsRoot 'listmonk-mail'
if (Test-Path -LiteralPath $targetSkill) { throw '目标技能已存在，请先查看差异再更新。' }
Copy-Item -LiteralPath '.\skills\listmonk-mail' -Destination $targetSkill -Recurse
```

重新打开聊天或刷新技能列表后，用 `$listmonk-mail` 调用。也可直接把 SKILL.md 提供给支持 Agent Skills 的工具；具体安装位置因工具不同而异。

## 使用示例

- “用 $listmonk-mail 检查本地 listmonk 为什么打不开。”
- “把这份 CSV 整理并导入客户通知列表，保留已有退订记录。”
- “给这个名单创建一封会议通知草稿，按姓名称呼，先预览。”
- “查看活动 123 的状态和退信数量。”
- “向我指定的测试邮箱发送活动 123 的测试邮件。”

## 配置与依赖

需要已有 listmonk 实例；Windows 原生程序依赖 PostgreSQL。辅助脚本需要 Python 3.10+，只用标准库，无需 pip 安装。

API 认证：在 listmonk 的 Admin → Users 创建 API 用户和 Token，把 `LISTMONK_URL`、`LISTMONK_API_USER`、`LISTMONK_API_TOKEN` 私下设置到当前运行环境。不要将管理员密码当作 API Token，不要提交密钥或把它发进聊天。

没有 API 凭据时仍可整理 CSV、生成草稿内容，并通过已经登录的 listmonk 界面导入与操作。邮箱 SMTP 密码在 listmonk 后台私下填写，技能中不保存。

## 提供的能力

| 能力 | 实现方式 |
|---|---|
| CSV 校验、中文列名转换、去重 | prepare_contacts.py，本地运行 |
| 服务检测、列表/模板/活动查询、导入状态查询 | listmonk_api.py |
| 新建私有列表、新建邮件草稿 | listmonk_api.py |
| 名单导入、测试和正式发送 | 技能指导使用后台或官方 API；需用户相应授权 |
| 阿里 SMTP 配置、本地启动排错 | 按需加载 references |

辅助 API 脚本没有发送命令，也不支持任意 HTTP 路径。真实发送需要用户明确指令。收到 API 超时不会自动重试写入；先检查状态。

## 限制

- 阿里企业邮箱按官方政策禁止发送营销邮件；营销用途应选择支持该用途的代发服务。
- 只监听本机的部署可连接 SMTP，但收件人无法访问本机的退订页、图片和跟踪链接。对外订阅推送需可访问的 HTTPS 部署或相应外部方案。
- SMTP 接受不保证进入收件箱。发送额度、投递效果和账号权限取决于服务商。
- CSV 语法校验不等于邮箱真实性校验；Excel 要先导出为 CSV。额外列需要明确映射，避免静默丢失数据。
- 按 listmonk 6.2.0 文档编写。提供本地功能测试，不冒充生产 SMTP 投递验证。

## 验证与贡献

```text
python -m unittest discover -s tests -v
python skills/listmonk-mail/scripts/listmonk_api.py --help
```

欢迎提交 Issue 或 Pull Request。复现材料使用合成地址和占位内容，不上传真实客户名单、数据库、配置、令牌或完整日志。

详细流程见 [SKILL.md](skills/listmonk-mail/SKILL.md)。MIT 许可覆盖本仓库原创源码和文档；listmonk 本体使用其自身许可证，本仓库不分发它的程序。
