import os
import json
from typing import Optional
from pathlib import Path
from loguru import logger

_json_folder = Path(os.environ["LOCALAPPDATA"]) / 'SatisfactoryGoogleSharing'
if not _json_folder.is_dir():
    _json_folder.mkdir(parents=True, exist_ok=True)
_settings_path = _json_folder / 'settings.json'
_runtime_path = _json_folder / 'runtime.json'

class AppSettings:
    def __init__(self):
        self.saved_files_path: Path = Path(os.environ["LOCALAPPDATA"]) / 'FactoryGame' / 'Saved' / 'SaveGames'
        self.google_app_url: Optional[str] = None
        self.sync_period_min: int = 5
        
    def load(self):
        if not _settings_path.is_file():
            logger.warning(f"Settings file not found at {_settings_path}. Creating a new one.")
            self.save()
        with _settings_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self._from_dict(data)
        
    def save(self):
        data = self._to_dict()
        with _settings_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        
    def _to_dict(self) -> dict:
        return {
            "saved_files_path": str(self.saved_files_path),
            "google_app_url": self.google_app_url,
            "sync_period_min": self.sync_period_min
        }
        
    def _from_dict(self, data: dict):
        self.saved_files_path = Path(data["saved_files_path"])
        self.google_app_url = data["google_app_url"]
        self.sync_period_min = data["sync_period_min"]


class AppRuntime:
    def __init__(self):
        self.latest_save: Optional[str] = None
        self.last_sync: Optional[str] = None

    def load(self):
        if not _runtime_path.is_file():
            logger.warning(f"Runtime file not found at {_runtime_path}. Creating a new one.")
            self.save()
        with _runtime_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self._from_dict(data)
        
    def save(self):
        data = self._to_dict()
        with _runtime_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        
    def _to_dict(self) -> dict:
        return {
            "latest_save": self.latest_save,
            "last_sync": self.last_sync
        }
        
    def _from_dict(self, data: dict):
        self.latest_save = data["latest_save"]
        self.last_sync = data["last_sync"]
    