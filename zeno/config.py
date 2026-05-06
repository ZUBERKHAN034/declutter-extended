import logging
import os
from pathlib import Path
from appdirs import user_data_dir

VERSION = "1.0.0"

APP_FOLDER = user_data_dir("Zeno", appauthor='', roaming=True)
Path(APP_FOLDER).mkdir(parents=True, exist_ok=True)

LOG_FILE = os.path.join(APP_FOLDER, "Zeno.log")
DB_FILE = os.path.join(APP_FOLDER, "Zeno.db")

# Legacy JSON settings file; used only by the migration (do not write to it anymore)
SETTINGS_FILE = os.path.join(APP_FOLDER, "settings.json")

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.FileHandler(filename=LOG_FILE, encoding="utf-8", mode="a+")],
    format="%(asctime)-15s %(levelname)-8s %(message)s",
)
