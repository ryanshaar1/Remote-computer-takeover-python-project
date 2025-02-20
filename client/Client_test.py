import socket
import threading
import io
import struct
import keyboard
from pynput import mouse
import tkinter as tk
from PIL import Image, ImageTk
import time
import queue

# פונקציה לקבלת הודעה מהשרת
def recv_msg(sock):
    try:
        raw_msglen = recvall(sock, 4)  # קריאת אורך ההודעה
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]  # פריסת אורך ההודעה
        return recvall(sock, msglen)  # קריאת ההודעה כולה
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None

# פונקציה לקבלת נתונים מהשרת בגודל מסויים
def recvall(sock, n):
    data = bytearray()
    try:
        while len(data) < n:
            packet = sock.recv(n - len(data))  # קבלת חלק מהנתונים
            if not packet:
                return None
            data.extend(packet)  # הוספת החלקים למערך
        return data
    except Exception as e:
        print(f"Error receiving all data: {e}")
        return None

# פונקציה לשליחת הודעה לשרת
def send_msg(sock, msg):
    try:
        msg = msg.encode('utf-8') if isinstance(msg, str) else msg  # קידוד הודעה במידת הצורך
        msg = struct.pack('>I', len(msg)) + msg  # הוספת אורך ההודעה לתחילת ההודעה
        sock.sendall(msg)  # שליחת ההודעה כולה
        print(f"Sent message: {msg}")
    except Exception as e:
        print(f"Error sending message: {e}")

# פונקציה לשליחת אירועי מקלדת לשרת
def send_keyboard_events():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("10.100.102.11", 5001))  # חיבור לשרת
        print("Connected to server for keyboard")
        while True:
            button = keyboard.read_event()  # קריאת אירוע מקלדת
            if button.event_type == keyboard.KEY_DOWN:
                key_pressed = button.name
                print(f"Sending key: {key_pressed}")
                send_msg(sock, key_pressed)  # שליחת אירוע מקלדת
    except Exception as e:
        print(f"Error sending keyboard events: {e}")
    finally:
        sock.close()
        print("Keyboard connection closed")

# פונקציה לקבלת גודל המסך המקומי
def get_screen_size():
    from tkinter import Tk
    root = Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height

# פונקציה לקבלת גודל המסך מרחוק מהשרת
def receive_screen_size(sock):
    msg = recv_msg(sock)  # קבלת ההודעה
    if msg is None:
        raise Exception("Failed to receive screen size")
    msg = msg.decode('utf-8')
    action, width, height = msg.split(',')
    if action == 'screen_size':
        return int(width), int(height)
    else:
        raise Exception("Unexpected message")

# פונקציה לשליחת אירועי עכבר לשרת
def send_mouse_events(remote_screen_size):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("10.100.102.11", 5002))  # חיבור לשרת
        print("Connected to server for mouse")

        # קבלת גדלי המסכים המקומי והמרוחק
        local_screen_width, local_screen_height = get_screen_size()
        remote_screen_width, remote_screen_height = remote_screen_size

        # פונקציה להמרת קואורדינטות המקומיות לקואורדינטות המרוחקות
        def scale_coordinates(x, y):
            scaled_x = x * (remote_screen_width / local_screen_width)
            scaled_y = y * (remote_screen_height / local_screen_height)
            return int(scaled_x), int(scaled_y)

        # פונקציה לשליחת אירועי תזוזת עכבר
        def on_move(x, y):
            try:
                scaled_x, scaled_y = scale_coordinates(x, y)
                send_msg(sock, f"move,{scaled_x},{scaled_y}")
            except Exception as e:
                print(f"Error sending mouse move: {e}")

        # פונקציה לשליחת אירועי לחיצת עכבר
        def on_click(x, y, button, pressed):
            try:
                scaled_x, scaled_y = scale_coordinates(x, y)
                send_msg(sock, f"click,{scaled_x},{scaled_y},{button.name},{pressed}")
            except Exception as e:
                print(f"Error sending mouse click: {e}")

        with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
            listener.join()

    except Exception as e:
        print(f"Error sending mouse events: {e}")
    finally:
        sock.close()
        print("Mouse connection closed")

# פונקציה לטיפול בקבלת צילומי מסך מהשרת
def handle_received_screenshot(remote_screen_size, screenshot_queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("10.100.102.11", 5003))  # חיבור לשרת
        print("Connected to server for screenshots")
        
        while True:
            msg = recvall(sock, 4)  # קבלת גודל צילום המסך
            if not msg:
                break
            screenshot_size = struct.unpack('>I', msg)[0]

            screenshot_data = recvall(sock, screenshot_size)  # קבלת צילום המסך
            if screenshot_data is None:
                print("Did not receive complete screenshot data")
                continue
            
            screenshot_queue.put(screenshot_data)  # הוספת הנתונים לתור

    except Exception as e:
        print(f"Error handling screenshot: {e}")
    finally:
        sock.close()
        print("Screenshot connection closed")

# פונקציה לחיבור לשרת ולקבלת גודל המסך המרוחק
def get_remote_screen_size():
    screen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        screen_sock.connect(("10.100.102.11", 5000))
        remote_screen_size = receive_screen_size(screen_sock)  # קבלת גודל המסך
        print(f"Remote screen size: {remote_screen_size}")
        return remote_screen_size
    except Exception as e:
        print(f"Error getting remote screen size: {e}")
        return None
    finally:
        screen_sock.close()

# קבלת גודל המסך המרוחק לפני התחלת השרשורים האחרים 
remote_screen_size = get_remote_screen_size()
screen_size = get_screen_size()

# פונקציה לעדכון תווית צילום המסך בממשק הגרפי
def update_screenshot_label(root, label, screenshot_queue, remote_screen_size, screen_size):
    if not screenshot_queue.empty():
        screenshot_data = screenshot_queue.get()

        image_stream = io.BytesIO(screenshot_data)
        image_stream.seek(0)
        img = Image.open(image_stream)
        img = img.resize(screen_size)

        photo = ImageTk.PhotoImage(img)

        label.config(image=photo)
        label.image = photo

    root.after(100, update_screenshot_label, root, label, screenshot_queue, remote_screen_size, screen_size)

# פונקציה ראשית  
def main():
    if not remote_screen_size:
        print("Failed to get remote screen size. Exiting...")
        return

    screenshot_queue = queue.Queue()

    threading.Thread(target=handle_received_screenshot, args=(remote_screen_size, screenshot_queue), daemon=True).start()
    screen_width, screen_height = get_screen_size()
    root = tk.Tk()

    root.title("Live Screen")

    root.geometry(f"{screen_width}x{screen_height}")

    label = tk.Label(root)
    label.pack()

    root.after(100, update_screenshot_label, root, label, screenshot_queue, remote_screen_size, screen_size)
    root.mainloop()

if __name__ == "__main__":
    keyboard_thread = threading.Thread(target=send_keyboard_events, daemon=True)
    mouse_thread = threading.Thread(target=send_mouse_events, args=(remote_screen_size,), daemon=True)

    keyboard_thread.start()
    mouse_thread.start()

    main()
