import sys
import logging
import Setting
from PreviewWindow import PreviewWindow
from WallHaven import WallHaven, Category, WallHavenPicture
from collections import OrderedDict
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSlot, QThread, QWaitCondition, QMutex, QByteArray
from PictureLabel import PictureLabel


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
        self.center_layout.addWidget(self.preview_tabs)
        self.layout().addLayout(self.top_layout)
        self.layout().addLayout(self.center_layout)
        self.setMinimumSize(1300, 650)

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


class PreviewTab(QWidget):

    update_tab_signal = QtCore.pyqtSignal(Category, int)
    clicked_for_preview_signal = QtCore.pyqtSignal(WallHavenPicture)

    def __init__(self, category, num, parent=None):
        super().__init__(parent)
        self.num = num
        self.page = 1
        self.category = category
        self.updater = TabUpdaterEvenType()
        self.init_ui(num)

    def init_ui(self, num):
        self.setLayout(QtWidgets.QGridLayout())
        self.add_label_to_tab(num)
        self.updater.updated_one_picture_signal.connect(self.update_tab_slot)

    def add_label_to_tab(self, num):
        for i in range(num):
            label = PictureLabel()
            label.setText("None")
            # label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
            label.setFixedSize(300, 200)
            label.setMargin(0)
            label.setContentsMargins(0,0,0,0)
            label.clicked.connect(self.clicked_for_preview_slot)
            self.layout().addWidget(label, int(i / 4), i % 4)

    def update_tab(self, page=1):
        self.updater.stop_update()
        for i in range(self.num):
            self.layout().itemAt(i).widget().clear_picture()
        self.updater.acquire_update_tab(self.category, page)

    def current_page(self):
        return self.page

    def update_next_page(self):
        if self.category == Category.MAIN:
            return
        self.page += 1
        self.update_tab(self.page)

    def update_previous_page(self):
        if self.category == Category.MAIN:
            return
        if (self.page - 1) < 1:
            return
        self.page -= 1
        self.update_tab(self.page)

    @QtCore.pyqtSlot(WallHavenPicture, int, QPixmap)
    def update_tab_slot(self, picture, count, pixmap):
        label = self.layout().itemAt(count).widget()
        label.set_picture(picture, pixmap)

    @QtCore.pyqtSlot(WallHavenPicture)
    def clicked_for_preview_slot(self, picture):
        self.clicked_for_preview_signal.emit(picture)


class PreviewTabs(QtWidgets.QTabWidget):

    update_tab_signal = QtCore.pyqtSignal(Category, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.wh = WallHaven()
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.layout().setSpacing(1)

        self.main_tab = PreviewTab(Category.MAIN, 19)
        self.latest_tab = PreviewTab(Category.LATEST, 24)
        self.top_tab = PreviewTab(Category.TOPLIST, 24)
        self.random_tab = PreviewTab(Category.RANDOM, 24)
        self.all_tabs = (self.main_tab, self.latest_tab, self.top_tab, self.random_tab)

        self.preview_window = PreviewWindow()

        self.init_all_tabs()
        self.init_preview_window()
        self.update_all_tabs()

    def init_all_tabs(self):
        for tab, category in zip(self.all_tabs, Category):
            assert isinstance(tab, PreviewTab)
            tab.setStyleSheet('PictureLabel '
                              '{background-color: gray;'
                              'border-width: 2px;'
                              'border-radius: 10px;'
                              '}')
            tab.clicked_for_preview_signal.connect(self.preview_clicked_slot)
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidget(tab)
            scroll_area.setWidgetResizable(True)
            self.addTab(scroll_area, category.value)

    def init_preview_window(self):
        self.preview_window.hide()
        self.preview_window.setWindowModality(QtCore.Qt.ApplicationModal)

    def update_all_tabs(self):
        for tab in self.all_tabs:
            tab.update_tab()

    @QtCore.pyqtSlot(WallHavenPicture)
    def preview_clicked_slot(self, picture):
        self.preview_window.show()
        self.preview_window.setPixmap(QPixmap())
        self.preview_window.load_picture(picture)


class TabUpdaterEvenType(QtCore.QObject):

    update_tab_signal = QtCore.pyqtSignal(Category, int)

    updated_one_picture_signal = QtCore.pyqtSignal(WallHavenPicture, int, QPixmap)

    def __init__(self, wh=WallHaven()):
        super().__init__()
        self.wh = wh
        self.pixmap = QtGui.QPixmap()
        self.is_running = False
        self.mutex = QtCore.QMutex()
        self.thread = QtCore.QThread()
        self.update_tab_signal.connect(self.update_tab_slot)
        self.moveToThread(self.thread)
        self.thread.start()

    @pyqtSlot(Category, int)
    def update_tab_slot(self, category, page=1):
        assert isinstance(category, Category)
        if category == Category.MAIN:
            picture_iter = self.wh.get_main_web_pictures()
        else:
            picture_iter = self.wh.get_category_picture(category, page)
        count = 0
        for pic in picture_iter:
            self.pixmap.loadFromData(self.wh.get_preview_data(pic.id))
            self.updated_one_picture_signal.emit(pic, count, self.pixmap)
            count += 1
            log.debug('update tab:{} picture:{}'.format(category.value, pic.id))
            self.mutex.lock()
            if not self.is_running:
                self.mutex.unlock()
                break
            self.mutex.unlock()
        log.debug('updater stop')

    def stop_update(self):
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()

    def acquire_update_tab(self, category, page=1):
        self.mutex.lock()
        self.is_running = True
        self.mutex.unlock()
        self.update_tab_signal.emit(category, page)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MainGui()
    sys.exit(app.exec_())
