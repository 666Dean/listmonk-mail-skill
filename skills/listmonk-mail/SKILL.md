---
name: listmonk-mail
description: 管理 listmonk 的邮件名单、订阅者导入、个性化邮件草稿、发送结果与本地启动排错；适用于 listmonk 接入阿里企业邮箱或 SMTP 代发服务。用户提到 listmonk 群发、邮件列表或 listmonk API 时使用。
---

# listmonk 邮件管理

优先通过 listmonk API 执行可重复操作；没有 API 凭据时使用已登录的浏览器界面，或先生成可导入的文件和草稿。目标是完成用户要求的名单整理、草稿或发送任务。

## 接入

- 从用户提供的地址或现有部署确定实例；本地默认候选为 `http://127.0.0.1:9000`。先验证网页可访问，不把网页响应当作 API 鉴权成功。
- 辅助脚本需要 Python 3.10+，仅依赖标准库。以当前技能目录下的 `scripts/listmonk_api.py` 路径执行；命令示例中的相对路径需要展开。
- API 使用环境变量 `LISTMONK_URL`、`LISTMONK_API_USER`、`LISTMONK_API_TOKEN`。缺少凭据时指导用户在 Admin → Users 创建 API 用户和令牌，并在本机私下配置；不要求用户把密码或令牌发进聊天。详见 [references/workflows.md](references/workflows.md)。
- 默认只允许环回 HTTP 或 HTTPS。远端部署需要 HTTPS；不要禁用证书校验。脚本拒绝重定向，避免把认证头交给其他站点。

## 名单与草稿

- 名单整理用 `scripts/prepare_contacts.py 输入.csv 输出.csv`。支持英文或中文邮箱、姓名列，生成 `email,name,attributes` 三列；拒绝格式错误行，不在日志中打印邮箱，去重以保留首条为准。编码默认 UTF-8，GB18030 文件可用 `--encoding gb18030`。
- Excel 先转换为 UTF-8 CSV；不要把 `.xlsx` 直接当 CSV 读取。其他字段需要用户指定映射，不能默默丢弃；脚本发现额外列时停止。
- 导入前确认目标列表 ID、人数、单次/双重订阅类型以及重复记录处理。通过 Subscribers → Import 导入，按页面样例复核字段。不要覆盖已退订或已屏蔽的状态，不要将导入当作订阅同意证明。
- 创建草稿前确认发件人、主题、正文、列表 ID 和模板 ID。`create-draft` 只创建普通邮件草稿，不接受 `send_at` 或任意状态输入；创建后核对返回状态确实为 `draft`。
- 个性化姓名用 `{{ .Subscriber.Name }}`；自定义字段用 `{{ .Subscriber.Attribs.company }}`。名单中没有名字时预览空值，必要时使用模板条件补上称呼。
- 读取 [references/workflows.md](references/workflows.md) 获取具体命令、草稿 JSON 和导入检查。

## 发送与结果

- 创建技能、接入邮箱、导入名单或创建草稿都不构成发送授权。测试邮件也是实际发送；用户明确要求测试发送且给出收件人后才能执行。
- 正式发送、定时发送和恢复已暂停活动，都需要用户明确的发送指令。已有明确授权时继续执行，不重复询问。
- 执行前核对具体活动、内容、发件人、目标名单、人数与时间；信息不完整时先完成草稿和预览，询问缺失项。
- 辅助脚本不提供发送接口。获得授权后按 [references/workflows.md](references/workflows.md) 使用界面或经核实的官方 API 执行发送。
- 对创建、导入或发送请求出现超时，不自动重复提交；先查询是否已完成，避免重复草稿或重复邮件。
- 汇报活动状态、已提交数量、退信等可观察结果；SMTP 接受或 `sent` 不代表送达收件箱。打开率也受客户端图片策略影响。

## 阿里邮箱与本地实例

需要配置阿里 SMTP 或判断业务邮箱/代发通道时，读 [references/aliyun-smtp.md](references/aliyun-smtp.md)。

本地 EXE 闪退、缺配置、端口占用、数据库连接失败时，读 [references/windows-local.md](references/windows-local.md)。不要通过重新 `--install` 或删除数据库来“修复”已有实例。

## 发布边界

这个技能是可移植的操作说明与工具，不包含邮件服务器、发送额度或送达保证。只发布技能源码和合成示例；运行配置、令牌、数据库、日志、邮件正文和客户名单留在用户本地。
