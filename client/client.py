import socket
import threading
import io
import struct
import keyboard
from pynput import mouse
import tkinter as tk
from PIL import Image, ImageTk

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
        sock.connect("127.0.0.1", 5001)
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


def send_mouse_events():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", 5002))
        print("Connected to server for mouse")

        # Get screen sizes
        local_screen_width, local_screen_height = get_screen_size()
        remote_screen_width = 1920  
        remote_screen_height = 1080  

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

def handle_received_screenshot():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", 5003))
        print("Connected to server for screenshots")
        
        root = tk.Tk()
        root.title("Live Screen")
        
        label = tk.Label(root)
        label.pack()

        while True:
            msg = recvall(sock, 4)
            if not msg:
                break
            screenshot_size = struct.unpack('>I', msg)[0]

            screenshot_data = recvall(sock, screenshot_size)
            if screenshot_data is None:
                print("Did not receive complete screenshot data")
                continue
            
            image_stream = io.BytesIO(screenshot_data)
            image_stream.seek(0)
            img = Image.open(image_stream)
            img = img.resize((1920, 1080))  # Adjust size as needed



            photo = ImageTk.PhotoImage(img)

            label.config(image=photo)
            label.image = photo



            root.update()

        root.mainloop()

    except Exception as e:
        print(f"Error handling screenshot: {e}")
    finally:
        sock.close()
        print("Screenshot connection closed")

def receive_screen_size():
    pass

# Start threads for each functionality
screensize_thread = threading.Thread(target=receive_screen_size)
keyboard_thread = threading.Thread(target=send_keyboard_events)
mouse_thread = threading.Thread(target=send_mouse_events)
screenshot_thread = threading.Thread(target=handle_received_screenshot)

screensize_thread.start()
keyboard_thread.start()
mouse_thread.start()
screenshot_thread.start()

screensize_thread.join()
keyboard_thread.join()
mouse_thread.join()
screenshot_thread.join()