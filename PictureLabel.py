from WallHaven import Picture
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QPicture
from PyQt5.QtCore import QByteArray


class PictureLabel(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)

    def set_picture(self, picture):
        assert isinstance(picture, Picture)
        data = picture.get_preview_data()
        pixmap = QPixmap()
        loaded = pixmap.loadFromData(QByteArray(data))
        if loaded:
            print("Loaded!")
            self.setPixmap(pixmap)
