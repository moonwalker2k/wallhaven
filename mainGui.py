import sys
import threading
from WallHaven import WallHaven, WallHavenPicture

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QDesktopWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSlot, QThread
from PictureLabel import PictureLabel


class MainGui(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('WallHaven')
        self.setWindowIcon(QIcon('src/logo.png'))
        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.resize(1280, 720)
        self.tabs_widget = PreviewTabs(self)
        self.init_preview_tabs()
        self.move_to_center()
        self.show()

    def move_to_center(self):
        fg = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        fg.moveCenter(screen_center)
        self.move(fg.topLeft())

    def init_preview_tabs(self):
        self.layout().addWidget(self.tabs_widget)
        self.tabs_widget.init_all_tabs()


class MainTabUpdate(QThread):

    update_signal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.wh = WallHaven()
        self.pixmap = None

    def run(self):
        count = 0
        for pic in self.wh.get_main_web_pictures():
            self.pixmap = QPixmap()
            self.pixmap.loadFromData(QtCore.QByteArray(pic.get_preview_data()))
            self.update_signal.emit(count)
            count += 1


class PreviewTabs(QWidget):


    def __init__(self, parent=None):
        super().__init__(parent)
        self.wh = WallHaven()
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.tabs = QtWidgets.QTabWidget()

        self.main_tab = QWidget()
        self.latest_tab = QWidget()
        self.top_tab = QWidget()
        self.random_tab = QWidget()

        self.tabs.addTab(self.main_tab, 'Main')
        self.tabs.addTab(self.latest_tab, 'Latest')
        self.tabs.addTab(self.top_tab, 'Top')
        self.tabs.addTab(self.random_tab, 'Random')

        self.main_tabs_updater = MainTabUpdate()

        self.layout().addWidget(self.tabs)

    def init_all_tabs(self):
        self.main_tab.setLayout(QtWidgets.QGridLayout())
        self.main_tabs_updater.update_signal.connect(self.add_main_tab_label)

        self.main_tabs_updater.start()

    @pyqtSlot(int)
    def add_main_tab_label(self, count):
        print('update')
        picture_label = PictureLabel()
        picture_label.setPixmap(self.main_tabs_updater.pixmap)
        self.main_tab.layout().addWidget(picture_label, int(count / 4), count % 4)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MainGui()
    sys.exit(app.exec_())
