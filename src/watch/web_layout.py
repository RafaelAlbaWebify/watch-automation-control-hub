from __future__ import annotations

from html import escape

from fastapi.responses import HTMLResponse

STYLE = """
:root { color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }
body { margin: 0; background: #101418; color: #edf2f7; }
header { padding: 1.25rem 2rem; border-bottom: 1px solid #2d3748; }
nav { display: flex; flex-wrap: wrap; gap: .75rem 1rem; }
nav a { color: #90cdf4; text-decoration: none; }
main { padding: 2rem; max-width: 1200px; margin: 0 auto; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}
.card {
  background: #1a202c;
  border: 1px solid #2d3748;
  border-radius: 10px;
  padding: 1rem;
}
.metric { font-size: 2rem; font-weight: 700; margin: .25rem 0; }
table { width: 100%; border-collapse: collapse; background: #1a202c; }
th, td {
  padding: .75rem;
  border-bottom: 1px solid #2d3748;
  text-align: left;
  vertical-align: top;
}
th { color: #a0aec0; }
.badge {
  display: inline-block;
  padding: .15rem .5rem;
  border-radius: 999px;
  background: #2d3748;
}
.empty { color: #a0aec0; font-style: italic; }
.note { color: #a0aec0; }
pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #1a202c;
  padding: 1rem;
  border-radius: 10px;
}
a { color: #90cdf4; }
code { overflow-wrap: anywhere; }
"""

NAVIGATION = (
    ("Dashboard", "/"),
    ("Targets", "/targets"),
    ("Schedules", "/schedules"),
    ("Occurrences", "/occurrences"),
    ("Attention", "/attention"),
    ("Runs", "/runs"),
    ("Changes", "/changes"),
    ("Actions", "/actions"),
    ("API", "/docs"),
)


def navigation() -> str:
    return "".join(
        f'<a href="{escape(path)}">{escape(label)}</a>'
        for label, path in NAVIGATION
    )


def page(title: str, body: str) -> HTMLResponse:
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · WATCH</title>
  <style>{STYLE}</style>
</head>
<body>
<header>
  <h1>WATCH</h1>
  <p>Workflow Automation &amp; Technical Control Hub</p>
  <nav>{navigation()}</nav>
</header>
<main>
  <h2>{escape(title)}</h2>
  {body}
</main>
</body>
</html>"""
    return HTMLResponse(document)
