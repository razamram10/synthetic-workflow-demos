"""Render a report .md into a clean, branded RTL HTML file for email.

Usage: python tools/render_report.py reports/YYYY-MM-DD-weekly.md
Writes reports/YYYY-MM-DD-weekly.html next to it and prints the path.
The same HTML is used as the email htmlBody and as the attachment.
Needs: pip install markdown
"""
import re
import sys
from html import escape
from pathlib import Path

import markdown

CSS = """
body{margin:0;background:#eef1f6;font-family:Heebo,Assistant,Arial,sans-serif;color:#1c2333;line-height:1.65;font-size:15px}
.wrap{max-width:760px;margin:0 auto;padding:24px 16px}
.head{background:#1d3f8f;color:#fff;border-radius:14px;padding:22px 24px;margin-bottom:16px}
.head .brand{font-size:12px;letter-spacing:3px;opacity:.75}
.head h1{margin:6px 0 0;font-size:22px;line-height:1.35}
.card{background:#fff;border-radius:12px;padding:6px 22px 16px;margin-bottom:14px;border:1px solid #dde3ee}
h2{font-size:18px;color:#1d3f8f;margin:16px 0 8px;padding-bottom:6px;border-bottom:2px solid #e3e9f5}
h3{font-size:15px;color:#1c2333;margin:16px 0 6px}
.urgent{background:#fff1f0;border:1px solid #f3c2bd;border-right:5px solid #d93025;border-radius:10px;padding:12px 16px;margin-bottom:14px}
.urgent p{margin:0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}
th{background:#1d3f8f;color:#fff;font-weight:600;padding:8px 10px;text-align:right}
td{padding:8px 10px;border-bottom:1px solid #e6eaf2;vertical-align:top}
tr:nth-child(even) td{background:#f7f9fc}
ul,ol{padding-right:22px;padding-left:0}
li{margin:4px 0}
code{background:#eef1f6;border-radius:4px;padding:1px 5px;font-size:13px;direction:ltr;unicode-bidi:embed}
.post{position:relative;direction:rtl;text-align:right;background:#f9fbff;border:1px solid #cdd8ee;border-right:5px solid #1d3f8f;border-radius:10px;padding:16px 18px;margin:10px 0;white-space:pre-wrap;scroll-margin:0;font-family:Heebo,Arial,sans-serif;font-size:14.5px;line-height:1.6}
.copy{display:none;position:absolute;top:8px;left:8px;background:#1d3f8f;color:#fff;border:0;border-radius:6px;padding:5px 12px;font-size:12px;cursor:pointer}
.foot{text-align:center;color:#7a8499;font-size:12px;margin-top:18px}
a{color:#1d3f8f}
bdi{white-space:nowrap}
"""

# Copy buttons only appear where scripts run (browser), never in the email body.
JS = """<script>
document.querySelectorAll('.post').forEach(function(p){
  var b=document.createElement('button');b.className='copy';b.textContent='Copy';b.style.display='block';p.style.paddingTop='42px';var t=p.textContent;
  b.onclick=function(){navigator.clipboard.writeText(t).then(function(){b.textContent='Copied';setTimeout(function(){b.textContent='Copy'},1500)})};
  p.appendChild(b);
});
</script>"""

LIST_ITEM = r"\s*(?:[-*]|\d+\.)\s"
DATE = re.compile(r"(?<![\w-])(\d{4}-\d{2}-\d{2})(?![\w-])")


def ltr_dates(html: str) -> str:
    """Keep YYYY-MM-DD in one piece inside Hebrew text."""
    return DATE.sub(lambda m: '<bdi dir="ltr">' + m.group(1) + "</bdi>", html)


def render(md_text: str) -> str:
    lines = md_text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("# ") else "Polyben Facebook"
    body = "\n".join(lines[1:])

    # Fenced code blocks are post drafts: pull them out so markdown doesn't touch them.
    posts = []

    def stash(m):
        posts.append(m.group(1).strip("\n"))
        return "\n\nPOSTBLOCK" + str(len(posts) - 1) + "\n\n"

    body = re.sub(r"```[a-z]*\n(.*?)```", stash, body, flags=re.S)

    # Urgent line gets its own red box.
    urgent = ""
    m = re.search(r"^🔴.*$", body, flags=re.M)
    if m:
        urgent = '<div class="urgent">' + markdown.markdown(m.group(0)) + "</div>"
        body = body.replace(m.group(0), "", 1)

    # Markdown needs a blank line before a list; the agent's reports often omit it.
    body = re.sub(r"(?m)^(?!" + LIST_ITEM + r")(.+)\n(?=" + LIST_ITEM + ")",
                  lambda m: m.group(1) + "\n\n", body)
    # Same for tables: markdown needs a blank line before the header row.
    body = re.sub(r"(?m)^(?!\|)(.+)\n(?=\|)", lambda m: m.group(1) + "\n\n", body)

    html = markdown.markdown(body, extensions=["tables", "sane_lists"])
    for i, text in enumerate(posts):
        block = '<div class="post">' + escape(text) + "</div>"
        html = html.replace("<p>POSTBLOCK" + str(i) + "</p>", block)
    html = ltr_dates(html)

    # One card per H2 section.
    parts = re.split(r"(?=<h2>)", html)
    cards = "".join('<div class="card">' + p + "</div>" for p in parts if p.strip())

    return f"""<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body><div class="wrap" dir="rtl">
<div class="head"><div class="brand">POLYBEN TECHNOLOGIES · FACEBOOK</div><h1>{ltr_dates(escape(title))}</h1></div>
{urgent}{cards}
<div class="foot">מנהל הפייסבוק של Polyben · נוצר אוטומטית</div>
</div>{JS}</body></html>"""


if __name__ == "__main__":
    src = Path(sys.argv[1])
    md_text = src.read_text(encoding="utf-8")
    html = render(md_text)
    # Self-check: every draft rendered and no placeholder left behind.
    assert "POSTBLOCK" not in html, "post placeholder left in output"
    assert html.count('class="post"') == md_text.count("```") // 2, "a post draft went missing"
    # UTF-8 + BOM so browsers opening the attachment from disk pick the right charset.
    # Emailing is done by ../tools/send_report.py, never by copying bytes by hand.
    out = src.with_suffix(".html")
    out.write_bytes(html.encode("utf-8-sig"))
    print(out)
