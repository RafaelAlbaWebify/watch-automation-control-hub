from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import Page


PAGES = [
    ("dashboard", "/", "Operator dashboard"),
    ("targets", "/targets", "Registered operational targets"),
    ("schedules", "/schedules", "Configured recurring schedules"),
    ("occurrences", "/occurrences", "Persisted schedule occurrences"),
    ("attention", "/attention", "Missed and stale occurrence attention"),
    ("attempts", "/attempts", "Operator-controlled retry attempt history"),
    ("runs", "/runs", "Immutable workflow run history"),
    ("changes", "/changes", "Change timeline"),
    ("actions", "/actions", "Operational action history"),
]

SELECTED_PORTFOLIO_SCREENSHOTS = [
    "desktop-dashboard.png",
    "desktop-targets.png",
    "desktop-changes.png",
    "desktop-actions.png",
]


def _review_viewport(
    page: Page,
    base_url: str,
    screenshots: Path,
    viewport_name: str,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for name, route, heading in PAGES:
        response = page.goto(f"{base_url}{route}", wait_until="networkidle")
        assert response is not None and response.ok, f"{route} did not return success"
        page.get_by_text(heading, exact=False).first.wait_for(state="visible")
        page.locator("main").wait_for(state="visible")
        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")
        overflow = body_width > viewport_width + 2
        if overflow and viewport_name == "mobile":
            tables = page.locator(".table-scroll")
            assert tables.count() > 0, f"Unexpected mobile overflow on {route}"
        image = screenshots / f"{viewport_name}-{name}.png"
        page.screenshot(path=image, full_page=True)
        results.append(
            {
                "page": name,
                "route": route,
                "heading": heading,
                "status": "pass",
                "body_width": body_width,
                "viewport_width": viewport_width,
                "controlled_overflow": overflow,
                "screenshot": image.name,
            }
        )
    return results


def _portfolio_review(root: Path, screenshots: Path) -> dict[str, object]:
    readme = (root / "README.md").read_text(encoding="utf-8")
    required_claims = [
        "Workflow Automation & Technical Control Hub",
        "Current verified capability",
        "Quick start on Windows",
        "Windows Task Scheduler lifecycle",
        "Scheduling and execution safety",
        "Automated proof",
    ]
    missing_claims = [claim for claim in required_claims if claim not in readme]
    if missing_claims:
        raise AssertionError(f"README portfolio claims missing: {missing_claims}")

    for image in SELECTED_PORTFOLIO_SCREENSHOTS:
        if not (screenshots / image).is_file():
            raise AssertionError(f"Selected portfolio screenshot is missing: {image}")

    return {
        "result": "pass",
        "readme_claims_checked": required_claims,
        "missing_readme_claims": missing_claims,
        "selected_screenshots": SELECTED_PORTFOLIO_SCREENSHOTS,
        "selection_reason": {
            "desktop-dashboard.png": "overall operational summary",
            "desktop-targets.png": "managed target inventory",
            "desktop-changes.png": "change detection and evidence chronology",
            "desktop-actions.png": "actionable operational outcomes",
        },
    }


def main() -> None:
    from playwright.sync_api import ConsoleMessage, sync_playwright

    parser = argparse.ArgumentParser(description="Run a human-like WATCH V1 browser review.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()

    root = Path.cwd().resolve()
    artifacts = args.artifacts.resolve()
    screenshots = artifacts / "human-review-screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    console_errors: list[str] = []

    def record_console(message: ConsoleMessage) -> None:
        if message.type == "error":
            console_errors.append(message.text)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        desktop = browser.new_context(viewport={"width": 1440, "height": 1000})
        desktop_page = desktop.new_page()
        desktop_page.on("console", record_console)
        desktop_results = _review_viewport(
            desktop_page, args.base_url, screenshots, "desktop"
        )
        desktop_page.goto(args.base_url, wait_until="networkidle")
        desktop_page.keyboard.press("Tab")
        skip_link = desktop_page.get_by_role("link", name="Skip to main content")
        assert skip_link.evaluate("element => element === document.activeElement")
        desktop_page.keyboard.press("Enter")
        assert desktop_page.locator("#main-content").evaluate(
            "element => element === document.activeElement"
        )
        desktop.close()

        mobile = browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = mobile.new_page()
        mobile_page.on("console", record_console)
        mobile_results = _review_viewport(
            mobile_page, args.base_url, screenshots, "mobile"
        )
        mobile.close()
        browser.close()

    if console_errors:
        raise AssertionError("Browser console errors:\n" + "\n".join(console_errors))

    portfolio = _portfolio_review(root, screenshots)
    report: dict[str, Any] = {
        "result": "pass",
        "review_style": "playwright-human-like",
        "desktop_pages_reviewed": len(desktop_results),
        "mobile_pages_reviewed": len(mobile_results),
        "keyboard_skip_link": "pass",
        "console_errors": console_errors,
        "portfolio_review": portfolio,
        "desktop": desktop_results,
        "mobile": mobile_results,
    }
    (artifacts / "v1-human-review.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (artifacts / "portfolio-review.json").write_text(
        json.dumps(portfolio, indent=2) + "\n", encoding="utf-8"
    )
    (artifacts / "v1-human-review.md").write_text(
        "# WATCH V1 Playwright human review\n\n"
        "- Result: **PASS**\n"
        f"- Desktop pages reviewed: **{len(desktop_results)}**\n"
        f"- Mobile pages reviewed: **{len(mobile_results)}**\n"
        "- Keyboard skip-link workflow: **PASS**\n"
        "- Browser console errors: **0**\n"
        "- README portfolio claims: **PASS**\n"
        "- Final screenshot shortlist: dashboard, targets, changes, actions.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
