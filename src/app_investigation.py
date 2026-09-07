import time
import psutil
from loguru import logger
from PyQt6.QtCore import QThread, pyqtSignal, Qt

GAME_PROCESS_NAMES = [name.lower() for name in ["FactoryGameSteam-Win64-Shipping.exe",
                                                "FactoryGame-Win64-Shipping.exe"]]

def is_steam_running():
    ...
    
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

            time.sleep(self.interval)

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
                time.sleep(app_settings.sync_period_min * 60)
                if app_settings.autosync:
                    self.time_passed.emit()
                else:
                    logger.debug("Autosync has been disabled meanwhile, skipping sync...")
            else:
                time.sleep(1)

    def stop(self):
        self._is_running = False
        self.wait()
