# 阿里企业邮箱及代发通道

业务邮箱通用配置：Host `smtp.qiye.aliyun.com`，端口 `465`，SSL/TLS；完整邮箱地址为用户名，使用第三方客户端安全密码。管理员需开放第三方客户端权限。阿里通用配置不支持 SMTP 587，不能套用其他服务商的 STARTTLS 587 示例。密码由用户私下填写后台，不放进 skill。

阿里官方说明任何版本的企业邮箱禁止发送营销邮件；该限制属于阿里企业邮箱服务，不应推广为所有 SMTP 通道都禁止营销。业务通知可按实际账号限制发送；营销/订阅推送按业务选择支持该用途的服务，例如 DirectMail，保留阿里邮箱作为回复地址。阿里邮箱安全密码与 DirectMail SMTP 密码不是同一套凭据。

后台 Settings → SMTP 新建并启用服务器。发件人匹配已认证账号或平台授权地址。先获授权向明确的测试邮箱发送测试；并发初次可设为 1，发送速率依据账号实际限制设置。第三方软件和付费计划不会提高阿里业务邮箱限额，不以连接池轮换规避限制。

错误排查：

- 认证失败：检查完整地址、安全密码、账号权限和登录限制。
- 连接超时：检查域名、465 端口、TLS 模式及网络出口。
- too frequently sending：暂停，查看平台实际限额，不反复重试。
- SMTP 接受但未收到：检查垃圾箱、退信和平台日志；不宣称保证进收件箱。

参考（使用时价格、政策和参数有变化则重新查官方资料）：

- https://help.aliyun.com/zh/document_detail/36576.html
- https://help.aliyun.com/zh/document_detail/36711.html
- https://help.aliyun.com/zh/document_detail/36642.html
- https://help.aliyun.com/zh/direct-mail/user-guide/overview
