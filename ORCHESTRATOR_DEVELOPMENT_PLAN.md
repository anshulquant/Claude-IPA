# ClaudeOrchestrator Development Plan

## 🎯 Goal
Build `core/orchestrator.py` - the "brain" that analyzes screenshots and decides actions.

**Based on BUILD_PLAN.md - Developer 1 Tasks**

---

## 📋 Task Checklist

### Day 2: Core Implementation
- [x] Create `core/orchestrator.py` file
- [x] Import dependencies: `anthropic`, `os`, `json`
- [x] Create `ClaudeOrchestrator` class
- [x] Add `__init__` method - load API key from `.env`
- [x] Implement `understand_screen_and_decide()` method
- [ ] Test Claude API with sample screenshots
- [x] Parse JSON responses from Claude
- [x] Add basic error handling for API failures
- [ ] Push to branch: `feat/claude-integration`

### Day 5: Workflow Planning
- [x] Implement `generate_workflow_plan()` method
- [ ] Test Claude workflow planning with various inputs
- [ ] Help Developer 2 with async integration issues

---

## 🏗️ Interface Contract (From BUILD_PLAN.md)

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
        Analyze screenshot and decide next action.
        
        Returns:
            {
                "action": "click" | "type" | "navigate" | "complete" | "error",
                "target": "CSS selector or URL",
                "value": "text to type (if action=type)",
                "reasoning": "explanation of decision",
                "confidence": 0.0-1.0,
                "needs_human_review": bool
            }
        """
        pass
    
    async def generate_workflow_plan(self, natural_language_goal: str) -> list[str]:
        """
        Generate step-by-step workflow plan from natural language goal.
        
        Returns:
            ["Step 1 description", "Step 2 description", ...]
        """
        pass
    
```

---

## 📊 Expected Response Format (From BUILD_PLAN.md)

```json
{
  "action": "click" | "type" | "navigate" | "complete" | "error",
  "target": "selector or text or URL",
  "value": "text to type (if action=type)",
  "reasoning": "why this action",
  "confidence": 0.0 to 1.0,
  "needs_human_review": bool
}
```

---

## 🧪 Testing (From BUILD_PLAN.md - Day 2)

- [ ] Test Claude API with sample screenshots
- [ ] Verify JSON response parsing
- [ ] Test error handling for API failures

---

## ✅ Definition of Done (From BUILD_PLAN.md)

Day 2 Complete When:
- [ ] `core/orchestrator.py` created
- [ ] `understand_screen_and_decide()` working
- [ ] Claude API tested with screenshots
- [ ] JSON parsing working
- [ ] Basic error handling added
- [ ] Pushed to `feat/claude-integration` branch

Day 5 Complete When:
- [ ] `generate_workflow_plan()` working
- [ ] Tested with various goals

---

## 🚀 Ready to Build!

Let's create `core/orchestrator.py` following BUILD_PLAN.md requirements only.
