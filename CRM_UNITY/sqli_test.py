import requests

# Your local development URL and login endpoint
target_url = "http://127.0.0.1:8000/login" 

# Common SQLi payloads to test authentication bypass
payloads = [
    "' OR '1'='1",
    "admin' --",
    "' OR TRUE --",
    "\" OR \"1\"=\"1"
]

def test_sql_injection(url):
    print(f"Starting SQLi test on {url}...\n")
    
    for payload in payloads:
        # These keys ('username', 'password') must match the 'name' attributes 
        # in your HTML form tags.
        data = {
            "username": payload,
            "password": "password123" 
        }
        
        try:
            response = requests.post(url, data=data)
            
            # Check if the payload caused a change in behavior
            # (e.g., redirected to a dashboard or didn't show "Invalid credentials")
            if "Dashboard" in response.text or response.status_code == 302:
                print(f"[!] POTENTIAL VULNERABILITY: Payload '{payload}' bypassed login!")
            else:
                print(f"[SAFE] Payload '{payload}' was rejected.")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_sql_injection(target_url)