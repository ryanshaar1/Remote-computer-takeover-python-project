import socket
import threading
import json
from PIL import Image
import io
import keyboard  # Assuming you have keyboard module installed
import mouse  # Assuming you have mouse module installed

def recv_msg(sock):
    try:
        raw_msglen = recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = int.from_bytes(raw_msglen, byteorder='big')
        print(f"Receiving message of length: {msglen}")
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
                keyboard.press_and_release(key_pressed)
    except Exception as e:
        print(f"Error handling keyboard: {e}")
    finally:
        connection.close()
        print("Keyboard connection closed")

def handle_received_mouse(connection):
    try:
        while True:
            msg = recv_msg(connection)
            if msg is None:
                break
            mouse_data = msg.decode('utf-8')
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
            msg = recv_msg(connection)
            if msg is None:
                break
            screenshot_size = int(msg.decode('utf-8'))
            screenshot_data = b''
            remaining_size = screenshot_size
            while remaining_size > 0:
                chunk = connection.recv(min(remaining_size, 4096))
                screenshot_data += chunk
                remaining_size -= len(chunk)

            received_screenshot = Image.open(io.BytesIO(screenshot_data))
            received_screenshot.show()

            received_message = recv_msg(connection)
            if received_message:
                print("Received message from client: ", received_message.decode())
    except Exception as e:
        print(f"Error handling screenshot: {e}")
    finally:
        connection.close()
        print("Screenshot connection closed")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = "127.0.0.1"
port = 5000

try:
    sock.bind((ip, port))
    sock.listen(5)
    print("Server started, waiting for connections...")

    while True:
        try:
            connection, address = sock.accept()
            print(f"Connection established with {address}")

            socket_type_msg = recv_msg(connection)
            if socket_type_msg is None:
                connection.close()
                continue

            socket_type_data = json.loads(socket_type_msg.decode('utf-8'))
            socket_type = socket_type_data.get('socket_type')

            if socket_type == "keyboard":
                threading.Thread(target=handle_received_keyboard, args=(connection,)).start()
            elif socket_type == "mouse":
                threading.Thread(target=handle_received_mouse, args=(connection,)).start()
            elif socket_type == "screenshot":
                threading.Thread(target=handle_screenshot, args=(connection,)).start()
            else:
                print(f"Unknown socket type: {socket_type}")
                connection.close()
        except Exception as e:
            print(f"Error accepting connection: {e}")
except KeyboardInterrupt:
    print("Shutting down server.")
finally:
    sock.close()
    print("Server socket closed")
