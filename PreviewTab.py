import logging, sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap
from WallHaven import WallHaven, Category
from PreviewWindow import PreviewWindow
from PictureCacher import PictureCacher
from PictureLabel import PictureLabel


log = logging.getLogger('PreviewTabLog')
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)-4s: %(message)s')
console_handler.setFormatter(formatter)
log.addHandler(console_handler)


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
                              'border-radius: 7px;'
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

    @QtCore.pyqtSlot(str)
    def preview_clicked_slot(self, picture):
        self.preview_window.show()
        self.preview_window.setPixmap(QPixmap())
        self.preview_window.load_picture(picture)


class PreviewTab(QtWidgets.QWidget):

    update_tab_signal = QtCore.pyqtSignal(Category, int)
    clicked_for_preview_signal = QtCore.pyqtSignal(str)

    def __init__(self, category, num, parent=None):
        super().__init__(parent)
        self.num = num
        self.page = 1
        self.category = category
        self.updater = TabUpdater()
        self.init_ui(num)

    def init_ui(self, num):
        self.setLayout(QtWidgets.QGridLayout())
        self.add_label_to_tab(num)
        self.updater.updated_one_picture_signal.connect(self.update_tab_slot)

    def add_label_to_tab(self, num):
        for i in range(num):
            label = PictureLabel()
            # label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
            label.setFixedSize(300, 200)
            label.setMargin(0)
            label.setContentsMargins(0,0,0,0)
            label.clicked.connect(self.clicked_for_preview_slot)
            self.layout().addWidget(label, int(i / 4), i % 4)
            self.layout()

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
        if self.page == 1:
            return
        self.page -= 1
        self.update_tab(self.page)

    @QtCore.pyqtSlot(str, int, QPixmap)
    def update_tab_slot(self, picture, count, pixmap):
        label = self.layout().itemAt(count).widget()
        label.set_picture(picture, pixmap)

    @QtCore.pyqtSlot(str)
    def clicked_for_preview_slot(self, picture):
        self.clicked_for_preview_signal.emit(picture)


class TabUpdater(QtCore.QObject):

    update_tab_signal = QtCore.pyqtSignal(Category, int)

    updated_one_picture_signal = QtCore.pyqtSignal(str, int, QPixmap)

    def __init__(self, wh=WallHaven()):
        super().__init__()
        self.wh = wh
        self.cache = PictureCacher()
        self.pixmap = QtGui.QPixmap()
        self.is_running = False
        self.mutex = QtCore.QMutex()
        self.thread = QtCore.QThread()
        self.update_tab_signal.connect(self.update_tab_slot)
        # self.thread.finished.connect(self.deleteLater)
        self.moveToThread(self.thread)
        self.thread.start()

    def __del__(self):
        self.thread.quit()
        self.thread.wait()

    @QtCore.pyqtSlot(Category, int)
    def update_tab_slot(self, category, page=1):
        if category == Category.MAIN:
            picture_iter = self.wh.get_main_web_pictures()
        else:
            picture_iter = self.wh.get_category_picture(category, page)
        count = 0
        log.info('updater restart')
        for pic in picture_iter:
            self.mutex.lock()
            if not self.is_running:
                self.mutex.unlock()
                break
            self.mutex.unlock()
            pixmap = self.cache.get_pixmap(pic)
            if pixmap:
                log.debug('load from cache, id:' + pic)
                self.pixmap = pixmap
            else:
                self.pixmap.loadFromData(self.wh.get_preview_data(pic))
                self.cache.enqueue(pic, self.pixmap.copy())
                log.debug('update tab:{} picture:{}'.format(category.value, pic))
            self.updated_one_picture_signal.emit(pic, count, self.pixmap)
            count += 1
        log.info('updater stop')

    def stop_update(self):
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()
        self.thread.quit()
        self.thread.wait()

    def acquire_update_tab(self, category, page=1):
        self.thread.start()
        self.mutex.lock()
        self.is_running = True
        self.mutex.unlock()
        self.update_tab_signal.emit(category, page)
