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
        self.picture = None
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
        # self.setScaledContents(True)
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
        self.loader.load_part_complete_signal.connect(self.load_picture_slot)
        self.loader_thread.finished.connect(self.loader.deleteLater)
        self.load_picture_signal.connect(self.loader.load_picture)
        self.loader_thread.start()

    def load_picture(self, picture):
        log.debug('load new picture id {}'.format(picture.id))
        self.picture = picture
        self.show()
        self.load_picture_signal.emit(picture)


    @QtCore.pyqtSlot(QtGui.QPixmap)
    def load_picture_slot(self, pixmap):
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
        self.mutex = QtCore.QMutex()
        self.is_running = False
        self.preview_windows_size = QtCore.QSize(1600, 900)
        self.pixmap = QtGui.QPixmap()

    @QtCore.pyqtSlot(WallHaven)
    def load_picture(self, picture):
        self.mutex.lock()
        self.is_running = True
        self.mutex.unlock()
        picture_data = bytearray()
        data_size = 0
        pixmap = QtGui.QPixmap(self.preview_windows_size)
        data_iter, total_size = self.wh.get_origin_data(picture)
        log.debug('load picture {}, size {:.2f}KB'.format(picture.id, total_size / 1024))
        for block in data_iter:
            picture_data += block
            data_size += len(block)
            if self.is_stopped():
                break
            log.debug('load picture {} in {:.1f}%'.format(picture.id, 100.0 * data_size / total_size))
            self.pixmap.loadFromData(picture_data)
            self.pixmap = self.pixmap.scaled(self.preview_windows_size, QtCore.Qt.KeepAspectRatioByExpanding)
            self.load_part_complete_signal.emit(self.pixmap)
        log.debug('stop load picture')

    def is_stopped(self):
        self.mutex.lock()
        if not self.is_running:
            self.mutex.unlock()
            return True
        else:
            self.mutex.unlock()
            return False


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