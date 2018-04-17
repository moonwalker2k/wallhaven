from PyQt5 import QtCore, QtWidgets,QtGui
from queue import LifoQueue
from collections import OrderedDict


class PictureCacher:
    '''
    PictureCacher
    图片缓存类
    将图片临时保存于内存和硬盘中，增加加载速度
    '''

    def __init__(self, max_size=64):
        self.max_size = max_size
        self.storage = OrderedDict()

    def enqueue(self, id, pixmap):
        if (len(self.storage) == self.max_size) and not self.has_pixmap(id):
            self.dequeue()
        self.storage[id] = pixmap

    def dequeue(self):
        if len(self.storage) > 0:
            id, _ = self.storage.popitem(False)
            print('pop id %s' % id)

    def get_pixmap(self, id):
        if self.has_pixmap(id):
            old_pixmap = self.storage[id]
            del self.storage[id]
            self.storage[id] = old_pixmap
            return old_pixmap
        else:
            return None

    def has_pixmap(self, id):
        return id in self.storage


