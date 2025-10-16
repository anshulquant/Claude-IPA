# 🚀 Quick Start: LMS Automation

## TL;DR - 3 Simple Steps

### **1. Save Your Login (One Time)**
```bash
python workflows/auth_helper.py
```
- Browser opens
- Login with Google OAuth manually
- Press Enter when logged in
- Done! Session saved to `auth_state.json`

### **2. Run Automated Workflow**
```bash
python workflows/lms_workflow.py
```
- Enter your LMS URL
- Describe what you want Claude to do
- Watch it work autonomously!

### **3. Check Results**
- View screenshots in `screenshots/` folder
- See step-by-step execution in terminal

---

## 💡 Example Tasks

**Simple:**
- "Navigate to the dashboard"
- "Find the Python course"
- "Show my assignments"

**Advanced:**
- "Find the Python course and download all materials"
- "Check my progress in all enrolled courses"
- "Navigate to Module 3 and read the lesson content"

---

## ⚠️ Important

- `auth_state.json` = Your login session (keep private!)
- Session expires after some time (re-run step 1 if needed)
- Headless mode = invisible browser (faster)
- Screenshots saved for debugging

---

## 🎯 What Makes This Different?

**Traditional automation:**
```python
# ❌ Breaks when website changes
driver.find_element_by_id("course-123").click()
```

**Our AI-guided automation:**
```python
# ✅ Adapts to changes
Claude sees the page → Finds the course visually → Clicks it
```

---

## 📚 Full Documentation

See `LMS_SETUP_GUIDE.md` for detailed instructions.

---

**Ready? Run `python workflows/auth_helper.py` to get started!** 🎉
