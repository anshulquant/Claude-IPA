# Quick Test Guide - Safe Scenarios

## 🚀 How to Test

### Option 1: Automated Test Runner (Recommended)
```bash
python run_test_scenarios.py
```
This will run all 4 scenarios automatically and show a summary.

### Option 2: Manual Testing via Web UI

1. **Start the server:**
   ```bash
   python api/main.py
   ```

2. **Open browser:**
   ```
   http://127.0.0.1:8000
   ```

3. **Test each scenario below** (copy/paste into the form)

---

## 📋 Test Scenarios (Copy/Paste These)

### ✅ Test 1: Wikipedia Search (EASY)
```
Goal: Search for 'Python programming' on Wikipedia
Start URL: https://en.wikipedia.org
```

**Expected:**
- 5-7 steps
- Finds search box
- Types query
- Submits search
- Completes

**Why it works:** Wikipedia is automation-friendly, no captcha

---

### ✅ Test 2: Example.com (VERY EASY)
```
Goal: Read the main heading text from example.com
Start URL: https://example.com
```

**Expected:**
- 3-4 steps
- Navigates
- Reads text
- Completes

**Why it works:** Simplest possible page, always works

---

### ✅ Test 3: MDN Search (MEDIUM)
```
Goal: Search for 'JavaScript arrays' on MDN
Start URL: https://developer.mozilla.org
```

**Expected:**
- 5-7 steps
- Finds search
- Types query
- Submits
- Completes

**Why it works:** Developer docs, automation-friendly

---

### ✅ Test 4: W3Schools (EASY)
```
Goal: Navigate to W3Schools HTML try-it editor
Start URL: https://www.w3schools.com/html/tryit.asp?filename=tryhtml_default
```

**Expected:**
- 2-3 steps
- Navigates
- Verifies page
- Completes

**Why it works:** Educational site, no restrictions

---

## 🎯 What to Look For

### ✅ Good Signs:
- Steps complete in < 10 iterations
- No repeated actions
- Fields detected correctly
- Auto-completes when done
- No errors in logs

### ❌ Bad Signs:
- More than 15 steps
- Same action repeated 3+ times
- "Extracted 0 form fields" errors
- Workflow times out
- Browser crashes

---

## 📊 Expected Results

| Test | Steps | Time | Difficulty |
|------|-------|------|------------|
| Wikipedia | 5-7 | 30-40s | Easy |
| Example.com | 3-4 | 20-30s | Very Easy |
| MDN | 5-7 | 30-40s | Medium |
| W3Schools | 2-3 | 15-25s | Easy |

---

## 🐛 Troubleshooting

### If a test fails:

1. **Check the logs** - Look for error messages
2. **Check screenshots** - See what Claude saw (in `screenshots/` folder)
3. **Try again** - Some sites have rate limiting
4. **Reduce max_steps** - Set to 10 if it's looping

### Common Issues:

**"Extracted 0 form fields"**
- Site might be using dynamic forms (JavaScript)
- Try a simpler site first

**"Timeout waiting for selector"**
- Site might be slow to load
- Increase timeout in browser_controller.py

**"Too many steps"**
- Loop detection might not be working
- Check if filled fields are being tracked

---

## 🚫 Sites to AVOID

Don't test these (they WILL fail):

- ❌ Google.com (captcha)
- ❌ Facebook.com (blocks bots)
- ❌ Amazon.com (captcha)
- ❌ LinkedIn.com (requires auth)
- ❌ Twitter/X.com (blocks bots)

---

## 📝 Test Results Template

After each test, record:

```
Test: [Name]
Status: [PASS/FAIL]
Steps: [Number]
Time: [Seconds]
Issues: [Any problems]
Notes: [Observations]
```

---

## 🎉 Success Criteria

**All tests should:**
- ✅ Complete successfully
- ✅ Use < 10 steps
- ✅ Finish in < 60 seconds
- ✅ Show no errors
- ✅ Auto-complete when done

**If 3/4 tests pass, you're good to move to Iteration 3!**

---

## 🚀 Next Steps After Testing

Once tests pass:
1. Commit the changes
2. Move to **Iteration 3: Error Handling**
3. Add more advanced features
4. Test with real-world scenarios

---

**Ready? Start with Test 1 (Wikipedia)!** 🎯
