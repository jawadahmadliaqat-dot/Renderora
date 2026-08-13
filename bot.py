import time
import requests

# Enter your Render app's live URL here (which should be your home or render endpoint)
RENDER_URL = "https://renderora.onrender.com" 

def keep_alive():
    print(f"Uptime bot started for: {RENDER_URL}")
    while True:
        try:
            response = requests.get(RENDER_URL)
            if response.status_code == 200:
                print(f"[SUCCESS] Pinged successfully! Status: {response.status_code}")
            else:
                print(f"[WARNING] Server responded with status: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Failed to ping server: {e}")
        
        # Ping again after every 10 minutes (600 seconds) because Render goes to sleep after 15 minutes of inactivity
        time.sleep(600)

if __name__ == "__main__":
    keep_alive()
