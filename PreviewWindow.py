import sys
import threading
from WallHaven import WallHaven
from PyQt5 import QtWidgets, QtCore, QtGui
from WallHaven import WallHavenPicture


class PreviewWindow(QtWidgets.QLabel):

    refresh_picture_signal = QtCore.pyqtSignal(str)
    stop_loader_signal = QtCore.pyqtSignal()
    load_picture_signal = QtCore.pyqtSignal(WallHavenPicture)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.picture_label = QtWidgets.QLabel(self)
        self.close_button = QtWidgets.QPushButton(self)
        self.wh = WallHaven()
        self.loader = PictureLoader()
        self.pixmap = QtGui.QPixmap()
        self.wallhaven_picture = None
        self.mouse_press_pos = None
        self.picture_data = bytearray()
        self.init_ui()
        self.close_button_init()
        self.picture_loader_init()
        self.loader.start()

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
        self.loader.loaded_parted_complete_signal.connect(self.load_parted_complete_slot)
        self.stop_loader_signal.connect(self.loader.stop_load_slot, QtCore.Qt.QueuedConnection)
        self.load_picture_signal.connect(self.loader.load_picture_slot, QtCore.Qt.QueuedConnection)

    def load_picture(self, picture):
        print('load noew picture')
        self.show()
        self.load_picture_signal.emit(picture)

    @QtCore.pyqtSlot(QtGui.QPixmap)
    def load_parted_complete_slot(self, pixmap):
        print('set parted pixmap')
        self.setPixmap(pixmap)

    @QtCore.pyqtSlot()
    def preview_window_close_slot(self):
        self.hide()
        self.stop_loader_signal.emit()

    def mousePressEvent(self, a0: QtGui.QMouseEvent):
        if a0.button()  == QtCore.Qt.LeftButton:
            self.mouse_press_pos = a0.globalPos() - self.frameGeometry().topLeft()
            a0.ignore()

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent):
        if a0.buttons() == QtCore.Qt.LeftButton:
            self.move(a0.globalPos() - self.mouse_press_pos)
            a0.ignore()


class PictureLoader(QtCore.QThread):

    loaded_parted_complete_signal = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.wh = WallHaven()
        self.loading = False
        self.picture = None
        self.pixmap = QtGui.QPixmap()
        self.picture_data = bytearray()
        self.mutex = QtCore.QMutex()
        self.wait_condition = QtCore.QWaitCondition()

    @QtCore.pyqtSlot()
    def stop_load_slot(self):
        self.mutex.lock()
        self.loading = False
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    @QtCore.pyqtSlot(WallHavenPicture)
    def load_picture_slot(self, picture):
        self.mutex.lock()
        if self.picture == picture:
            self.mutex.unlock()
            return
        self.picture = picture
        self.loading = True
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def run(self):
        while True:
            self.mutex.lock()
            if not self.loading:
                print('loader watting....')
                self.wait_condition.wait(self.mutex)
                self.mutex.unlock()
                continue
            self.mutex.unlock()
            print('loader start to work')
            data_iter, size = self.wh.get_origin_data(self.picture)
            print('size {:.2f}KB'.format(size / 1024))
            self.picture_data.clear()
            count = 0
            for part in data_iter:
                self.mutex.lock()
                if not self.loading:
                    break
                count += 1
                print('loading part {}'.format(count))
                self.picture_data += part
                # print('load to image result:', self.image.loadFromData(self.picture_data))
                print('part pixmap load result:', self.pixmap.loadFromData(self.picture_data))
                self.loaded_parted_complete_signal.emit(self.pixmap)
                self.mutex.unlock()
            # print('load picture result:', self.pixmap.loadFromData(self.picture_data))
            # self.loaded_complete_signal.emit(self.pixmap)
            print('load complete')
            self.loading = False


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui = PreviewWindow()
    gui.show()
    sys.exit(app.exec_())