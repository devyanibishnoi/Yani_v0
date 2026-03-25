import sqlite3

# Open a connection to the SQLite database file.
# If `yani.db` does not exist yet, SQLite will create it for us.
conn = sqlite3.connect("yani.db")

# Create a cursor object.
# The cursor is the tool we use to send SQL commands to the database.
cursor = conn.cursor()

# Create the `conversations` table if it does not already exist.
# `CREATE TABLE IF NOT EXISTS` is safe to run many times because it will only create the table once.
cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE,
    saved INTEGER DEFAULT 0
)
""")

# Column meaning:
# `id` is the main unique number for each conversation.
# `INTEGER PRIMARY KEY AUTOINCREMENT` means SQLite automatically creates a new number each time.
# `date TEXT UNIQUE` stores a date label as text and does not allow duplicates.
# `saved INTEGER DEFAULT 0` stores a simple true/false style flag:
# 0 means "not saved"
# 1 means "saved"

# Create the `messages` table if it does not already exist.
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    sender TEXT,
    message TEXT,
    timestamp TEXT,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
)
""")

# Column meaning:
# `conversation_id` links each message back to the conversation it belongs to.
# `sender` stores who wrote the message, such as "user" or "yani".
# `message` stores the actual text content.
# `timestamp` stores when the message was created.
# `FOREIGN KEY(...) REFERENCES ...` tells the database how the two tables are connected.

# This next block is for older databases that were created before the `saved` column existed.
# We try to add the column once.
try:
    cursor.execute("ALTER TABLE conversations ADD COLUMN saved INTEGER DEFAULT 0")
    print("Added 'saved' column to conversations table")
except sqlite3.OperationalError as e:
    # `OperationalError` is a database error type from sqlite3.
    # If the column already exists, SQLite throws an error.
    if "duplicate column name" in str(e):
        print("'saved' column already exists")
    else:
        # If the error is something else, print it so we know what went wrong.
        print(f"Error adding column: {e}")

# Save all database changes permanently.
conn.commit()

# Close the database connection so the file is not left open.
conn.close()
