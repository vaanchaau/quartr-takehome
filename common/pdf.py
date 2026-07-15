"""HTML -> PDF conversion via headless Chromium.

Callers launch one browser (via launch_browser) per job run and pass it into
html_to_pdf for every document, instead of paying Chromium startup cost per document.
"""

from contextlib import asynccontextmanager

from playwright.async_api import Browser, async_playwright


@asynccontextmanager
async def launch_browser():
    """Launch one headless Chromium instance, shared across multiple html_to_pdf calls."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            yield browser
        finally:
            await browser.close()


async def html_to_pdf(browser: Browser, html: str) -> bytes:
    """Render HTML content to a PDF using the given headless Chromium instance."""
    page = await browser.new_page()
    try:
        await page.set_content(html, wait_until="networkidle")
        return await page.pdf()
    finally:
        await page.close()
