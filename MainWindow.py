import logging, sys
import Setting
from PreviewTab import PreviewTabs
from PyQt5 import QtWidgets, QtCore, QtGui

log = logging.getLogger('MainGUILog')
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)-4s: %(message)s')
console_handler.setFormatter(formatter)
log.addHandler(console_handler)


class MainWindow(QtWidgets.QWidget):

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
        self.init_background()
        self.init_preview_tabs()
        self.move_to_center()
        self.show()

    def move_to_center(self):
        fg = self.frameGeometry()
        screen_center = QtWidgets.QDesktopWidget().availableGeometry().center()
        fg.moveCenter(screen_center)
        self.move(fg.topLeft())

    def init_ui(self):
        self.setWindowTitle('WallHaven')
        self.setWindowIcon(QtGui.QIcon('src/logo.png'))
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

    def init_background(self):
        self.setObjectName('MainWindow')
        self.setStyleSheet('QWidget#MainWindow {color: rgb(7, 64, 101);}')

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


class BaseWidget(QtWidgets.QWidget):
    """
    基础自定义QWidget，包括自带的返回按钮，用于QStackWidget中进行切换
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._back_button = QtWidgets.QPushButton(self)
        self.init_back_button()
        self.show()

    def init_ui(self):


    def init_back_button(self):
        pixmap = QtGui.QPixmap('src/icons8-back-arrow-64.png')
        self._back_button.setFlat(True)
        self._back_button.setFixedSize(pixmap.size())
        self._back_button.setIcon(QtGui.QIcon(pixmap))
        self._back_button.setIconSize(pixmap.size())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui = BaseWidget()
    sys.exit(app.exec_())
