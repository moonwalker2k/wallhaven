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
        self.storage = {}
        self.storage_list = []

    def enqueue(self, id, pixmap, force=False):
        if self.has_pixmap(id):
            if force:
                self.storage[id] = pixmap
        elif len(self.storage_list) > self.max_size:
            self.dequeue()
            self.storage_list.append(id)
            self.storage[id] = pixmap
        else:
            self.storage_list.append(id)
            self.storage[id] = pixmap

    def dequeue(self):
        if len(self.storage_list) > 0:
            id = self.storage_list.pop(0)
            del(self.storage[id])

    def get_pixmap(self, id):
        return self.storage[id]

    def has_pixmap(self, id):
        try:
            self.storage_list.index(id)
            return True
        except ValueError:
            return False


