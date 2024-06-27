import socket
import threading
import json
import time
from PIL import ImageGrab as image  # This should be used to capture screenshots
import io
import keyboard  # This is for capturing keyboard events
import mouse  # This is for capturing mouse events
import struct

def send_msg(sock, msg):
    try:
        msg = msg.encode('utf-8') if isinstance(msg, str) else msg
        msg = struct.pack('>I', len(msg)) + msg  # Prefix with message length
        sock.sendall(msg)
        print(f"Sent message: {msg}")  # Debug print
    except Exception as e:
        print(f"Error sending message: {e}")


def send_screenshots():
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(("127.0.0.1", 5003))
            print("Connected to server for screenshots")
            
            screenshot = image.grab(bbox=(0, 0, 1920, 1080))
            screenshot_bytes = io.BytesIO()
            screenshot.save(screenshot_bytes, format='JPEG')
            screenshot_data = screenshot_bytes.getvalue()

            send_msg(sock, str(len(screenshot_data)))

            chunk_size = 4096
            for i in range(0, len(screenshot_data), chunk_size):
                sock.send(screenshot_data[i:i+chunk_size])
            
            time.sleep(0.05)
        except socket.error as e:
            print(f"Socket error sending screenshots: {e}")
        except Exception as e:
            print(f"Error sending screenshots: {e}")
        finally:
            sock.close()  # Ensure the socket is closed
            print("Screenshot connection closed")

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

def listener_mouse():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", 5003))
        send_msg(sock, json.dumps({"socket_type": "mouse"}))
        print("Connected to server for mouse")

        def on_move(x, y):
            try:
                send_msg(sock, f"move,{x},{y}")
            except Exception as e:
                print(f"Error sending mouse move: {e}")

        def on_click(x, y, button, pressed):
            if pressed:
                try:
                    send_msg(sock, f"click,{x},{y}")
                except Exception as e:
                    print(f"Error sending mouse click: {e}")

        mouse.on_move(on_move)
        mouse.on_click(on_click)
        while True:
            time.sleep(0.1)
    except Exception as e:
        print(f"Error connecting to server for mouse: {e}")
    finally:
        sock.close()  # Ensure the socket is closed
        print("Mouse connection closed")

screenshot_thread = threading.Thread(target=send_screenshots)
message_thread = threading.Thread(target=send_messages)
listener_thread = threading.Thread(target=listener_mouse)

screenshot_thread.start()
message_thread.start()
listener_thread.start()

screenshot_thread.join()
message_thread.join()
listener_thread.join()
