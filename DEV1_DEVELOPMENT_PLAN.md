# Developer 1 - Development Plan
## Claude IPA MVP - Backend Core (Claude + Browser Automation)

---

## 🎯 Your Mission
Build the **brain and hands** of the automation system:
- **Brain**: Claude API integration for intelligent decision-making
- **Hands**: Playwright browser automation for executing actions

---

## 📋 Quick Reference

### Your Responsibilities
- ✅ Claude API integration and prompt engineering
- ✅ Browser automation with Playwright
- ✅ Screenshot capture and processing
- ✅ Action execution (click, type, navigate)
- ✅ Testing automation components
- ✅ Error handling and retry logic

### Your Files
```
core/
├── browser_controller.py      # Browser automation engine
└── orchestrator.py            # Claude AI decision-making

workflows/
├── google_search.py           # Demo workflow 1
└── form_filling.py            # Demo workflow 2
```

---

## 📅 Day-by-Day Action Plan

### **Day 1: Environment Setup & Browser Foundation**

#### Morning (3-4 hours)
**Goal**: Get browser automation working

1. **Setup Environment**
   ```bash
   cd d:\Claude-Automation
   python -m venv venv
   venv\Scripts\activate
   pip install playwright anthropic pillow python-dotenv
   playwright install chromium
   ```

2. **Create `.env` file**
   - Add your `ANTHROPIC_API_KEY`
   - Test API key with simple curl/request

3. **Create `core/browser_controller.py`**
   - Implement `BrowserController` class skeleton
   - Add methods:
     - `async def start()` - Initialize Playwright browser
     - `async def navigate(url)` - Navigate to URL
     - `async def capture_screenshot()` - Take screenshot
     - `async def close()` - Cleanup
   
4. **Test Browser Basics**
   - Create `test_browser.py` in project root
   - Test: Open browser → Navigate to google.com → Take screenshot → Close
   - Verify screenshot saved to `screenshots/` folder

#### Afternoon (3-4 hours)
**Goal**: Add more browser capabilities

5. **Extend Browser Controller**
   - Add `async def get_page_text()` - Extract visible text
   - Add `async def get_page_html()` - Get HTML content
   - Add error handling for navigation failures
   - Add timeout configurations

6. **Test Advanced Features**
   - Test navigation to multiple sites
   - Test screenshot quality and encoding
   - Test text extraction accuracy
   - Handle popup/cookie banners

7. **Git Workflow**
   ```bash
   git checkout -b feat/browser-controller
   git add .
   git commit -m "feat: implement basic browser controller with Playwright"
   git push origin feat/browser-controller
   ```

#### End of Day 1 Checklist
- [ ] Browser opens and closes successfully
- [ ] Can navigate to any URL
- [ ] Screenshots captured and saved
- [ ] Page text extraction works
- [ ] Code pushed to feature branch
- [ ] Sync with Developer 2 on interface contracts

---

### **Day 2: Claude API Integration**

#### Morning (3-4 hours)
**Goal**: Get Claude making decisions from screenshots

1. **Create `core/orchestrator.py`**
   - Implement `ClaudeOrchestrator` class
   - Setup Anthropic client
   - Load API key from environment

2. **Implement `understand_screen_and_decide()`**
   - Accept: screenshot (base64), goal, current_step, page_text
   - Build prompt for Claude:
     ```
     You are a browser automation assistant.
     Goal: {goal}
     Current Step: {current_step}
     
     Analyze this screenshot and decide the next action.
     Return JSON with: action, target, value, reasoning, confidence
     ```
   - Parse Claude's JSON response
   - Validate response structure

3. **Test Claude Integration**
   - Create `test_claude.py`
   - Test with sample screenshot of Google homepage
   - Goal: "Search for Anthropic"
   - Verify Claude returns valid action JSON

#### Afternoon (3-4 hours)
**Goal**: Robust error handling and prompt optimization

4. **Improve Prompt Engineering**
   - Add examples of good actions to prompt
   - Specify exact JSON schema required
   - Add confidence scoring guidance
   - Test with different websites

5. **Error Handling**
   - Handle API rate limits
   - Handle malformed JSON responses
   - Add retry logic (3 attempts)
   - Log all API calls and responses

6. **Response Validation**
   - Create `validate_action()` function
   - Check required fields exist
   - Validate action types
   - Ensure confidence is 0.0-1.0

7. **Git Workflow**
   ```bash
   git checkout -b feat/claude-integration
   git add .
   git commit -m "feat: implement Claude orchestrator with vision API"
   git push origin feat/claude-integration
   ```

#### End of Day 2 Checklist
- [ ] Claude API successfully called
- [ ] Screenshot sent to Claude
- [ ] Valid JSON response received
- [ ] Error handling implemented
- [ ] Code pushed to feature branch
- [ ] Share sample responses with Developer 2

---

### **Day 3: Integration Day 🔗**

#### Full Day (6-8 hours) - Pair Programming
**Goal**: Connect all components end-to-end

1. **Morning Sync (30 min)**
   - Review Developer 2's workflow executor
   - Discuss integration points
   - Merge all branches to `integration`

2. **Connect Components**
   - Help integrate `BrowserController` with `WorkflowExecutor`
   - Help integrate `ClaudeOrchestrator` with execution loop
   - Replace mocks with real function calls

3. **First End-to-End Test**
   - Goal: "Go to Google and search for Anthropic"
   - Expected flow:
     1. Browser opens
     2. Navigate to google.com
     3. Screenshot taken
     4. Claude analyzes → suggests typing in search box
     5. Execute type action
     6. Claude analyzes → suggests clicking search button
     7. Execute click action
     8. Workflow completes

4. **Debug Together**
   - Fix async/await issues
   - Fix selector problems
   - Add detailed logging
   - Handle edge cases

5. **Celebrate & Document**
   - Record successful workflow run
   - Document any quirks discovered
   - Update interface contracts if needed
   - Merge to `develop`

#### End of Day 3 Checklist
- [ ] First workflow runs end-to-end
- [ ] Browser + Claude + Executor working together
- [ ] Screenshots saved with timestamps
- [ ] Logs show complete execution flow
- [ ] Code merged to develop branch

---

### **Day 4: Action Execution & Reliability**

#### Morning (3-4 hours)
**Goal**: Implement all browser actions

1. **Add Action Methods to BrowserController**
   - `async def click_element(selector)` - Click by CSS selector
   - `async def click_by_text(text)` - Click element containing text
   - `async def type_text(selector, text)` - Type into input field
   - `async def press_key(key)` - Press keyboard key (Enter, Tab, etc.)
   - `async def scroll_to(selector)` - Scroll element into view

2. **Test Each Action**
   - Test clicking buttons, links, divs
   - Test typing in various input types
   - Test keyboard navigation
   - Test scrolling behavior

3. **Handle Dynamic Content**
   - Add wait for element visibility
   - Add wait for network idle
   - Handle lazy-loaded content
   - Handle AJAX requests

#### Afternoon (3-4 hours)
**Goal**: Bulletproof error handling

4. **Implement Retry Logic**
   - Retry failed actions up to 3 times
   - Add exponential backoff
   - Log each retry attempt
   - Return detailed error messages

5. **Improve Error Messages**
   - "Element not found: {selector}"
   - "Timeout waiting for: {element}"
   - "Navigation failed: {url}"
   - Include screenshot on error

6. **Optimize Claude Prompts**
   - Test with 10+ different websites
   - Refine prompt based on failures
   - Add more context about page state
   - Improve action selection accuracy

7. **Performance Improvements**
   - Reduce screenshot size (compress)
   - Cache repeated API calls
   - Optimize page load waits
   - Measure execution time

#### End of Day 4 Checklist
- [ ] All action methods implemented
- [ ] Retry logic working
- [ ] Error handling comprehensive
- [ ] Tested on complex websites
- [ ] Performance optimized
- [ ] Code pushed and reviewed

---

### **Day 5: Workflow Planning & Demo Workflows**

#### Morning (3-4 hours)
**Goal**: Natural language workflow planning

1. **Implement `generate_workflow_plan()`**
   - Accept: natural language goal
   - Prompt Claude to break down into steps
   - Return: List of step descriptions
   - Example:
     ```
     Goal: "Book a flight to NYC"
     Steps:
     1. Navigate to airline website
     2. Enter departure city
     3. Enter destination city
     4. Select dates
     5. Search flights
     6. Select flight
     7. Proceed to checkout
     ```

2. **Test Workflow Planning**
   - Test with 5+ different goals
   - Verify steps are logical
   - Ensure steps are actionable
   - Refine prompt for better plans

3. **Create `workflows/google_search.py`**
   ```python
   async def google_search_workflow(query: str):
       """Demo: Search Google for a query"""
       # Initialize components
       # Execute workflow
       # Return results
   ```

#### Afternoon (3-4 hours)
**Goal**: Build demo workflows

4. **Create `workflows/form_filling.py`**
   ```python
   async def form_filling_workflow(form_data: dict):
       """Demo: Fill out a sample form"""
       # Navigate to form
       # Fill each field
       # Submit form
       # Verify success
   ```

5. **Test Demo Workflows**
   - Run each demo 5+ times
   - Document success rate
   - Note any failures
   - Refine prompts/selectors

6. **Help Developer 2**
   - Assist with async integration issues
   - Help debug API endpoint problems
   - Review frontend integration code

#### End of Day 5 Checklist
- [ ] Workflow planning working
- [ ] Google search demo complete
- [ ] Form filling demo complete
- [ ] Demos tested multiple times
- [ ] Helped Developer 2 with integration
- [ ] Code pushed and documented

---

### **Day 6: Demo Preparation & Polish**

#### Morning (3-4 hours)
**Goal**: Perfect the demos

1. **Polish Google Search Demo**
   - Test with 20+ different queries
   - Handle "no results" case
   - Handle "did you mean" suggestions
   - Add result extraction
   - Document edge cases

2. **Polish Form Filling Demo**
   - Test with different form types
   - Handle validation errors
   - Handle required fields
   - Handle dropdowns/checkboxes
   - Add success verification

3. **Create Demo Documentation**
   - Write step-by-step demo script
   - Document expected behavior
   - List known limitations
   - Create troubleshooting guide

#### Afternoon (3-4 hours)
**Goal**: Final testing and preparation

4. **Stress Testing**
   - Run demos back-to-back
   - Test with slow internet
   - Test with different screen sizes
   - Test error recovery

5. **Create Backup Plan**
   - Record successful demo videos
   - Prepare screenshots of each step
   - Create fallback demo data
   - Test on fresh environment

6. **Practice Demo with Developer 2**
   - Full run-through of all workflows
   - Time the demo (aim for 10-15 min)
   - Prepare for Q&A
   - Identify potential issues

#### End of Day 6 Checklist
- [ ] Demos run reliably (90%+ success)
- [ ] Documentation complete
- [ ] Demo script prepared
- [ ] Backup videos recorded
- [ ] Practice demo completed
- [ ] Ready for final day

---

### **Day 7: Final Polish & Demo Day 🎬**

#### Morning (2-3 hours)
**Goal**: Fix any remaining issues

1. **Bug Fixes**
   - Address issues from Day 6 testing
   - Fix any race conditions
   - Improve error messages
   - Add final logging

2. **Code Cleanup**
   - Remove debug print statements
   - Add docstrings to all functions
   - Format code consistently
   - Remove unused imports

3. **Final Testing**
   - Test all workflows one last time
   - Verify on clean environment
   - Check all dependencies installed
   - Verify .env.example is correct

#### Afternoon (2-3 hours)
**Goal**: Demo preparation

4. **Setup Demo Environment**
   - Fresh browser profile
   - Clear cache and cookies
   - Test internet connection
   - Prepare demo URLs

5. **Pre-Demo Checklist**
   - [ ] API key loaded and working
   - [ ] Browser automation working
   - [ ] All demos tested
   - [ ] Logs configured properly
   - [ ] Screenshots folder ready
   - [ ] Backup plan ready

#### Demo Time! 🎬
**Your Role During Demo**:
- Monitor logs in real-time
- Watch for errors
- Be ready to explain technical details
- Answer questions about Claude integration
- Demonstrate browser automation
- Explain decision-making process

#### Post-Demo
- Gather feedback
- Document issues encountered
- Plan next iteration
- Celebrate success! 🎉

---

## 🔧 Technical Implementation Guide

### BrowserController Architecture

```python
# core/browser_controller.py

from playwright.async_api import async_playwright, Browser, Page
import base64
from pathlib import Path

class BrowserController:
    def __init__(self):
        self.playwright = None
        self.browser: Browser = None
        self.page: Page = None
        
    async def start(self, headless: bool = False):
        """Initialize browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=['--start-maximized']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await context.new_page()
        
    async def navigate(self, url: str, wait_until: str = "networkidle"):
        """Navigate to URL"""
        await self.page.goto(url, wait_until=wait_until, timeout=30000)
        
    async def capture_screenshot(self) -> tuple[bytes, str]:
        """Capture and return screenshot"""
        screenshot_bytes = await self.page.screenshot(full_page=False)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
        
        # Save to disk
        Path("screenshots").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"screenshots/screenshot_{timestamp}.png"
        with open(filepath, "wb") as f:
            f.write(screenshot_bytes)
            
        return screenshot_bytes, screenshot_b64
        
    async def click_element(self, selector: str, retry: int = 3):
        """Click element by CSS selector"""
        for attempt in range(retry):
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                await self.page.click(selector)
                return True
            except Exception as e:
                if attempt == retry - 1:
                    raise Exception(f"Failed to click {selector}: {e}")
                await asyncio.sleep(1)
        return False
        
    async def type_text(self, selector: str, text: str):
        """Type text into element"""
        await self.page.wait_for_selector(selector)
        await self.page.fill(selector, text)
        
    async def click_by_text(self, text: str):
        """Click element containing text"""
        await self.page.click(f"text={text}")
        
    async def get_page_text(self) -> str:
        """Get all visible text"""
        return await self.page.inner_text("body")
        
    async def close(self):
        """Cleanup"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
```

### ClaudeOrchestrator Architecture

```python
# core/orchestrator.py

from anthropic import Anthropic
import json
import os

class ClaudeOrchestrator:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
        
    async def understand_screen_and_decide(
        self,
        screenshot_b64: str,
        goal: str,
        current_step: str,
        page_text: str = ""
    ) -> dict:
        """Analyze screenshot and decide next action"""
        
        prompt = f"""You are a browser automation assistant. Analyze this screenshot and decide the next action.

GOAL: {goal}
CURRENT STEP: {current_step}

PAGE TEXT (for context):
{page_text[:500]}...

Analyze the screenshot and return ONLY valid JSON with this exact structure:
{{
    "action": "click" | "type" | "navigate" | "complete" | "error",
    "target": "CSS selector or text or URL",
    "value": "text to type (only if action=type)",
    "reasoning": "brief explanation of why this action",
    "confidence": 0.85,
    "needs_human_review": false
}}

RULES:
- Use CSS selectors for "target" when possible (e.g., "input[name='q']")
- Use "text=..." for clicking by text (e.g., "text=Search")
- Set confidence lower if uncertain
- Set needs_human_review=true for risky actions
- Use action="complete" when goal is achieved
- Use action="error" if goal cannot be completed
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            
            # Parse response
            response_text = response.content[0].text
            action_data = json.loads(response_text)
            
            # Validate
            required_fields = ["action", "target", "reasoning", "confidence"]
            if not all(field in action_data for field in required_fields):
                raise ValueError("Missing required fields in response")
                
            return action_data
            
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return {
                "action": "error",
                "target": "",
                "reasoning": f"API error: {str(e)}",
                "confidence": 0.0,
                "needs_human_review": True
            }
            
    async def generate_workflow_plan(self, natural_language_goal: str) -> list[str]:
        """Generate step-by-step workflow plan"""
        
        prompt = f"""Break down this goal into specific, actionable steps:

GOAL: {natural_language_goal}

Return ONLY a JSON array of step descriptions:
["Step 1 description", "Step 2 description", ...]

Each step should be:
- Specific and actionable
- In logical order
- Achievable by browser automation
- Clear and concise

Example:
["Navigate to google.com", "Type 'Anthropic' in search box", "Click Search button", "Verify results loaded"]
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            
            steps = json.loads(response.content[0].text)
            return steps
            
        except Exception as e:
            print(f"Error generating plan: {e}")
            return ["Error: Could not generate plan"]
```

---

## 🧪 Testing Checklist

### Browser Controller Tests
- [ ] Browser launches successfully
- [ ] Navigation works with valid URLs
- [ ] Navigation handles invalid URLs gracefully
- [ ] Screenshots captured correctly
- [ ] Screenshots saved to disk
- [ ] Page text extraction works
- [ ] Click actions work on buttons
- [ ] Click actions work on links
- [ ] Type actions work in input fields
- [ ] Handles elements not found
- [ ] Handles timeouts appropriately
- [ ] Browser closes cleanly

### Claude Orchestrator Tests
- [ ] API key loads from environment
- [ ] Can send screenshot to Claude
- [ ] Receives valid JSON response
- [ ] Handles malformed JSON
- [ ] Handles API errors
- [ ] Retry logic works
- [ ] Confidence scores are reasonable
- [ ] Actions are appropriate for goal
- [ ] Workflow planning works
- [ ] Plans are logical and actionable

### Integration Tests
- [ ] Browser + Claude work together
- [ ] Actions execute based on Claude decisions
- [ ] Screenshots taken at right times
- [ ] Logs show complete flow
- [ ] Errors handled gracefully
- [ ] Workflow completes successfully

---

## 🚨 Common Issues & Solutions

### Issue: Playwright not installed
**Solution**: Run `playwright install chromium`

### Issue: API key not found
**Solution**: Check `.env` file exists and has `ANTHROPIC_API_KEY=...`

### Issue: Element not found
**Solution**: 
- Add wait for selector
- Use more specific selector
- Check if element is in iframe
- Verify page fully loaded

### Issue: Claude returns invalid JSON
**Solution**:
- Improve prompt to specify exact format
- Add JSON validation
- Use retry logic
- Log raw response for debugging

### Issue: Screenshot too large
**Solution**:
- Compress image before encoding
- Use viewport size instead of full page
- Reduce image quality slightly

### Issue: Actions too slow
**Solution**:
- Reduce wait times
- Use "domcontentloaded" instead of "networkidle"
- Optimize screenshot capture
- Cache repeated operations

---

## 📚 Resources

### Documentation
- [Playwright Python Docs](https://playwright.dev/python/docs/intro)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [Claude Vision Guide](https://docs.anthropic.com/claude/docs/vision)

### Example Selectors
```python
# Common CSS selectors
"input[type='text']"           # Text input
"input[name='q']"              # Input with name attribute
"button[type='submit']"        # Submit button
"a[href='/login']"             # Link with href
".search-button"               # Class selector
"#submit-btn"                  # ID selector
"div > button"                 # Direct child
"text=Click me"                # By text content
```

### Debugging Tips
```python
# Add these for debugging
await self.page.pause()                    # Pause execution
await self.page.screenshot(path="debug.png")  # Debug screenshot
print(await self.page.content())           # Print HTML
print(await self.page.title())             # Print page title
```

---

## ✅ Daily Commit Messages

Use these commit message formats:

```bash
# Day 1
git commit -m "feat: implement browser controller with Playwright"
git commit -m "feat: add screenshot capture and page text extraction"

# Day 2
git commit -m "feat: implement Claude orchestrator with vision API"
git commit -m "feat: add action decision-making and JSON parsing"

# Day 3
git commit -m "feat: integrate browser controller with workflow executor"
git commit -m "fix: resolve async/await issues in integration"

# Day 4
git commit -m "feat: add all browser action methods (click, type, scroll)"
git commit -m "feat: implement retry logic and error handling"

# Day 5
git commit -m "feat: implement workflow planning with Claude"
git commit -m "feat: create google search demo workflow"
git commit -m "feat: create form filling demo workflow"

# Day 6
git commit -m "refactor: polish demo workflows and improve reliability"
git commit -m "docs: add demo script and troubleshooting guide"

# Day 7
git commit -m "fix: final bug fixes and code cleanup"
git commit -m "docs: update documentation for demo"
```

---

## 🎯 Success Metrics

By end of Week 1, you should have:

✅ **Functional Browser Automation**
- Browser opens, navigates, captures screenshots
- All action methods working (click, type, scroll)
- Error handling and retry logic

✅ **Working Claude Integration**
- Screenshots sent to Claude API
- Valid action decisions received
- Workflow planning functional

✅ **2 Demo Workflows**
- Google search automation
- Form filling automation
- Both run reliably (90%+ success)

✅ **Clean, Documented Code**
- All functions have docstrings
- Error messages are clear
- Code follows Python best practices

✅ **Ready for Demo**
- Workflows tested extensively
- Demo script prepared
- Backup plan ready

---

## 💡 Pro Tips

1. **Start Simple**: Get basic functionality working before adding complexity
2. **Test Often**: Test each function immediately after writing it
3. **Log Everything**: Add detailed logging for debugging
4. **Use Headless=False**: Keep browser visible during development
5. **Save Screenshots**: Save every screenshot for debugging
6. **Commit Frequently**: Commit working code multiple times per day
7. **Ask for Help**: Don't hesitate to pair program with Developer 2
8. **Document Quirks**: Note any weird behavior you discover
9. **Optimize Later**: Focus on functionality first, performance second
10. **Have Fun**: This is a cool project! Enjoy building it! 🚀

---

## 📞 Communication with Developer 2

### Daily Sync Points
- **Morning**: Share today's plan, discuss any blockers
- **Midday**: Quick update on progress
- **Evening**: Demo what you built, merge code together

### What to Share
- Sample Claude API responses
- Screenshot examples
- Error messages you're seeing
- Interface changes needed
- Testing results

### When to Ask for Help
- Async/await issues
- FastAPI integration problems
- Workflow executor questions
- UI feedback needed

---

## 🎉 You've Got This!

This plan breaks down a complex project into manageable daily tasks. Focus on one day at a time, test thoroughly, and communicate with Developer 2. By Day 7, you'll have built an impressive AI-powered browser automation system!

**Remember**: Progress over perfection. Get it working first, then make it better.

**Good luck, Developer 1! Let's build something amazing! 🚀**
