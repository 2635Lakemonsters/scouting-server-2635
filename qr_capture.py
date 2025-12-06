import cv2, json, os
from pyzbar.pyzbar import decode
from datetime import datetime

# Load field keys from config
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    KEYS = [field['name'] for field in config['fields']]
ARCHIVE_DIR = "data/raw/"
os.makedirs(ARCHIVE_DIR, exist_ok=True)

cap = cv2.VideoCapture(1)
seen = set()

print("Scanning QR codes... Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    decoded_objects = decode(frame)
    for obj in decoded_objects:
        payload = obj.data.decode("utf-8")
        
        print(type(payload))
        print(payload, end="\n\n\n")
        

        if payload in seen:
            continue
        seen.add(payload)

        try:
            qr_list = json.loads(str(payload))
            qr_data = dict(zip(KEYS, qr_list))
        except json.JSONDecodeError:
            print("Invalid QR payload, skipping.")
            continue
        print(type(qr_data))

        filename = f"{qr_data['matchNumber']}_{qr_data['teamNumber']}_{qr_data['timeStamp']}.json"
        filepath = os.path.join(ARCHIVE_DIR, filename)

        with open(filepath, "w") as f:
            json.dump(qr_data, f, indent=2)

        print(f"Saved QR -> {filepath}")

    cv2.imshow("QR Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
