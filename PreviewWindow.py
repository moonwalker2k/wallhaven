import sys
import threading
from WallHaven import WallHaven
from PyQt5 import QtWidgets, QtCore, QtGui
from WallHaven import WallHavenPicture


class PreviewWindow(QtWidgets.QLabel):

    refresh_picture_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.picture_label = QtWidgets.QLabel(self)
        self.close_button = QtWidgets.QPushButton(self)
        self.load_picture_button = QtWidgets.QPushButton(self)
        self.wh = WallHaven()
        self.loader = PictureLoader()
        self.pixmap = QtGui.QPixmap()
        self.wallhaven_picture = None
        self.mouse_press_pos = None
        self.picture_data = bytearray()
        self.init_ui()
        self.close_button_init()
        self.load_picture_button_init()
        self.picture_loader_init()
        self.loader.start()

    def init_ui(self):
        self.setWindowFlags(QtCore.Qt.BypassWindowManagerHint)
        screen_center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        self.setGeometry(0, 0, 1600, 900)
        fg = self.frameGeometry()
        fg.moveCenter(screen_center_point)
        self.move(fg.topLeft())
        self.setStyleSheet('Background-color: rgb(222, 222, 222, 100)')
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def close_button_init(self):
        self.close_button.setText('Close')
        self.close_button.setGeometry(self.rect().width() - 40, 0, 40, 40)
        self.close_button.clicked.connect(self.hide)
        self.close_button.setStyleSheet('Background-color: gray;'
                                        'border-radius: 20px')
        self.close_button.setWindowOpacity(1)

    def load_picture_button_init(self):
        self.load_picture_button.setText('Load')
        self.load_picture_button.setGeometry(self.rect().width() - 80, 0, 40, 40)
        self.load_picture_button.setStyleSheet('Background-color: gray;'
                                        'border-radius: 20px')
        self.refresh_picture_signal.connect(self.refresh_picture_slot)
        self.load_picture_button.clicked.connect(self.test_picture_load_slot)

    def picture_loader_init(self):
        self.loader.loaded_complete_signal.connect(self.load_complete_slot)

    def load_picture(self, picture):
        self.loader.stop_load()
        self.loader.update_picture(picture.id)
        print('loader start to work')

    @QtCore.pyqtSlot()
    def test_picture_load_slot(self):
        self.refresh_picture_signal.emit('620963')
        print('refresh signal emit')

    @QtCore.pyqtSlot(str)
    def refresh_picture_slot(self, id):
        self.loader.update_picture(id)
        print('loader start to work')

    @QtCore.pyqtSlot(QtGui.QPixmap)
    def load_complete_slot(self, pixmap):
        print('setPixmap')
        self.setPixmap(pixmap)

    def mousePressEvent(self, a0: QtGui.QMouseEvent):
        if a0.button()  == QtCore.Qt.LeftButton:
            self.mouse_press_pos = a0.globalPos() - self.frameGeometry().topLeft()
            a0.ignore()

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent):
        if a0.buttons() == QtCore.Qt.LeftButton:
            self.move(a0.globalPos() - self.mouse_press_pos)
            a0.ignore()


class PictureLoader(QtCore.QThread):

    loaded_complete_signal = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.wh = WallHaven()
        self.loading = False
        self.picture = None
        self.pixmap = QtGui.QPixmap()
        self.picture_data = bytearray()
        self.mutex = QtCore.QMutex()
        self.wait_condition = QtCore.QWaitCondition()

    def stop_load(self):
        self.mutex.lock()
        self.loading = False
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def update_picture(self, picture):
        self.stop_load()
        self.mutex.lock()
        self.picture = picture
        self.loading = True
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def run(self):
        while True:
            self.mutex.lock()
            if not self.loading:
                print('Watting....')
                self.wait_condition.wait(self.mutex)
                self.mutex.unlock()
                continue
            self.mutex.unlock()
            data_iter, size = self.wh.get_origin_data(self.picture)
            print('size ', size)
            self.picture_data.clear()
            for part in data_iter:
                self.mutex.lock()
                if not self.loading:
                    break
                print('loading....')
                self.picture_data += part
                self.mutex.unlock()
            print('load picture result:', self.pixmap.loadFromData(self.picture_data))
            print('save picture result:', self.pixmap.save('/home/moonwalker/Picture/test.jpg', 'JPG'))
            self.loaded_complete_signal.emit(self.pixmap)
            print('load complete')
            self.loading = False


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui = PreviewWindow()
    gui.show()
    sys.exit(app.exec_())