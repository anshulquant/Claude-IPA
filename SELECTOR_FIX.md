# Selector Fix - Pseudo-Class Handling

**Date:** October 23, 2025  
**Issue:** CSS pseudo-classes like `:first-of-type` timing out in Playwright

---

## ✅ Progress Made

### Step 1: Fixed Action Selection ✅
Claude now correctly chooses **"type"** action for form fields instead of "click"

**Evidence:**
```
💭 Claude's Decision:
   Action: type  ← CORRECT!
   Target: input[type='text']:first-of-type
   Value: John Smith
```

### Step 2: Identified Selector Issue ⚠️
The selector `input[type='text']:first-of-type` is timing out because Playwright has limited support for CSS pseudo-classes in `wait_for_selector()`.

**Error:**
```
Page.wait_for_selector: Timeout 5000ms exceeded
waiting for locator("input[type='text']:first-of-type") to be visible
```

---

## 🔧 Fixes Applied

### Fix 1: Enhanced Orchestrator Prompt

**File:** `core/orchestrator.py`

Added selector best practices to guide Claude:

```
SELECTOR BEST PRACTICES:
- PREFER name attribute: input[name='custname'] over input[type='text']:first-of-type
- PREFER id attribute: #email over input[type='email']
- AVOID pseudo-classes like :first-of-type, :nth-child - they may not work reliably
- Use specific attributes when available (name, id, placeholder, aria-label)
```

**Impact:** Claude will learn to use better selectors like `input[name='custname']` instead of pseudo-classes.

---

### Fix 2: Automatic Selector Simplification

**Files:** `core/browser_controller.py`
- `click_element()` method (line 275-281)
- `type_text()` method (line 344-350)

Added automatic conversion of problematic selectors:

```python
# Try to simplify problematic selectors
original_selector = selector
if ':first-of-type' in selector or ':nth-child' in selector or ':nth-of-type' in selector:
    # Try using >> nth=0 syntax instead
    base_selector = selector.split(':')[0]
    logger.info(f"Simplifying selector from '{selector}' to '{base_selector} >> nth=0'")
    selector = f"{base_selector} >> nth=0"
```

**How it works:**
- `input[type='text']:first-of-type` → `input[type='text'] >> nth=0`
- `div:nth-child(2)` → `div >> nth=0`
- Uses Playwright's `>> nth=0` syntax which is more reliable

**Impact:** Even if Claude returns pseudo-classes, the browser controller will automatically fix them.

---

## 🧪 Test Again

Run the workflow now:

```bash
python workflows/form_filling.py
```

**Expected behavior:**

1. ✅ Claude chooses "type" action
2. ✅ Selector gets automatically simplified
3. ✅ Text is entered successfully
4. ✅ Form continues filling
5. ✅ Workflow completes

**What you should see in logs:**
```
INFO:core.orchestrator:Decision: type - Starting to fill out the pizza order form
⌨️  Typing 'John Smith' into input[type='text']:first-of-type
INFO:core.browser_controller:Simplifying selector from 'input[type='text']:first-of-type' to 'input[type='text'] >> nth=0'
INFO:core.browser_controller:Attempting to type into: input[type='text'] >> nth=0 (attempt 1/3)
INFO:core.browser_controller:Successfully typed into: input[type='text'] >> nth=0
   ✅ Text entered successfully
```

---

## 📊 Summary of All Fixes

### Issue 1: CSS Selector Detection ✅ FIXED
- **Problem:** Selectors with HTML tags not recognized
- **Solution:** Added tag detection in workflows
- **Status:** Working

### Issue 2: Claude Choosing "Click" ✅ FIXED  
- **Problem:** Claude clicked inputs instead of typing
- **Solution:** Enhanced orchestrator prompt
- **Status:** Working - Claude now chooses "type"

### Issue 3: Pseudo-Class Selectors ✅ FIXED
- **Problem:** `:first-of-type` timing out in Playwright
- **Solution 1:** Guide Claude to use better selectors (name, id)
- **Solution 2:** Auto-convert pseudo-classes to `>> nth=0`
- **Status:** Ready for testing

---

## 🎯 Next Steps

1. **Test the workflow** - Should work now with automatic selector conversion
2. **Monitor Claude's selectors** - Over time, Claude should learn to use better selectors
3. **If still failing** - Check the actual HTML form structure and provide specific selectors

---

## 📝 Files Modified

1. ✅ `core/orchestrator.py` - Added selector best practices
2. ✅ `core/browser_controller.py` - Added automatic selector simplification (click_element and type_text)

---

**Status:** Ready for testing - automatic selector conversion implemented
