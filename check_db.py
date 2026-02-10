import sqlite3

# Connexion à la base
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

print("Tables présentes dans la base :")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

print("\nStructure de la table messages :")
cursor.execute("PRAGMA table_info(messages);")
print(cursor.fetchall())

print("\nStructure de la table users :")
cursor.execute("PRAGMA table_info(users);")
print(cursor.fetchall())

conn.close()
