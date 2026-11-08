# Inside the Facebook reporting agent

## What I built

I configured the agent to collect campaign performance and delivery issues through the Facebook Ads connector, then check page activity, messages and pending leads in the browser. I defined what the weekly and midweek reports should contain, which findings deserve attention, and when a person needs to approve an action. The reporting workflow uses read-only checks.

The agent writes the findings in Hebrew Markdown. The Python renderer turns that file into an RTL report: it highlights the urgent line, turns sections into cards, renders metric tables and preserves the layout of draft posts. [View the reviewed midweek report](../facebook.html).

## Run the reporting step

With Python 3.9 or later, run these commands from the repository root:

    python -m pip install -r facebook-agent/requirements.txt
    python facebook-agent/render_report.py facebook-agent/sample.md

Open facebook-agent/sample.html in your browser. Edit the urgent finding in [sample.md](sample.md), run the second command again and compare the highlighted text. The repository includes [the generated HTML](sample.html). This demo starts with fictional Markdown input and runs locally without account credentials. Data collection and email delivery belong to the operational workflow.

## One decision from the agent instructions

The browser-check rule in the operational WORKFLOW.md reads:

> לא זמין / לא מחובר → "סריקה לא בוצעה — סיבה" ולהמשיך.

If the ad metrics are available but the inbox cannot be opened, the agent can still report campaign performance. It records the reason for the missing inbox check and leaves the message count unknown. In the sample, the ad table is populated and the coverage section explicitly records the unavailable connection. This distinction lets the reader decide whether someone needs to check messages manually.