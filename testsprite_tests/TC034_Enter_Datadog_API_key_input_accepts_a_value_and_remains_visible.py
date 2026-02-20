import asyncio
from playwright import async_api
from playwright.async_api import expect

async def run_test():
    pw = None
    browser = None
    context = None

    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()

        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",         # Set the browser window size
                "--disable-dev-shm-usage",        # Avoid using /dev/shm which can cause issues in containers
                "--ipc=host",                     # Use host-level IPC for better stability
                "--single-process"                # Run the browser in a single process mode
            ],
        )

        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        context.set_default_timeout(5000)

        # Open a new page in the browser context
        page = await context.new_page()

        # Interact with the page elements to simulate user flow
        # -> Navigate to http://localhost:8501
        await page.goto("http://localhost:8501", wait_until="commit", timeout=10000)
        
        # -> Type 'dd_test_key_12345' into the Datadog API Key input (index 248), clearing the existing value, then finish the task.
        frame = context.pages[-1]
        # Input text
        elem = frame.locator('xpath=/html/body/div/div[1]/div[1]/div/div/section/div[1]/div[2]/div/div/div[6]/div/div/div/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('dd_test_key_12345')
        
        # --> Assertions to verify final state
        frame = context.pages[-1]
        # Assertions for Datadog presence and Datadog API Key input visibility/value
        locator = frame.locator('xpath=/html/body/div/div[1]/div[1]/div/div/section/div[1]/div[2]/div/div/div/6]/div/div/div/input')
        # Ensure the Datadog related element is visible
        assert await locator.is_visible()
        # Ensure the aria-label contains the text 'Datadog'
        aria = await locator.get_attribute('aria-label')
        assert aria and 'Datadog' in aria
        # Small pause to allow any UI updates after typing
        await frame.wait_for_timeout(500)
        # Verify the Datadog API key input is still visible after typing
        assert await locator.is_visible()
        # Verify the input contains the entered value
        value = await locator.input_value()
        assert value == 'dd_test_key_12345'
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    