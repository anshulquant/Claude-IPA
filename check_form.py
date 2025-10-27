import asyncio
from playwright.async_api import async_playwright

async def check_form():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://httpbin.org/forms/post')
        
        # Get all input fields
        inputs = await page.query_selector_all('input')
        print(f"Found {len(inputs)} input fields:\n")
        
        for i, inp in enumerate(inputs, 1):
            name = await inp.get_attribute('name')
            input_type = await inp.get_attribute('type')
            value = await inp.get_attribute('value')
            placeholder = await inp.get_attribute('placeholder')
            print(f"{i}. name='{name}', type='{input_type}', value='{value}', placeholder='{placeholder}'")
        
        # Get all select fields
        selects = await page.query_selector_all('select')
        print(f"\nFound {len(selects)} select fields:\n")
        
        for i, sel in enumerate(selects, 1):
            name = await sel.get_attribute('name')
            print(f"{i}. name='{name}'")
        
        # Get all textarea fields
        textareas = await page.query_selector_all('textarea')
        print(f"\nFound {len(textareas)} textarea fields:\n")
        
        for i, ta in enumerate(textareas, 1):
            name = await ta.get_attribute('name')
            print(f"{i}. name='{name}'")
        
        # Get radio buttons specifically
        radios = await page.query_selector_all('input[type="radio"]')
        print(f"\nRadio buttons detail:\n")
        for i, radio in enumerate(radios, 1):
            name = await radio.get_attribute('name')
            value = await radio.get_attribute('value')
            print(f"{i}. name='{name}', value='{value}'")

        # Get all button elements
        buttons = await page.query_selector_all('button')
        print(f"\nFound {len(buttons)} button elements:\n")
        for i, btn in enumerate(buttons, 1):
            btn_type = await btn.get_attribute('type')
            btn_text = await btn.inner_text()
            btn_name = await btn.get_attribute('name')
            print(f"{i}. type='{btn_type}', name='{btn_name}', text='{btn_text}'")

        # Check for submit inputs specifically
        submit_inputs = await page.query_selector_all('input[type="submit"]')
        print(f"\nFound {len(submit_inputs)} submit input elements")

        # Check for any element with submit
        all_submits = await page.query_selector_all('button[type="submit"], input[type="submit"]')
        print(f"\nFound {len(all_submits)} total submit elements")

        await browser.close()

asyncio.run(check_form())
