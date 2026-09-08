import time
import psutil
from loguru import logger
from PyQt6.QtCore import QThread, pyqtSignal, Qt

GAME_PROCESS_NAMES = [name.lower() for name in ["FactoryGameSteam-Win64-Shipping.exe",
                                                "FactoryGame-Win64-Shipping.exe"]]
    
def is_satisfactory_running():
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in GAME_PROCESS_NAMES:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


class GameMonitorThread(QThread):
    # True = is running, False = is not running
    status_changed = pyqtSignal(bool)

    def __init__(self, check_interval_seconds: int = 1):
        super().__init__()
        self.interval = check_interval_seconds
        self._is_running = True
        self.last_state = None

    def run(self):
        while self._is_running:
            current_state = is_satisfactory_running()

            if current_state != self.last_state:
                last_state_was_none = self.last_state is None
                self.last_state = current_state
                if not last_state_was_none:
                    self.status_changed.emit(current_state)

            # sleep and check for termination
            for _ in range(self.interval):
                time.sleep(1)
                if not self._is_running:
                    return

    def stop(self):
        self._is_running = False
        self.wait()
        

class AutoSyncThread(QThread):
    time_passed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._is_running = True

    def run(self):
        from .settings import app_settings
        while self._is_running:
            if app_settings.autosync:
                logger.debug(f"Waiting before autosync: {app_settings.sync_period_min * 60}s")
                if app_settings.autosync:
                    self.time_passed.emit()
                else:
                    logger.debug("Autosync has been disabled meanwhile, skipping sync...")
                
                # sleep and check for termination
                for _ in range(app_settings.sync_period_min * 60):
                    time.sleep(1)
                    if not self._is_running:
                        return
            else:
                time.sleep(1)

    def stop(self):
        self._is_running = False
        self.wait()
        

class FriendsPlayingCheckThread(QThread):
    # True = is running, False = is not running
    status_changed = pyqtSignal(bool)

    def __init__(self, check_interval_seconds: int = 25):
        super().__init__()
        self.interval = check_interval_seconds
        self._is_running = True
        self.last_state = None

    def run(self):
        from .steam_api import is_friend_playing_satisfactory
        from .settings import app_settings
        while self._is_running:
            friend_playing = False
            if app_settings.steam_api_key.strip() != "":
                for friend in app_settings.friend_list:
                    if is_friend_playing_satisfactory(friend["steam_id"]):
                        friend_playing = True
                        logger.debug(f"Friend '{friend["nickname"]}' [{friend["steam_id"]}] is playing Satisfactory right now")
                        self.status_changed.emit(True)
                if not friend_playing:
                    if len(app_settings.friend_list):
                        logger.debug(f"No friend is playing Satosfactory ({len(app_settings.friend_list)} friends specified)")
                    self.status_changed.emit(False)
            
            # sleep and check for termination
            for _ in range(self.interval):
                time.sleep(1)
                if not self._is_running:
                    return

    def stop(self):
        self._is_running = False
        self.wait()
