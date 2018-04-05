import re
import abc
import unittest
import logging
from enum import Enum
from urllib import request


class WallHaven:
    '''
    WallHaven.cc
    用于爬取wallhaven壁纸
    '''

    def __init__(self):
        self.main_web = 'https://alpha.wallhaven.cc'
        self.categories = { 'latest' : '/latest',
                            'toplist' : '/toplist',
                            'random' : '/random'
                            }
        self.opener = request.build_opener()
        self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
                                                 ' (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36')]

    def get_main_web_pictures(self):
        rsp = self.opener.open(self.main_web)
        data = rsp.read().decode('utf-8')
        rsp.close()
        patten = re.compile(r'<img src="//.*?th-(\d*?)\.\S{3}"')
        for match in patten.finditer(data):
            yield WallHavenPicture(match.group(1))

    def get_category_picture(self, category, page=1):
        assert isinstance(category, Category)
        url = self.main_web + self.categories[category.value] + '?' + str(page)
        rsp = self.opener.open(url)
        data = rsp.read().decode('utf-8')
        rsp.close()
        patten = re.compile(r'data-wallpaper-id="(\d*?)"')
        for match in patten.finditer(data):
            yield WallHavenPicture(match.group(1))


class Category(Enum):
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


class WallHavenPicture(Picture):
    '''
    wallhaven壁纸类
    '''
    def __init__(self, id):
        super().__init__(id)
        self.log = logging.getLogger('PictureClass')
        self.log.setLevel(logging.DEBUG)
        self.__pre_url = 'https://alpha.wallhaven.cc/wallpaper'
        self.url = '{}/{}'.format(self.__pre_url, id)
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
                                      ' (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}
        req = request.Request(self.url, headers=self.headers)
        rsp = request.urlopen(req)
        if rsp.status != 200:
            raise Exception('fail to open {}, request return {}'.format(self.url, rsp.status))
        data = rsp.read().decode('utf-8')
        patten = re.compile(r'<img id="wallpaper" src="(.*?)" alt="(.*?)"')
        self.origin_url = 'https:' + patten.search(data).group(1)
        self.alt = patten.search(data).group(2)

    def download_picture(self, path):
        if path.endswith('/'):
            path = path[:-2]
        file_name = path + self.origin_url[self.origin_url.rfind('/'):]
        with open(file_name, 'wb') as f:
            for block in self.get_origin_data():
                f.write(block)

    def get_preview_url(self):
        return "https://alpha.wallhaven.cc/wallpapers/thumb/small/th-{}.jpg".format(self.id)

    def get_preview_data(self):
        url = self.get_preview_url()
        req = request.Request(url, headers=self.headers)
        rsp = request.urlopen(req)
        return rsp.read()

    def get_origin_url(self):
        return self.origin_url

    def get_origin_data(self):
        file_name = self.origin_url[self.origin_url.rfind('/'):]
        req = request.Request(self.origin_url, headers=self.headers)
        rsp = request.urlopen(req)

        if rsp.code == 200:
            size = rsp.length
            size_count = 0
            while True:
                block = rsp.read(1024 * 1024)
                block_size = len(block)
                if not block:
                    break
                yield block
                size_count += block_size
                self.log.debug('Downloading {} {:.2f}%'.format(file_name, 100.0 * size_count / size))

    def get_resolution(self):
        resolution = self.alt.split()[1]
        width = int(resolution.split('x')[0])
        height = int(resolution.split('x')[1])
        return width, height

    resolution = property(get_resolution)


class PictureTest(unittest.TestCase):

    def setUp(self):
        self.wallhaven = WallHaven()

    def test_pincture_create(self):
        pic = WallHavenPicture(632744)
        self.assertEqual(pic.url, 'https://alpha.wallhaven.cc/wallpaper/632744')
        self.assertEqual(pic.origin_url, 'https://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-632744.jpg')
        self.assertEqual(pic.alt, 'General 4096x2304 landscape horizon clouds sunrise mountain top Switzerland Saentis Mountain mountains sun rays sky HDR')
        self.assertTupleEqual(pic.resolution, (4096, 2304))

    def test_picture_download(self):
        print('test picture_download')
        pic = WallHavenPicture(632744)
        pic.download_picture("/home/moonwalker/Picture")

    def test_get_main_web_picture(self):
        for p in self.wallhaven.get_main_web_pictures():
            print(p.alt)

    def test_get_latest_web_picture(self):
        for p in self.wallhaven.get_category_picture(Category.LATEST):
            print(p.alt)


if __name__ == '__main__':
    unittest.main()