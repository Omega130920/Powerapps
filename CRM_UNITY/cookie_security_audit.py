import requests

# Using a session ensures we capture and persist cookies correctly
session = requests.Session()
# Hitting the admin login is a reliable way to trigger CSRF and Session cookies
url = "http://127.0.0.1:8000/admin/login/" 

def audit_cookie_metadata():
    try:
        # We simulate a real browser User-Agent to avoid being blocked by security middleware
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = session.get(url, headers=headers, timeout=5)
        
        print(f"--- Cookie Security Audit for {url} ---")
        
        if not session.cookies:
            print("[FAIL] No cookies detected. Ensure your Django server is running and the URL is correct.")
            return

        for cookie in session.cookies:
            print(f"\n[Cookie Name: {cookie.name}]")
            
            # 1. HttpOnly Check: Prevents JavaScript (XSS) from accessing the cookie
            if cookie.has_nonstandard_attr('HttpOnly') or 'HttpOnly' in str(cookie):
                print("  [PASS] HttpOnly: YES (Protected against XSS theft)")
            else:
                print("  [FAIL] HttpOnly: NO (CRITICAL: JavaScript can steal this session!)")
            
            # 2. Secure Check: Ensures cookie is only sent over HTTPS
            if cookie.secure:
                print("  [PASS] Secure: YES (Encrypted transit only)")
            else:
                # Normal for 127.0.0.1, but should be FAIL in production
                print("  [INFO] Secure: NO (Acceptable for local development, but required for LIVE)")

            # 3. SameSite Check: Prevents CSRF attacks
            samesite = cookie.get_nonstandard_attr('SameSite')
            if samesite:
                print(f"  [PASS] SameSite: {samesite}")
            else:
                print("  [WARN] SameSite: Not set (Potential CSRF risk)")

    except requests.RequestException as e:
        print(f"[ERROR] Connection failed: {e}")

if __name__ == "__main__":
    audit_cookie_metadata()