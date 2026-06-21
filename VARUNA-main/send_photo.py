import os
import requests

# Load token from environment or ../.env
token = os.getenv('TELEGRAM_BOT_TOKEN')
if not token:
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith('TELEGRAM_BOT_TOKEN'):
                    token = line.split('=', 1)[1].strip()
                    break
if not token:
    raise SystemExit('TELEGRAM_BOT_TOKEN not found')

chat_id = os.getenv('TELEGRAM_CHAT_ID') or '5205831814'
photo_path = os.path.join(os.path.dirname(__file__), 'test.jpg')

with open(photo_path, 'rb') as img:
    resp = requests.post(f'https://api.telegram.org/bot{token}/sendPhoto',
                         data={'chat_id': chat_id, 'caption': 'Test photo from SIH'},
                         files={'photo': img})
print(resp.status_code)
print(resp.text)
