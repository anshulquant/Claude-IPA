# 🤖 Claude IPA Workflows - Quick Start Guide

## 📋 Available Workflows

### 1. Form Filling Workflow
**File:** `workflows/form_filling.py`  
**Purpose:** Automatically fill out web forms using Claude AI

**Quick Start:**
```bash
python workflows/form_filling.py
```

**What it does:**
- Opens a browser to httpbin.org/forms/post
- Claude analyzes the form fields
- Automatically fills in customer information
- Submits the form
- Shows execution logs and screenshots

---

### 2. Google Search Workflow
**File:** `workflows/google_search.py`  
**Purpose:** Automatically search Google and extract results

**Quick Start:**
```bash
python workflows/google_search.py
```

**What it does:**
- Opens Google homepage
- Claude finds the search box
- Types your query
- Submits the search
- Extracts search results
- Optionally clicks first result

---

## 🚀 Running the Workflows

### Option 1: Interactive Demo Mode

Both workflows have interactive menus:

```bash
# Form Filling
python workflows/form_filling.py
# Then select: 1 for simple demo, 2 for custom form

# Google Search
python workflows/google_search.py
# Then select: 1 for simple search, 2 for search+click, 3 for custom
```

### Option 2: Direct Python Import

```python
import asyncio
from workflows.form_filling import FormFillingWorkflow
from workflows.google_search import GoogleSearchWorkflow

# Form filling
async def test_form():
    workflow = FormFillingWorkflow(headless=False)
    result = await workflow.execute(
        form_url="https://httpbin.org/forms/post",
        goal="Fill out the pizza order form"
    )
    print(result)

# Google search
async def test_search():
    workflow = GoogleSearchWorkflow(headless=False)
    result = await workflow.execute(
        search_query="Anthropic Claude AI",
        click_first_result=False
    )
    print(result)

# Run
asyncio.run(test_form())
asyncio.run(test_search())
```

---

## ⚙️ Configuration Options

### Headless Mode

Run browser in background (no visible window):

```python
workflow = FormFillingWorkflow(headless=True)
```

### Max Steps

Limit the number of automation steps:

```python
workflow.max_steps = 10  # Default is 15-20
```

---

## 📸 Screenshots

All workflows automatically save screenshots to:
```
screenshots/
  screenshot_YYYYMMDD_HHMMSS.png
```

---

## 📊 Understanding the Output

### Console Output

The workflows provide detailed console output:

```
🎯 FORM FILLING WORKFLOW
============================================================
Goal: Fill out the pizza order form
Form URL: https://httpbin.org/forms/post
============================================================

✅ Browser started

✅ Navigated to: https://httpbin.org/forms/post

────────────────────────────────────────────────────────────
📍 STEP 1
────────────────────────────────────────────────────────────
📸 Screenshot saved: screenshots/screenshot_20250123_140530.png
🔗 Current URL: https://httpbin.org/forms/post

🤖 Asking Claude for next action...

💭 Claude's Decision:
   Action: type
   Target: input[name="custname"]
   Value: John Doe
   Reasoning: Fill in customer name field
   Confidence: 95.00%

⌨️  Typing 'John Doe' into input[name="custname"]
   ✅ Text entered successfully
```

### Return Data

```python
{
    "success": True,
    "steps_executed": 8,
    "execution_log": [
        {
            "step": 1,
            "url": "https://httpbin.org/forms/post",
            "decision": {...},
            "screenshot": "screenshots/screenshot_20250123_140530.png"
        },
        # ... more steps
    ],
    "final_url": "https://httpbin.org/post"
}
```

---

## 🐛 Troubleshooting

### Issue: "ANTHROPIC_API_KEY not found"

**Solution:** Create a `.env` file with your API key:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

### Issue: "Playwright browser not installed"

**Solution:** Install Playwright browsers:
```bash
playwright install chromium
```

### Issue: Workflow times out

**Solution:** Increase max_steps or check internet connection:
```python
workflow.max_steps = 30  # Increase from default
```

### Issue: Elements not found

**Solution:** The workflow uses Claude's vision to find elements. If it fails:
1. Check if the page loaded correctly
2. Try running in non-headless mode to see what's happening
3. Check the screenshots to see what Claude is seeing

---

## 🔧 Advanced Usage

### Custom Form Data

Modify the form data in `FormFillingWorkflow`:

```python
workflow = FormFillingWorkflow(headless=False)
workflow.form_data = {
    "custname": "Jane Smith",
    "custemail": "jane@example.com",
    # ... more fields
}
```

### Custom Search Query

```python
workflow = GoogleSearchWorkflow(headless=False)
result = await workflow.execute(
    search_query="Your custom query here",
    click_first_result=True  # Click first result
)
```

### Access Execution Logs

```python
result = await workflow.execute(...)

# Print all steps
for step in result['execution_log']:
    print(f"Step {step['step']}: {step['decision']['action']}")
    print(f"  Screenshot: {step['screenshot']}")
```

---

## 📝 Creating Your Own Workflow

Use the existing workflows as templates:

```python
import asyncio
from core.browser_controller import BrowserController
from core.orchestrator import ClaudeOrchestrator

class MyCustomWorkflow:
    def __init__(self, headless=False):
        self.browser = BrowserController(headless=headless)
        self.orchestrator = ClaudeOrchestrator()
        self.max_steps = 20
    
    async def execute(self, url, goal):
        await self.browser.start()
        await self.browser.navigate(url)
        
        for step in range(self.max_steps):
            # Capture state
            _, _, screenshot_b64 = await self.browser.capture_screenshot()
            page_text = await self.browser.get_page_text()
            
            # Ask Claude
            decision = await self.orchestrator.understand_screen_and_decide(
                screenshot_b64=screenshot_b64,
                goal=goal,
                current_step=f"Step {step}",
                page_text=page_text
            )
            
            # Execute action
            action = decision.get('action')
            if action == 'complete':
                break
            elif action == 'type':
                await self.browser.type_text(
                    decision['target'],
                    decision['value']
                )
            # ... handle other actions
        
        await self.browser.close()
        return {"success": True}

# Run it
async def main():
    workflow = MyCustomWorkflow()
    await workflow.execute("https://example.com", "Do something")

asyncio.run(main())
```

---

## 🎯 Next Steps

1. **Test the workflows:**
   ```bash
   python workflows/form_filling.py
   python workflows/google_search.py
   ```

2. **Review the code:**
   - `workflows/form_filling.py` - Form automation logic
   - `workflows/google_search.py` - Search automation logic

3. **Create your own workflow:**
   - Copy one of the existing workflows
   - Modify the goal and actions
   - Test and iterate

4. **Integrate with Dev 2's components:**
   - Connect to WorkflowExecutor
   - Use ReviewQueue for human approval
   - Expose via API endpoints

---

## 📚 Related Documentation

- `BUILD_PLAN.md` - Overall project plan
- `DEV1_WORKFLOWS_COMPLETE.md` - Detailed workflow documentation
- `core/browser_controller.py` - Browser automation API
- `core/orchestrator.py` - Claude AI integration

---

**Happy Automating! 🚀**
