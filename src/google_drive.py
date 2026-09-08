import base64
import requests
from datetime import datetime
from typing import Optional, List
from loguru import logger
from .settings import app_settings
from .settings.settings import SaveFile


def get_files() -> List[SaveFile]:

    payload = {
        "token": app_settings.google_app_token,
        "action": "list"
    }

    try:
        response = requests.post(
            app_settings.google_app_url,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
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
            logger.error(f"Server error: {data.get('message')}")

            if data.get("message") == "Unauthorized":
                text = "Invalid Google App Token value!"
            else:
                text = data.get("message")

            raise RuntimeError(text)

    except requests.exceptions.JSONDecodeError:
        logger.error(
            f"Invalid JSON response. Response: {response.text[:200]}"
        )
        raise RuntimeError("Invalid response from Google Apps Script")

    except requests.exceptions.RequestException as e:
        logger.error("Google Drive API communication error:")
        logger.exception(e)
        raise RuntimeError("Could not communicate with Google Drive")


def get_file(file: SaveFile) -> Optional[SaveFile]:

    try:
        logger.info(
            f"Downloading file from Google Drive: "
            f"{file.filename} (ID: {file.drive_id})"
        )

        payload = {
            "token": app_settings.google_app_token,
            "action": "download",
            "fileId": file.drive_id
        }

        response = requests.post(
            app_settings.google_app_url,
            json=payload,
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            if "fileContent" not in data:
                logger.error(
                    "Missing 'fileContent' in server response. "
                    f"Returned keys: {list(data.keys())}"
                )
                return None

            file.filename = data["fileName"]

            file.creation_time = datetime.fromisoformat(
                data["updated"]
            ).strftime('%d.%m.%Y %H:%M:%S')

            file_bytes = base64.b64decode(data["fileContent"])

            # Ensure parent folder exists
            file.local_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            file.local_path.write_bytes(file_bytes)

            logger.info(
                f"File was downloaded and saved: {file.local_path}"
            )

            return file

        else:
            logger.error(
                f"Download error: {data.get('message')}"
            )
            return None

    except requests.exceptions.JSONDecodeError:
        logger.error(
            f"Invalid JSON response. Response: {response.text[:200]}"
        )
        return None

    except requests.exceptions.RequestException as e:
        logger.error(
            "Google Drive API communication error:"
        )
        logger.exception(e)
        return None


def push_file(file: SaveFile) -> Optional[SaveFile]:

    if not file or not file.local_path:
        logger.error(
            f"Invalid SaveFile or missing local_path: {file}"
        )
        return None

    if not file.local_path.exists() or not file.local_path.is_file():
        logger.error(
            f"Local file does not exist: {file.local_path}"
        )
        return None

    try:
        filename = file.filename or file.local_path.name

        logger.info(
            f"Uploading local file to Google Drive: "
            f"{filename} ({file.local_path})"
        )

        file_bytes = file.local_path.read_bytes()
        encoded_content = base64.b64encode(
            file_bytes
        ).decode("utf-8")

        payload = {
            "token": app_settings.google_app_token,
            "fileName": filename,
            "mimeType": "application/octet-stream",
            "fileContent": encoded_content
        }

        response = requests.post(
            app_settings.google_app_url,
            json=payload,
            timeout=180,
            allow_redirects=True
        )

        response.raise_for_status()

        try:
            data = response.json()

        except requests.exceptions.JSONDecodeError:
            logger.error(
                "Google Apps Script did not return JSON. "
                f"Status: {response.status_code}"
            )
            logger.error(
                f"Response (first 300 chars): {response.text[:300]}"
            )
            return None

        if data.get("status") == "success":
            uploaded_id = data.get("fileId")

            logger.info(
                f"File '{filename}' has been uploaded to Google Drive. "
                f"(ID: {uploaded_id})"
            )

            if hasattr(file, "drive_id") and uploaded_id:
                file.drive_id = uploaded_id

            return file

        else:
            logger.error(
                f"Upload error: {data.get('message')}"
            )
            return None
        
    except requests.exceptions.Timeout:
        logger.error(
            f"Upload request timed out for '{filename}'. "
            "The server may still have completed the upload."
        )
        return None

    except Exception as e:
        logger.error("Upload error")
        logger.exception(e)
        return None
