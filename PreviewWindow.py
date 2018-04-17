import sys, os
import logging
import pathlib
from WallHaven import WallHaven
from PyQt5 import QtWidgets, QtCore, QtGui
from WallHaven import WallHavenPicture

log = logging.getLogger('PreviewWindowLog')
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)-4s: %(message)s')
console_handler.setFormatter(formatter)
log.addHandler(console_handler)

setting = QtCore.QSettings('./setting.ini', QtCore.QSettings.IniFormat)


class PreviewWindow(QtWidgets.QLabel):

    stop_loader_signal = QtCore.pyqtSignal()
    load_picture_signal = QtCore.pyqtSignal(str)
    download_picture_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.close_button = QtWidgets.QPushButton(self)
        self.download_button = QtWidgets.QPushButton(self)
        self.loader = PictureLoader()
        self.pixmap = QtGui.QPixmap()
        self.picture = None
        self.mouse_press_pos = None
        self.init_ui()
        self.init_close_button()
        self.init_download_button()
        self.init_picture_loader()

    def init_ui(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        screen_center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        self.setGeometry(0, 0, 1600, 900)
        fg = self.frameGeometry()
        fg.moveCenter(screen_center_point)
        self.move(fg.topLeft())
        # self.setScaledContents(True)
        self.setStyleSheet('Background-color: rgb(222, 222, 222, 100)')
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def init_close_button(self):
        self.close_button.setText('Close')
        self.close_button.setGeometry(self.rect().width() - 40, 0, 40, 40)
        self.close_button.clicked.connect(self.preview_window_close_slot)
        self.close_button.setStyleSheet('Background-color: gray;'
                                        'border-radius: 20px')
        self.close_button.setWindowOpacity(1)

    def init_picture_loader(self):
        self.loader.load_part_complete_signal.connect(self.load_picture_slot)
        self.load_picture_signal.connect(self.loader.load_picture)

    def init_download_button(self):
        self.download_button.setText('下载壁纸')
        self.download_button.setGeometry(int(self.rect().width() / 2 - 50), self.height() - 50, 100, 40)
        self.download_picture_signal.connect(self.loader.download_picture)
        self.download_button.clicked.connect(self.download_picture_slot)

    def load_picture(self, picture):
        log.debug('load new picture id {}'.format(picture))
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

    @QtCore.pyqtSlot()
    def download_picture_slot(self):
        log.info('download picture:' + self.picture)
        self.download_picture_signal.emit(setting.value('download_path'))

    def mousePressEvent(self, a0: QtGui.QMouseEvent):
        if a0.button() == QtCore.Qt.LeftButton:
            self.mouse_press_pos = a0.globalPos() - self.frameGeometry().topLeft()
            a0.ignore()

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent):
        if a0.buttons() == QtCore.Qt.LeftButton:
            self.move(a0.globalPos() - self.mouse_press_pos)
            a0.ignore()


class PictureLoader(QtCore.QObject):

    load_part_complete_signal = QtCore.pyqtSignal(QtGui.QPixmap)
    progress_signal = QtCore.pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.wh = WallHaven()
        self.mutex = QtCore.QMutex()
        self.is_running = False
        self.is_complete = False
        self.preview_windows_size = QtCore.QSize(1600, 900)
        self.picture = None
        self.pixmap = QtGui.QPixmap()
        self.loader_thread = QtCore.QThread()
        self.thread().finished.connect(self.deleteLater)
        self.moveToThread(self.loader_thread)
        self.loader_thread.start()

    def __del__(self):
        self.thread().quit()
        self.thread().wait()

    @QtCore.pyqtSlot(str)
    def load_picture(self, picture):
        self.mutex.lock()
        self.is_complete = False
        self.is_running = True
        self.mutex.unlock()
        self.picture = picture
        picture_data = bytearray()
        data_size = 0
        data_iter, total_size = self.wh.get_origin_data(picture)
        log.debug('load picture {}, size {:.2f}KB'.format(picture, total_size / 1024))
        for block in data_iter:
            picture_data += block
            data_size += len(block)
            if self.is_stopped():
                break
            progress = 100.0 * data_size / total_size
            log.debug('load picture {} in {:.1f}%'.format(picture, progress))
            if progress == 100.0:
                self.is_complete = True
            self.progress_signal.emit(progress)
            self.pixmap.loadFromData(picture_data)
            self.pixmap = self.pixmap.scaled(self.preview_windows_size, QtCore.Qt.KeepAspectRatioByExpanding)
            self.load_part_complete_signal.emit(self.pixmap)
        log.debug('stop load picture')

    @QtCore.pyqtSlot(str)
    def download_picture(self, path):
        origin_url, _ = self.wh.get_picture_info(self.picture)
        filename = origin_url[origin_url.rfind('/') + 1:]
        log.info('old path' + path)
        path = os.path.join(path, filename)
        log.info('start download picture, path:' + path)

        if self.is_complete:
            self.pixmap.save(path)
        else:
            self.wh.download_picture(self.picture, path)
        log.info('finish download')

    def is_stopped(self):
        self.mutex.lock()
        status = not self.is_running
        self.mutex.unlock()
        return status

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