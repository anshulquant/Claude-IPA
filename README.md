# Claude IPA MVP - Day 1 Setup Complete! 🚀

## 🎯 Project Overview

This is a Claude-powered Intelligent Process Automation MVP built by two developers in parallel. You are **Developer 2** focusing on orchestration and frontend components.

## 📁 Project Structure

```
claude-ipa-mvp/
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore file
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── core/                        # Core business logic
│   ├── __init__.py
│   ├── workflow_executor.py    # [YOURS] Main execution engine
│   └── review_queue.py          # [YOURS] Human review logic
│
├── api/                         # FastAPI server
│   ├── __init__.py
│   └── main.py                  # [YOURS] REST API endpoints
│
├── templates/                   # HTML templates
│   └── index.html              # [YOURS] Web UI
│
├── static/                      # Static files
│   ├── style.css               # [YOURS] CSS styles
│   └── app.js                  # [YOURS] JavaScript
│
├── workflows/                   # Demo workflows
│   ├── __init__.py
│   └── data_extraction.py       # [YOURS] Demo workflow #3
│
├── tests/                       # Unit tests
│   ├── __init__.py
│   ├── test_browser.py
│   └── test_orchestrator.py
│
├── logs/                        # Execution logs (auto-generated)
└── screenshots/                 # Screenshot storage (auto-generated)
```

## 🚀 Quick Start

### 1. Set Up Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
copy env.example .env

# Edit .env file with your credentials
# Add your Anthropic API key:
ANTHROPIC_API_KEY=your_api_key_here

# Add your Azure Storage credentials:
AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string_here
AZURE_STORAGE_CONTAINER_NAME=claude-ipa-screenshots
AZURE_STORAGE_CONTAINER_LOGS=claude-ipa-logs
```

### 3. Start the Server

```bash
# Start FastAPI server
python api/main.py

# Or use uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the Web UI

Open your browser and go to: http://localhost:8000

## 🎨 Features Implemented (Day 1)

### ✅ FastAPI Server
- REST API endpoints for workflow execution
- Real-time status updates
- Background task processing
- CORS middleware for frontend integration

### ✅ Web UI
- Modern, responsive design
- Workflow submission form
- Real-time progress tracking
- Execution log display
- Workflow history

### ✅ Core Components
- `WorkflowExecutor` skeleton with mock execution
- `ReviewQueue` with console-based human review
- Comprehensive logging system
- Error handling and recovery

### ✅ Demo Workflow
- Data extraction workflow template
- Multi-page extraction support
- Data validation and formatting

### ✅ Azure Storage Integration
- Automatic screenshot storage in Azure Blob Storage
- Workflow logs and data persistence
- Local fallback when Azure Storage unavailable
- File management and retrieval APIs

## 🔌 API Endpoints

### Workflow Execution
```http
POST /api/execute-workflow
Content-Type: application/json

{
    "goal": "Go to Google and search for 'machine learning tutorials'",
    "start_url": "https://google.com"
}
```

### Status Checking
```http
GET /api/workflow-status/{workflow_id}
```

### Workflow History
```http
GET /api/workflow-history
```

### Health Check
```http
GET /api/health
```

### Azure Storage Info
```http
GET /api/storage/info
```

### Workflow Files
```http
GET /api/workflow-files/{workflow_id}
```

## 🧪 Testing the Setup

### 1. Test Server Startup
```bash
python api/main.py
```
You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Test Web UI
1. Open http://localhost:8000
2. Fill in a workflow goal
3. Click "Start Automation"
4. Watch the real-time progress

### 3. Test API Endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# Start workflow
curl -X POST http://localhost:8000/api/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{"goal": "Test workflow", "start_url": "https://google.com"}'
```

## 🔧 Development Commands

### Run with Auto-reload
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest tests/
```

### Check Logs
```bash
# View application logs
tail -f logs/app.log
```

## 📝 Day 1 Checklist

- [x] ✅ Clone repository and set up Python virtual environment
- [x] ✅ Install dependencies: `pip install fastapi uvicorn python-dotenv jinja2`
- [x] ✅ Create basic project structure
- [x] ✅ Set up logging configuration
- [x] ✅ Create `api/main.py` with basic FastAPI app
- [x] ✅ Create `templates/index.html` with simple workflow submission form
- [x] ✅ Create `core/workflow_executor.py` skeleton
- [x] ✅ Test basic FastAPI server startup

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
uvicorn api.main:app --port 8001
```

### Module Import Errors
```bash
# Make sure you're in the project root directory
cd claude-ipa-mvp

# Check Python path
python -c "import sys; print(sys.path)"
```

### Static Files Not Loading
- Ensure `static/` directory exists
- Check FastAPI static file mounting in `api/main.py`
- Verify file permissions

### Environment Variables Not Loading
- Check `.env` file exists in project root
- Verify `python-dotenv` is installed
- Ensure `.env` is not in `.gitignore` (but `.env` should be)

## 🔄 Next Steps (Day 2)

### Morning Tasks:
- [ ] Pull latest `develop` branch
- [ ] Implement `WorkflowExecutor.execute_workflow()` method
- [ ] Add execution loop with mock browser/claude calls
- [ ] Implement comprehensive logging system

### Afternoon Tasks:
- [ ] Create `core/review_queue.py` stub
- [ ] Add basic human review workflow
- [ ] Test workflow execution with mock data
- [ ] Push to branch: `feat/workflow-engine`

## 🤝 Integration with Developer 1

### Interface Contracts (Agree on Day 1)
You'll need to integrate with Developer 1's components:

```python
# BrowserController (Developer 1)
class BrowserController:
    async def start(self) -> None
    async def navigate(self, url: str) -> None
    async def capture_screenshot(self) -> tuple[bytes, str]
    async def click_element(self, selector: str) -> None
    async def type_text(self, selector: str, text: str) -> None

# ClaudeOrchestrator (Developer 1)
class ClaudeOrchestrator:
    async def understand_screen_and_decide(
        self, screenshot_b64: str, goal: str, current_step: str
    ) -> dict
```

## 📞 Support

If you encounter any issues:

1. Check the logs in `logs/app.log`
2. Verify all dependencies are installed
3. Ensure environment variables are set correctly
4. Test individual components separately

## 🎉 Congratulations!

You've successfully completed Day 1 setup! Your FastAPI server is running, the web UI is functional, and you have a solid foundation for the next 6 days of development.

**Ready for Day 2? Let's build the core workflow execution engine! 🚀**
