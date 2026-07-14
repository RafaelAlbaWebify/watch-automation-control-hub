from __future__ import annotations

from html import escape

from fastapi.responses import HTMLResponse

STYLE = """
:root { color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }
* { box-sizing: border-box; }
body { margin: 0; background: #101418; color: #edf2f7; }
header { padding: 1.25rem 2rem; border-bottom: 1px solid #2d3748; }
nav { display: flex; flex-wrap: wrap; gap: .5rem; }
nav a {
  color: #90cdf4;
  padding: .45rem .65rem;
  border-radius: 6px;
  text-decoration: none;
}
nav a[aria-current="page"] { background: #2d3748; color: #fff; font-weight: 700; }
a:focus-visible { outline: 3px solid #f6e05e; outline-offset: 3px; }
.skip-link {
  position: absolute;
  left: .75rem;
  top: -4rem;
  padding: .6rem .8rem;
  background: #fff;
  color: #101418;
  z-index: 10;
}
.skip-link:focus { top: .75rem; }
main { padding: 2rem; max-width: 1200px; margin: 0 auto; overflow-x: auto; }
section { margin-block: 1.5rem; }
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
.table-scroll { overflow-x: auto; border: 1px solid #2d3748; border-radius: 10px; }
table { width: 100%; min-width: 680px; border-collapse: collapse; background: #1a202c; }
table.compact { min-width: 0; }
caption { padding: .75rem; color: #cbd5e0; font-weight: 700; text-align: left; }
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
  border: 1px solid #4a5568;
  border-radius: 999px;
  background: #2d3748;
  font-weight: 700;
}
.badge-success { border-color: #68d391; }
.badge-warning { border-color: #f6ad55; }
.badge-danger { border-color: #fc8181; }
.badge-muted { color: #cbd5e0; }
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
@media (max-width: 640px) {
  header, main { padding: 1rem; }
  nav { gap: .25rem; }
  nav a { padding: .55rem; }
  .metric { font-size: 1.6rem; }
}
"""

NAVIGATION = (
    ("Dashboard", "/"),
    ("Targets", "/targets"),
    ("Schedules", "/schedules"),
    ("Occurrences", "/occurrences"),
    ("Attempts", "/attempts"),
    ("Attention", "/attention"),
    ("Runs", "/runs"),
    ("Changes", "/changes"),
    ("Actions", "/actions"),
    ("API", "/docs"),
)

_TITLE_PATHS = {
    "Operator dashboard": "/",
    "Targets": "/targets",
    "Schedules": "/schedules",
    "Occurrences": "/occurrences",
    "Attempts": "/attempts",
    "Schedule attention": "/attention",
    "Runs": "/runs",
    "Change timeline": "/changes",
    "Actions": "/actions",
}


def navigation(current_path: str) -> str:
    links: list[str] = []
    for label, path in NAVIGATION:
        active = current_path == path or (
            path == "/targets" and current_path.startswith("/targets/")
        )
        current = ' aria-current="page"' if active else ""
        links.append(f'<a href="{escape(path)}"{current}>{escape(label)}</a>')
    return "".join(links)


def badge(value: str) -> str:
    normalized = value.lower()
    if normalized in {"completed", "enabled", "resolved", "healthy"}:
        tone = "success"
    elif normalized in {
        "partial",
        "acknowledged",
        "claimed",
        "executing",
        "missed-unclaimed",
        "executing-stale",
    }:
        tone = "warning"
    elif normalized in {"failed", "open", "critical", "high", "disabled"}:
        tone = "danger"
    else:
        tone = "muted"
    return f'<span class="badge badge-{tone}">{escape(value)}</span>'


def table(content: str, caption: str, *, compact: bool = False) -> str:
    class_name = ' class="compact"' if compact else ""
    return (
        '<div class="table-scroll">'
        f"<table{class_name}><caption>{escape(caption)}</caption>{content}</table>"
        "</div>"
    )


def page(
    title: str,
    body: str,
    *,
    current_path: str | None = None,
) -> HTMLResponse:
    active_path = current_path or _TITLE_PATHS.get(title, "/targets")
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · WATCH</title>
  <style>{STYLE}</style>
</head>
<body>
<a class="skip-link" href="#main-content">Skip to main content</a>
<header>
  <h1>WATCH</h1>
  <p>Workflow Automation &amp; Technical Control Hub</p>
  <nav aria-label="Primary">{navigation(active_path)}</nav>
</header>
<main id="main-content" tabindex="-1">
  <h2>{escape(title)}</h2>
  {body}
</main>
</body>
</html>"""
    return HTMLResponse(document)
