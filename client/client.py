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

def send_screenshots(sock):
    try:
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
    except socket.error as e:
        print(f"Socket error sending screenshots: {e}")
    except Exception as e:
        print(f"Error sending screenshots: {e}")
    finally:
        sock.close()  # Ensure the socket is closed
        print("Screenshot connection closed")

def start_screenshot_thread():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", 5003))
        print("Connected to server for screenshots")
        send_screenshots(sock)
    except Exception as e:
        print(f"Error connecting to server for screenshots: {e}")
    finally:
        sock.close()

def send_messages():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", 5001))
        send_msg(sock, json.dumps({"socket_type": "keyboard"}))
        print("Connected to server for keyboard")
        
        while True:
            button = keyboard.read_event()
            if button.event_type == keyboard.KEY_DOWN:
                key_pressed = button.name
                print(f"Sending key: {key_pressed}")  # Debug print
                if key_pressed == "space":
                    key_pressed = " "
                elif key_pressed == "enter":
                    key_pressed = "\n"
                elif key_pressed == "tab":
                    key_pressed = "\t"
                elif key_pressed == "backspace":
                    key_pressed = "\b"
                elif key_pressed == "ctrl":
                    key_pressed = "^"
                elif key_pressed == "shift":
                    key_pressed = "@"
                send_msg(sock, key_pressed)
    except Exception as e:
        print(f"Error sending messages: {e}")
    finally:
        sock.close()  # Ensure the socket is closed
        print("Keyboard connection closed")

def on_move(x, y):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 5002))  # Connect to mouse server port
        send_msg(sock, f"move,{x},{y}")
    except Exception as e:
        print(f"Error sending mouse move: {e}")
    finally:
        sock.close()

def on_click(x, y, button, pressed):
    if pressed:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("127.0.0.1", 5002))  # Connect to mouse server port
            send_msg(sock, f"click,{x},{y},{button.name},{pressed}")
        except Exception as e:
            print(f"Error sending mouse click: {e}")
        finally:
            sock.close()

def listener_mouse():
    try:
        with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
            listener.join()
    except Exception as e:
        print(f"Error handling mouse events: {e}")
    finally:
        print("Mouse listener stopped")

# Start threads for each functionality
screenshot_thread = threading.Thread(target=start_screenshot_thread)
message_thread = threading.Thread(target=send_messages)
mouse_listener_thread = threading.Thread(target=listener_mouse)

screenshot_thread.start()
message_thread.start()
mouse_listener_thread.start()

# Join threads to wait for them to finish
screenshot_thread.join()
message_thread.join()
mouse_listener_thread.join()
