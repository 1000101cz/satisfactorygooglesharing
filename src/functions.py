from pathlib import Path
from loguru import logger
from typing import Optional, List

from .settings import app_settings
from .google_drive import get_file, get_files, push_file
from .settings.settings import SaveFile, SyncedFiles
from .local_files import get_local_files


def compare(synclist: SyncedFiles, drivelist, worldname: Optional[str]):
    """
    :param synclist:    instance of settings.SyncedFiles (list of synced files - both local and online)
    :param drivelist:   list of files available online
    
    :returns:
        list of new local files ( List[pathlib.Path] - list of paths )
        list of new online files ( List[str] - list of IDs )
    """
    
    new_local = []
    new_online = []
    
    # files available online
    online = drivelist
    _online = []
    for f in online:
        if f.filename.startswith(worldname):
            _online.append(f)
    online = _online
    
    # synced list
    sf = SyncedFiles()
    for f in synclist.files:
        if f.filename.startswith(worldname):
            sf.files.append(f)
    synclist = sf
    
    # local files
    local = get_local_files(world_name=app_settings.world_name)
    
    
    
    # find new local files (files not yet uploaded to google drive)
    for f in local:
        if not sf.contains(f):
            new_local.append(f.filename)
            logger.debug(f"New local file found: {f.filename}")
    
    # find new online files (files not yet downloaded from google drive)
    for f in online:
        if not sf.contains(f):
            new_online.append(f.drive_id)
            logger.debug(f"New online file found: {f.drive_id}")
    
    return new_local, new_online


def get_missing_online_files(new_online: List[str], synclist):
    "Download new files form google drive"
    for no in new_online:
        sf = SaveFile()
        sf.drive_id = no
        f = get_file(sf)
        if f:
            synclist.files.append(f)
        else:
            logger.error(f"Failed to get file: {no}")
    
    return synclist
    
    
def upload_new_local_files(new_local: List[str], synclist):
    "Upload new local files to google drive"
    for nl in new_local:
        sf = SaveFile()
        sf.filename = nl
        sf.creation_time = sf.local_creation_time()
        f = push_file(sf)
        if f:
            synclist.files.append(f)
        else:
            logger.error(f"Failed to upload file: {nl}")
    
    return synclist
    

def upload_and_download_diff(new_local, new_online, synclist):
    """
    Solve differance between local files and online files (download/upload missing)
    :returns:
        updated synced list
    """
    synclist = get_missing_online_files(new_online, synclist)
    synclist = upload_new_local_files(new_local, synclist)
    return synclist
