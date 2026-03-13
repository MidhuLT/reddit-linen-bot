import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_FROM, EMAIL_TO, GMAIL_APP_PASSWORD, TOPIC


# --------------------------------------------------------------------------- #
# HTML template
# --------------------------------------------------------------------------- #

def _html_header(post_count: int) -> str:
    date_str = datetime.now().strftime("%B %d, %Y")
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Linen Digest</title>
</head>
<body style="margin:0;padding:0;background:#f5f0eb;font-family:'Segoe UI',Arial,sans-serif;">

<!-- Wrapper -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0eb;padding:30px 0;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;">

  <!-- Header -->
  <tr>
    <td style="background:#4a3728;border-radius:12px 12px 0 0;padding:32px 36px;text-align:center;">
      <p style="margin:0 0 6px 0;color:#d4b896;font-size:12px;letter-spacing:3px;text-transform:uppercase;">Daily Digest</p>
      <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;letter-spacing:1px;">🧵 Pure Linen &amp; Linen Clothing</h1>
      <p style="margin:10px 0 0 0;color:#c9a882;font-size:14px;">{date_str} &nbsp;·&nbsp; {post_count} new post{"s" if post_count != 1 else ""} from Reddit</p>
    </td>
  </tr>

  <!-- Body -->
  <tr>
    <td style="background:#ffffff;padding:28px 36px;">
"""


def _html_post_card(post: dict, index: int) -> str:
    subreddit = post["subreddit"]
    sub_label = f"r/{subreddit}" if subreddit != "global" else "🌐 Global search"
    # Strip HTML tags from summary for a clean preview
    import re
    clean_summary = re.sub(r"<[^>]+>", "", post.get("summary", "")).strip()
    preview = clean_summary[:200] + ("…" if len(clean_summary) > 200 else "")

    return f"""
      <!-- Post card -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:18px;border:1px solid #e8ddd4;border-radius:10px;overflow:hidden;">
        <tr>
          <td style="background:#faf7f4;padding:4px 16px;border-bottom:1px solid #e8ddd4;">
            <span style="font-size:11px;color:#8b6f5e;font-weight:600;text-transform:uppercase;letter-spacing:1px;">{sub_label}</span>
          </td>
        </tr>
        <tr>
          <td style="padding:16px;">
            <a href="{post['link']}" style="color:#4a3728;font-size:15px;font-weight:700;text-decoration:none;line-height:1.4;display:block;"
               target="_blank">{post['title']}</a>
            {f'<p style="margin:8px 0 0 0;color:#666;font-size:13px;line-height:1.5;">{preview}</p>' if preview else ''}
            <p style="margin:12px 0 0 0;">
              <a href="{post['link']}" style="display:inline-block;background:#4a3728;color:#ffffff;font-size:12px;font-weight:600;
                 padding:7px 16px;border-radius:6px;text-decoration:none;">Read on Reddit →</a>
            </p>
          </td>
        </tr>
      </table>
"""


def _html_empty() -> str:
    return """
      <div style="text-align:center;padding:40px 0;color:#999;">
        <p style="font-size:40px;margin:0;">🔍</p>
        <p style="margin:12px 0 0 0;font-size:15px;">🔍 No new linen posts found after checking 20 times across the last 30 days.<br>Reddit may be quiet on linen topics right now — will check again tomorrow!</p>
      </div>
"""


def _html_footer() -> str:
    return f"""
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background:#f5f0eb;border-top:1px solid #e0d5c8;padding:20px 36px;text-align:center;border-radius:0 0 12px 12px;">
      <p style="margin:0;color:#a08070;font-size:12px;">
        This digest is sent daily at 10 AM &nbsp;·&nbsp; Posts sourced from Reddit RSS<br>
        <span style="color:#c0a898;">Powered by your Reddit Linen Bot 🧵</span>
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>

</body>
</html>
"""


def build_email_html(posts: list) -> str:
    html = _html_header(len(posts))
    if not posts:
        html += _html_empty()
    else:
        for i, post in enumerate(posts):
            html += _html_post_card(post, i)
    html += _html_footer()
    return html


# --------------------------------------------------------------------------- #
# Send
# --------------------------------------------------------------------------- #

def send_email(posts: list):
    subject = f"🧵 Linen Digest — {len(posts)} new post{'s' if len(posts) != 1 else ''} · {datetime.now().strftime('%b %d')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO

    html = build_email_html(posts)
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(EMAIL_FROM, GMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print(f"[emailer] ✅ Email sent → {EMAIL_TO}  ({len(posts)} posts)")
    except Exception as e:
        print(f"[emailer] ❌ Failed to send email: {e}")
        raise
