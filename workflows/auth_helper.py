#!/usr/bin/env python3
"""
Authentication Helper for LMS with Google OAuth

This script helps you login once and save the authentication state.
Then your automation workflows can reuse the saved session.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from browser_controller import BrowserController


async def save_auth_state(lms_url: str, auth_state_file: str = "auth_state.json"):
    """
    Open browser, let user login manually, then save the auth state.
    
    Args:
        lms_url: Your LMS URL
        auth_state_file: File to save authentication state
    """
    print("\n" + "="*70)
    print("AUTHENTICATION HELPER")
    print("="*70)
    print(f"\nLMS URL: {lms_url}")
    print(f"Auth state will be saved to: {auth_state_file}\n")
    
    # Use non-headless so you can see and interact
    browser = BrowserController(headless=False)
    
    try:
        await browser.start()
        print("[1/4] Browser started")
        
        # Navigate to your LMS
        print(f"[2/4] Navigating to {lms_url}...")
        await browser.navigate(lms_url)
        
        print("\n" + "="*70)
        print("MANUAL LOGIN REQUIRED")
        print("="*70)
        print("\n1. Complete the Google OAuth login in the browser window")
        print("2. Wait until you're fully logged into your LMS")
        print("3. Press Enter here when you're logged in...")
        input("\nPress Enter when logged in: ")
        
        # Save the authentication state
        print("\n[3/4] Saving authentication state...")
        context = browser._context
        if context:
            await context.storage_state(path=auth_state_file)
            print(f"[OK] Authentication state saved to: {auth_state_file}")
        else:
            print("[ERROR] No browser context available")
            return
        
        print("\n[4/4] Verifying saved state...")
        current_url = await browser.get_current_url()
        print(f"      Current URL: {current_url}")
        
        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"\nAuthentication state saved to: {auth_state_file}")
        print("\nYou can now use this in your workflows:")
        print(f"  browser = BrowserController(auth_state_file='{auth_state_file}')")
        
    finally:
        await browser.close()


async def test_auth_state(lms_url: str, auth_state_file: str = "auth_state.json"):
    """
    Test if the saved auth state works.
    
    Args:
        lms_url: Your LMS URL
        auth_state_file: Saved authentication state file
    """
    print("\n" + "="*70)
    print("TESTING SAVED AUTHENTICATION")
    print("="*70)
    
    if not Path(auth_state_file).exists():
        print(f"\n[ERROR] Auth state file not found: {auth_state_file}")
        print("Run save_auth_state() first!")
        return
    
    browser = BrowserController(headless=True, auth_state_file=auth_state_file)
    
    try:
        await browser.start()
        print("[1/3] Browser started with saved auth state")
        
        print(f"[2/3] Navigating to {lms_url}...")
        await browser.navigate(lms_url)
        await asyncio.sleep(3)
        
        print("[3/3] Checking if logged in...")
        current_url = await browser.get_current_url()
        page_title = await browser.get_page_title()
        
        print(f"\n      URL: {current_url}")
        print(f"      Title: {page_title}")
        
        if "login" in current_url.lower() or "signin" in current_url.lower():
            print("\n[WARNING] Might not be logged in (URL contains 'login')")
        else:
            print("\n[OK] Appears to be logged in!")
        
    finally:
        await browser.close()


async def main():
    """Interactive menu."""
    print("\n" + "="*70)
    print("LMS AUTHENTICATION HELPER")
    print("="*70)
    
    lms_url = input("\nEnter your LMS URL (e.g., https://lms.yourcompany.com): ").strip()
    
    if not lms_url:
        print("[ERROR] LMS URL is required!")
        return
    
    print("\nWhat would you like to do?")
    print("1. Save authentication state (login manually)")
    print("2. Test saved authentication state")
    
    choice = input("\nChoice (1 or 2): ").strip()
    
    if choice == "1":
        await save_auth_state(lms_url)
    elif choice == "2":
        await test_auth_state(lms_url)
    else:
        print("[ERROR] Invalid choice!")


if __name__ == "__main__":
    asyncio.run(main())
