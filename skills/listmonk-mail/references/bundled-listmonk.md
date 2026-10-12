# 随 Skill 提供的 listmonk 本体

## 包含什么

- `assets/listmonk/windows-amd64/listmonk.exe`：官方 listmonk v6.2.0 Windows x64 程序，未修改。
- `assets/listmonk/config.example.toml`：有注释的配置样例，只有占位密码。
- `assets/listmonk/LICENSE`：上游 AGPL-3.0 许可证原文。
- `assets/listmonk/listmonk-v6.2.0-source.tar.gz`：同版本上游源码归档。
- `assets/listmonk/upstream-checksums.txt`：上游发布包校验值。

**不包含 PostgreSQL 本体、已初始化数据库、SMTP 密码、联系人、日志或发送记录。** 安装 Skill 并不自动启动或安装数据库。

## Windows 使用

1. 单独安装 PostgreSQL 12+，创建名为 `listmonk` 的空数据库和专用用户。
2. 在用户选择的可写部署目录复制 EXE 和配置样例，将样例重命名为 `config.toml`，填写自己的数据库连接信息。不要直接在已安装的 Skill 目录初始化运行数据。
3. 在部署目录执行：

```powershell
# 仅在首次初始化新的空数据库时执行；已有实例不要重复安装。
.\listmonk.exe --install --config .\config.toml
# 启动服务。关闭此终端会停止服务，发送期间保持运行。
.\listmonk.exe --config .\config.toml
```

4. 浏览器访问 `http://127.0.0.1:9000`，首次创建管理员，再在 SMTP 设置填写自己的邮箱。EXE 是网页服务，不是双击后弹出窗口的桌面应用。

已有部署继续使用它原来的启动脚本和数据库。不要复制当前机器的运行配置或数据库进入开源包。macOS/Linux/ARM 用户应从官方发行页取得对应平台程序。

## 来源与许可

- 官方发行：https://github.com/knadh/listmonk/releases/tag/v6.2.0
- 对应源码：https://github.com/knadh/listmonk/tree/v6.2.0
- 源码归档：https://github.com/knadh/listmonk/archive/refs/tags/v6.2.0.tar.gz
- 安装说明：https://listmonk.app/docs/installation/
- EXE SHA256：`c697d845247625dda1ed4e4a55a8f98b6fe44f732686c13ad2f6c3a250d6e0c7`

仓库原创 Skill 和辅助脚本使用 MIT；随附 listmonk 程序及源码保留上游 AGPL-3.0，MIT 不适用于该第三方程序。源码归档包含上游构建说明、依赖清单及构建配置。分发或修改 listmonk 时遵循其自身许可证。
