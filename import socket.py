import socket
import threading

NUM_CLIENTS = 1000
MESSAGE_INTERVAL = 1 # seconds

clients = []

# Connect a client to the server
def connect_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 8080))
    clients.append(client)
    print(f'Client connected: {client.getsockname()}')

# Send a message to all connected clients
def send_message():
    message = b'Hello, world!'
    for client in clients:
        client.send(message)

# Connect the specified number of clients to the server
for i in range(NUM_CLIENTS):
    threading.Thread(target=connect_client).start()

# Send a message to all connected clients at the specified interval
while True:
    threading.Timer(MESSAGE_INTERVAL, send_message).start()