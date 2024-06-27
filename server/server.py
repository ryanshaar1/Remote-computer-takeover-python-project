import socket
import threading
import json
from PIL import Image
import io
import keyboard  # Assuming you have keyboard module installed
import mouse  # Assuming you have mouse module installed

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = int.from_bytes(raw_msglen, byteorder='big')
    print(f"Receiving message of length: {msglen}")
    # Read the message data
    return recvall(sock, msglen)

def recvall(sock, n):
    # Helper function to receive n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def handle_received_keyboard(connection):
    try:
        while True:
            key_pressed = recv_msg(connection).decode('utf-8')
            if key_pressed:
                print(f"Received key: {key_pressed}")
                keyboard.press_and_release(key_pressed)  # Simulate key press
    except Exception as e:
        print(f"Error handling keyboard: {e}")
    finally:
        connection.close()
        print("Keyboard connection closed")

def handle_received_mouse(connection):
    try:
        while True:
            mouse_data = recv_msg(connection).decode('utf-8')
            if mouse_data:
                print(f"Received mouse data: {mouse_data}")
                action, x, y = mouse_data.split(',')
                x, y = int(x), int(y)
                if action == "move":
                    mouse.move(x, y)
                elif action == "click":
                    mouse.click()
    except Exception as e:
        print(f"Error handling mouse: {e}")
    finally:
        connection.close()
        print("Mouse connection closed")

def handle_screenshot(connection):
    try:
        while True:
            screenshot_size = int(recv_msg(connection).decode('utf-8'))
            screenshot_data = b''
            remaining_size = screenshot_size
            while remaining_size > 0:
                chunk = connection.recv(min(remaining_size, 4096))
                screenshot_data += chunk
                remaining_size -= len(chunk)

            received_screenshot = Image.open(io.BytesIO(screenshot_data))
            received_screenshot.show()

            received_message = recv_msg(connection).decode()
            if received_message:
                print("Received message from client: ", received_message)
    except Exception as e:
        print(f"Error handling screenshot: {e}")
    finally:
        connection.close()
        print("Screenshot connection closed")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = "127.0.0.1"
port = 5000
sock.bind((ip, port))
sock.listen(5)

try:
    while True:
        print("Waiting for a connection...")
        connection, address = sock.accept()
        print(f"Connection established with {address}")
        
        socket_type_msg = recv_msg(connection).decode('utf-8')
        print(f"Received socket type message: {socket_type_msg}")

        try:
            socket_type_data = json.loads(socket_type_msg)
            socket_type = socket_type_data.get('socket_type')

            if socket_type == "keyboard":
                threading.Thread(target=handle_received_keyboard, args=(connection,)).start()
            elif socket_type == "mouse":
                threading.Thread(target=handle_received_mouse, args=(connection,)).start()
            elif socket_type == "screenshot":
                threading.Thread(target=handle_screenshot, args=(connection,)).start()
            else:
                print(f"Unknown socket type: {socket_type}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except KeyError as e:
            print(f"KeyError accessing socket_type: {e}")
        except Exception as e:
            print(f"Exception handling socket_type: {e}")
except KeyboardInterrupt:
    print("Shutting down server.")
finally:
    sock.close()
    print("Server socket closed")
