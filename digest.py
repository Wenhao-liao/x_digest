"""
X Daily Digest
每晚自动抓取指定X账号的最新推文，用AI总结后发到邮件。
支持第三方中转 API（兼容 OpenAI 格式）。
"""

import os
import json
import smtplib
import requests
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from openai import OpenAI

# ── 配置文件路径 ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ── 1. 用 GetXAPI 拉取推文 ────────────────────────────────────────────────────

def fetch_user_tweets(username: str, api_key: str, hours: int = 24) -> list[dict]:
    """
    用 advanced_search + from: 操作符拉取指定用户的最新推文。
    文档：https://docs.getxapi.com/docs/tweets/advanced-search
    """
    url = "https://api.getxapi.com/twitter/tweet/advanced_search"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "q": f"from:{username}",
        "product": "Latest",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        tweets = data.get("tweets", [])

        # 只保留最近 hours 小时内的
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent = []
        for t in tweets:
            created = t.get("createdAt", "")
            if created:
                try:
                    # GetXAPI 返回格式："Sun Jan 25 13:05:46 +0000 2026"
                    dt = datetime.strptime(created, "%a %b %d %H:%M:%S +0000 %Y")
                    dt = dt.replace(tzinfo=timezone.utc)
                    if dt >= cutoff:
                        recent.append(t)
                except Exception:
                    recent.append(t)  # 解析失败就保留
            else:
                recent.append(t)

        return recent

    except requests.RequestException as e:
        print(f"  [!] 拉取 @{username} 失败: {e}")
        return []


# ── 2. 用 AI 生成摘要 ─────────────────────────────────────────────────────────

def summarize_with_claude(username: str, tweets: list[dict], client: OpenAI, model: str) -> str:
    """
    把推文列表交给 AI，生成结构化摘要。
    兼容任何 OpenAI 格式的中转 API。
    """
    if not tweets:
        return f"@{username}：今日无新推文。"

    tweet_text = "\n---\n".join([
        f"[{t.get('createdAt','')[:16]}] {t.get('text','')}"
        for t in tweets
    ])

    prompt = f"""以下是 X 用户 @{username} 在过去24小时内的推文：

{tweet_text}

请用中文做一个简洁的摘要，格式如下：
1. 【核心观点】：用2-3句话概括今天的主要内容
2. 【重要信息】：列出值得关注的具体数据、事件、或观点（如有）
3. 【情绪/立场】：一句话描述该用户今天的整体情绪或立场倾向

如果推文与投资/金融/AI/科技相关，请特别注明。
保持简洁，整体不超过200字。"""

    resp = client.chat.completions.create(
        model=model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content


# ── 3. 发送邮件 ───────────────────────────────────────────────────────────────

def build_html_email(summaries: dict[str, str], date_str: str) -> str:
    """生成好看的HTML邮件"""
    items_html = ""
    for username, summary in summaries.items():
        summary_html = summary.replace("\n", "<br>")
        items_html += f"""
        <div style="margin-bottom:28px; padding:16px 20px; background:#f9f9f9;
                    border-left:4px solid #1DA1F2; border-radius:4px;">
            <div style="font-size:15px; font-weight:600; color:#1DA1F2; margin-bottom:8px;">
                @{username}
            </div>
            <div style="font-size:14px; color:#333; line-height:1.7;">
                {summary_html}
            </div>
        </div>
        """

    return f"""
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                       max-width:680px; margin:0 auto; padding:24px; color:#222;">
        <h2 style="font-size:20px; color:#111; border-bottom:1px solid #eee; padding-bottom:12px;">
            📰 X 每日摘要 · {date_str}
        </h2>
        {items_html}
        <p style="font-size:12px; color:#999; margin-top:32px;">
            由 AI + GetXAPI 自动生成 · 仅供参考，不构成投资建议
        </p>
    </body></html>
    """


def send_email(subject: str, html_body: str, cfg: dict):
    """通过 Gmail SMTP 发送邮件（需开启应用专用密码）"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["smtp_user"]
    msg["To"] = cfg["to_email"]
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(cfg["smtp_user"], cfg["smtp_password"])
        server.sendmail(cfg["smtp_user"], cfg["to_email"], msg.as_string())


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    cfg = load_config()

    # 初始化 OpenAI 兼容客户端（支持第三方中转）
    client = OpenAI(
        api_key=cfg["api_key"],
        base_url=cfg["api_base_url"]
    )
    model = cfg["model"]

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*50}")
    print(f"X Digest 运行中 · {today}")
    print(f"{'='*50}")

    summaries = {}
    for username in cfg["accounts"]:
        print(f"\n→ 正在处理 @{username} ...")
        tweets = fetch_user_tweets(username, cfg["getxapi_key"])
        print(f"  拉到 {len(tweets)} 条推文")
        summary = summarize_with_claude(username, tweets, client, model)
        summaries[username] = summary
        print(f"  摘要生成完毕")

    # 生成并发送邮件
    html = build_html_email(summaries, today)
    subject = f"📰 X 每日摘要 · {today}（{len(cfg['accounts'])}个账号）"
    send_email(subject, html, cfg)
    print(f"\n✅ 邮件已发送至 {cfg['to_email']}")


if __name__ == "__main__":
    main()
