from PyQt6.QtWidgets import QMessageBox, QWidget, QSpacerItem, QSizePolicy, QGridLayout

def show_error_dialog(message: str, title: str = "Chyba", parent: QWidget = None, details: str = None, min_width: int = 400):
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if details:
        msg_box.setDetailedText(details)
        
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

    layout = msg_box.layout()
    if isinstance(layout, QGridLayout):
        spacer = QSpacerItem(min_width, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())

    msg_box.exec()
