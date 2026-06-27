
# X 每日摘要系统

每晚10点自动抓取指定X账号的推文，用AI生成摘要，发到你的邮箱。
使用 GitHub Actions 定时触发，电脑不需要开着。

## 文件说明

```
x_digest/
├── digest.py                      # 主程序
├── config.template.json           # 配置模板（参考用，不要提交 config.json）
├── .gitignore                     # 排除敏感文件
└── .github/
    └── workflows/
        └── daily.yml              # GitHub Actions 定时任务
```

---

## 第一步：安装依赖（本地测试用）

```bash
pip3 install openai requests
```

---

## 第二步：申请需要的 Key

### GetXAPI（拉推文）

1. 访问 https://getxapi.com 注册账号
2. 注册即赠 $0.10 试用额度
3. 在控制台复制 API Key

### AI 中转 API（生成摘要）

使用第三方中转服务（如 laozhang.ai），记录以下三个信息：

- `api_base_url`：如 `https://api.laozhang.ai/v1`
- `api_key`：sk- 开头的密钥
- `model`：如 `deepseek-v3` 或 `claude-sonnet-4-6`

### Gmail 应用专用密码（发邮件）

1. 打开 Google 账户 → 安全性
2. 搜索「应用专用密码」
3. 创建一个，复制 16 位密码（填写时去掉空格）
4. **注意**：需要先开启两步验证

---

## 第三步：本地测试

复制配置文件并填写：

```bash
cp config.template.json config.json
```

编辑 `config.json`，填入所有字段，然后运行：

```bash
python3 digest.py
```

看到 `✅ 邮件已发送` 说明一切正常，继续下一步。

---

## 第四步：创建 .gitignore

在项目根目录创建 `.gitignore` 文件，内容如下：

```
config.json
logs/
__pycache__/
*.pyc
```

---

## 第五步：创建 GitHub Actions 工作流

创建 `.github/workflows/daily.yml` 文件，内容如下：

```yaml
name: X Daily Digest

on:
  schedule:
    - cron: '0 14 * * *'  # UTC 14:00 = 北京时间 22:00
  workflow_dispatch:       # 允许手动触发测试

jobs:
  digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install openai requests

      - name: Write config
        run: |
          cat > config.json << EOF
          {
            "accounts": ${{ secrets.ACCOUNTS }},
            "getxapi_key": "${{ secrets.GETXAPI_KEY }}",
            "api_base_url": "${{ secrets.API_BASE_URL }}",
            "api_key": "${{ secrets.API_KEY }}",
            "model": "${{ secrets.MODEL }}",
            "smtp_user": "${{ secrets.SMTP_USER }}",
            "smtp_password": "${{ secrets.SMTP_PASSWORD }}",
            "to_email": "${{ secrets.TO_EMAIL }}"
          }
          EOF

      - name: Run digest
        run: python digest.py
```

---

## 第六步：推送代码到 GitHub

```bash
git init
git add digest.py .gitignore .github/
git commit -m "init x digest"
git branch -M main
git remote add origin https://github.com/你的用户名/x_digest.git
git push --set-upstream origin main
```

**提示：**

- 国内需要开代理才能访问 GitHub，推送前先设置终端代理：
  ```bash
  export https_proxy=http://127.0.0.1:7890
  export http_proxy=http://127.0.0.1:7890
  ```
- GitHub 不支持密码登录，推送时密码一栏填 Personal Access Token（在 https://github.com/settings/tokens/new 生成，勾选 repo 权限）

---

## 第七步：在 GitHub 设置 Secrets

进入仓库页面 → Settings → Secrets and variables → Actions → New repository secret

逐个添加以下 Secrets：

| Secret 名称       | 填入的值                                 |
| ----------------- | ---------------------------------------- |
| `ACCOUNTS`      | `["elonmusk","sama"]`（JSON 数组格式） |
| `GETXAPI_KEY`   | 你的 GetXAPI Key                         |
| `API_BASE_URL`  | `https://api.laozhang.ai/v1`           |
| `API_KEY`       | 你的中转 sk-xxx                          |
| `MODEL`         | `deepseek-v3`                          |
| `SMTP_USER`     | 你的 Gmail 地址                          |
| `SMTP_PASSWORD` | Gmail 应用专用密码（16位，无空格）       |
| `TO_EMAIL`      | 接收摘要的邮箱                           |

---

## 第八步：手动触发测试

进入仓库 → Actions → X Daily Digest → Run workflow

点击 Run workflow 按钮，等待执行完成，检查邮件是否收到。

---

## 费用参考

每天运行一次，追踪 10 个账号：

- GetXAPI：约 $0.01/天
- AI 中转（deepseek-v3）：约 $0.01/天
- GitHub Actions：免费（公开仓库无限制，私有仓库每月 2000 分钟免费额度）
- **合计：每月约 $0.5-1**

---

## 常见问题

**Q：想追加新账号？**
A：去 GitHub 仓库的 Settings → Secrets，修改 `ACCOUNTS` 的值即可，格式为 JSON 数组：`["用户名1","用户名2","用户名3"]`

**Q：想换模型？**
A：修改 Secrets 里的 `MODEL` 字段，填入新模型名称，无需改代码。

**Q：想换用 QQ 邮箱发送？**
A：修改 `digest.py` 中 `send_email()` 函数的 SMTP 地址：

- QQ 邮箱：`smtp.qq.com:465`（SSL）
- Outlook：`smtp.office365.com:587`（TLS）

**Q：Actions 跑失败了怎么排查？**
A：进入仓库 → Actions → 点击失败的任务 → 展开 Run digest 步骤，查看具体报错信息。
