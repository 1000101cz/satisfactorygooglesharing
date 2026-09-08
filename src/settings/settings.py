import os
import json
from typing import Optional, List
from pathlib import Path
from loguru import logger
from datetime import datetime

from ..local_files import get_user_save_directory

_json_folder = Path(os.environ["LOCALAPPDATA"]) / 'SatisfactoryGoogleSharing'
if not _json_folder.is_dir():
    _json_folder.mkdir(parents=True, exist_ok=True)
_settings_path = _json_folder / 'settings.json'
_runtime_path = _json_folder / 'runtime.json'
_synced_files_path = _json_folder / 'synced_files.json'

class AppSettings:
    def __init__(self):
        self.steam_api_key: str = ""
        self.friend_list: List[str] = []
        self.saved_files_path: Optional[Path] = get_user_save_directory()
        self.world_name: str = ""
        self.google_app_url: str = ""
        self.autosync: bool = False
        self.sync_period_min: int = 5
        
    def load(self):
        if not _settings_path.is_file():
            logger.warning(f"Settings file not found at {_settings_path}. Creating a new one.")
            self.save()
        with _settings_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self._from_dict(data)
        logger.debug(f"Settings loaded [{_settings_path}]")
        
    def save(self):
        data = self._to_dict()
        with _settings_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        logger.debug(f"Settings saved [{_settings_path}]")
        
    def _to_dict(self) -> dict:
        return {
            "steam_api_key": self.steam_api_key,
            "friend_list": self.friend_list,
            "saved_files_path": str(self.saved_files_path),
            "world_name": self.world_name,
            "google_app_url": self.google_app_url,
            "autosync": self.autosync,
            "sync_period_min": self.sync_period_min
        }
        
    def _from_dict(self, data: dict):
        self.steam_api_key = data.get("steam_api_key", "")
        self.friend_list = data.get("friend_list", [])
        self.saved_files_path = Path(data.get("saved_files_path"))
        self.world_name = data.get("world_name")
        self.google_app_url = data.get("google_app_url")
        self.autosync = data.get("autosync", False)
        self.sync_period_min = data.get("sync_period_min")


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


class SaveFile:
    def __init__(self):
        self.filename: Optional[str] = None
        self.drive_id: Optional[str] = None
        self.creation_time: Optional[datetime] = None

    @property
    def local_path(self) -> Optional[Path]:
        from . import app_settings
        return (app_settings.saved_files_path / self.filename) if self.filename else None

    @property
    def is_local(self) -> bool:
        return self.local_path.is_file() if self.local_path else False

    @property
    def is_online(self) -> bool:
        return self.drive_id is not None

    @property
    def world_name(self) -> Optional[str]:
        if self.filename:
            parts = self.filename.split('_')
            if len(parts) >= 2:
                return parts[0]
        return None

    def __str__(self):
        return f"Filename: {self.filename} | Drive ID: {self.drive_id} | Creation Time: {self.creation_time} | Local Path: {self.local_path} | Is Local: {self.is_local} | Is Online: {self.is_online}"

    def from_dict(self, data: dict):
        self.filename = data.get("filename")
        self.drive_id = data.get("drive_id")
        self.creation_time = data.get("creation_time")

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "drive_id": self.drive_id,
            "creation_time": self.creation_time
        }

    def from_drive_dict(self, data: dict):
        logger.debug(f"Parsing drive dict: {data}")
        self.filename = data.get("name")
        self.drive_id = data.get("id")
        self.creation_time = datetime.fromisoformat(data["updated"]) if data.get("updated") else None
        
    def local_creation_time(self):
        return datetime.fromtimestamp(self.local_path.stat().st_mtime).strftime('%d.%m.%Y %H:%M:%S')
        

class SyncedFiles:
    def __init__(self):
        self.files: list[SaveFile] = []
        
    def load(self):
        self.files = []
        if not _synced_files_path.is_file():
            logger.warning(f"Synced files file not found at {_synced_files_path}. Creating a new one.")
            self.save()
        with _synced_files_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        all_dicts = data.get("all_dicts", [])
        for _dict in all_dicts:
            sf = SaveFile()
            sf.from_dict(_dict)
            self.files.append(sf)
    
    def save(self):
        all_dicts = [file.to_dict() for file in self.files]
        with _synced_files_path.open("w", encoding="utf-8") as file:
            json.dump({"all_dicts": all_dicts}, file, indent=4)
            
    def contains(self, file: SaveFile) -> bool:
        "Check whether file is already synced"
        for f in self.files:
            if file.local_path == f.local_path or file.drive_id == f.drive_id:
                return True
        return False

    def get_newest(self) -> Optional[SaveFile]:
        newest_so_far = None
        for f in self.files:
            if newest_so_far is None:
                newest_so_far = f
            else:
                dt_object_so_far = datetime.strptime(newest_so_far.creation_time, "%d.%m.%Y %H:%M:%S")
                dt_f = datetime.strptime(f.creation_time, "%d.%m.%Y %H:%M:%S")
                if dt_f > dt_object_so_far:
                    newest_so_far = f
        return newest_so_far
