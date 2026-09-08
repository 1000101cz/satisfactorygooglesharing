import sys
from PyQt6.QtWidgets import QApplication
from .logging.setup import setup_logging
setup_logging()

from .app import Window

def launch_app():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    window.raise_()
    app.exec()