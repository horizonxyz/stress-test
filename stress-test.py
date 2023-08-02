import socket
import threading
import struct
import ctypes
import mysql.connector
import time

# The stress-test.py file performs a stress test on a game server by simulating multiple
# client connections. It connects to a MySQL database and selects a specified number of 
# rows from the game_accounts and characters tables using a JOIN statement. It then packs
# the selected data into a C++ data structure called CZ_ENTER, which represents the data 
# that would be sent from a client to the server when logging in. Finally, it sends the
# packed data to the server using a TCP socket connection. This process is repeated for a 
# specified number of iterations to simulate multiple client connections. The purpose of
# this stress test is to evaluate the performance and stability of the game server 
# under heavy load.

# Connect to the database
db = mysql.connector.connect(
  host="localhost",
  user="horizon",
  password="horizon",
  database="horizon",
  auth_plugin='mysql_native_password'
)
cursor = db.cursor()

# Pack the data into a binary format
NUM_CLIENTS = 5000
# Execute the SELECT statement with a JOIN
sql = f"SELECT a.id, b.id FROM game_accounts as a JOIN characters as b ON a.id = b.account_id WHERE a.id != 1 LIMIT {NUM_CLIENTS}"
cursor.execute(sql)

# Fetch all the rows and print them to the console
rows = cursor.fetchall()

# Define the C++ data structure
class CZ_ENTER(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('_packet_id', ctypes.c_uint16),
        ('_account_id', ctypes.c_uint32),
        ('_char_id', ctypes.c_uint32),
        ('_auth_code', ctypes.c_uint32),
        ('_client_time', ctypes.c_uint32),
        ('_gender', ctypes.c_uint8)
    ]

class ZC_REFUSE_ENTER(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('_packet_id', ctypes.c_uint16),
        ('_type', ctypes.c_uint8)
    ]
MESSAGE_INTERVAL = 1 # seconds

clients = []

# Connect a client to the server
def connect_client(account_id, character_id):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 5121))
    clients.append(client)
    print(f'Client connected: {client.getsockname()}')
    
    data = CZ_ENTER()
    data._packet_id = 0x0436
    data._account_id = account_id
    data._char_id = character_id
    data._auth_code = account_id
    data._client_time = 0
    data._gender = 0
    login_data = ctypes.string_at(ctypes.addressof(data), ctypes.sizeof(data))

    expected_size = ctypes.sizeof(data)
    actual_size = len(login_data)
    print(ctypes.sizeof(data), len(login_data))
    if actual_size != expected_size:
        raise ValueError(f'Packed data size does not match expected size: {actual_size} != {expected_size}')

    client.send(login_data)
    receive_messages(client)

# Receive messages from the server
def receive_messages(client):
    while True:
        message = client.recv(client.getsockname()[1])
        if not message:
            break
        #print(f'Received message: {message.decode()}')
        packet_id = int.from_bytes(message[:2], byteorder='little')
        print(hex(packet_id))
        if packet_id == 0x0074:
            data = ZC_REFUSE_ENTER.from_buffer_copy(message)
            print(f"Rejected from server {data._type}")

# Connect the specified number of clients to the server
for row in rows:
    sql = f"SELECT * from session_data WHERE auth_code = {row[0]}"
    cursor.execute(sql)
    r = cursor.fetchone()
    if r is None:
        sql = "INSERT INTO session_data (auth_code, game_account_id, client_version, client_type, character_slots, group_id, connect_time, current_server, last_update) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (row[0], row[0], 20190530, 22, 3, 0, int(time.time()), 'C', int(time.time())))
        db.commit()
    else:
        print(r)
    threading.Thread(target=connect_client, args=(row[0], row[1])).start()