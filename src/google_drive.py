import base64
import requests
from datetime import datetime
from typing import Optional, List
from loguru import logger
from pathlib import Path
from .settings import app_settings
from .settings.settings import SaveFile


def get_files() -> List[SaveFile]:
    try:
        response = requests.get(app_settings.google_app_url, timeout=15)
        data = response.json()
        
        if data.get("status") == "success":
            drive_dicts = data.get("files", [])
            output = []
            for drive_dict in drive_dicts:
                fl = SaveFile()
                fl.from_drive_dict(drive_dict)
                if fl.local_path.suffix != '.sav':
                    continue
                output.append(fl)
            return output
        else:
            print(f"Server error: {data.get('message')}")
            return []

    except Exception as e:
        logger.error(f"Communication error with Google Drive: {e}")
        return []

def get_file(file: SaveFile) -> Optional[SaveFile]:
    try:
        logger.info(f"Downloading file from Google Drive: {file.filename} (ID: {file.drive_id})")
        
        download_url = f"{app_settings.google_app_url}?fileId={file.drive_id}"
        response = requests.get(download_url, timeout=30)
        data = response.json()

        if data.get("status") == "success":
            if "fileContent" not in data:
                logger.error(f"Missing 'fileContent' in server response. Returned keys: {list(data.keys())}")
                return None
            
            file.filename = data["fileName"]
            file.creation_time = datetime.fromisoformat(data["updated"]).strftime('%d.%m.%Y %H:%M:%S')
            file_bytes = base64.b64decode(data["fileContent"])
            
            # Zajištění existencí nadřazené složky
            file.local_path.parent.mkdir(parents=True, exist_ok=True)
            file.local_path.write_bytes(file_bytes)
            
            logger.info(f"File was downloaded and saved: {file.local_path}")
            return file
        else:
            logger.error(f"Download error: {data.get('message')}")
            return None

    except Exception as e:
        logger.error("Communication error")
        logger.exception(e)
        return None
    

def push_file(file: SaveFile) -> Optional[SaveFile]:
    """
    Upload SaveFile to Google Drive.
    """

    if not file or not file.local_path:
        logger.error(f"Invalid SaveFile or missing local_path: {file}")
        return None

    if not file.local_path.exists() or not file.local_path.is_file():
        logger.error(f"Lokální soubor neexistuje: {file.local_path}")
        return None

    try:
        filename = file.filename or file.local_path.name
        logger.info(f"Uploading local file to Google Drive: {filename} ({file.local_path})")

        file_bytes = file.local_path.read_bytes()
        encoded_content = base64.b64encode(file_bytes).decode("utf-8")

        payload = {
            "fileName": filename,
            "mimeType": "application/octet-stream",
            "fileContent": encoded_content
        }

        response = requests.post(
            app_settings.google_app_url,
            json=payload,
            timeout=60,
            allow_redirects=True
        )
        
        data = response.json()

        if data.get("status") == "success":
            uploaded_id = data.get("fileId")
            logger.info(f"File '{filename}' has been uploaded to Google Drive. (ID: {uploaded_id})")
            
            if hasattr(file, "drive_id") and uploaded_id:
                file.drive_id = uploaded_id
                
            return file
        else:
            logger.error(f"Upload error: {data.get('message')}")
            return None

    except Exception as e:
        logger.error("Upload error")
        logger.exception(e)
        return None
