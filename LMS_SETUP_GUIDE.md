# LMS Automation Setup Guide

## 🎯 Goal
Automate tasks in your company's Learning Management System (LMS) that uses Google OAuth authentication.

---

## 📋 Step-by-Step Setup

### **Step 1: Save Your Login Session**

Run the authentication helper to login once and save your session:

```bash
python workflows/auth_helper.py
```

**What happens:**
1. Browser opens (non-headless so you can see it)
2. You navigate to your LMS
3. You complete Google OAuth login manually
4. Script saves your authentication cookies/tokens to `auth_state.json`
5. Future workflows will reuse this saved session!

**Example interaction:**
```
Enter your LMS URL: https://lms.yourcompany.com
Choice (1 or 2): 1

[Browser opens]
[You login with Google]
[You see your LMS dashboard]

Press Enter when logged in: [ENTER]

✓ Authentication state saved to: auth_state.json
```

---

### **Step 2: Test the Saved Authentication**

Verify that the saved session works:

```bash
python workflows/auth_helper.py
```

Choose option 2 to test:

```
Choice (1 or 2): 2

[1/3] Browser started with saved auth state
[2/3] Navigating to https://lms.yourcompany.com...
[3/3] Checking if logged in...

      URL: https://lms.yourcompany.com/dashboard
      Title: Dashboard - LMS

[OK] Appears to be logged in!
```

---

### **Step 3: Run Automated Workflows**

Now you can run autonomous workflows on your LMS:

```bash
python workflows/lms_workflow.py
```

**Example tasks:**
- "Find and open the Python programming course"
- "Navigate to my assignments and show the latest one"
- "Go to the dashboard and check my progress"
- "Download the course materials for Module 3"

**What happens:**
1. Browser starts with your saved login session (already authenticated!)
2. Claude analyzes the LMS interface
3. Claude autonomously navigates to complete your task
4. Screenshots saved at each step for debugging

---

## 🔐 How Google OAuth Authentication Works

### **Traditional Approach (Won't Work):**
```python
# ❌ Can't automate Google OAuth directly
browser.type("email", "your@email.com")
browser.type("password", "yourpassword")
# Google detects automation and blocks it!
```

### **Our Approach (Works!):**
```python
# ✅ Login once manually, save the session
# Step 1: Manual login (one time)
python workflows/auth_helper.py  # You login manually

# Step 2: Reuse saved session (automated)
browser = BrowserController(auth_state_file="auth_state.json")
# Browser is already logged in! No need to login again!
```

---

## 📁 Files Created

After running the auth helper:

```
d:\Claude-Automation\
├── auth_state.json          # Your saved login session (KEEP PRIVATE!)
├── workflows/
│   ├── auth_helper.py       # Tool to save/test authentication
│   └── lms_workflow.py      # Autonomous LMS workflows
└── screenshots/
    └── lms_step_*.png       # Screenshots from workflow execution
```

---

## ⚠️ Important Notes

### **Security:**
- `auth_state.json` contains your login cookies/tokens
- **DO NOT commit this file to Git!**
- **DO NOT share this file!**
- Add it to `.gitignore`

### **Session Expiration:**
- Saved sessions may expire after some time (hours/days)
- If workflows start failing, re-run `auth_helper.py` to refresh the session

### **Headless Mode:**
- Workflows run in headless mode (invisible browser) for speed
- Change to `headless=False` in `lms_workflow.py` if you want to watch

---

## 🎯 Example Workflow

**Goal:** Find and open a specific course

```bash
python workflows/lms_workflow.py
```

```
Enter your LMS URL: https://lms.yourcompany.com
Task description: Find and open the Python programming course

STEP 1: Navigating to LMS...
STEP 2: Claude sees dashboard, clicking on "Courses" menu
STEP 3: Claude sees course list, searching for "Python"
STEP 4: Claude found "Python Programming 101", clicking it
STEP 5: Course page loaded, reading content

SUCCESS! Goal achieved in 5 steps!
```

---

## 🚀 Advanced Usage

### **Custom Workflows:**

Create your own workflow by copying `lms_workflow.py`:

```python
async def my_custom_lms_task():
    orchestrator = ClaudeOrchestrator()
    
    async with BrowserController(auth_state_file="auth_state.json") as browser:
        # Your custom automation logic
        await browser.navigate("https://lms.yourcompany.com")
        
        # Let Claude decide what to do
        decision = await orchestrator.understand_screen_and_decide(
            screenshot_b64=screenshot,
            goal="Your custom goal here",
            current_step="Starting",
            page_text=page_text
        )
        
        # Execute Claude's decision
        # ... (see lms_workflow.py for full example)
```

---

## 🐛 Troubleshooting

### **Problem: "Auth state file not found"**
**Solution:** Run `python workflows/auth_helper.py` first to save your login session

### **Problem: "Appears to be on login page"**
**Solution:** Session expired. Re-run `auth_helper.py` to refresh

### **Problem: "Browser crashes on startup"**
**Solution:** Use `headless=True` mode (default in workflows)

### **Problem: "Claude gets stuck in a loop"**
**Solution:** Workflow has built-in loop detection. Check screenshots to debug

---

## 📚 Next Steps

1. ✅ Save your authentication with `auth_helper.py`
2. ✅ Test it works with option 2
3. ✅ Run your first workflow with `lms_workflow.py`
4. ✅ Create custom workflows for your specific LMS tasks
5. ✅ Build a web UI to trigger workflows (see BUILD_PLAN.md)

---

## 💡 Tips

- **Start simple:** Test with basic tasks like "Navigate to dashboard"
- **Check screenshots:** All steps are captured in `screenshots/` folder
- **Adjust max_steps:** Increase if your task needs more steps
- **Use descriptive goals:** "Find Python course and download materials" is better than "Find course"
- **Monitor costs:** Each Claude API call costs money, check your usage

---

**Happy Automating! 🎉**
