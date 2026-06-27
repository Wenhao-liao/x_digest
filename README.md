# X 每日摘要系统

每晚10点自动抓取指定X账号的推文，用Claude生成摘要，发到你的邮箱。

## 文件说明

```
x_digest/
├── digest.py               # 主程序
├── config.json             # 你的配置（从 config.template.json 复制）
├── config.template.json    # 配置模板
├── com.x.digest.plist      # Mac 定时任务配置
└── logs/                   # 运行日志（自动创建）
```

---

## 第一步：安装依赖

```bash
pip3 install anthropic requests
```

---

## 第二步：申请 API Key

### GetXAPI（拉推文）
1. 访问 https://getxapi.com 注册账号
2. 注册即赠 $0.10 试用额度（够跑几百次）
3. 在控制台复制 API Key

### Gmail 应用专用密码（发邮件）
1. 打开 Google 账户 → 安全性
2. 搜索「应用专用密码」
3. 创建一个，复制16位密码
4. **注意**：需要先开启两步验证

---

## 第三步：填写配置

```bash
cp config.template.json config.json
```

编辑 `config.json`，填入：
- `accounts`：要追踪的X用户名列表（不含@）
- `getxapi_key`：GetXAPI 的 Key
- `anthropic_api_key`：你的 Claude API Key
- `smtp_user` / `smtp_password`：Gmail 地址 + 应用专用密码
- `to_email`：接收摘要的邮箱

---

## 第四步：手动测试

```bash
cd x_digest
python3 digest.py
```

看到 `✅ 邮件已发送` 说明一切正常。

---

## 第五步：设置每晚10点自动运行（Mac）

**1. 修改 plist 文件中的路径**

打开 `com.x.digest.plist`，把所有 `/path/to/x_digest` 替换成你的实际路径，例如：
```
/Users/yourname/projects/x_digest
```

查看你的 python3 路径：
```bash
which python3
# 例如：/usr/local/bin/python3 或 /opt/homebrew/bin/python3
```

**2. 创建日志目录**

```bash
mkdir -p ~/projects/x_digest/logs
```

**3. 安装定时任务**

```bash
cp com.x.digest.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.x.digest.plist
```

**4. 验证是否安装成功**

```bash
launchctl list | grep x.digest
# 看到输出说明已加载
```

**5. 手动触发一次测试**

```bash
launchctl start com.x.digest
```

---

## 常用命令

```bash
# 查看运行日志
tail -f logs/digest.log

# 查看错误日志
tail -f logs/digest_error.log

# 停止定时任务
launchctl unload ~/Library/LaunchAgents/com.x.digest.plist

# 重新加载（修改配置后）
launchctl unload ~/Library/LaunchAgents/com.x.digest.plist
launchctl load ~/Library/LaunchAgents/com.x.digest.plist
```

---

## 费用参考

每天运行一次，追踪10个账号：
- GetXAPI：约 $0.01/天（几乎可以忽略）
- Claude API：约 $0.03-0.05/天
- **合计：每月约 $1-2**

---

## 常见问题

**Q：电脑关着/睡眠时会漏跑吗？**
A：会。launchd 不会在睡眠期间唤醒电脑。如果你的Mac经常关机，考虑改用 GitHub Actions 方案（我可以另外帮你写）。

**Q：想换用 Outlook/QQ邮箱？**
A：修改 `send_email()` 函数中的 SMTP 地址即可：
- Outlook: `smtp.office365.com:587`（TLS）
- QQ邮箱: `smtp.qq.com:465`（SSL）

**Q：想追加新账号？**
A：直接编辑 `config.json` 的 `accounts` 列表，无需重启定时任务。
