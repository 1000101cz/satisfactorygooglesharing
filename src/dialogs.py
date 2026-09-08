from PyQt6 import uic
import requests
from typing import List, Dict
from PyQt6.QtWidgets import QMessageBox, QWidget, QSpacerItem, QSizePolicy, QGridLayout, QDialog, QInputDialog, QTableWidgetItem
from .steam_api import get_steam_id_from_url

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


from .utils import get_resource_path
friend_list_dialog_ui_path = get_resource_path("data/friend_list.ui")
friend_list_dialog, _ = uic.loadUiType(str(friend_list_dialog_ui_path))


class FriendListDialog(QDialog, friend_list_dialog):
    def __init__(self, api_key: str, current_friends: List[Dict[str, str]] = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        self.api_key = api_key
        
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["Nickname", "Steam ID"])
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        
        self.pushButton_add.clicked.connect(self._add_friend)
        self.pushButton_remove.clicked.connect(self._remove_friend)
        self.pushButton_use.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)
        
        # Načtení stávajících přátel (pokud nějací jsou)
        if current_friends:
            for friend in current_friends:
                self._add_row_to_table(friend.get("nickname", "Neznámý"), friend.get("steam_id", ""))

    def _add_friend(self):
        url, ok = QInputDialog.getText(
            self, 
            "Add friend", 
            "Enter profile URL or Steam ID:"
        )
        
        if not ok or not url.strip():
            return

        steam_id = get_steam_id_from_url(url)
        if not steam_id:
            QMessageBox.warning(self, "Error", "Invalid Steam ID.")
            return

        if self._is_steam_id_in_table(steam_id):
            QMessageBox.information(self, "Warning", "User already on the list.")
            return

        nickname = self._fetch_nickname(steam_id)
        self._add_row_to_table(nickname, steam_id)

    def _remove_friend(self):
        current_row = self.tableWidget.currentRow()
        if current_row >= 0:
            self.tableWidget.removeRow(current_row)
        else:
            QMessageBox.information(self, "Warning", "Select row to be deleted first")

    def _add_row_to_table(self, nickname: str, steam_id: str):
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row, 0, QTableWidgetItem(nickname))
        self.tableWidget.setItem(row, 1, QTableWidgetItem(steam_id))

    def _is_steam_id_in_table(self, steam_id: str) -> bool:
        """ Check if friend is already in table """
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 1)
            if item and item.text() == steam_id:
                return True
        return False

    def _fetch_nickname(self, steam_id: str) -> str:
        """ Get nickname based on Steam ID """
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={self.api_key}&steamids={steam_id}"
        try:
            res = requests.get(url, timeout=5).json()
            players = res.get("response", {}).get("players", [])
            if players:
                return players[0].get("personaname", "Neznámý")
        except Exception:
            pass
        return "Neznámý"

    def get_friends_list(self) -> List[Dict[str, str]]:
        """ Get list of friends from table """
        friends = []
        for row in range(self.tableWidget.rowCount()):
            nickname_item = self.tableWidget.item(row, 0)
            steam_id_item = self.tableWidget.item(row, 1)
            if nickname_item and steam_id_item:
                friends.append({
                    "nickname": nickname_item.text(),
                    "steam_id": steam_id_item.text()
                })
        return friends