import socket
import threading
import tkinter as tk
from PIL import Image, ImageTk
import io
import struct

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
                # Handle key press here
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
                # Handle mouse action here
    except Exception as e:
        print(f"Error handling mouse: {e}")
    finally:
        connection.close()
        print("Mouse connection closed")

def handle_received_screenshot(connection):
    try:
        root = tk.Tk()
        root.title("Live Screen")
        
        label = tk.Label(root)
        label.pack()

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

            # Create a PIL image from the received data
            image_stream = io.BytesIO(screenshot_data)
            image_stream.seek(0)
            img = Image.open(image_stream)
            
            # Resize the image if necessary
            img = img.resize((640, 360))  # Adjust size as needed

            # Convert PIL image to Tkinter PhotoImage
            photo = ImageTk.PhotoImage(img)

            # Update label with the new image
            label.config(image=photo)
            label.image = photo

            root.update()

        root.mainloop()

    except Exception as e:
        print(f"Error handling screenshot: {e}")
    finally:
        connection.close()
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
