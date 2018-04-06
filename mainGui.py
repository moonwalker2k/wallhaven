import sys
import threading
import time
from WallHaven import WallHaven, WallHavenPicture, Category
from collections import OrderedDict
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSlot, QThread, QWaitCondition, QMutex, QByteArray
from PictureLabel import PictureLabel


class MainGui(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('WallHaven')
        self.setWindowIcon(QIcon('src/logo.png'))
        # self.setFixedSize(1280, 720)
        self.setMinimumSize(1330, 720)
        self.setLayout(QtWidgets.QHBoxLayout(self))
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
        self.all_tabs = (self.main_tab, self.latest_tab, self.top_tab, self.random_tab)
        self.all_tabs_dict = OrderedDict({'main': self.main_tab, 'latest': self.latest_tab,
                              'toplist': self.top_tab, 'random': self.random_tab})

        self.tab_updater = TabUpdater()
        self.updaters_list = []
        for i in range(4):
            self.updaters_list.append(TabUpdater())
        self.init_all_tabs()

    def init_all_tabs(self):
        for tab, category in zip(self.all_tabs, Category):
            tab.setLayout(QtWidgets.QGridLayout())
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidget(tab)
            scroll_area.setWidgetResizable(True)
            self.tabs.addTab(scroll_area, category.value)

        def add_label_to_tab(tab, num):
            for i in range(num):
                label = PictureLabel()
                label.setText("None")
                label.setFixedSize(300, 200)
                label.setMargin(2)
                tab.layout().addWidget(label, int(i / 4), i % 4)

        add_label_to_tab(self.main_tab, 19)
        for tab in self.all_tabs[1:]:
            add_label_to_tab(tab, 24)

        self.layout().addWidget(self.tabs)

        for updater, category in zip(self.updaters_list, Category):
            updater.update_signal.connect(self.update_tab_slot)
            updater.start()
            updater.update_tab(category)

    def update_tab(self, category, page=1):
        self.tab_updater.stop_update()
        self.tab_updater.update_signal.connect(self.update_tab_slot)
        self.tab_updater.update_tab(category, page)

    @pyqtSlot(int, Category, QPixmap)
    def update_tab_slot(self, count, category, pixmap):
        label = self.all_tabs_dict[category.value].layout().itemAt(count).widget()
        label.setPixmap(pixmap)


class TabUpdater(QThread):

    update_signal = QtCore.pyqtSignal(int, Category, QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__wh = WallHaven()
        self.__pixmap = QPixmap()
        self.__updating = False
        self.__update_category = Category.MAIN
        self.__update_category_page = 1
        self.__wait_condition = QWaitCondition()
        self.__mutex = QMutex()

    def update_tab(self, category, page=1):
        assert isinstance(category, Category)
        self.__mutex.lock()
        self.__updating = False
        self.__update_category = category
        self.__update_category_page = page
        self.__updating = True
        self.__wait_condition.wakeAll()
        self.__mutex.unlock()

    def stop_update(self):
        self.__mutex.lock()
        self.__updating = False
        self.__mutex.unlock()

    def get_pixmap(self):
        self.__mutex.lock()
        pixmap = QPixmap(self.__pixmap)
        self.__mutex.unlock()
        return pixmap

    def run(self):
        while True:
            self.__mutex.lock()
            if not self.__updating:
                print("TabUpdater watting")
                self.__wait_condition.wait(self.__mutex)
            self.__mutex.unlock()
            count = 0
            if self.__update_category == Category.MAIN:
                pic_iter = self.__wh.get_main_web_pictures()
            else:
                pic_iter = self.__wh.get_category_picture(self.__update_category, self.__update_category_page)
            for pic in pic_iter:
                start_time = time.time()
                if not self.__updating:
                    break
                self.__mutex.lock()
                self.__pixmap.loadFromData(QByteArray(self.__wh.get_preview_data(pic.id)))
                self.update_signal.emit(count, self.__update_category, QPixmap(self.__pixmap))
                count += 1
                self.__mutex.unlock()
                stop_time = time.time()
                print("updater elapsed time {:.3f}".format(stop_time - start_time))
            self.__updating = False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MainGui()
    sys.exit(app.exec_())
