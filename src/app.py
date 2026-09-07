from pathlib import Path
from PyQt6 import uic
from loguru import logger
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from datetime import datetime
import webbrowser

from .settings import app_settings, app_runtime, synced_list
from .app_investigation import is_steam_running, is_satisfactory_running, GameMonitorThread, AutoSyncThread
from .google_drive import get_files
from .functions import compare, upload_and_download_diff
from .utils import get_resource_path
from .dialogs import show_error_dialog


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
        
        # Steam running
        text = "Yes" if is_steam_running() else "No"
        self.label_steam_running.setText(text)
        
        # Satisfactory running
        text = "Yes" if is_satisfactory_running() else "No"
        if text == "Yes":
            self.lock_play_button(True)
        else:
            self.lock_play_button(False)
        self.label_satisfactory_running.setText(text)
        
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
        
    def _on_game_status_changed(self, is_running: bool):
        self._fill_gui()
        if is_running:
            logger.info("Game launched")
        else:
            logger.info("Game closed")
            self._fetch()
            
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
