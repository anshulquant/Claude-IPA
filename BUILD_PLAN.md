# Claude IPA MVP - 2 Developer Parallel Build Plan

## 🎯 Project Goal
Build a working Claude-powered Intelligent Process Automation MVP in 7 days that can automate web workflows using natural language instructions.

---

## 👥 Developer Role Split

### Developer 1: Backend Core (Claude + Browser)
**Responsibilities:**
- Claude API integration
- Browser automation with Playwright
- Screenshot capture and processing
- Action execution (click, type, navigate)
- Testing automation components

**Files Owned:**
- `core/browser_controller.py`
- `core/orchestrator.py`
- `workflows/google_search.py`
- `workflows/form_filling.py`

---

### Developer 2: Orchestration + Frontend
**Responsibilities:**
- Workflow execution engine
- Human review queue
- FastAPI server and REST endpoints
- Web UI (HTML/CSS/JS)
- Logging and validation

**Files Owned:**
- `core/workflow_executor.py`
- `core/review_queue.py`
- `api/main.py`
- `templates/index.html`
- `workflows/data_extraction.py`

---

## 📁 Complete Project Structure

```
claude-ipa-mvp/
│
├── .env                           # API keys (create from .env.example)
├── .gitignore                     # Git ignore file
├── requirements.txt               # Python dependencies
├── README.md                      # Setup and usage instructions
│
├── core/                          # Core business logic
│   ├── __init__.py
│   ├── browser_controller.py     # [DEV 1] Playwright automation
│   ├── orchestrator.py           # [DEV 1] Claude API integration
│   ├── workflow_executor.py      # [DEV 2] Execution engine
│   └── review_queue.py           # [DEV 2] Human review logic
│
├── api/                           # FastAPI server
│   ├── __init__.py
│   └── main.py                   # [DEV 2] REST API endpoints
│
├── templates/                     # HTML templates
│   └── index.html                # [DEV 2] Web UI
│
├── workflows/                     # Demo workflows
│   ├── __init__.py
│   ├── google_search.py          # [DEV 1] Demo 1
│   ├── form_filling.py           # [DEV 1] Demo 2
│   └── data_extraction.py        # [DEV 2] Demo 3
│
├── tests/                         # Unit tests (optional for MVP)
│   ├── __init__.py
│   ├── test_browser.py
│   └── test_orchestrator.py
│
├── logs/                          # Execution logs (auto-generated)
└── screenshots/                   # Screenshot storage (auto-generated)
```

---

## 📅 Day-by-Day Parallel Work Plan

### **Day 1: Setup & Foundation**

#### Developer 1 Tasks:
- [ ] Clone repo, create `.env` with `ANTHROPIC_API_KEY`
- [ ] Install: `pip install playwright anthropic pillow`
- [ ] Run: `playwright install chromium`
- [ ] Create `core/browser_controller.py` (skeleton)
- [ ] Implement: `start()`, `navigate()`, `capture_screenshot()`
- [ ] Test: Open browser, go to google.com, take screenshot
- [ ] Push to branch: `feat/browser-controller`

#### Developer 2 Tasks:
- [ ] Clone repo, setup Python virtual environment
- [ ] Install: `pip install fastapi uvicorn python-dotenv`
- [ ] Create `api/main.py` with basic FastAPI app
- [ ] Create `templates/index.html` with simple form
- [ ] Create `core/workflow_executor.py` (skeleton)
- [ ] Setup logging configuration
- [ ] Push to branch: `feat/fastapi-setup`

#### End of Day 1 Sync:
- [ ] Both merge to `develop` branch
- [ ] Review each other's code
- [ ] Agree on interface contracts (see below)

---

### **Day 2: Core Components**

#### Developer 1 Tasks:
- [ ] Pull latest `develop`
- [ ] Create `core/orchestrator.py`
- [ ] Implement `understand_screen_and_decide(screenshot, goal)`
- [ ] Test Claude API with sample screenshots
- [ ] Parse JSON responses from Claude
- [ ] Add error handling for API failures
- [ ] Push to branch: `feat/claude-integration`

#### Developer 2 Tasks:
- [ ] Pull latest `develop`
- [ ] Implement `WorkflowExecutor.execute_workflow(goal, start_url)`
- [ ] Add execution loop (mock browser/claude calls)
- [ ] Implement logging for each step
- [ ] Create `core/review_queue.py` stub
- [ ] Push to branch: `feat/workflow-engine`

#### End of Day 2 Sync:
- [ ] Quick call to review data structures
- [ ] Share sample Claude API responses
- [ ] Dev 1 shares screenshot examples

---

### **Day 3: Integration Day 🔗**

#### Both Developers (Pair Programming):
- [ ] Merge all feature branches to `integration` branch
- [ ] Connect `WorkflowExecutor` → `BrowserController` → `Orchestrator`
- [ ] Replace mocks with real function calls
- [ ] Test first end-to-end workflow: "Go to Google, search for Anthropic"
- [ ] Debug integration issues together
- [ ] Add screenshot saving to disk
- [ ] Celebrate first successful workflow! 🎉
- [ ] Merge to `develop`

---

### **Day 4: Polish & Human Review**

#### Developer 1 Tasks:
- [ ] Add action execution: `click_element()`, `type_text()`, `click_by_text()`
- [ ] Improve error handling for failed actions
- [ ] Add retry logic (3 attempts)
- [ ] Test with complex websites
- [ ] Optimize Claude prompts for better accuracy
- [ ] Performance improvements

#### Developer 2 Tasks:
- [ ] Implement `ReviewQueue` properly
- [ ] Add confidence threshold checking
- [ ] Console-based approval flow
- [ ] Improve logging output (colors, formatting)
- [ ] Add execution report generation
- [ ] Test workflow pause/resume

#### End of Day 4 Sync:
- [ ] Test all features together
- [ ] Fix any bugs found

---

### **Day 5: UI & Natural Language**

#### Developer 1 Tasks:
- [ ] Implement `generate_workflow_plan(natural_language_goal)`
- [ ] Test Claude workflow planning with various inputs
- [ ] Create `workflows/google_search.py` demo
- [ ] Create `workflows/form_filling.py` demo
- [ ] Help Dev 2 with async integration issues

#### Developer 2 Tasks:
- [ ] Build FastAPI endpoint: `POST /api/execute-workflow`
- [ ] Create HTML form for workflow submission
- [ ] Add JavaScript for status updates
- [ ] Style the interface (CSS)
- [ ] Connect frontend to backend API
- [ ] Test full user flow from UI

#### End of Day 5 Sync:
- [ ] Test complete UI flow together
- [ ] Ensure workflows can be triggered from browser

---

### **Day 6: Demo Preparation**

#### Developer 1 Tasks:
- [ ] Polish `google_search.py` demo
- [ ] Polish `form_filling.py` demo
- [ ] Test demos 10+ times each
- [ ] Document any edge cases
- [ ] Prepare troubleshooting guide

#### Developer 2 Tasks:
- [ ] Create `workflows/data_extraction.py` demo
- [ ] Write comprehensive `README.md`
- [ ] Add setup instructions
- [ ] Create demo script document
- [ ] Polish UI for presentation

#### End of Day 6 Sync:
- [ ] Practice demo together (full run-through)
- [ ] Record backup demo video
- [ ] Dry run with a colleague

---

### **Day 7: Final Polish & Demo**

#### Developer 1 Tasks:
- [ ] Fix bugs from Day 6 testing
- [ ] Add more error handling
- [ ] Optimize Claude API usage
- [ ] Final testing of all workflows
- [ ] Be on standby during demo

#### Developer 2 Tasks:
- [ ] Fix any UI bugs
- [ ] Update documentation
- [ ] Prepare presentation slides
- [ ] Setup demo environment
- [ ] Lead the demo presentation

#### Demo Time! 🎬
- [ ] Show Google search automation
- [ ] Show form filling with human review
- [ ] Show data extraction
- [ ] Answer stakeholder questions
- [ ] Gather feedback for next phase

---

## 🔌 Interface Contracts (Agree on Day 1)

### 1. BrowserController Interface
```python
class BrowserController:
    async def start(self) -> None:
        """Initialize browser"""
        
    async def navigate(self, url: str) -> None:
        """Navigate to URL"""
        
    async def capture_screenshot(self) -> tuple[bytes, str]:
        """Returns: (screenshot_bytes, base64_encoded_string)"""
        
    async def type_text(self, selector: str, text: str) -> None:
        """Type text into element"""
        
    async def click_element(self, selector: str) -> None:
        """Click element by CSS selector"""
        
    async def click_by_text(self, text: str) -> None:
        """Click element containing text"""
        
    async def get_page_text(self) -> str:
        """Get all visible text on page"""
        
    async def close(self) -> None:
        """Clean up and close browser"""
```

### 2. ClaudeOrchestrator Interface
```python
class ClaudeOrchestrator:
    async def understand_screen_and_decide(
        self,
        screenshot_b64: str,
        goal: str,
        current_step: str,
        page_text: str = ""
    ) -> dict:
        """
        Returns:
        {
            "action": "click" | "type" | "navigate" | "complete" | "error",
            "target": "selector or text or URL",
            "value": "text to type (if action=type)",
            "reasoning": "why this action",
            "confidence": 0.0 to 1.0,
            "needs_human_review": bool
        }
        """
        
    async def generate_workflow_plan(self, natural_language_goal: str) -> list[str]:
        """Returns: ["Step 1 description", "Step 2", ...]"""
```

### 3. WorkflowExecutor Interface
```python
class WorkflowExecutor:
    async def execute_workflow(self, goal: str, start_url: str = None) -> dict:
        """
        Returns:
        {
            "goal": str,
            "success": bool,
            "actions_taken": int,
            "execution_log": list[dict]
        }
        """
```

### 4. ReviewQueue Interface
```python
class ReviewQueue:
    async def request_review(
        self,
        workflow_goal: str,
        current_step: str,
        suggested_action: dict,
        screenshot: bytes
    ) -> dict:
        """
        Returns:
        {
            "approved": bool,
            "modified_action": dict or None,
            "reviewer": str,
            "notes": str
        }
        """
```

---

## 🌿 Git Workflow

### Branch Strategy
```
main                    # Production-ready only
  └── develop          # Integration branch (merge here daily)
      ├── feat/browser-controller
      ├── feat/claude-integration
      ├── feat/workflow-engine
      ├── feat/fastapi-setup
      └── feat/ui-interface
```

### Daily Git Routine

**Morning:**
```bash
git checkout develop
git pull origin develop
git checkout -b feat/your-feature-name
```

**During Day (commit often):**
```bash
git add .
git commit -m "feat: descriptive message"
git push origin feat/your-feature-name
```

**End of Day:**
```bash
# Create PR or merge directly
git checkout develop
git pull origin develop
git merge feat/your-feature-name
git push origin develop
```

### Conflict Prevention Rules
1. ⚠️ Never work on the same file simultaneously
2. 🔄 Pull `develop` every morning
3. 💬 Quick Slack/message before editing shared files
4. 🤝 Merge to `develop` at end of each day
5. 👀 Review each other's code before merging

---

## 📦 Dependencies (requirements.txt)

```txt
anthropic>=0.39.0
playwright>=1.40.0
fastapi>=0.109.0
uvicorn>=0.27.0
python-dotenv>=1.0.0
pillow>=10.2.0
jinja2>=3.1.3
```

---

## 🔧 Configuration Files

### .env.example
```bash
# Anthropic API Key (get from console.anthropic.com)
ANTHROPIC_API_KEY=your_api_key_here

# Server Configuration
PORT=8000
HOST=0.0.0.0

# Claude Configuration
CLAUDE_MODEL=claude-sonnet-4-5-20250929
MAX_TOKENS=1024

# Logging
LOG_LEVEL=INFO
```

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
env/

# Environment
.env

# IDE
.vscode/
.cursor/
.idea/

# Project specific
logs/
screenshots/
*.log

# OS
.DS_Store
Thumbs.db
```

---

## 🔄 Daily Sync Points

### Morning Standup (15 min)
- What did I do yesterday?
- What will I do today?
- Any blockers?
- Agree on shared files for the day

### Mid-Day Check-in (5 min)
- Quick Slack message with progress
- Share any issues encountered
- Coordinate on shared components

### End of Day Review (30 min)
- Demo what was built
- Code review in Cursor
- Merge to develop together
- Plan next day's work

---

## 🧪 Testing Strategy

### Developer 1 Testing
- Test browser automation with 5+ different websites
- Test Claude API with various screenshot types
- Verify action execution accuracy
- Test error handling

### Developer 2 Testing
- Test workflow execution with different goals
- Test UI with various inputs
- Test human review flow
- Verify logging completeness

### Integration Testing (Day 3-7)
- Test complete workflows end-to-end
- Test error scenarios
- Test with invalid inputs
- Performance testing

---

## 🎯 Success Criteria (End of Week)

By the end of 7 days, you should be able to:

✅ Type a natural language goal in the web UI
✅ Watch the browser automatically execute the workflow
✅ See Claude making intelligent decisions (via logs)
✅ Trigger human review for uncertain actions
✅ View complete execution logs with screenshots
✅ Demo 3 working workflows to stakeholders

---

## 📞 Communication Plan

### Tools
- **Git**: Version control & code review
- **Slack/Discord**: Quick questions & updates
- **Cursor**: Pair programming & conflict resolution
- **Google Meet/Zoom**: Daily standups & sync sessions

### Response Time Expectations
- Slack messages: < 30 minutes during work hours
- Code review requests: < 2 hours
- Blocker issues: Immediate (drop everything)

---

## 🚨 Risk Mitigation

### If Developer 1 Gets Blocked
- Developer 2 can help with Claude API debugging
- Use mock responses temporarily
- Fallback: Use simpler Playwright automation

### If Developer 2 Gets Blocked
- Developer 1 can help with async/FastAPI issues
- Start with console-based UI first
- Fallback: Use CLI instead of web UI

### If Integration Fails on Day 3
- Both pair program to debug
- Check interface contracts
- Add more logging for visibility
- Worst case: Extend to 8-9 days

---

## 📝 Deliverables Checklist

### Code
- [ ] All files in project structure created
- [ ] Clean, commented code
- [ ] No hardcoded credentials
- [ ] Error handling implemented

### Documentation
- [ ] README.md with setup instructions
- [ ] Code comments for complex logic
- [ ] Demo script document
- [ ] Known issues documented

### Demos
- [ ] 3 working demo workflows
- [ ] Recorded backup video
- [ ] Presentation slides
- [ ] Troubleshooting guide

---

## 🚀 Next Steps After MVP

If MVP is successful, Week 2+ roadmap:
1. Add PostgreSQL database for persistence
2. Build real-time review dashboard
3. Add email triggers
4. Desktop application support
5. Advanced error recovery
6. Performance optimization
7. Production deployment

---

## 📧 Questions?

Before starting, ensure both developers:
- ✅ Have Anthropic API key
- ✅ Understand their role split
- ✅ Have development environment ready
- ✅ Reviewed interface contracts
- ✅ Agreed on communication tools

**Let's build this! 🚀**