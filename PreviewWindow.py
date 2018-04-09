import sys
import logging
from WallHaven import WallHaven
from PyQt5 import QtWidgets, QtCore, QtGui
from WallHaven import WallHavenPicture


log = logging.getLogger('PreviewWindowLog')
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)-4s: %(message)s')
console_handler.setFormatter(formatter)
log.addHandler(console_handler)


class PreviewWindow(QtWidgets.QLabel):

    stop_loader_signal = QtCore.pyqtSignal()
    load_picture_signal = QtCore.pyqtSignal(WallHavenPicture)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.close_button = QtWidgets.QPushButton(self)
        self.loader = PictureLoader()
        self.loader_thread = QtCore.QThread()
        self.pixmap = QtGui.QPixmap()
        self.wallhaven_picture = None
        self.mouse_press_pos = None
        self.init_ui()
        self.close_button_init()
        self.picture_loader_init()

    def __del__(self):
        self.loader_thread.quit()
        self.loader_thread.wait()

    def init_ui(self):
        self.setWindowFlags(QtCore.Qt.BypassWindowManagerHint)
        screen_center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        self.setGeometry(0, 0, 1600, 900)
        fg = self.frameGeometry()
        fg.moveCenter(screen_center_point)
        self.move(fg.topLeft())
        self.setScaledContents(True)
        self.setStyleSheet('Background-color: rgb(222, 222, 222, 100)')
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def close_button_init(self):
        self.close_button.setText('Close')
        self.close_button.setGeometry(self.rect().width() - 40, 0, 40, 40)
        self.close_button.clicked.connect(self.preview_window_close_slot)
        self.close_button.setStyleSheet('Background-color: gray;'
                                        'border-radius: 20px')
        self.close_button.setWindowOpacity(1)

    def picture_loader_init(self):
        self.loader.moveToThread(self.loader_thread)
        self.loader.load_part_complete_signal.connect(self.load_part_complete_slot)
        self.loader_thread.finished.connect(self.loader.deleteLater)
        self.load_picture_signal.connect(self.loader.load_picture)
        self.loader_thread.start()

    def load_picture(self, picture):
        log.debug('load new picture id {}'.format(picture.id))
        self.show()
        self.load_picture_signal.emit(picture)

    @QtCore.pyqtSlot(QtGui.QPixmap)
    def load_part_complete_slot(self, pixmap):
        self.setPixmap(pixmap)

    @QtCore.pyqtSlot()
    def preview_window_close_slot(self):
        self.hide()
        self.loader.stop_loader()

    def mousePressEvent(self, a0: QtGui.QMouseEvent):
        if a0.button()  == QtCore.Qt.LeftButton:
            self.mouse_press_pos = a0.globalPos() - self.frameGeometry().topLeft()
            a0.ignore()

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent):
        if a0.buttons() == QtCore.Qt.LeftButton:
            self.move(a0.globalPos() - self.mouse_press_pos)
            a0.ignore()


class PictureLoader(QtCore.QObject):

    load_part_complete_signal = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self):
        super().__init__()
        self.wh = WallHaven()
        self.pixmap = QtGui.QPixmap()
        self.picture = None
        self.mutex = QtCore.QMutex()
        self.is_running = False

    @QtCore.pyqtSlot(WallHaven)
    def load_picture(self, picture):
        self.mutex.lock()
        self.is_running = True
        self.mutex.unlock()
        self.picture = picture
        picture_data = bytearray()
        size = 0
        data_iter, total_size = self.wh.get_origin_data(self.picture)
        log.debug('load picture {}, size {:.2f}KB'.format(picture.id, total_size / 1024))
        for block in data_iter:
            picture_data += block
            size += len(block)
            self.pixmap.loadFromData(picture_data)
            self.load_part_complete_signal.emit(self.pixmap)
            log.debug('load picture {} in {:.1f}%'.format(picture.id, 100.0 * size / total_size))
            self.mutex.lock()
            if not self.is_running:
                self.mutex.unlock()
                break
            self.mutex.unlock()
        log.debug('stop load picture')

    def stop_loader(self):
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()
        log.debug('stop loader')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui = PreviewWindow()
    gui.show()
    sys.exit(app.exec_())