import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()

async def test_browser():
    print("Testing browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.google.com")
        print("Browser working!")
        await browser.close()

async def test_api():
    print("Testing Claude API...")
    from anthropic import Anthropic
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say 'API working!'"}]
    )
    print(f"Claude API working! Response: {response.content[0].text}")

async def main():
    await test_browser()
    await test_api()
    print("\nAll systems ready! You can start coding!")

if __name__ == "__main__":
    asyncio.run(main())