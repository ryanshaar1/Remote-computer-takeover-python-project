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

def recv_msg(sock):
    try:
        raw_msglen = recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        return recvall(sock, msglen)
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None

def recvall(sock, n):
    data = bytearray()
    try:
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
    except Exception as e:
        print(f"Error receiving all data: {e}")
        return None

def send_msg(sock, msg):
    try:
        msg = msg.encode('utf-8') if isinstance(msg, str) else msg
        msg = struct.pack('>I', len(msg)) + msg
        sock.sendall(msg)
        print(f"Sent message: {msg}")
    except Exception as e:
        print(f"Error sending message: {e}")

def send_keyboard_events():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("10.100.102.11", 5001))
        print("Connected to server for keyboard")
        while True:
            button = keyboard.read_event()
            if button.event_type == keyboard.KEY_DOWN:
                key_pressed = button.name
                print(f"Sending key: {key_pressed}")
                send_msg(sock, key_pressed)
    except Exception as e:
        print(f"Error sending keyboard events: {e}")
    finally:
        sock.close()
        print("Keyboard connection closed")

def get_screen_size():
    from tkinter import Tk
    root = Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height

def receive_screen_size(sock):
    msg = recv_msg(sock)
    if msg is None:
        raise Exception("Failed to receive screen size")
    msg = msg.decode('utf-8')
    action, width, height = msg.split(',')
    if action == 'screen_size':
        return int(width), int(height)
    else:
        raise Exception("Unexpected message")

def send_mouse_events(remote_screen_size):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("10.100.102.11", 5002))
        print("Connected to server for mouse")

        # Get local screen sizes
        local_screen_width, local_screen_height = get_screen_size()
        remote_screen_width, remote_screen_height = remote_screen_size

        def scale_coordinates(x, y):
            scaled_x = x * (remote_screen_width / local_screen_width)
            scaled_y = y * (remote_screen_height / local_screen_height)
            return int(scaled_x), int(scaled_y)

        def on_move(x, y):
            try:
                scaled_x, scaled_y = scale_coordinates(x, y)
                send_msg(sock, f"move,{scaled_x},{scaled_y}")
            except Exception as e:
                print(f"Error sending mouse move: {e}")

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

def handle_received_screenshot(remote_screen_size, screenshot_queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("10.100.102.11", 5003))
        print("Connected to server for screenshots")
        
        while True:
            msg = recvall(sock, 4)
            if not msg:
                break
            screenshot_size = struct.unpack('>I', msg)[0]

            screenshot_data = recvall(sock, screenshot_size)
            if screenshot_data is None:
                print("Did not receive complete screenshot data")
                continue
            
            screenshot_queue.put(screenshot_data)

    except Exception as e:
        print(f"Error handling screenshot: {e}")
    finally:
        sock.close()
        print("Screenshot connection closed")

# Function to setup and connect to the screen size server
def get_remote_screen_size():
    screen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        screen_sock.connect(("10.100.102.11", 5000))
        remote_screen_size = receive_screen_size(screen_sock)
        print(f"Remote screen size: {remote_screen_size}")
        return remote_screen_size
    except Exception as e:
        print(f"Error getting remote screen size: {e}")
        return None
    finally:
        screen_sock.close()

# Get remote screen size before starting other threads
remote_screen_size = get_remote_screen_size()
screen_size = get_screen_size()
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

def main():
    if not remote_screen_size:
        print("Failed to get remote screen size. Exiting...")
        return

    screenshot_queue = queue.Queue()

    threading.Thread(target=handle_received_screenshot, args=(remote_screen_size, screenshot_queue), daemon=True).start()

    root = tk.Tk()
    root.title("Live Screen")

    remote_screen_width, remote_screen_height = remote_screen_size
    root.geometry(f"{remote_screen_width}x{remote_screen_height}")

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
