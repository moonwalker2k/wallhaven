import re
import abc
import unittest
from PyQt5 import QtCore
import requests
from enum import Enum


class WallHaven:
    '''
    WallHaven.cc
    用于爬取wallhaven壁纸
    '''

    def __init__(self):
        self.categories = {'latest': '/latest',
                           'toplist': '/toplist',
                           'random': '/random'}
        self.session = requests.session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
                                                   ' (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'})
        self.index_url = 'https://alpha.wallhaven.cc'

    def get_main_web_pictures(self):
        data = self.session.get(self.index_url).text
        patten = re.compile(r'<img src="//.*?th-(\d*?)\.\S{3}"')
        for match in patten.finditer(data):
            yield self.create_picture(match.group(1))

    def get_category_picture(self, category, page=1):
        assert isinstance(category, Category)
        url = self.index_url + self.categories[category.value] + '?page=' + str(page)
        data = self.session.get(url).text
        patten = re.compile(r'data-wallpaper-id="(\d*?)"')
        for match in patten.finditer(data):
            yield self.create_picture(match.group(1))

    def get_preview_data(self, id):
        url = "https://alpha.wallhaven.cc/wallpapers/thumb/small/th-{}.jpg".format(id)
        return self.session.get(url).content

    def get_picture_info(self, id):
        page_url = 'https://alpha.wallhaven.cc/wallpaper'
        url = '{}/{}'.format(page_url, id)
        rsp = self.session.get(url)
        data = rsp.text
        patten = re.compile(r'<img id="wallpaper" src="(.*?)" alt="(.*?)"')
        try:
            origin_url = 'https:' + patten.search(data).group(1)
            alt = patten.search(data).group(2)
        except AttributeError as e:
            print('error when get picture info of id:{}, respond code {}, reason {}'.format(
                id, rsp.status_code, rsp.reason))
        return origin_url, alt

    def get_origin_data(self, id_or_pic):
        if isinstance(id_or_pic, WallHavenPicture):
            origin_url = id_or_pic.origin_url
        else:
            origin_url, alt = self.get_picture_info(id_or_pic)
        rsp = self.session.get(origin_url, stream=True)
        return rsp.iter_content(1024 * 128), int(rsp.headers['Content-Length'])

    def create_picture(self, id):
        origin_url, alt = self.get_picture_info(id)
        return WallHavenPicture(id, origin_url, alt)

    def download_picture(self, id_or_pic, path):
        if isinstance(id_or_pic, WallHavenPicture):
            origin_url = id_or_pic.origin_url
        else:
            origin_url, alt = self.get_picture_info(id_or_pic)
        if path.endswith('/'):
            path = path[:-2]
        file_name = origin_url[origin_url.rfind('/'):]
        path = path + file_name
        size = 0
        with open(path, 'wb') as f:
            block_iter, total_size = self.get_origin_data(id_or_pic)
            for block in block_iter:
                f.write(block)
                size += len(block)
                print("Download Picture {} {:.2f}%".format(path, 100.0 * size / total_size))


class Category(Enum):
    MAIN = 'main'
    LATEST = 'latest'
    TOPLIST = 'toplist'
    RANDOM = 'random'


class Picture:
    __metaclass__ = abc.ABCMeta

    def __init__(self, id):
        self.id = str(id)

    @abc.abstractmethod
    def download_picture(self, path):
        pass

    @abc.abstractmethod
    def get_preview_url(self):
        pass

    @abc.abstractmethod
    def get_origin_url(self):
        pass

    @abc.abstractmethod
    def get_preview_data(self):
        pass

    @abc.abstractmethod
    def get_origin_data(self):
        pass


class WallHavenPicture():
    '''
    wallhaven壁纸类
    '''

    def __init__(self, id, origin_url=None, alt=None):
        self.id = id
        self.__pre_url = 'https://alpha.wallhaven.cc/wallpaper'
        self.url = '{}/{}'.format(self.__pre_url, id)
        self.origin_url = origin_url
        self.alt = alt

    def get_resolution(self):
        if not self.alt:
            return None
        resolution = self.alt.split()[1]
        width = int(resolution.split('x')[0])
        height = int(resolution.split('x')[1])
        return width, height

    resolution = property(get_resolution)


class PictureTest(unittest.TestCase):

    def setUp(self):
        self.wallhaven = WallHaven()

    def test_pincture_create(self):
        pic = self.wallhaven.create_picture(632744)
        self.assertEqual(pic.url, 'https://alpha.wallhaven.cc/wallpaper/632744')
        self.assertEqual(pic.origin_url, 'https://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-632744.jpg')
        self.assertEqual(pic.alt, 'General 4096x2304 landscape horizon clouds sunrise mountain top Switzerland Saentis Mountain mountains sun rays sky HDR')
        self.assertTupleEqual(pic.resolution, (4096, 2304))

    def test_picture_download(self):
        print('test picture_download')
        pic = self.wallhaven.create_picture(632744)
        self.wallhaven.download_picture(pic, "/home/moonwalker/Picture")

    def test_get_main_web_picture(self):
        for p in self.wallhaven.get_main_web_pictures():
            print(p.alt)

    def test_get_latest_web_picture(self):
        for p in self.wallhaven.get_category_picture(Category.LATEST):
            print(p.alt)


if __name__ == '__main__':
    unittest.main()
