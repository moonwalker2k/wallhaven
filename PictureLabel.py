from WallHaven import Picture
from PyQt5 import QtWidgets, QtCore, QtGui
from WallHaven import WallHavenPicture


class PictureLabel(QtWidgets.QLabel):

    clicked = QtCore.pyqtSignal(WallHavenPicture)

    def __init__(self, parent=None, picture=None):
        super().__init__(parent)
        self.picture = picture

    def clear_picture(self):
        self.setPixmap(QtGui.QPixmap())

    def set_picture(self, picture, pixmap):
        self.picture = picture
        self.setPixmap(pixmap)

    def mousePressEvent(self, ev: QtGui.QMouseEvent):
        if ev.buttons() == QtCore.Qt.LeftButton:
            if self.picture:
                self.clicked.emit(self.picture)
            ev.accept()