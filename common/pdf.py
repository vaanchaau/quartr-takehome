"""HTML -> PDF conversion via headless Chromium.

Direct navigation (page.goto against the filing URL) was tried for better fidelity on
relative assets, but SEC's bot detection returns a 403 ("Undeclared Automated Tool") to
headless Chromium regardless of User-Agent. So the HTML is fetched separately via
httpx (which SEC does accept) and rendered from the string instead.
"""

from playwright.async_api import async_playwright


async def html_to_pdf(html: str) -> bytes:
    """Render HTML content to a PDF using headless Chromium."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        pdf_bytes = await page.pdf()
        await browser.close()
    return pdf_bytes
