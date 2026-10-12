# API、名单与发送流程

## 配置认证

在 listmonk 后台 Admin → Users 创建 API 用户和 Token，授予实际需要的名单/订阅者/活动权限。管理账号登录密码不是 API Token。凭据使用环境变量或本地秘密管理器；不要写在命令参数、仓库、示例文件或聊天中。PowerShell 可以用 `Read-Host -AsSecureString` 私下输入令牌，再转成当前进程的环境变量；结束会话后清除。

变量名：`LISTMONK_URL`、`LISTMONK_API_USER`、`LISTMONK_API_TOKEN`。

脚本命令（相对当前技能目录）：

```text
python scripts/listmonk_api.py health
python scripts/listmonk_api.py lists --page 1
python scripts/listmonk_api.py templates --page 1
python scripts/listmonk_api.py campaigns --page 1
python scripts/listmonk_api.py campaign 123
python scripts/listmonk_api.py create-list 内部测试
python scripts/listmonk_api.py create-draft /absolute/path/draft.json
python scripts/listmonk_api.py import-status
```

列表默认每页 100 项；要完整检索必须按返回的 total 翻页，不能只查第一页就断定列表不存在。创建前先检查同名对象，避免重复。

## 名单准备与导入

```text
python scripts/prepare_contacts.py /absolute/path/contacts.csv /absolute/path/contacts-clean.csv
```

接受列名 `email/邮箱/邮件地址`、`name/姓名/名字`、`attributes/属性`。attributes 必须是 JSON 对象。只有邮箱为必需列。校验只是语法校验，不会证明邮箱存在。

脚本发现错误时不创建输出文件；报告行号而不是客户地址。去重规则是忽略邮箱大小写、保留首条；如同地址的其他行含不同信息，需要用户判断合并方法。

进入 Subscribers → Import，选择清理后的 CSV、明确的目标列表，保持 overwrite 关闭（除非用户要求且已明确其影响）。保留退订/屏蔽状态。双重订阅名单必须完成真实确认，不通过标为 confirmed 绕过。

API 导入是异步任务，检查 `/api/import/subscribers` 和导入日志后的计数/错误，不能把上传成功当作全部导入成功。脚本只读取导入状态，上传用界面或官方 multipart API。

## 草稿

JSON 示例中的地址是占位域名，list IDs 和 template ID 必须替换为实际读取的值。外部 JSON 可使用 `name,subject,from_email,lists,body,content_type,template_id,tags,altbody,headers`；其余键会被拒绝。

```json
{
  "name": "客户通知草稿",
  "subject": "业务安排通知",
  "from_email": "公司名称 <service@example.com>",
  "lists": [123],
  "template_id": 456,
  "content_type": "html",
  "body": "<p>{{ .Subscriber.Name }}，您好！</p><p>此处填写通知内容。</p>"
}
```

脚本固定 `type=regular`、`messenger=email` 并省略调度/发送状态字段。返回必须是 draft 才汇报成功。只支持 html/richtext/markdown/plain；可视化编辑器内容使用 UI。

## 发送

已有用户发送授权后，先查询具体 campaign 和 lists，确认正文、状态、发件人及人数。授权测试发送时使用 UI 的 Send test 或 `POST /api/campaigns/{id}/test`，明确 `subscribers` 数组；请求需要活动内容字段，按当前版本文档检查。

立即发送使用 UI 或 `PUT /api/campaigns/{id}/status`，JSON 为 `{"status":"running"}`；定时发送先设置活动时间，再切换到 scheduled。时区采用用户指定时区，将时间转成含时区的 RFC3339 格式；本地部署电脑休眠或停止服务会影响执行，不能承诺关机后发送。

暂停/恢复的状态转换按现有状态检查。发送超时先查询活动，不重复启动。结果查询优先读取具体 campaign 的 `status,sent,to_send,bounces`；结合平台投递反馈区分已提交、已投递与失败。

## 官方资料

- https://listmonk.app/docs/apis/apis/
- https://listmonk.app/docs/apis/lists/
- https://listmonk.app/docs/apis/import/
- https://listmonk.app/docs/apis/campaigns/
- https://listmonk.app/docs/templating/

依据 listmonk 6.2.0 官方接口编写；不同部署版本应核对接口。
