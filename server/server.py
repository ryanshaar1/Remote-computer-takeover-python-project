import socket
import threading
from PIL import Image
import io
import struct
import cv2
import numpy as np
import keyboard
import mouse

def recv_msg(sock):
    try:
        raw_msglen = recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]  # Unpack message length
        print(f"Receiving message of length: {msglen}")
        return recvall(sock, msglen)  # Read message data based on length
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
                try:
                    parts = mouse_data.split(',')
                    action = parts[0]
                    if action == "move":
                        x = int(parts[1])
                        y = int(parts[2])
                        mouse.move(x, y)
                    elif action == "click":
                        x = int(parts[1])
                        y = int(parts[2])
                        button = parts[3]
                        pressed = parts[4] == 'True'
                        if pressed:
                            mouse.press(button)
                        else:
                            mouse.release(button)
                    else:
                        print(f"Unknown action: {action}")
                except (IndexError, ValueError) as e:
                    print(f"Error parsing mouse data: {e}")
    except Exception as e:
        print(f"Error handling mouse: {e}")
    finally:
        connection.close()
        print("Mouse connection closed")

def handle_received_screenshot(connection):
    # Create an Empty window
    cv2.namedWindow("Live", cv2.WINDOW_NORMAL)
    # Resize this window
    cv2.resizeWindow("Live", 480, 270)
    
    try:
        while True:
            msg = recv_msg(connection)
            if msg is None:
                break
            screenshot_size = int(msg.decode('utf-8'))
            print(f"Expecting screenshot of size: {screenshot_size}")
            
            screenshot_data = recvall(connection, screenshot_size)
            if screenshot_data is None:
                print("Did not receive complete screenshot data")
                continue
            
            print(f"Received screenshot of size: {len(screenshot_data)}")
            # Convert the received bytes to numpy array
            frame = np.frombuffer(screenshot_data, dtype=np.uint8)
            # Decode the image
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            if frame is None:
                print("Error decoding image")
                continue

            # Display the frame
            cv2.imshow('Live', frame)

            # Wait for a short period to display the image
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Error handling screenshot: {e}")
    finally:
        connection.close()
        cv2.destroyAllWindows()
        print("Screenshot connection closed")

# Define ports for each functionality
keyboard_port = 5001
mouse_port = 5002
screenshot_port = 5003

# Create socket listeners for each port
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
            # Accept connections for keyboard
            keyboard_connection, keyboard_address = keyboard_sock.accept()
            print(f"Connection established with Keyboard at {keyboard_address}")
            threading.Thread(target=handle_received_keyboard, args=(keyboard_connection,)).start()

            # Accept connections for mouse
            mouse_connection, mouse_address = mouse_sock.accept()
            print(f"Connection established with Mouse at {mouse_address}")
            threading.Thread(target=handle_received_mouse, args=(mouse_connection,)).start()

            # Accept connections for screenshot
            screenshot_connection, screenshot_address = screenshot_sock.accept()
            print(f"Connection established with Screenshot at {screenshot_address}")
            threading.Thread(target=handle_received_screenshot, args=(screenshot_connection,)).start()

        except Exception as e:
            print(f"Error accepting connection: {e}")

except KeyboardInterrupt:
    print("Shutting down server.")
finally:
    keyboard_sock.close()
    mouse_sock.close()
    screenshot_sock.close()
    print("Server sockets closed")
