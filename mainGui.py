import sys
import logging
import Setting
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget
from PyQt5.QtGui import QIcon
from PreviewTab import PreviewTabs


log = logging.getLogger('MainGUILog')
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)-4s: %(message)s')
console_handler.setFormatter(formatter)
log.addHandler(console_handler)


class MainGui(QWidget):

    def __init__(self):
        super().__init__()
        self.top_layout = QtWidgets.QHBoxLayout()
        self.center_layout = QtWidgets.QHBoxLayout()
        self.setting_button = QtWidgets.QPushButton()
        self.previous_page_button = QtWidgets.QPushButton()
        self.next_page_button = QtWidgets.QPushButton()
        self.page_edit = QtWidgets.QLineEdit()
        self.setting_dialog = Setting.SettingDialog(self)
        self.preview_tabs = PreviewTabs()
        self.init_ui()
        self.init_preview_tabs()
        self.move_to_center()
        self.show()

    def move_to_center(self):
        fg = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        fg.moveCenter(screen_center)
        self.move(fg.topLeft())

    def init_ui(self):
        self.setWindowTitle('WallHaven')
        self.setWindowIcon(QIcon('src/logo.png'))
        self.setLayout(QtWidgets.QVBoxLayout(self))
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.layout().setSpacing(0)

        self.previous_page_button.setText('<')
        self.next_page_button.setText('>')
        self.previous_page_button.setFixedWidth(30)
        self.next_page_button.setFixedWidth(30)
        self.previous_page_button.clicked.connect(self.previous_page_slot)
        self.next_page_button.clicked.connect(self.next_page_slot)
        self.page_edit.setFixedWidth(30)
        self.page_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.page_edit.setText(str(self.preview_tabs.currentWidget().widget().current_page()))

        self.setting_button.setText('设置')
        self.setting_button.clicked.connect(self.setting_dialog.show)

        self.top_layout.addStretch()
        self.top_layout.addWidget(self.previous_page_button)
        self.top_layout.addWidget(self.page_edit)
        self.top_layout.addWidget(self.next_page_button)
        self.top_layout.addWidget(self.setting_button)
        self.top_layout.setSpacing(5)
        self.center_layout.addWidget(self.preview_tabs)
        self.layout().addLayout(self.top_layout)
        self.layout().addLayout(self.center_layout)
        self.setMinimumSize(1300, 900)

    def init_preview_tabs(self):
        self.preview_tabs.currentChanged.connect(self.tab_change_slot)

    @QtCore.pyqtSlot()
    def previous_page_slot(self):
        current_tab = self.preview_tabs.currentWidget().widget()
        current_tab.update_previous_page()
        self.page_edit.setText(str(current_tab.current_page()))

    @QtCore.pyqtSlot()
    def next_page_slot(self):
        current_tab = self.preview_tabs.currentWidget().widget()
        current_tab.update_next_page()
        self.page_edit.setText(str(current_tab.current_page()))

    @QtCore.pyqtSlot()
    def tab_change_slot(self):
        current_tab = self.preview_tabs.currentWidget().widget()
        self.page_edit.setText(str(current_tab.current_page()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MainGui()
    sys.exit(app.exec_())
