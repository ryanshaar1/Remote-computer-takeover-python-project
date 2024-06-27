import socket
import pickle
from PIL import Image
import zlib
import threading

# קליטת והצגת מסך בזמן אמת
def receive_screenshots():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, UDP_PORT))
        while True:
            data, addr = s.recvfrom(65536)
            screenshot = pickle.loads(zlib.decompress(data))
            screenshot.show()

# הגדרת התקשורת
HOST = '0.0.0.0'  # מאפשר קבלה מכל כתובת IP
UDP_PORT = 5001

def main():
    screenshot_thread = threading.Thread(target=receive_screenshots)
    screenshot_thread.start()
    screenshot_thread.join()

if __name__ == "__main__":
    main()
