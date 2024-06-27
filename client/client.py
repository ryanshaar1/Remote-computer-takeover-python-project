import socket
import threading
import json
import time
from PIL import ImageGrab as image  # For capturing screenshots
import io
import keyboard  # For capturing keyboard events
from pynput import mouse  # For capturing mouse events
import struct

def send_msg(sock, msg):
    try:
        msg = msg.encode('utf-8') if isinstance(msg, str) else msg
        msg = struct.pack('>I', len(msg)) + msg  # Prefix with message length
        sock.sendall(msg)
        print(f"Sent message: {msg}")  # Debug print
    except Exception as e:
        print(f"Error sending message: {e}")

def send_keyboard_events():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", 5001))  # Connect to keyboard server port
        print("Connected to server for keyboard")
        
        while True:
            button = keyboard.read_event()
            if button.event_type == keyboard.KEY_DOWN:
                key_pressed = button.name
                print(f"Sending key: {key_pressed}")  # Debug print
                send_msg(sock, key_pressed)
    except Exception as e:
        print(f"Error sending keyboard events: {e}")
    finally:
        sock.close()
        print("Keyboard connection closed")

def send_mouse_events():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", 5002))  # Connect to mouse server port
        print("Connected to server for mouse")

        def on_move(x, y):
            try:
                send_msg(sock, f"move,{x},{y}")
            except Exception as e:
                print(f"Error sending mouse move: {e}")

        def on_click(x, y, button, pressed):
            try:
                send_msg(sock, f"click,{x},{y},{button.name},{pressed}")
            except Exception as e:
                print(f"Error sending mouse click: {e}")

        with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
            listener.join()

    except Exception as e:
        print(f"Error sending mouse events: {e}")
    finally:
        sock.close()
        print("Mouse connection closed")

def send_screenshots():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", 5003))  # Connect to screenshot server port
        print("Connected to server for screenshots")

        while True:
            screenshot = image.grab(bbox=(0, 0, 1920, 1080))
            screenshot_bytes = io.BytesIO()
            screenshot.save(screenshot_bytes, format='JPEG')
            screenshot_data = screenshot_bytes.getvalue()

            send_msg(sock, str(len(screenshot_data)))

            chunk_size = 4096
            for i in range(0, len(screenshot_data), chunk_size):
                sock.send(screenshot_data[i:i+chunk_size])
            
            time.sleep(0.1)
    except Exception as e:
        print(f"Error sending screenshots: {e}")
    finally:
        sock.close()
        print("Screenshot connection closed")

# Start threads for each functionality
keyboard_thread = threading.Thread(target=send_keyboard_events)
mouse_thread = threading.Thread(target=send_mouse_events)
screenshot_thread = threading.Thread(target=send_screenshots)

keyboard_thread.start()
mouse_thread.start()
screenshot_thread.start()

# Join threads to wait for them to finish
keyboard_thread.join()
mouse_thread.join()
screenshot_thread.join()
