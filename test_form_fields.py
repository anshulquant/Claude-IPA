"""
Test script to verify form field detection works correctly.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.browser_controller import BrowserController


async def test_form_fields():
    """Test form field detection on httpbin.org form"""
    print("🧪 Testing Form Field Detection\n")
    
    browser = BrowserController(headless=False)  # Visible for debugging
    
    try:
        # Start browser
        print("1️⃣ Starting browser...")
        await browser.start()
        print("✅ Browser started\n")
        
        # Navigate to form
        print("2️⃣ Navigating to httpbin.org/forms/post...")
        await browser.navigate("https://httpbin.org/forms/post")
        print("✅ Navigation complete\n")
        
        # Get form fields (should be empty)
        print("3️⃣ Getting form fields (before filling)...")
        fields = await browser.get_form_fields()
        print(f"✅ Found {len(fields)} fields:\n")
        
        for field in fields:
            status = "✅ FILLED" if field['is_filled'] else "⬜ EMPTY"
            print(f"   {status} {field['selector']} ({field['type']})")
            if field['is_filled']:
                print(f"      Value: '{field['value']}'")
        
        print("\n" + "="*60 + "\n")
        
        # Fill a field
        print("4️⃣ Filling customer name field...")
        await browser.type_text("input[name='custname']", "John Doe")
        print("✅ Field filled\n")
        
        # Wait a bit for value to update
        await asyncio.sleep(1)
        
        # Get form fields again (should show filled)
        print("5️⃣ Getting form fields (after filling)...")
        fields = await browser.get_form_fields()
        print(f"✅ Found {len(fields)} fields:\n")
        
        filled_count = 0
        for field in fields:
            status = "✅ FILLED" if field['is_filled'] else "⬜ EMPTY"
            print(f"   {status} {field['selector']} ({field['type']})")
            if field['is_filled']:
                print(f"      Value: '{field['value']}'")
                filled_count += 1
        
        print(f"\n📊 Summary: {filled_count}/{len(fields)} fields filled")
        
        # Verify the name field is detected as filled
        name_field = next((f for f in fields if f['name'] == 'custname'), None)
        if name_field:
            if name_field['is_filled'] and name_field['value'] == 'John Doe':
                print("\n✅ SUCCESS: Field detection working correctly!")
            else:
                print(f"\n❌ FAILED: Name field not detected as filled")
                print(f"   is_filled: {name_field['is_filled']}")
                print(f"   value: '{name_field['value']}'")
        else:
            print("\n❌ FAILED: Name field not found")
        
        # Keep browser open for 5 seconds to inspect
        print("\n⏳ Keeping browser open for 5 seconds...")
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n6️⃣ Closing browser...")
        await browser.close()
        print("✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_form_fields())
