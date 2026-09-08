pip install nuitka
pip install zstandard
python -m nuitka --standalone --onefile --onefile-as-archive `
                --plugin-enable=pyqt6 --noinclude-qt-translations `
                --windows-console-mode=disable --include-data-dir=data=data `
                --windows-icon-from-ico=data/icon.ico `
                --nofollow-import-to=PyQt6.QtWebEngine,PyQt6.QtWebEngineCore,PyQt6.QtQuick,PyQt6.QtQml,PyQt6.Qt3D,PyQt6.QtSql,PyQt6.QtTest,PyQt6.QtSensors `
                --output-filename=SatisfactorySaveSync.exe main.py