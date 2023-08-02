import random
import mysql.connector

# Connect to the database
db = mysql.connector.connect(
  host="localhost",
  user="horizon",
  password="horizon",
  database="horizon",
  auth_plugin='mysql_native_password'
)
cursor = db.cursor()

# Generate fake data for the game_accounts table
for i in range(5000):
    game_account = {}
    game_account['username'] = f"example_username_{i}"
    game_account['hash'] = f"example_password_{i}"
    game_account['email'] = f"example_email_{i}@example.com"
    game_account['gender'] = "M"
    game_account['group_id'] = 1
    game_account['state'] = 0
    game_account['unban_time'] = 0
    game_account['expiration_time'] = 0

    sql = f"INSERT INTO game_accounts (username, hash, email, gender, group_id, state, unban_time) VALUES ('{game_account['username']}', '{game_account['hash']}', '{game_account['email']}', '{game_account['gender']}', {game_account['group_id']}, {game_account['state']}, {game_account['unban_time']})"
    cursor.execute(sql)

    # Get the last inserted game account ID
    game_account_id = cursor.lastrowid
    character = {}
    character['account_id'] = game_account_id
    character['slot'] = 0
    character['name'] = f"example_character_{i}"
    character['online'] = 0
    character['gender'] = "M"
    character['delete_reserved_at'] = 0
    character['deleted_at'] = 0
    character['unban_time'] = 0
    character['rename_count'] = 0
    character['last_unique_id'] = 0
    character['hotkey_row_index'] = 0
    character['change_slot_count'] = 0
    character['font'] = 0
    character['show_equip'] = 0
    character['allow_party'] = 0
    character['partner_aid'] = 0
    character['father_aid'] = 0
    character['mother_aid'] = 0
    character['child_aid'] = 0
    character['party_id'] = 0
    character['guild_id'] = 0
    character['pet_id'] = random.randint(0, 1000000000)
    character['homun_id'] = random.randint(0, 1000000000)
    character['elemental_id'] = random.randint(0, 1000000000)
    character['current_map'] = 'new_1-1'
    character['current_x'] = random.randint(0, 100)
    character['current_y'] = random.randint(0, 100)
    character['saved_map'] = 'new_1-1'
    character['saved_x'] = random.randint(0, 100)
    character['saved_y'] = random.randint(0, 100)

    # Insert the object into the database
    sql = "INSERT INTO characters (account_id, slot, name, online, gender, delete_reserved_at, deleted_at, unban_time, rename_count, last_unique_id, hotkey_row_index, change_slot_count, font, saved_map, saved_x, saved_y) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = (character['account_id'], character['slot'], character['name'], character['online'], character['gender'], character['delete_reserved_at'], character['deleted_at'], character['unban_time'], character['rename_count'], character['last_unique_id'], character['hotkey_row_index'], character['change_slot_count'], character['font'], character['saved_map'], character['saved_x'], character['saved_y'])
    cursor.execute(sql, values)

    character_id = cursor.lastrowid
    character_status = {}
    character_status['id'] = character_id
    character_status['job_id'] = 0
    character_status['base_level'] = random.randint(1, 99)
    character_status['job_level'] = random.randint(1, 10)
    character_status['base_experience'] = random.randint(1, 1000000000)
    character_status['job_experience'] = random.randint(1, 1000000000)
    character_status['zeny'] = random.randint(1, 1000000)
    character_status['strength'] = random.randint(1, 99)
    character_status['agility'] = random.randint(1, 99)
    character_status['vitality'] = random.randint(1, 99)
    character_status['intelligence'] = random.randint(1, 99)
    character_status['dexterity'] = random.randint(1, 99)
    character_status['luck'] = random.randint(1, 99)
    character_status['maximum_hp'] = random.randint(40, 10000)
    character_status['hp'] = random.randint(1, character_status['maximum_hp'])
    character_status['maximum_sp'] = random.randint(40, 10000)
    character_status['sp'] = random.randint(1, character_status['maximum_sp'])
    character_status['status_points'] = random.randint(0, 99)
    character_status['skill_points'] = random.randint(0, 99)
    character_status['hair_style_id'] = 0
    character_status['hair_color_id'] = 0
    character_status['cloth_color_id'] = 0
    character_status['body_id'] = 0
    character_status['weapon_view_id'] = 0
    character_status['shield_view_id'] = 0
    character_status['head_top_view_id'] = 0
    character_status['head_mid_view_id'] = 0
    character_status['head_bottom_view_id'] = 0
    character_status['robe_view_id'] = 0

    # Insert the object into the database
    sql = "INSERT INTO character_status (id, job_id, base_level, job_level, base_experience, job_experience, zeny, strength, agility, vitality, intelligence, dexterity, luck, maximum_hp, hp, maximum_sp, sp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = (character_status['id'], character_status['job_id'], character_status['base_level'], character_status['job_level'], character_status['base_experience'], character_status['job_experience'], character_status['zeny'], character_status['strength'], character_status['agility'], character_status['vitality'], character_status['intelligence'], character_status['dexterity'], character_status['luck'], character_status['maximum_hp'], character_status['hp'], character_status['maximum_sp'], character_status['sp'])
    cursor.execute(sql, values)
    print(f"Added character {character['name']} (ID: {character_id})")
db.commit()
db.close()