import os, json, sqlite3, shutil, time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DB_PATH = "data/db.sqlite"
RAW_DIR = "data/raw/"
PROC_DIR = "data/processed/"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            timeStamp TEXT,
            teamNumber TEXT,
            matchNumber TEXT,
            autoPoints INTEGER,
            autoCanScoreAlgae INTEGER,
            autoCanScoreCorrals INTEGER,
            teleopPoints INTEGER,
            canScoreCorralsL1 INTEGER,
            canScoreCorralsL2 INTEGER,
            canScoreCorralsL3 INTEGER,
            canScoreCorralsL4 INTEGER,
            canScoreAlgae INTEGER,
            defenseAbility INTEGER,
            endgamePoints INTEGER,
            parkedInEndgame INTEGER,
            climbedInEndgame INTEGER,
            coOpAchieved INTEGER,
            canPickupCoralFromFloor INTEGER,
            canPickupCorralFromFeeder INTEGER,
            canPickupAlgaeFromFloor INTEGER,
            canPickupAlgaeFromReef INTEGER,
            mobilitySpeed INTEGER,
            reliabilityRating INTEGER,
            scoutNotes TEXT,
            UNIQUE(timeStamp, teamNumber, matchNumber) ON CONFLICT IGNORE
        )
    """)
    conn.commit()
    conn.close()

def insert_match(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO matches VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["timeStamp"],
        data["teamNumber"],
        data["matchNumber"],
        data.get("autoPoints"),
        data.get("autoCanScoreAlgae"),
        data.get("autoCanScoreCorrals"),
        data.get("teleopPoints"),
        data.get("canScoreCorralsL1"),
        data.get("canScoreCorralsL2"),
        data.get("canScoreCorralsL3"),
        data.get("canScoreCorralsL4"),
        data.get("canScoreAlgae"),
        data.get("defenseAbility"),
        data.get("endgamePoints"),
        data.get("parkedInEndgame"),
        data.get("climbedInEndgame"),
        data.get("coOpAchieved"),
        data.get("canPickupCoralFromFloor"),
        data.get("canPickupCorralFromFeeder"),
        data.get("canPickupAlgaeFromFloor"),
        data.get("canPickupAlgaeFromReef"),
        data.get("mobilitySpeed"),
        data.get("reliabilityRating"),
        data.get("scoutNotes")
    ))
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
