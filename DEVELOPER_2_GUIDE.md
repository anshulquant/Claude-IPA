# Developer 2 Guide - Claude IPA MVP

## 🎯 Your Role: Orchestration + Frontend Developer

You are **Developer 2** in this 7-day sprint to build a Claude-powered Intelligent Process Automation MVP. Your focus is on the orchestration layer and user interface components.

---

## 📋 Your Core Responsibilities

### 1. **Workflow Execution Engine** (`core/workflow_executor.py`)
- Main orchestrator that coordinates the entire automation process
- Manages the execution loop between browser actions and Claude decisions
- Handles error recovery and retry logic
- Tracks execution progress and generates reports

### 2. **Human Review Queue** (`core/review_queue.py`)
- Safety mechanism for uncertain or risky actions
- Implements confidence threshold checking
- Provides console-based approval workflow
- Records human decisions and modifications

### 3. **FastAPI Server** (`api/main.py`)
- REST API endpoints for workflow submission
- Real-time status updates
- Error handling and validation
- Integration with frontend UI

### 4. **Web UI** (`templates/index.html`)
- User-friendly interface for workflow submission
- Real-time status updates via JavaScript
- Modern, responsive design
- Integration with FastAPI backend

### 5. **Logging & Validation**
- Comprehensive execution logging
- Structured log formatting with colors
- Error tracking and debugging information
- Execution report generation

---

## 📁 Files You Own

```
claude-ipa-mvp/
├── core/
│   ├── workflow_executor.py      # [YOURS] Main execution engine
│   └── review_queue.py           # [YOURS] Human review logic
├── api/
│   └── main.py                   # [YOURS] FastAPI server & REST endpoints
├── templates/
│   └── index.html                # [YOURS] Web UI interface
└── workflows/
    └── data_extraction.py        # [YOURS] Demo workflow #3
```

---

## 🗓️ Your 7-Day Development Schedule

### **Day 1: Setup & Foundation**
**Morning Tasks:**
- [ ] Clone repository and set up Python virtual environment
- [ ] Install dependencies: `pip install fastapi uvicorn python-dotenv jinja2`
- [ ] Create basic project structure
- [ ] Set up logging configuration

**Afternoon Tasks:**
- [ ] Create `api/main.py` with basic FastAPI app
- [ ] Create `templates/index.html` with simple workflow submission form
- [ ] Create `core/workflow_executor.py` skeleton
- [ ] Test basic FastAPI server startup
- [ ] Push to branch: `feat/fastapi-setup`

**End of Day Sync:**
- [ ] Merge to `develop` branch
- [ ] Review Developer 1's browser controller code
- [ ] Agree on interface contracts

---

### **Day 2: Core Components**
**Morning Tasks:**
- [ ] Pull latest `develop` branch
- [ ] Implement `WorkflowExecutor.execute_workflow()` method
- [ ] Add execution loop with mock browser/claude calls
- [ ] Implement comprehensive logging system

**Afternoon Tasks:**
- [ ] Create `core/review_queue.py` stub
- [ ] Add basic human review workflow
- [ ] Test workflow execution with mock data
- [ ] Push to branch: `feat/workflow-engine`

**End of Day Sync:**
- [ ] Quick call to review data structures
- [ ] Share sample workflow execution logs
- [ ] Coordinate integration points

---

### **Day 3: Integration Day** 🔗
**All Day - Pair Programming with Developer 1:**
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
**Morning Tasks:**
- [ ] Implement full `ReviewQueue` functionality
- [ ] Add confidence threshold checking (default: 0.7)
- [ ] Build console-based approval flow
- [ ] Test human review scenarios

**Afternoon Tasks:**
- [ ] Enhance logging with colors and formatting
- [ ] Add execution report generation
- [ ] Test workflow pause/resume functionality
- [ ] Improve error handling and recovery

**End of Day Sync:**
- [ ] Test all features together
- [ ] Fix any bugs found
- [ ] Prepare for UI development

---

### **Day 5: UI & Natural Language**
**Morning Tasks:**
- [ ] Build FastAPI endpoint: `POST /api/execute-workflow`
- [ ] Enhance HTML form with JavaScript for status updates
- [ ] Add real-time progress indicators
- [ ] Style the interface with modern CSS

**Afternoon Tasks:**
- [ ] Connect frontend to backend API
- [ ] Add error handling in UI
- [ ] Test complete user flow from browser
- [ ] Implement workflow status polling

**End of Day Sync:**
- [ ] Test complete UI flow together
- [ ] Ensure workflows can be triggered from browser
- [ ] Verify real-time updates work correctly

---

### **Day 6: Demo Preparation**
**Morning Tasks:**
- [ ] Create `workflows/data_extraction.py` demo
- [ ] Write comprehensive `README.md` with setup instructions
- [ ] Create demo script document
- [ ] Test all three demo workflows

**Afternoon Tasks:**
- [ ] Polish UI for presentation
- [ ] Add demo-specific features
- [ ] Create troubleshooting guide
- [ ] Record backup demo video

**End of Day Sync:**
- [ ] Practice demo together (full run-through)
- [ ] Record backup demo video
- [ ] Dry run with a colleague

---

### **Day 7: Final Polish & Demo**
**Morning Tasks:**
- [ ] Fix any bugs from Day 6 testing
- [ ] Update documentation
- [ ] Prepare presentation slides
- [ ] Setup demo environment

**Afternoon - Demo Time!** 🎬
- [ ] **Lead the demo presentation**
- [ ] Show Google search automation
- [ ] Show form filling with human review
- [ ] Show data extraction workflow
- [ ] Answer stakeholder questions
- [ ] Gather feedback for next phase

---

## 🔌 Interface Contracts You Must Implement

### 1. WorkflowExecutor Interface
```python
class WorkflowExecutor:
    def __init__(self):
        self.browser_controller = None  # Will be injected
        self.orchestrator = None        # Will be injected
        self.review_queue = None       # Will be injected
        
    async def execute_workflow(self, goal: str, start_url: str = None) -> dict:
        """
        Main workflow execution method.
        
        Args:
            goal: Natural language description of what to accomplish
            start_url: Optional starting URL (defaults to Google)
            
        Returns:
            {
                "goal": str,
                "success": bool,
                "actions_taken": int,
                "execution_log": list[dict],
                "final_screenshot": str,  # base64 encoded
                "execution_time": float   # seconds
            }
        """
        pass
        
    async def _execute_step(self, step_description: str) -> dict:
        """Execute a single workflow step"""
        pass
        
    async def _handle_human_review(self, action: dict) -> dict:
        """Handle actions that need human review"""
        pass
```

### 2. ReviewQueue Interface
```python
class ReviewQueue:
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        
    async def request_review(
        self,
        workflow_goal: str,
        current_step: str,
        suggested_action: dict,
        screenshot: bytes
    ) -> dict:
        """
        Request human review for an uncertain action.
        
        Args:
            workflow_goal: The overall goal of the workflow
            current_step: Description of current step
            suggested_action: Action suggested by Claude
            screenshot: Current page screenshot
            
        Returns:
            {
                "approved": bool,
                "modified_action": dict or None,
                "reviewer": str,
                "notes": str,
                "review_time": float
            }
        """
        pass
        
    async def _display_review_interface(self, data: dict) -> dict:
        """Display console-based review interface"""
        pass
```

### 3. FastAPI Endpoints You Need to Create
```python
# In api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request

app = FastAPI(title="Claude IPA MVP", version="1.0.0")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main UI"""
    pass

@app.post("/api/execute-workflow")
async def execute_workflow(workflow_data: dict):
    """Execute a workflow from the UI"""
    pass

@app.get("/api/workflow-status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get real-time workflow status"""
    pass

@app.get("/api/workflow-history")
async def get_workflow_history():
    """Get list of executed workflows"""
    pass
```

---

## 🛠️ Required Dependencies

Add these to your `requirements.txt`:
```txt
fastapi>=0.109.0
uvicorn>=0.27.0
python-dotenv>=1.0.0
jinja2>=3.1.3
websockets>=12.0
aiofiles>=23.2.1
```

Install with:
```bash
pip install fastapi uvicorn python-dotenv jinja2 websockets aiofiles
```

---

## 🎨 UI Design Requirements

### HTML Structure (`templates/index.html`)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude IPA MVP</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Claude IPA MVP</h1>
            <p>Intelligent Process Automation</p>
        </header>
        
        <main>
            <form id="workflow-form">
                <div class="form-group">
                    <label for="goal">What would you like me to automate?</label>
                    <textarea id="goal" placeholder="e.g., Go to Google and search for 'machine learning tutorials'"></textarea>
                </div>
                
                <div class="form-group">
                    <label for="start-url">Starting URL (optional)</label>
                    <input type="url" id="start-url" placeholder="https://google.com">
                </div>
                
                <button type="submit">Start Automation</button>
            </form>
            
            <div id="workflow-status" class="hidden">
                <h3>Workflow Status</h3>
                <div id="progress-bar"></div>
                <div id="current-step"></div>
                <div id="execution-log"></div>
            </div>
        </main>
    </div>
    
    <script src="/static/app.js"></script>
</body>
</html>
```

### Key UI Features to Implement:
- **Real-time status updates** via WebSocket or polling
- **Progress bar** showing execution progress
- **Live execution log** with timestamps
- **Screenshot display** for human review
- **Error handling** with user-friendly messages
- **Responsive design** for mobile/desktop

---

## 🔄 Integration Points with Developer 1

### What Developer 1 Provides:
- `BrowserController` - Handles all browser automation
- `ClaudeOrchestrator` - Makes AI decisions based on screenshots
- Screenshot capture and processing
- Action execution (click, type, navigate)

### How You Integrate:
```python
# In your WorkflowExecutor
from core.browser_controller import BrowserController
from core.orchestrator import ClaudeOrchestrator

class WorkflowExecutor:
    def __init__(self):
        self.browser = BrowserController()
        self.claude = ClaudeOrchestrator()
        self.review_queue = ReviewQueue()
        
    async def execute_workflow(self, goal: str, start_url: str = None):
        # Your orchestration logic here
        # Call self.browser.navigate(), self.browser.capture_screenshot()
        # Call self.claude.understand_screen_and_decide()
        # Handle human review when needed
        pass
```

---

## 🧪 Testing Strategy

### Your Testing Responsibilities:
1. **Workflow Execution Testing**
   - Test with various goal descriptions
   - Test error scenarios (invalid URLs, network issues)
   - Test human review flow
   - Verify logging completeness

2. **UI Testing**
   - Test form submission
   - Test real-time updates
   - Test error handling in UI
   - Test responsive design

3. **Integration Testing**
   - Test complete workflows end-to-end
   - Test with Developer 1's components
   - Performance testing
   - Load testing

---

## 🚨 Common Issues & Solutions

### Issue: FastAPI CORS Errors
**Solution:** Add CORS middleware
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

### Issue: Async/Await Problems
**Solution:** Ensure all your methods are async and use await properly
```python
async def execute_workflow(self, goal: str):
    result = await self.browser.navigate(url)  # Use await!
```

### Issue: Template Not Found
**Solution:** Check your template directory structure
```python
templates = Jinja2Templates(directory="templates")  # Relative to main.py
```

### Issue: Static Files Not Loading
**Solution:** Mount static files correctly
```python
app.mount("/static", StaticFiles(directory="static"), name="static")
```

---

## 📞 Communication with Developer 1

### Daily Sync Points:
1. **Morning Standup (15 min)**
   - What did you do yesterday?
   - What will you do today?
   - Any blockers?
   - Agree on shared files for the day

2. **Mid-Day Check-in (5 min)**
   - Quick progress update
   - Share any issues encountered
   - Coordinate on shared components

3. **End of Day Review (30 min)**
   - Demo what was built
   - Code review together
   - Merge to develop branch
   - Plan next day's work

### Key Communication Points:
- **Interface Contracts** - Agree on method signatures
- **Data Structures** - Share sample JSON responses
- **Error Handling** - Coordinate error codes and messages
- **Integration Points** - Test together on Day 3

---

## 🎯 Success Criteria

By the end of Day 7, you should have:

✅ **Working FastAPI server** with all required endpoints
✅ **Functional web UI** for workflow submission
✅ **Complete workflow execution engine** that coordinates everything
✅ **Human review system** with console-based approval
✅ **Comprehensive logging** with structured output
✅ **Data extraction demo** workflow
✅ **Complete documentation** and setup instructions
✅ **Successful demo presentation** to stakeholders

---

## 🚀 Getting Started Checklist

Before you begin coding:

- [ ] ✅ Have Anthropic API key (for testing Claude integration)
- [ ] ✅ Understand your role split with Developer 1
- [ ] ✅ Have development environment ready (Python 3.8+)
- [ ] ✅ Reviewed interface contracts
- [ ] ✅ Agreed on communication tools with Developer 1
- [ ] ✅ Cloned the repository
- [ ] ✅ Created your development branch

---

## 📚 Additional Resources

### FastAPI Documentation:
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [WebSocket Support](https://fastapi.tiangolo.com/advanced/websockets/)
- [Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)

### Async Python:
- [Async/Await Tutorial](https://docs.python.org/3/library/asyncio.html)
- [FastAPI Async Patterns](https://fastapi.tiangolo.com/async/)

### Frontend Integration:
- [JavaScript Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

## 🎉 Ready to Build!

You're now equipped with everything you need to succeed as Developer 2. Remember:

1. **Focus on your responsibilities** - Don't worry about Developer 1's tasks
2. **Communicate regularly** - Daily syncs are crucial
3. **Test thoroughly** - Your components are critical for the overall system
4. **Document everything** - You'll be leading the demo presentation
5. **Ask for help** - I'm here to assist you throughout the project

**Let's build an amazing Claude IPA MVP! 🚀**

---

*This guide will be updated as the project progresses. Keep it handy and refer to it daily.*
