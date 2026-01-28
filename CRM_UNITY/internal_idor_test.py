import requests

# 1. REPLACE THIS with the sessionid from your Browser Dev Tools
# (F12 -> Application -> Cookies -> sessionid)
USER_SESSION_ID = "PASTE_YOUR_SESSION_ID_HERE"

# 2. Pick a Member Code you want to test access for
target_member = "MIP001" 
target_url = f"http://127.0.0.1:8000/global-members/{target_member}/"

def test_internal_permissions():
    cookies = {'sessionid': USER_SESSION_ID}
    print(f"--- Testing Internal Access for Member: {target_member} ---")
    
    try:
        # allow_redirects=False ensures we see the real server response
        response = requests.get(target_url, cookies=cookies, allow_redirects=False)
        
        if response.status_code == 200:
            print(f"[!] ALERT: Access Granted to {target_url}")
            print("    Check: Are you supposed to have access to this specific member?")
        elif response.status_code == 403:
            print(f"[SAFE] 403 Forbidden: Server blocked the request (Good!)")
        elif response.status_code == 302:
            print(f"[INFO] 302 Redirect: Your session might be expired or invalid.")
        else:
            print(f"Server returned status: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_internal_permissions()