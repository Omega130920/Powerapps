import requests

targets = [
    "http://127.0.0.1:8000/global-members/",
    "http://127.0.0.1:8000/emails/"
]

def run_crm_audit():
    print("--- Starting CRM Depth Audit ---")
    
    for base in targets:
        print(f"\nChecking path: {base}")
        for i in range(1, 15):
            test_url = f"{base}{i}/"
            try:
                # allow_redirects=False lets us see if the server tries to kick us to /login/
                response = requests.get(test_url, allow_redirects=False)
                
                if response.status_code == 200:
                    print(f"[!] EXPOSED: {test_url} (No login required!)")
                elif response.status_code in [301, 302]:
                    print(f"[SAFE] {test_url} - Redirected to Login")
                elif response.status_code == 403:
                    print(f"[SAFE] {test_url} - Forbidden")
                
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    run_crm_audit()