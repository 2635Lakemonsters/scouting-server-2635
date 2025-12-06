import os, json, sqlite3, shutil, time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    FIELDS = config['fields']

DB_PATH = "data/db.sqlite"
RAW_DIR = "data/raw/"
PROC_DIR = "data/processed/"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Build column definitions dynamically from config
    column_defs = ", ".join([f"{field['name']} {field['type']}" for field in FIELDS])
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS matches (
            {column_defs},
            UNIQUE(timeStamp, teamNumber, matchNumber) ON CONFLICT IGNORE
        )
    """)
    conn.commit()
    conn.close()

def insert_match(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    field_names = [field['name'] for field in FIELDS]
    placeholders = ", ".join(["?" for _ in FIELDS])
    field_names_str = ", ".join(field_names)
    values = tuple(data.get(field) for field in field_names)
    c.execute(f"INSERT OR IGNORE INTO matches ({field_names_str}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()

class QRHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".json"):
            return

        try:
            with open(event.src_path, "r") as f:
                data = json.load(f)

            insert_match(data)
            shutil.move(event.src_path, os.path.join(PROC_DIR, os.path.basename(event.src_path)))
            print(f"✔ Imported {event.src_path}")
        except Exception as e:
            print(f"✘ Failed to import {event.src_path}: {e}")

def watch():
    observer = Observer()
    observer.schedule(QRHandler(), RAW_DIR, recursive=False)
    observer.start()
    print("Watching for new JSON files in /data/raw/...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROC_DIR, exist_ok=True)
    init_db()
    watch()
