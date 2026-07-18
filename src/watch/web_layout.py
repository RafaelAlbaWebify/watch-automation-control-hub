from __future__ import annotations

from html import escape

from fastapi.responses import HTMLResponse

STYLE = """
:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  --navy-950: #071a33;
  --navy-900: #0b2342;
  --navy-800: #12345c;
  --blue-700: #135fca;
  --blue-600: #1976e9;
  --blue-100: #e9f2ff;
  --slate-950: #152238;
  --slate-700: #46566c;
  --slate-600: #64748b;
  --slate-500: #7c8ba1;
  --slate-300: #cfd8e5;
  --slate-200: #e4e9f1;
  --slate-100: #eef2f7;
  --slate-50: #f7f9fc;
  --white: #ffffff;
  --success: #287a4a;
  --success-soft: #eaf7ef;
  --warning: #95620d;
  --warning-soft: #fff7df;
  --danger: #a63c35;
  --danger-soft: #fff0ee;
  --radius-sm: .45rem;
  --radius-md: .7rem;
  --radius-lg: .95rem;
  --shadow-panel: 0 1px 2px rgba(7, 26, 51, .05), 0 8px 24px rgba(7, 26, 51, .04);
  --sidebar-width: 15.5rem;
}
* { box-sizing: border-box; }
html { background: var(--slate-50); }
body {
  margin: 0;
  min-width: 20rem;
  background: var(--slate-50);
  color: var(--slate-950);
  line-height: 1.5;
}
a { color: var(--blue-700); }
a:hover { color: var(--blue-600); }
a:focus-visible,
button:focus-visible,
[tabindex]:focus-visible {
  outline: 3px solid #f5bf42;
  outline-offset: 3px;
}
.skip-link {
  position: fixed;
  left: .75rem;
  top: -5rem;
  z-index: 100;
  padding: .65rem .9rem;
  border-radius: var(--radius-sm);
  background: var(--white);
  color: var(--navy-950);
  box-shadow: var(--shadow-panel);
}
.skip-link:focus { top: .75rem; }
.app-shell { min-height: 100vh; }
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 20;
  display: flex;
  width: var(--sidebar-width);
  flex-direction: column;
  overflow-y: auto;
  background: linear-gradient(180deg, var(--navy-950), var(--navy-900));
  color: var(--white);
  border-right: 1px solid rgba(255, 255, 255, .08);
}
.brand {
  padding: 1.55rem 1.35rem 1.2rem;
  border-bottom: 1px solid rgba(255, 255, 255, .1);
}
.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: .65rem;
  color: var(--white);
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: .04em;
}
.brand-symbol {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, .24);
  border-radius: .65rem;
  background: rgba(255, 255, 255, .08);
  font-size: .72rem;
  letter-spacing: -.02em;
}
.brand p {
  margin: .45rem 0 0;
  color: #b9c7d9;
  font-size: .76rem;
  line-height: 1.4;
}
nav {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: .25rem;
  padding: 1rem .8rem;
}
nav a {
  display: flex;
  min-height: 2.55rem;
  align-items: center;
  padding: .62rem .8rem;
  border-radius: var(--radius-md);
  color: #c9d5e5;
  font-size: .9rem;
  font-weight: 600;
  text-decoration: none;
  transition: background .15s ease, color .15s ease, transform .15s ease;
}
nav a:hover {
  background: rgba(255, 255, 255, .08);
  color: var(--white);
  transform: translateX(2px);
}
nav a[aria-current="page"] {
  background: var(--white);
  color: var(--navy-950);
  box-shadow: 0 8px 20px rgba(0, 0, 0, .12);
}
.sidebar-footer {
  padding: 1rem 1.35rem 1.3rem;
  border-top: 1px solid rgba(255, 255, 255, .1);
  color: #aebed2;
  font-size: .72rem;
}
.content-shell {
  min-height: 100vh;
  margin-left: var(--sidebar-width);
}
.topbar {
  display: flex;
  min-height: 4rem;
  align-items: center;
  justify-content: flex-end;
  padding: .75rem 2rem;
  border-bottom: 1px solid var(--slate-200);
  background: rgba(255, 255, 255, .94);
}
.mode-chip {
  display: inline-flex;
  align-items: center;
  gap: .45rem;
  padding: .42rem .7rem;
  border: 1px solid var(--slate-200);
  border-radius: 999px;
  color: var(--slate-600);
  background: var(--white);
  font-size: .76rem;
  font-weight: 700;
}
.mode-dot {
  width: .5rem;
  height: .5rem;
  border-radius: 999px;
  background: var(--success);
  box-shadow: 0 0 0 3px var(--success-soft);
}
main {
  width: 100%;
  max-width: 112rem;
  margin: 0 auto;
  padding: 2rem 2.1rem 3rem;
}
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.35rem;
  padding-bottom: 1.35rem;
  border-bottom: 1px solid var(--slate-200);
}
.page-eyebrow {
  margin: 0 0 .3rem;
  color: var(--blue-700);
  font-size: .7rem;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}
.page-header h1 {
  margin: 0;
  color: var(--slate-950);
  font-size: clamp(1.45rem, 2.1vw, 2rem);
  line-height: 1.2;
}
.page-description {
  max-width: 48rem;
  margin: .45rem 0 0;
  color: var(--slate-600);
  font-size: .9rem;
}
section { margin-block: 1.35rem; }
section > h3 {
  margin: 0 0 .75rem;
  color: var(--slate-950);
  font-size: 1rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10.5rem, 1fr));
  gap: .85rem;
}
.card,
.panel {
  border: 1px solid var(--slate-200);
  border-radius: var(--radius-lg);
  background: var(--white);
  box-shadow: var(--shadow-panel);
}
.card {
  min-height: 8rem;
  padding: 1rem 1.05rem;
}
.card h3 {
  margin: 0;
  color: var(--slate-600);
  font-size: .69rem;
  font-weight: 800;
  letter-spacing: .07em;
  text-transform: uppercase;
}
.card p { margin: .25rem 0 0; color: var(--slate-600); font-size: .79rem; }
.card a { font-weight: 700; text-decoration: none; }
.metric {
  margin: .38rem 0 .1rem !important;
  color: var(--slate-950) !important;
  font-size: 1.72rem !important;
  font-weight: 800;
  line-height: 1.1;
}
.dashboard-columns {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(17rem, .8fr);
  gap: 1rem;
}
.panel { padding: 1rem; }
.panel-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: .85rem;
}
.panel-heading h3 { margin: 0; font-size: 1rem; }
.panel-heading p { margin: 0; color: var(--slate-600); font-size: .75rem; }
.target-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: .65rem;
  margin: 0;
  padding: 0;
  list-style: none;
}
.target-list a {
  display: block;
  padding: .75rem .85rem;
  border: 1px solid var(--slate-200);
  border-radius: var(--radius-md);
  background: var(--slate-50);
  color: var(--slate-950);
  font-size: .84rem;
  font-weight: 700;
  text-decoration: none;
}
.target-list a:hover { border-color: #a9c8f2; background: var(--blue-100); }
.table-scroll {
  overflow-x: auto;
  border: 1px solid var(--slate-200);
  border-radius: var(--radius-lg);
  background: var(--white);
  box-shadow: var(--shadow-panel);
}
table {
  width: 100%;
  min-width: 43rem;
  border-collapse: collapse;
  background: var(--white);
  font-size: .8rem;
}
table.compact { min-width: 0; }
caption {
  padding: .9rem 1rem;
  border-bottom: 1px solid var(--slate-200);
  color: var(--slate-950);
  font-size: .92rem;
  font-weight: 800;
  text-align: left;
}
th, td {
  padding: .72rem 1rem;
  border-bottom: 1px solid var(--slate-100);
  text-align: left;
  vertical-align: top;
}
th {
  background: var(--slate-50);
  color: var(--slate-600);
  font-size: .66rem;
  font-weight: 800;
  letter-spacing: .055em;
  text-transform: uppercase;
}
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: #fbfcfe; }
.badge {
  display: inline-flex;
  align-items: center;
  padding: .18rem .5rem;
  border: 1px solid var(--slate-300);
  border-radius: 999px;
  background: var(--slate-50);
  color: var(--slate-700);
  font-size: .68rem;
  font-weight: 800;
  line-height: 1.25;
  white-space: nowrap;
}
.badge-success { border-color: #a8d8b9; background: var(--success-soft); color: var(--success); }
.badge-warning { border-color: #ead08c; background: var(--warning-soft); color: var(--warning); }
.badge-danger { border-color: #e7b1ac; background: var(--danger-soft); color: var(--danger); }
.badge-muted { color: var(--slate-600); }
.empty,
.note {
  padding: .85rem 1rem;
  border: 1px solid var(--slate-200);
  border-radius: var(--radius-md);
  background: var(--white);
  color: var(--slate-600);
  font-size: .84rem;
}
.empty { font-style: normal; }
pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  padding: 1rem;
  border: 1px solid var(--slate-200);
  border-radius: var(--radius-lg);
  background: var(--navy-950);
  color: #dce7f5;
  box-shadow: var(--shadow-panel);
}
code {
  color: #334766;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: .92em;
  overflow-wrap: anywhere;
}
pre code { color: inherit; }
@media (max-width: 960px) {
  :root { --sidebar-width: 13.5rem; }
  main { padding-inline: 1.35rem; }
  .dashboard-columns { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .sidebar {
    position: static;
    width: 100%;
    max-height: none;
  }
  .brand { padding: 1rem; }
  .brand p, .sidebar-footer { display: none; }
  nav {
    flex: none;
    flex-direction: row;
    overflow-x: auto;
    padding: .65rem;
  }
  nav a {
    flex: 0 0 auto;
    min-height: 2.25rem;
    padding: .5rem .7rem;
  }
  nav a:hover { transform: none; }
  .content-shell { margin-left: 0; }
  .topbar { min-height: 3.2rem; padding: .55rem 1rem; }
  main { padding: 1.25rem 1rem 2rem; }
  .page-header { margin-bottom: 1rem; padding-bottom: 1rem; }
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .card { min-height: 7rem; }
}
@media (max-width: 430px) {
  .grid { grid-template-columns: 1fr; }
  .page-header { display: block; }
  .metric { font-size: 1.5rem !important; }
}
"""

NAVIGATION = (
    ("Dashboard", "/"),
    ("Targets", "/targets"),
    ("Schedules", "/schedules"),
    ("Occurrences", "/occurrences"),
    ("Attention", "/attention"),
    ("Attempts", "/attempts"),
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
    "Schedule attention": "/attention",
    "Retry attempts": "/attempts",
    "Runs": "/runs",
    "Change timeline": "/changes",
    "Actions": "/actions",
}

_PAGE_DESCRIPTIONS = {
    "Operator dashboard": (
        "Monitor registered websites, recurring schedules, execution evidence, and "
        "operational follow-up from one local control surface."
    ),
    "Targets": "Review the public websites registered for controlled technical checks.",
    "Schedules": "Inspect recurring execution definitions and their enabled state.",
    "Occurrences": "Trace persisted schedule boundaries, claims, outcomes, and linked runs.",
    "Schedule attention": "Review missed or stale execution evidence without changing it.",
    "Retry attempts": "Inspect bounded retry history while preserving original run evidence.",
    "Runs": "Review immutable workflow runs, findings, changes, and generated reports.",
    "Change timeline": "Follow chronological evidence changes for each registered target.",
    "Actions": "Track operational findings that require acknowledgement or follow-up.",
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
    description = _PAGE_DESCRIPTIONS.get(
        title,
        "Review retained WATCH operational evidence in the local control hub.",
    )
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
<div class="app-shell">
  <aside class="sidebar" aria-label="WATCH application navigation">
    <div class="brand">
      <div class="brand-mark"><span class="brand-symbol">W</span> WATCH</div>
      <p>Web Operations Control Hub</p>
    </div>
    <nav aria-label="Primary">{navigation(active_path)}</nav>
    <div class="sidebar-footer">Local-first · Evidence retained · No remediation</div>
  </aside>
  <div class="content-shell">
    <header class="topbar">
      <span class="mode-chip"><span class="mode-dot" aria-hidden="true"></span>Local operator</span>
    </header>
    <main id="main-content" tabindex="-1">
      <div class="page-header">
        <div>
          <p class="page-eyebrow">WATCH operations</p>
          <h1>{escape(title)}</h1>
          <p class="page-description">{escape(description)}</p>
        </div>
      </div>
      {body}
    </main>
  </div>
</div>
</body>
</html>"""
    return HTMLResponse(document)
