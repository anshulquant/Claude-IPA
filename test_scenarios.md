# Test Scenarios - Safe Sites (No Captcha)

## ✅ Scenario 1: httpbin.org Form (TESTED)
**Status:** PASSED ✅
- Goal: Fill form with name and email
- Steps: 8 (was 40 before)
- Result: Success, auto-completed

---

## 🧪 Scenario 2: Wikipedia Search

**Site:** https://en.wikipedia.org
**Goal:** Search for "Python programming" and verify results
**Expected Steps:** 5-7

### Test Command:
```json
{
  "goal": "Search for 'Python programming' on Wikipedia",
  "start_url": "https://en.wikipedia.org"
}
```

### Expected Behavior:
1. Navigate to Wikipedia
2. Find search input
3. Type "Python programming"
4. Press Enter or click search
5. Verify results page loaded
6. Complete

### Why This Works:
- ✅ No captcha
- ✅ Simple search form
- ✅ Fast loading
- ✅ Stable selectors

---

## 🧪 Scenario 3: Example.com Text Extraction

**Site:** https://example.com
**Goal:** Extract the main heading text
**Expected Steps:** 3-4

### Test Command:
```json
{
  "goal": "Read the main heading text from example.com",
  "start_url": "https://example.com"
}
```

### Expected Behavior:
1. Navigate to example.com
2. Analyze page
3. Extract text "Example Domain"
4. Complete

### Why This Works:
- ✅ Simplest possible page
- ✅ No forms, no interactions
- ✅ Just text extraction
- ✅ Always available

---

## 🧪 Scenario 4: The Cat API (Public API Form)

**Site:** https://thecatapi.com
**Goal:** Navigate and explore the documentation
**Expected Steps:** 4-6

### Test Command:
```json
{
  "goal": "Go to The Cat API homepage and find the documentation link",
  "start_url": "https://thecatapi.com"
}
```

### Expected Behavior:
1. Navigate to site
2. Find documentation link
3. Click it
4. Verify new page
5. Complete

### Why This Works:
- ✅ Public API site
- ✅ No authentication needed
- ✅ Simple navigation
- ✅ Developer-friendly

---

## 🧪 Scenario 5: JSONPlaceholder Form Test

**Site:** https://jsonplaceholder.typicode.com
**Goal:** Navigate to the guide section
**Expected Steps:** 3-5

### Test Command:
```json
{
  "goal": "Navigate to JSONPlaceholder and find the guide",
  "start_url": "https://jsonplaceholder.typicode.com"
}
```

### Expected Behavior:
1. Navigate to site
2. Analyze page
3. Find guide link
4. Click if needed
5. Complete

### Why This Works:
- ✅ Free fake API service
- ✅ No rate limiting for browsing
- ✅ Simple layout
- ✅ Automation-friendly

---

## 🧪 Scenario 6: MDN Web Docs Search

**Site:** https://developer.mozilla.org
**Goal:** Search for "JavaScript arrays"
**Expected Steps:** 5-7

### Test Command:
```json
{
  "goal": "Search for 'JavaScript arrays' on MDN",
  "start_url": "https://developer.mozilla.org"
}
```

### Expected Behavior:
1. Navigate to MDN
2. Find search box
3. Type "JavaScript arrays"
4. Submit search
5. Verify results
6. Complete

### Why This Works:
- ✅ Developer documentation
- ✅ No captcha
- ✅ Good for automation
- ✅ Fast and reliable

---

## 🧪 Scenario 7: W3Schools Try It Editor

**Site:** https://www.w3schools.com/html/tryit.asp?filename=tryhtml_default
**Goal:** Navigate to the try-it editor
**Expected Steps:** 2-3

### Test Command:
```json
{
  "goal": "Navigate to W3Schools HTML try-it editor",
  "start_url": "https://www.w3schools.com/html/tryit.asp?filename=tryhtml_default"
}
```

### Expected Behavior:
1. Navigate to editor
2. Verify page loaded
3. Complete

### Why This Works:
- ✅ Educational site
- ✅ No restrictions
- ✅ Simple page
- ✅ Always accessible

---

## ❌ Sites to AVOID (Will Block/Captcha)

### Don't Test These:
- ❌ **Google.com** - Captcha for automation
- ❌ **Facebook.com** - Blocks bots aggressively
- ❌ **Twitter/X.com** - Requires auth, blocks bots
- ❌ **Amazon.com** - Captcha and bot detection
- ❌ **LinkedIn.com** - Requires auth, blocks bots
- ❌ **Instagram.com** - Blocks automated access
- ❌ **Reddit.com** - Rate limiting and captcha

---

## 📋 Test Checklist

Run these in order:

1. ✅ **httpbin.org form** (Already passed)
2. ⬜ **Wikipedia search** (Simple search)
3. ⬜ **Example.com** (Text extraction)
4. ⬜ **MDN search** (Documentation search)
5. ⬜ **W3Schools** (Navigation only)

---

## 🎯 Success Criteria

For each test:
- ✅ Completes in < 10 steps
- ✅ No infinite loops
- ✅ Correct field detection
- ✅ Auto-completes when done
- ✅ No errors or crashes

---

## 🚀 How to Run Tests

### Via Web UI:
1. Start server: `python api/main.py`
2. Go to http://127.0.0.1:8000
3. Paste goal and URL from scenarios above
4. Click "Execute Workflow"
5. Watch the logs

### Via Test Script:
```bash
python test_full_workflow.py
```
(Edit the goal/URL in the script first)

---

## 📊 Expected Results Summary

| Scenario | Steps | Time | Status |
|----------|-------|------|--------|
| httpbin form | 8 | 37s | ✅ PASS |
| Wikipedia search | 5-7 | 30-40s | ⬜ TBD |
| Example.com | 3-4 | 20-30s | ⬜ TBD |
| MDN search | 5-7 | 30-40s | ⬜ TBD |
| W3Schools | 2-3 | 15-25s | ⬜ TBD |

---

**Ready to test? Start with Wikipedia search!** 🚀
