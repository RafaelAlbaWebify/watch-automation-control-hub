from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import ConsoleMessage, Page, sync_playwright


def _assert_text(page: Page, text: str) -> None:
    page.get_by_text(text, exact=False).first.wait_for(state="visible")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the WATCH operator UI.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()

    artifacts = args.artifacts.resolve()
    screenshots = artifacts / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    trace_path = artifacts / "playwright-trace.zip"
    console_errors: list[str] = []

    def record_console(message: ConsoleMessage) -> None:
        if message.type == "error":
            console_errors.append(message.text)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.on("console", record_console)

        try:
            page.goto(args.base_url, wait_until="networkidle")
            _assert_text(page, "Operator dashboard")
            page.keyboard.press("Tab")
            skip_link = page.get_by_role("link", name="Skip to main content")
            skip_link.wait_for(state="visible")
            assert skip_link.evaluate("element => element === document.activeElement")
            page.keyboard.press("Enter")
            assert page.locator("#main-content").evaluate(
                "element => element === document.activeElement"
            )
            assert (
                page.get_by_role("link", name="Dashboard").get_attribute("aria-current")
                == "page"
            )
            _assert_text(page, "Target drill-down")
            _assert_text(page, "Changes")
            page.screenshot(path=screenshots / "dashboard.png", full_page=True)

            page.get_by_role("link", name="Targets").click()
            assert (
                page.get_by_role("link", name="Targets").get_attribute("aria-current")
                == "page"
            )
            _assert_text(page, "Healthy public demo")
            _assert_text(page, "Degraded public demo")
            _assert_text(page, "Disabled public demo")
            page.get_by_role("link", name="Degraded public demo").click()
            page.get_by_label("Target summary").wait_for(state="visible")
            assert (
                page.get_by_role("link", name="Targets").get_attribute("aria-current")
                == "page"
            )
            _assert_text(page, "degraded-hourly")
            _assert_text(page, "Run and change history")
            _assert_text(page, "http_status")
            _assert_text(page, "UNEXPECTED_HTTP_STATUS")
            page.screenshot(path=screenshots / "target-detail.png", full_page=True)

            page.get_by_role("link", name="Schedules").click()
            _assert_text(page, "healthy-hourly")
            _assert_text(page, "degraded-hourly")
            page.screenshot(path=screenshots / "schedules.png", full_page=True)

            page.get_by_role("link", name="Occurrences").click()
            _assert_text(page, "degraded-hourly")
            _assert_text(page, "executing")
            page.screenshot(path=screenshots / "occurrences.png", full_page=True)

            page.get_by_role("link", name="Attention").click()
            _assert_text(page, "missed-unclaimed")
            _assert_text(page, "executing-stale")
            page.screenshot(path=screenshots / "attention.png", full_page=True)

            page.get_by_role("link", name="Runs").click()
            _assert_text(page, "healthy-demo")
            _assert_text(page, "degraded-demo")
            page.screenshot(path=screenshots / "runs.png", full_page=True)

            page.get_by_role("link", name="Changes").click()
            _assert_text(page, "Change timeline")
            _assert_text(page, "baseline evidence")
            _assert_text(page, "http_status")
            page.screenshot(path=screenshots / "changes.png", full_page=True)

            page.get_by_role("link", name="Actions").click()
            _assert_text(page, "UNEXPECTED_HTTP_STATUS")
            _assert_text(page, "SLOW_RESPONSE")
            _assert_text(page, "TLS_EXPIRY_APPROACHING")
            page.screenshot(path=screenshots / "actions.png", full_page=True)

            page.get_by_role("link", name="Runs").click()
            page.get_by_role("link", name="Open report").first.click()
            _assert_text(page, "WATCH Operational Report")
            page.screenshot(path=screenshots / "report.png", full_page=True)

            if console_errors:
                raise AssertionError(
                    "Unexpected browser console errors:\n" + "\n".join(console_errors)
                )
        except Exception:
            context.tracing.stop(path=trace_path)
            raise
        else:
            context.tracing.stop()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
