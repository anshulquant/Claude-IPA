# Developer 1 - Quick Start Guide
## Get Started in 30 Minutes

---

## 🚀 Immediate Actions (Do This First!)

### 1. Environment Setup (10 minutes)
```bash
# Navigate to project
cd d:\Claude-Automation

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install playwright anthropic pillow python-dotenv

# Install Chromium browser
playwright install chromium
```

### 2. Configure API Key (5 minutes)
1. Get your Anthropic API key from https://console.anthropic.com/
2. Open `.env` file (already exists in your project)
3. Add your key:
   ```
   ANTHROPIC_API_KEY=your_actual_key_here
   ```

### 3. Test Setup (5 minutes)
Create `test_setup.py`:
```python
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
        print("✅ Browser working!")
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
    print(f"✅ Claude API working! Response: {response.content[0].text}")

async def main():
    await test_browser()
    await test_api()
    print("\n🎉 All systems ready! You can start coding!")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_setup.py
```

---

## 📋 Your First Day Tasks

### Morning: Browser Controller
**Goal**: Get browser automation working

1. **Create `core/browser_controller.py`**
   - Copy the implementation from `DEV1_DEVELOPMENT_PLAN.md` (Section: BrowserController Architecture)
   - Start with basic methods: `start()`, `navigate()`, `capture_screenshot()`, `close()`

2. **Test It**
   ```python
   # test_browser_basic.py
   import asyncio
   from core.browser_controller import BrowserController
   
   async def main():
       browser = BrowserController()
       await browser.start(headless=False)
       await browser.navigate("https://www.google.com")
       screenshot_bytes, screenshot_b64 = await browser.capture_screenshot()
       print(f"✅ Screenshot captured: {len(screenshot_b64)} bytes")
       await browser.close()
   
   asyncio.run(main())
   ```

### Afternoon: Claude Integration
**Goal**: Get Claude analyzing screenshots

1. **Create `core/orchestrator.py`**
   - Copy the implementation from `DEV1_DEVELOPMENT_PLAN.md` (Section: ClaudeOrchestrator Architecture)
   - Implement `understand_screen_and_decide()`

2. **Test It**
   ```python
   # test_claude_basic.py
   import asyncio
   from core.browser_controller import BrowserController
   from core.orchestrator import ClaudeOrchestrator
   
   async def main():
       browser = BrowserController()
       claude = ClaudeOrchestrator()
       
       await browser.start(headless=False)
       await browser.navigate("https://www.google.com")
       screenshot_bytes, screenshot_b64 = await browser.capture_screenshot()
       page_text = await browser.get_page_text()
       
       action = await claude.understand_screen_and_decide(
           screenshot_b64=screenshot_b64,
           goal="Search for Anthropic",
           current_step="On Google homepage",
           page_text=page_text
       )
       
       print(f"✅ Claude decided: {action}")
       await browser.close()
   
   asyncio.run(main())
   ```

---

## 📁 File Structure You'll Create

```
d:\Claude-Automation\
├── core/
│   ├── __init__.py                    # Create empty file
│   ├── browser_controller.py          # YOU CREATE THIS (Day 1 AM)
│   └── orchestrator.py                # YOU CREATE THIS (Day 1 PM)
│
├── workflows/
│   ├── __init__.py                    # Create empty file
│   ├── google_search.py               # YOU CREATE THIS (Day 5)
│   └── form_filling.py                # YOU CREATE THIS (Day 5)
│
├── screenshots/                        # Auto-created by your code
├── logs/                               # Auto-created by your code
│
├── test_setup.py                       # Create this first!
├── test_browser_basic.py               # Test browser
└── test_claude_basic.py                # Test Claude
```

---

## 🎯 Success Checklist for Day 1

By end of Day 1, you should have:

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Playwright Chromium installed
- [ ] API key configured in `.env`
- [ ] `test_setup.py` runs successfully
- [ ] `core/browser_controller.py` created
- [ ] Browser opens, navigates, captures screenshots
- [ ] `core/orchestrator.py` created
- [ ] Claude API successfully analyzes a screenshot
- [ ] Code committed to `feat/browser-controller` branch
- [ ] Synced with Developer 2 on interface contracts

---

## 🆘 Troubleshooting

### "playwright not found"
```bash
pip install playwright
playwright install chromium
```

### "ANTHROPIC_API_KEY not found"
- Check `.env` file exists
- Check key is on a line like: `ANTHROPIC_API_KEY=sk-ant-...`
- No quotes needed around the key
- Run `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"`

### "Browser won't open"
```bash
# Reinstall Chromium
playwright install --force chromium
```

### "Import errors"
```bash
# Make sure you're in virtual environment
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📞 Need Help?

1. **Check the detailed plan**: `DEV1_DEVELOPMENT_PLAN.md`
2. **Check the main build plan**: `BUILD_PLAN.md`
3. **Sync with Developer 2**: They might have insights
4. **Check documentation**:
   - [Playwright Docs](https://playwright.dev/python/)
   - [Anthropic Docs](https://docs.anthropic.com/)

---

## 💡 Pro Tips for Day 1

1. **Keep browser visible**: Use `headless=False` to see what's happening
2. **Print everything**: Add lots of print statements for debugging
3. **Save all screenshots**: You'll need them for debugging
4. **Test immediately**: Don't write a lot of code before testing
5. **Commit often**: Commit every time something works
6. **Take breaks**: This is a marathon, not a sprint

---

## 🎉 Ready to Start?

1. Run through the setup steps above
2. Create your first test file
3. Start building `browser_controller.py`
4. Test frequently
5. Have fun! 🚀

**You've got this, Developer 1! Let's build something amazing!**
