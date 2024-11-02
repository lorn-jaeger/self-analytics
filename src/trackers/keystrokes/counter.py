import time
import requests
from pynput import keyboard

keystroke_count = 0

def on_press(key):
    global keystroke_count
    keystroke_count += 1

keyboard.Listener(on_press=on_press).start()

while True:
    time.sleep(5)
    data = {
        'timestamp': int(time.time() * 1000),
        'keystrokes': keystroke_count
    }
    try:
        requests.post('http://localhost:8080/', json=data)
    except:
        pass
    keystroke_count = 0

