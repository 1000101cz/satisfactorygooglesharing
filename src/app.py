from pathlib import Path
from PyQt6 import uic
from loguru import logger
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from datetime import datetime
import webbrowser

from .settings import app_settings, app_runtime, synced_list
from .app_investigation import is_satisfactory_running, GameMonitorThread, AutoSyncThread, FriendsPlayingCheckThread
from .google_drive import get_files
from .functions import compare, upload_and_download_diff
from .utils import get_resource_path
from .dialogs import show_error_dialog, FriendListDialog


ui_path = get_resource_path('data/app.ui')
window = uic.loadUiType(str(ui_path))[0]


class Window(QMainWindow, window):
    def __init__(self, parent=None):
        self._initialization = True
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle("Satisfactory Save Syncer")
        
        icon_path = get_resource_path('data/icon.ico')
        self.setWindowIcon(QIcon(str(icon_path)))
        
        self._connects()
        
        self._fill_gui()
        
        self._start_threads()
        
        self.label_syncing.hide()
        self.pushButton_fetch.setEnabled(True)
        self.label_sync_start.hide()
        
    def _connects(self):
        self.pushButton_steam_api_key.clicked.connect(self._steam_api_key_clicked)
        self.pushButton_friend_list.clicked.connect(self._friend_list_clicked)
        self.pushButton_saved_files_path.clicked.connect(self._saved_files_path_clicked)
        self.pushButton_world_name.clicked.connect(self._world_name_clicked)
        self.pushButton_google_app_url.clicked.connect(self._google_app_url_clicked)
        self.checkBox_autosync.checkStateChanged.connect(self._autosync_switched)
        self.pushButton_sync_period.clicked.connect(self._sync_period_clicked)
        self.pushButton_fetch.clicked.connect(lambda: self._fetch(manual=True))
        self.pushButton_play.clicked.connect(self._launch_satisfactory)
        
    def _fill_gui(self):
        self._fill_gui_settings()
        self._fill_gui_runtime()
        
    def _fill_gui_settings(self):
        # Steam API Key
        self.lineEdit_steam_api_key.setText(app_settings.steam_api_key)
        self.pushButton_friend_list.setEnabled(app_settings.steam_api_key.strip() != "")
        
        # Saved files path
        if not isinstance(app_settings.saved_files_path, Path) or not app_settings.saved_files_path.is_dir():
            self.label_saved_files_path.setText("Not set")
        else:
            self.label_saved_files_path.setText(str(app_settings.saved_files_path))
            
        # World name
        self.lineEdit_world_name.setText(app_settings.world_name)
            
        # Google app URL
        self.lineEdit.setText(app_settings.google_app_url or "")
        
        # Autosync
        self.checkBox_autosync.setChecked(app_settings.autosync)
        
        # Sync period
        self.spinBox.setValue(app_settings.sync_period_min)
        
    def _fill_gui_runtime(self):
        # Latest save
        newest_file = synced_list.get_newest()
        if newest_file is None:
            text = "No file"
        else:
            text = f"{newest_file.filename} ({newest_file.creation_time})"
        self.label_latest_save.setText(text)
        
        # Last sync
        text = app_runtime.last_sync or "Unknown"
        self.label_last_sync.setText(text)
        
        # Satisfactory running
        self.label_satisfactory_running.setStyleSheet("color: green") if is_satisfactory_running() else self.label_satisfactory_running.setStyleSheet("color: red")
        text = "Yes" if is_satisfactory_running() else "No"
        if text == "Yes":
            self.lock_play_button(True)
        else:
            self.lock_play_button(False)
        self.label_satisfactory_running.setText(text)
        
    def _steam_api_key_clicked(self):
        steam_api_key = self.lineEdit_steam_api_key.text().strip()
        app_settings.steam_api_key = steam_api_key
        app_settings.save()
        self._fill_gui_settings()
        
        self.pushButton_friend_list.setEnabled(app_settings.steam_api_key.strip() != "")
        
    def _friend_list_clicked(self):
        dialog = FriendListDialog(
            api_key=app_settings.steam_api_key,
            current_friends=app_settings.friend_list,
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_friends = dialog.get_friends_list()
            
            app_settings.friend_list = updated_friends
            app_settings.save()
            
            logger.info(f"Seznam přátel aktualizován ({len(updated_friends)} přátel).")
        
    def _saved_files_path_clicked(self):
        selected_directory = QFileDialog.getExistingDirectory(
            self,
            "Select Saved Files Directory",
            str(app_settings.saved_files_path),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if selected_directory:
            app_settings.saved_files_path = Path(selected_directory)
            app_settings.save()
            self._fill_gui_settings()
            
    def _world_name_clicked(self):
        new_world_name = self.lineEdit_world_name.text().strip()
        if new_world_name == "":
            new_world_name = None
        app_settings.world_name = new_world_name
        app_settings.save()
        self._fill_gui_settings()
        
    def _google_app_url_clicked(self):
        new_url = self.lineEdit.text().strip()
        if new_url == "":
            new_url = None
        app_settings.google_app_url = new_url
        app_settings.save()
        self._fill_gui_settings()
        
    def _autosync_switched(self, state: Qt.CheckState):
        if state == Qt.CheckState.Checked:
            app_settings.autosync = True
        else:
            app_settings.autosync = False
        app_settings.save()
        self._fill_gui_settings()
        
    def _sync_period_clicked(self):
        new_period = self.spinBox.value()
        app_settings.sync_period_min = new_period
        app_settings.save()
        self._fill_gui_settings()
        
    def _start_threads(self):
        """
        Start background threads for monitoring game status.
        """
        self.monitor_thread = GameMonitorThread(check_interval_seconds=1)
        self.monitor_thread.status_changed.connect(self._on_game_status_changed)
        self.monitor_thread.start()
        
        
        self.autosync_thread = AutoSyncThread()
        self.autosync_thread.time_passed.connect(self._fetch)
        self.autosync_thread.start()
        
        
        self.friends_thread = FriendsPlayingCheckThread()
        self.friends_thread.status_changed.connect(self._on_friend_playing_check)
        self.friends_thread.start()
        
    def _on_game_status_changed(self, is_running: bool):
        self._fill_gui()
        if is_running:
            logger.info("Game launched")
        else:
            logger.info("Game closed")
            self._fetch()
            
    def _on_friend_playing_check(self, is_playing: bool):
        self.label_friend_playing.setStyleSheet("color: green;") if is_playing else self.label_friend_playing.setStyleSheet("color: red;")
        text = "Friend playing" if is_playing else "Offline"
        text = f"{text} ({datetime.now().strftime("%d.%m.%Y %H:%M:%S")})"
        self.label_friend_playing.setText(text)
            
    def _fetch(self, manual=False):
        try:
            logger.info("Starting synchronization...")
            
            if app_settings.google_app_url is None:
                raise ValueError("Google App URL not defined!")
            
            self.label_syncing.show()
            self.pushButton_fetch.setEnabled(False)
            self.label_sync_start.setText(f"Started at: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}")
            self.label_sync_start.show()
            
            QApplication.processEvents()
            
            global synced_list
            
            # 1. Load Sync list
            synced_list.load()
            # 2. Get list of files from Google Drive
            drivelist = get_files()
            # 3. Compare sync list with files available from Google Drive and files available locally
            new_local, new_online = compare(synclist=synced_list, drivelist=drivelist, worldname=app_settings.world_name)
            # 4. Upload/Download unsynced files & Update sync list
            synced_list = upload_and_download_diff(new_local=new_local, new_online=new_online, synclist=synced_list)
            synced_list.save()
            # 5. Update runtime info
            app_runtime.last_sync = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            app_runtime.save()
            
            self._fill_gui_runtime()
            
            self.label_syncing.hide()
            self.pushButton_fetch.setEnabled(True)
            self.label_sync_start.hide()
            
            logger.success("Sync finished")
        except Exception as e:
            self.label_syncing.hide()
            self.pushButton_fetch.setEnabled(True)
            self.label_sync_start.hide()
            
            logger.error("Synchronization failed!")
            logger.exception(e)
            
            if manual:
                show_error_dialog(message="Sync failed!", title="Synchronization error", details=str(e), parent=self)
                
    def _launch_satisfactory(self):
        try:
            webbrowser.open("steam://rungameid/526870")
        except Exception as e:
            logger.error("Launching Satisfactory failed!")
            logger.exception(e)
            show_error_dialog(message="Launch failed!", title="Launching Satisfactory failed", details=str(e), parent=self)
        
    def lock_play_button(self, lock: bool):
        self.pushButton_play.setEnabled(not lock)

    def closeEvent(self, event):
        self.monitor_thread.stop()
        event.accept()
