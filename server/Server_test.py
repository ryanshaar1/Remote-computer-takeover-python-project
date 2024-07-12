import socket
import threading
import io
import struct
from PIL import ImageGrab as ImageGrab
import time
import pyautogui
from pynput.mouse import Controller as MouseController

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

def handle_received_keyboard(connection):
    try:
        while True:
            msg = recv_msg(connection)
            if msg is None:
                break
            key_pressed = msg.decode('utf-8')
            if key_pressed:
                print(f"Received key: {key_pressed}")
                pyautogui.press(key_pressed)
    except Exception as e:
        print(f"Error handling keyboard: {e}")
    finally:
        connection.close()
        print("Keyboard connection closed")

def handle_received_mouse(connection):
    mouse = MouseController()
    try:
        while True:
            msg = recv_msg(connection)
            if msg is None:
                break
            mouse_data = msg.decode('utf-8')
            if mouse_data:
                print(f"Received mouse data: {mouse_data}")
                action, *params = mouse_data.split(',')
                if action == 'move':
                    x, y = map(int, params)
                    mouse.position = (x, y)
                elif action == 'click':
                    x, y, button, pressed = params
                    mouse.position = (int(x), int(y))
                    if pressed == 'True':
                        pyautogui.mouseDown(button=button)
                    else:
                        pyautogui.mouseUp(button=button)
    except Exception as e:
        print(f"Error handling mouse: {e}")
    finally:
        connection.close()
        print("Mouse connection closed")

def send_screenshots(connection):
    try:
        while True:
            screenshot = ImageGrab.grab()
            screenshot_bytes = io.BytesIO()
            screenshot.save(screenshot_bytes, format='JPEG')
            screenshot_data = screenshot_bytes.getvalue()

            connection.sendall(struct.pack('>I', len(screenshot_data)))
            connection.sendall(screenshot_data)
            
            time.sleep(0.1)
    except Exception as e:
        print(f"Error sending screenshots: {e}")
    finally:
        connection.close()
        print("Screenshot connection closed")

def send_screensize(connection):
    try:
        width, height = pyautogui.size()
        screensize_msg = f"screen_size,{width},{height}"
        send_msg(connection, screensize_msg)
    except Exception as e:
        print(f"Error sending screen size: {e}")
    finally:
        connection.close()
        print("Screen size connection closed")

def send_msg(sock, msg):
    try:
        msg = msg.encode('utf-8') if isinstance(msg, str) else msg
        msg = struct.pack('>I', len(msg)) + msg
        sock.sendall(msg)
        print(f"Sent message: {msg}")
    except Exception as e:
        print(f"Error sending message: {e}")

# Define ports for each functionality
screensize_port = 5000
keyboard_port = 5001
mouse_port = 5002
screenshot_port = 5003

# Create socket listeners for each port

screensize_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
screensize_sock.bind(("127.0.0.1", screensize_port))
screensize_sock.listen(5)  

keyboard_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
keyboard_sock.bind(("127.0.0.1", keyboard_port))
keyboard_sock.listen(5)

mouse_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mouse_sock.bind(("127.0.0.1", mouse_port))
mouse_sock.listen(5)

screenshot_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
screenshot_sock.bind(("127.0.0.1", screenshot_port))
screenshot_sock.listen(5)

print("Server started, waiting for connections...")

try:
    while True:
        try:
            screensize_connection, screensize_address = screensize_sock.accept()
            print(f"Connection established with Screensize at {screensize_address}")
            threading.Thread(target=send_screensize, args=(screensize_connection,)).start()

            keyboard_connection, keyboard_address = keyboard_sock.accept()
            print(f"Connection established with Keyboard at {keyboard_address}")
            threading.Thread(target=handle_received_keyboard, args=(keyboard_connection,)).start()

            mouse_connection, mouse_address = mouse_sock.accept()
            print(f"Connection established with Mouse at {mouse_address}")
            threading.Thread(target=handle_received_mouse, args=(mouse_connection,)).start()

            screenshot_connection, screenshot_address = screenshot_sock.accept()
            print(f"Connection established with Screenshot at {screenshot_address}")
            threading.Thread(target=send_screenshots, args=(screenshot_connection,)).start()

        except Exception as e:
            print(f"Error accepting connection: {e}")

except KeyboardInterrupt:
    print("Shutting down server.")
finally:
    screensize_sock.close()
    keyboard_sock.close()
    mouse_sock.close()
    screenshot_sock.close()
    print("Server sockets closed")
