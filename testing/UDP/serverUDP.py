import socket
import threading
import time
from PIL import ImageGrab
import pickle
import zlib

# שליחת צילומי מסך בזמן אמת
def send_screenshots():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        while True:
            screenshot = ImageGrab.grab()
            data = zlib.compress(pickle.dumps(screenshot))
            s.sendto(data, (HOST, UDP_PORT))
            time.sleep(0.1)  # 10 frames per second

# הגדרת התקשורת
HOST = 'IP של לפטופ'
UDP_PORT = 5001

def main():
    screenshot_thread = threading.Thread(target=send_screenshots)
    screenshot_thread.start()
    screenshot_thread.join()

if __name__ == "__main__":
    main()
