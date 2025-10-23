# csv_writer.py

import csv
import time
import asyncio
from config import CSV_FILENAME

class CSVLogger:
    def __init__(self, filename=CSV_FILENAME):
        self.filename = filename
        self.file = open(self.filename, mode='w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(["Timestamp", "Payload"])

    async def log(self, data):
        timestamp = time.time()
        self.writer.writerow([timestamp, data.decode("utf-8")])
        print(f"📥 Logged: {timestamp}, {data}")

    def close(self):
        self.file.close()
