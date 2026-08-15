import sqlite3

conn = sqlite3.connect("inventory.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE products ADD COLUMN image TEXT")
    print("Image column added successfully!")
except sqlite3.OperationalError as e:
    print(e)

conn.commit()
conn.close()