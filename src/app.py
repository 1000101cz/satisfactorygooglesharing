from pathlib import Path
from PyQt6 import uic
from loguru import logger
from PyQt6.QtWidgets import QMainWindow, QFileDialog

from .settings import app_settings, app_runtime
from .app_investigation import is_steam_running, is_satisfactory_running, GameMonitorThread


ui_path = Path(__file__).parent.parent / 'data' / 'app.ui'
window = uic.loadUiType(str(ui_path))[0]


class Window(QMainWindow, window):
    def __init__(self, parent=None):
        self._initialization = True
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        
        self._connects()
        
        self._fill_gui()
        
        self._start_threads()
        
    def _connects(self):
        self.pushButton_saved_files_path.clicked.connect(self._saved_files_path_clicked)
        self.pushButton_google_app_url.clicked.connect(self._google_app_url_clicked)
        self.pushButton_sync_period.clicked.connect(self._sync_period_clicked)
        
    def _fill_gui(self):
        self._fill_gui_settings()
        self._fill_gui_runtime()
        
    def _fill_gui_settings(self):
        # Saved files path
        if not isinstance(app_settings.saved_files_path, Path) or not app_settings.saved_files_path.is_dir():
            self.label_saved_files_path.setText("Not set")
        else:
            self.label_saved_files_path.setText(str(app_settings.saved_files_path))
            
        # Google app URL
        self.lineEdit.setText(app_settings.google_app_url or "")
        
        # Sync period
        self.spinBox.setValue(app_settings.sync_period_min)
        
    def _fill_gui_runtime(self):
        # Latest save
        text = app_runtime.latest_save or "Unknown"
        self.label_latest_save.setText(text)
        
        # Last sync
        text = app_runtime.last_sync or "Unknown"
        self.label_last_sync.setText(text)
        
        # Steam running
        text = "Yes" if is_steam_running() else "No"
        self.label_steam_running.setText(text)
        
        # Satisfactory running
        text = "Yes" if is_satisfactory_running() else "No"
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
            self._settings_changed()
        
    def _google_app_url_clicked(self):
        new_url = self.lineEdit.text().strip()
        if new_url == "":
            new_url = None
        app_settings.google_app_url = new_url
        app_settings.save()
        self._fill_gui_settings()
        self._settings_changed()
        
    def _sync_period_clicked(self):
        new_period = self.spinBox.value()
        app_settings.sync_period_min = new_period
        app_settings.save()
        self._fill_gui_settings()
        self._settings_changed()

    def _settings_changed(self):
        """
        Settings have changed, time for sync with google drive.
        """
        ...
        
    def _start_threads(self):
        """
        Start background threads for monitoring game status.
        """
        self.monitor_thread = GameMonitorThread(check_interval_seconds=1)
        self.monitor_thread.status_changed.connect(self._on_game_status_changed)
        self.monitor_thread.start()
        
    def _on_game_status_changed(self, is_running: bool):
        if is_running:
            self.label_satisfactory_running.setText("Running")
            logger.info("Game launched")
        else:
            self.label_satisfactory_running.setText("Not Running")
            logger.info("Game closed")

    def closeEvent(self, event):
        self.monitor_thread.stop()
        event.accept()
