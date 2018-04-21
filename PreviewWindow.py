import sys, os
import logging
import pathlib
from WallHaven import WallHaven
from PyQt5 import QtWidgets, QtCore, QtGui
from WallHaven import WallHavenPicture
from Setting import setting

log = logging.getLogger('PreviewWindowLog')
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)-4s: %(message)s')
console_handler.setFormatter(formatter)
log.addHandler(console_handler)


class PreviewWindow(QtWidgets.QLabel):

    stop_loader_signal = QtCore.pyqtSignal()
    load_picture_signal = QtCore.pyqtSignal(str)
    download_picture_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.close_button = QtWidgets.QPushButton(self)
        self.download_button = QtWidgets.QPushButton(self)
        self.info_label = QtWidgets.QLabel(self)
        self.download_complete_label = QtWidgets.QLabel(self)
        self.loader = PictureLoader()
        self.pixmap = QtGui.QPixmap()
        self.picture = None
        self.mouse_press_pos = None
        self.init_ui()
        self.init_info_label()
        self.init_close_button()
        self.init_download_button()
        self.init_picture_loader()

    def init_ui(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        screen_center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        self.setFixedSize(1600, 900)
        fg = self.frameGeometry()
        fg.moveCenter(screen_center_point)
        self.move(fg.topLeft())
        # 必须禁用Contents缩放，否则无法实现等比例缩放大图预览
        # self.setScaledContents(True)
        self.setAutoFillBackground(True)
        self.setStyleSheet('PreviewWindow{Background-color: rgba(128, 128, 128, 255)}')
        # palette = QtGui.QPalette()
        # palette.setColor(QtGui.QPalette.Background, QtGui.QColor(0, 255, 0, 0))
        # self.setPalette(palette)

        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def init_info_label(self):
        self.reset_info_label()
        self.info_label.move(20, self.height() - 40)
        self.info_label.setStyleSheet('color: black;'
                                      'background-color: rgba(255, 255, 255, 80);'
                                      'border-radius: 4px')

    def init_download_complete_label(self):
        self.download_complete_label.setText('下载完成')
        self.setStyleSheet('color: black;'
                           'background-color: rgba(255, 255, 255, 80'
                           'border-radius:12px')
        font = self.download_complete_label.font()
        font.setPointSize(20)
        font.setBold(True)
        self.download_complete_label.move(self.width(), 100)

    def reset_info_label(self):
        self.info_label.setText('ID:{:^8} {:^11}'.format('N/A', 0))

    def init_close_button(self):
        self.close_button.setText('Close')
        self.close_button.setGeometry(self.rect().width() - 40, 0, 40, 40)
        self.close_button.clicked.connect(self.preview_window_close_slot)
        self.close_button.setStyleSheet('Background-color: rgba(128, 128, 128, 100);'
                                        'border-radius: 8px')
        self.close_button.setWindowOpacity(0)

    def init_picture_loader(self):
        self.loader.load_part_complete_signal.connect(self.load_picture_slot)
        self.load_picture_signal.connect(self.loader.load_picture)

    def init_download_button(self):
        self.download_button.setText('下载壁纸')
        self.download_button.setStyleSheet('Background-color: rgba(255, 255, 255, 150)')
        self.download_button.setGeometry(int(self.rect().width() / 2 - 50), self.height() - 60, 100, 40)
        self.download_picture_signal.connect(self.loader.download_picture)
        self.download_button.clicked.connect(self.download_picture_slot)

    def load_picture(self, picture):
        log.debug('load new picture id {}'.format(picture))
        self.picture = picture
        self.show()
        self.load_picture_signal.emit(picture)

    def update_info(self, id, resolution, size=0, progress=0):
        if size == 0:
            self.info_label.setText('ID:{:^8} {:^12}'.format(id, resolution))
        else:
            self.info_label.setText('ID:{:^8} {:^11} {:^6.1f}KB {:^6.1f}%'.format(id, resolution, size / 1024, progress))
        self.info_label.resize(self.info_label.sizeHint())

    def show_complete_once(self):
        width = self.download_complete_label.width()
        move = 0
        while move < width:
            self.download_complete_label.move(self.width() - move, self.download_complete_label.geometry().y())
            move += 3
            QtCore.QThread.sleep(20)
        QtCore.QThread.sleep(500)
        move = 0
        while move < width:
            self.download_complete_label.move(self.width() - width + move, self.download_complete_label.geometry().y())
            move += 3
            QtCore.QThread.sleep(20)

    @QtCore.pyqtSlot(QtGui.QPixmap, str, int, float)
    def load_picture_slot(self, pixmap, resolution, size=0, progress=0):
        self.setPixmap(pixmap)
        self.update_info(self.picture, resolution, size, progress)

    @QtCore.pyqtSlot()
    def preview_window_close_slot(self):
        self.hide()
        self.reset_info_label()
        self.loader.stop_loader()

    @QtCore.pyqtSlot()
    def download_picture_slot(self):
        log.info('download picture:' + self.picture)
        self.download_picture_signal.emit(setting.value('download_path'))

    @QtCore.pyqtSlot(str)
    def download_complete_slot(self, path):
        log.info('download %s complete', path)

    def mousePressEvent(self, a0: QtGui.QMouseEvent):
        if a0.button() == QtCore.Qt.LeftButton:
            self.mouse_press_pos = a0.globalPos() - self.frameGeometry().topLeft()
            a0.accept()

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent):
        if a0.buttons() == QtCore.Qt.LeftButton:
            self.move(a0.globalPos() - self.mouse_press_pos)
            a0.accept()


class PictureLoader(QtCore.QObject):

    load_part_complete_signal = QtCore.pyqtSignal(QtGui.QPixmap, str, int, float)
    download_complete_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.wh = WallHaven()
        self.mutex = QtCore.QMutex()
        self.is_running = False
        self.is_complete = False
        self.preview_windows_size = QtCore.QSize(1600, 900)
        self.picture = None
        self.pixmap = QtGui.QPixmap(self.preview_windows_size)
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
        data_picture = self.wh.create_picture(picture)
        picture_data = bytearray()
        data_size = 0
        data_iter, total_size = self.wh.get_origin_data(data_picture)
        resolution = 'X'.join([str(s) for s in data_picture.resolution])
        self.load_part_complete_signal.emit(QtGui.QPixmap(), resolution, total_size, 0)
        log.debug('resolution:%s' % resolution)
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
            self.pixmap.loadFromData(picture_data)
            pixmap = self.pixmap.scaled(self.preview_windows_size, QtCore.Qt.KeepAspectRatioByExpanding,
                                             QtCore.Qt.SmoothTransformation)
            self.load_part_complete_signal.emit(pixmap, resolution, total_size, progress)
        log.debug('stop load picture')

    @QtCore.pyqtSlot(str)
    def download_picture(self, path):
        origin_url, _ = self.wh.get_picture_info(self.picture)
        filename = origin_url[origin_url.rfind('/') + 1:]
        path = str(pathlib.PurePath.joinpath(pathlib.PurePath(path), filename))
        log.info('start download picture, path:' + path)

        if self.is_complete:
            self.pixmap.save(path)
        else:
            self.wh.download_picture(self.picture, path)
        self.download_complete_signal.emit(path)
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