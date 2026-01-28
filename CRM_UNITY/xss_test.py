import requests
from html import escape

# Update this to your actual search or profile view URL
target_url = "http://127.0.0.1:8000/search" 

# Payloads ranging from basic to 'sneaky' (bypassing simple filters)
xss_payloads = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert(1)>",
    "'> <script>alert(1)</script>",
    "javascript:alert(1)"
]

def test_xss(url):
    print(f"--- Starting XSS Audit on {url} ---")
    
    for payload in xss_payloads:
        # 'q' is the name of the input field in your HTML (e.g., <input name="q">)
        params = {'q': payload}
        
        try:
            response = requests.get(url, params=params)
            
            # Check if the raw payload exists in the HTML response
            if payload in response.text:
                print(f"[!] VULNERABLE: Payload '{payload}' was reflected in the HTML!")
                print(f"    Evidence: ...{response.text[response.text.find(payload)-20:response.text.find(payload)+50]}...")
            else:
                print(f"[SAFE] Payload '{payload}' was not detected in the output.")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_xss(target_url)