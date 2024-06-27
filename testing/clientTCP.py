import socket
import threading
import pyautogui  # ספרייה לשליטה על העכבר והמקלדת

# קליטת לחיצות מקלדת ועכבר
def receive_messages():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, TCP_PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024)
                if data:
                    message = data.decode()
                    print(message)
                    process_message(message)

def process_message(message):
    if message.startswith("Key"):
        # טיפול בלחיצות מקלדת, ניתן להוסיף קוד לביצוע פעולה לפי הלחיצה
        pass
    elif message.startswith("Mouse clicked"):
        # טיפול בלחיצות עכבר, ניתן להוסיף קוד לביצוע פעולה לפי הלחיצה
        pass
    elif message.startswith("Mouse moved"):
        _, coords = message.split("to")
        x, y = map(int, coords.strip()[1:-1].split(","))
        pyautogui.moveTo(x, y)

# הגדרת התקשורת
HOST = '0.0.0.0'  # מאפשר קבלה מכל כתובת IP
TCP_PORT = 5000

def main():
    message_thread = threading.Thread(target=receive_messages)
    message_thread.start()
    message_thread.join()

if __name__ == "__main__":
    main()
