import socket
import threading
import struct
import ctypes
import mysql.connector
import time
import random
import queue
import json

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
NUM_CLIENTS = 5

# Read packet table from JSON file
with open('packet_table.json', 'r') as f:
    packet_table = json.load(f)

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

class ZC_ACCEPT_ENTER2(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('_packet_id', ctypes.c_uint16),
        ('_start_time', ctypes.c_int32),
        ('_packed_pos', ctypes.c_char * 3),
        ('_x_size', ctypes.c_int8),
        ('_y_size', ctypes.c_int8),
        ('_font', ctypes.c_int16)
    ]

class CZ_REQUEST_MOVE(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('_packet_id', ctypes.c_uint16),
        ('_packed_pos', ctypes.c_char * 3),
    ]

MESSAGE_INTERVAL = 1 # seconds

clients = []

# Create a queue to hold received messages
message_queue = queue.Queue()

# create a packet sending queue
send_queue = queue.Queue()

def pack_position(x: ctypes.c_uint16, y: ctypes.c_uint16, dir: ctypes.c_uint8) -> bytearray:
    if not isinstance(x, ctypes.c_uint16) or not isinstance(y, ctypes.c_uint16) or not isinstance(dir, ctypes.c_uint8):
        raise TypeError('x, y, and dir must be ctype integers')
    if not 0 <= x.value <= 65535 or not 0 <= y.value <= 65535 or not 0 <= dir.value <= 255:
        raise ValueError('x, y, and dir must be unsigned integers in the range of 0 to 65535 and 0 to 255, respectively')

    p = bytearray(3)
    p[0] = (x.value >> 2) & 0xff
    p[1] = ((x.value << 6) | ((y.value >> 4) & 0x3f)) & 0xff
    p[2] = ((y.value << 4) | (dir.value & 0xf)) & 0xff
    return p

def unpack_position(p: ctypes.c_char) -> list:
    x = ((p[0] & 0xff) << 2) | (p[1] >> 6)
    y = ((p[1] & 0x3f) << 4) | (p[2] >> 4)
    dir = (p[2] & 0x0f)
    return [x, y, dir]

def check_packed_data_size(data: ctypes.Structure, login_data: bytearray) -> None:
    expected_size = ctypes.sizeof(data)
    actual_size = len(login_data)
    if actual_size != expected_size:
        raise ValueError(f'Packed data size does not match expected size: {actual_size} != {expected_size}')
    
# Connect a client to the server
def connect_client(account_id, character_id):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 5121))
    clients.append(client)
    print(f'Client connected: {client.getsockname()}')
    threading.Thread(target=receive_messages, args=(client,)).start()
    # start the packet sending thread
    threading.Thread(target=send_packets, args=(client,)).start()

    data = CZ_ENTER()
    data._packet_id = 0x0436
    data._account_id = account_id
    data._char_id = character_id
    data._auth_code = account_id
    data._client_time = 0
    data._gender = 0
    login_data = ctypes.string_at(ctypes.addressof(data), ctypes.sizeof(data))
    check_packed_data_size(data, login_data)
    send_queue.put(login_data)

# define a function to send packets from the queue
def send_packets(client):
    while True:
        try:
            # get the next packet from the queue
            packet_data = send_queue.get()
            # send the packet to the client
            client.send(packet_data)
        except queue.Empty:
            # the queue is empty, wait for more packets to arrive
            time.sleep(0.1)
            
# Receive messages from the server
def receive_messages(client):
    current_position = [ctypes.c_uint16(0), ctypes.c_uint16(0), ctypes.c_uint8(0)]
    buffer_size = 1024
    packets = []
    while True:
        try:
            data = client.recv(buffer_size)
            if not data:
                break
            print(f'Received {len(data)} bytes from {client.getsockname()}; {data}')

            while True:
                packet_id = int.from_bytes(data[:2], byteorder='little')
                if f'{packet_id}' not in packet_table:
                    print(f"Packet ID {packet_id} not found in packet table")
                    break
                packet_len = packet_table[f'{packet_id}'][0]

                if packet_len == -1:
                    packet_len = int.from_bytes(data[2:4], byteorder='little')

                print(f"Packet ID {packet_id} of length {packet_len} was received.")
                packet = data[0:packet_len]
                packets.append(packet)
                data = data[packet_len:]
                if not data:
                    break
                print(f"Remaining data: {data}")
        except socket.error as e:
            print("Socket Error:", e)
        # compare messages and buffer here to make sure we don't lose any data
        for packet in packets:
            print(f'Packet: {packet}')
            if not packet:
                continue
            # print(f'Adding message to queue: {message}')
            message_queue.put(packet)

# Process messages from the queue
def process_messages():
    while True:
        try:
            message = message_queue.get()
            # Process the message here
            packet_id = int.from_bytes(message[:2], byteorder='little')
            print(f"Processing packet ID: {hex(packet_id)}")
            if packet_id == 0x0074:
                data = ZC_REFUSE_ENTER.from_buffer_copy(message)
                print(f"Rejected from server {data._type}")
            if packet_id == 0x02eb:
                data = ZC_ACCEPT_ENTER2.from_buffer_copy(message)
                p = unpack_position(data._packed_pos)
                current_position = [ctypes.c_uint16(p[0]), ctypes.c_uint16(p[1]), ctypes.c_uint8(p[2])]
                print(f"X: {p[0]}, Y: {p[1]}, Dir: {p[2]}")
                while True:
                    data = CZ_REQUEST_MOVE()
                    data._packet_id = 0x035f
                    x = ctypes.c_uint16(current_position[0].value + random.randint(-10, 10))
                    y = ctypes.c_uint16(current_position[1].value + random.randint(-10, 10))
                    packed_pos = pack_position(x, y, ctypes.c_uint8(current_position[2].value))
                    data._packed_pos = bytes(packed_pos)
                    move_data = ctypes.string_at(ctypes.addressof(data), ctypes.sizeof(data))
                    check_packed_data_size(data, move_data)
                    send_queue.put(move_data)
                    current_position = [x, y, current_position[2]] 
        except queue.Empty:
            # Queue is empty, do something else
            pass
            

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
    
process_thread = threading.Thread(target=process_messages)
process_thread.start()