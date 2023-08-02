import mysql.connector
import time

# Connect to the database
db = mysql.connector.connect(
  host="localhost",
  user="horizon",
  password="horizon",
  database="horizon",
  auth_plugin='mysql_native_password'
)
cursor = db.cursor()

# Execute the SELECT statement with a JOIN
sql = "SELECT a.id, b.id FROM game_accounts as a JOIN characters as b ON a.id = b.account_id WHERE a.id != 1"
cursor.execute(sql)

# Fetch all the rows and print them to the console
rows = cursor.fetchall()
for row in rows:
    sql = "INSERT INTO session_data (auth_code, game_account_id, client_version, client_type, character_slots, group_id, connect_time, current_server, last_update) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, (row[0], row[0], 20190530, 22, 3, 0, int(time.time()), 'C', int(time.time())))

db.commit()