import requests
r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe")
print(r.status_code, r.json())