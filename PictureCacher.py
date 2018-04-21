from PyQt5 import QtCore, QtWidgets, QtGui


class PictureCacher:
    """
    PictureCacher
    图片缓存类
    将图片临时保存于内存中，增加加载速度
    """

    def __init__(self, max_size=100):
        self.max_size = max_size
        QtGui.QPixmapCache.setCacheLimit(max_size * 1024)

    def enqueue(self, id, pixmap):
        return QtGui.QPixmapCache.insert(id, pixmap)

    def get_pixmap(self, id):
        result = QtGui.QPixmapCache.find(id)
        if result:
            return result
        else:
            return None
