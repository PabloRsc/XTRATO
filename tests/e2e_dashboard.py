import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("XTRATO_BASE_URL", "http://127.0.0.1:8000")
USERNAME = os.environ["XTRATO_TEST_USERNAME"]
PASSWORD = os.environ["XTRATO_TEST_PASSWORD"]
ARTIFACTS = Path(os.getenv("XTRATO_ARTIFACTS_DIR", "artifacts"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def record_console_error(message, viewport, errors):
    location = message.location or {}
    url = location.get("url", "")
    if "favicon.ico" in url or "fonts.googleapis.com" in url or "fonts.gstatic.com" in url:
        return
    errors.append(f"{viewport} console: {message.text}")


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        errors = []

        desktop = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        desktop.on("pageerror", lambda error: errors.append(f"Desktop JavaScript: {error}"))
        desktop.on(
            "console",
            lambda message: record_console_error(message, "Desktop", errors)
            if message.type == "error" else None,
        )
        desktop.on(
            "response",
            lambda response: errors.append(f"Desktop HTTP {response.status}: {response.url}")
            if response.status >= 500 else None,
        )
        desktop.goto(BASE_URL, wait_until="networkidle")
        desktop.locator("#loginView").wait_for(state="visible")
        desktop.locator('#loginForm input[name="username"]').fill(USERNAME)
        desktop.locator('#loginForm input[name="password"]').fill(PASSWORD)
        desktop.locator('#loginForm button[type="submit"]').click()
        desktop.locator("#appView").wait_for(state="visible", timeout=15000)
        desktop.locator("#page-dashboard").wait_for(state="visible")

        for selector in (
            "#budgetAvailable",
            "#walletCards",
            "#statementEntries",
            "#categoryChart",
            "#trendChart",
            "#forecastChart",
        ):
            desktop.locator(selector).wait_for(state="visible")
        desktop_dimensions = desktop.evaluate(
            "() => ({viewport: document.documentElement.clientWidth, content: document.documentElement.scrollWidth})"
        )
        if desktop_dimensions["content"] > desktop_dimensions["viewport"] + 2:
            errors.append(
                f"Horizontal overflow on desktop: {desktop_dimensions['content']}px content "
                f"for {desktop_dimensions['viewport']}px viewport"
            )
        desktop.screenshot(path=str(ARTIFACTS / "dashboard-desktop.png"), full_page=True)

        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
            is_mobile=True,
            has_touch=True,
        )
        mobile.on("pageerror", lambda error: errors.append(f"Mobile JavaScript: {error}"))
        mobile.on(
            "console",
            lambda message: record_console_error(message, "Mobile", errors)
            if message.type == "error" else None,
        )
        mobile.on(
            "response",
            lambda response: errors.append(f"Mobile HTTP {response.status}: {response.url}")
            if response.status >= 500 else None,
        )
        mobile.goto(BASE_URL, wait_until="networkidle")
        mobile.locator("#loginView").wait_for(state="visible")
        mobile.locator('#loginForm input[name="username"]').fill(USERNAME)
        mobile.locator('#loginForm input[name="password"]').fill(PASSWORD)
        mobile.locator('#loginForm button[type="submit"]').click()
        mobile.locator("#appView").wait_for(state="visible", timeout=15000)
        mobile.locator("#page-dashboard").wait_for(state="visible")
        mobile.locator("#forecastChart").wait_for(state="visible")
        mobile.screenshot(path=str(ARTIFACTS / "dashboard-mobile.png"), full_page=True)

        dimensions = mobile.evaluate(
            "() => ({viewport: document.documentElement.clientWidth, content: document.documentElement.scrollWidth})"
        )
        if dimensions["content"] > dimensions["viewport"] + 2:
            errors.append(
                f"Horizontal overflow on mobile: {dimensions['content']}px content "
                f"for {dimensions['viewport']}px viewport"
            )

        browser.close()
        if errors:
            raise AssertionError("\\n".join(errors))
        print("Playwright smoke test passed: login and dashboard rendered on desktop and mobile.")
        print(f"Desktop layout dimensions: {desktop_dimensions}")
        print(f"Mobile layout dimensions: {dimensions}")


if __name__ == "__main__":
    main()
