import os
from pathlib import Path
from loguru import logger
from typing import List
from datetime import datetime


def get_user_save_directory() -> Path:
    base_save_dir = Path(os.environ["LOCALAPPDATA"]) / "FactoryGame" / "Saved" / "SaveGames"
    
    if not base_save_dir.exists():
        base_save_dir.mkdir(parents=True, exist_ok=True)
        
    # find all steamID folders
    user_folders = [
        d for d in base_save_dir.iterdir() 
        if d.is_dir() and d.name.isdigit()
    ]
    
    if user_folders:
        # if there is multiple user folders, take the newest one
        latest_user_folder = max(user_folders, key=lambda f: f.stat().st_mtime)
        logger.debug(f"Found user save directory: {latest_user_folder}")
        return latest_user_folder
    else:
        logger.debug(f"Found user save directory: {base_save_dir}")
        return base_save_dir
    

def get_local_files(world_name: str = "") -> list:
    from .settings.settings import SaveFile
    from .settings import app_settings
    
    sav_files = list(app_settings.saved_files_path.glob(f"{world_name}*.sav"))
    output = []
    for sf in sav_files:
        f = SaveFile()
        f.filename = sf.name
        f.creation_time = datetime.fromtimestamp(sf.stat().st_mtime).strftime('%d.%m.%Y %H:%M:%S')
        output.append(f)
        
    return output
