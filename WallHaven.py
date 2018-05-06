import re
import unittest
import os
import io
from concurrent import futures
import threading
import requests
from enum import Enum
from collections import namedtuple

WallHavenPicture = namedtuple('WallHavenPicture', 'id resolution alt origin_url')


class WallHaven:
    '''
    WallHaven.cc
    用于爬取wallhaven壁纸
    '''

    def __init__(self):
        self.categories = {'latest': '/latest',
                           'toplist': '/toplist',
                           'random': '/random'}
        self._session = requests.session()
        self._session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
                                                   ' (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'})
        self._download_max_thread = 4
        self._download_part_size = 512 * 1024
        self.index_url = 'https://alpha.wallhaven.cc'

    def __del__(self):
        self._session.close()

    def get_main_web_pictures(self):
        data = self._session.get(self.index_url).text
        patten = re.compile(r'<img src="//.*?th-(\d*?)\.\S{3}"')
        for match in patten.finditer(data):
            yield match.group(1)

    def get_category_picture(self, category, page=1):
        assert isinstance(category, Category)
        url = self.index_url + self.categories[category.value] + '?page=' + str(page)
        data = self._session.get(url).text
        patten = re.compile(r'data-wallpaper-id="(\d*?)"')
        for match in patten.finditer(data):
            yield match.group(1)

    def get_preview_data(self, id):
        url = "https://alpha.wallhaven.cc/wallpapers/thumb/small/th-{}.jpg".format(id)
        return self._session.get(url).content

    def get_picture_info(self, id):
        page_url = 'https://alpha.wallhaven.cc/wallpaper'
        url = '{}/{}'.format(page_url, id)
        rsp = self._session.get(url)
        data = rsp.text
        patten = re.compile(r'<img id="wallpaper" src="(.*?)" alt="(.*?)"')
        try:
            origin_url = 'https:' + patten.search(data).group(1)
            alt = patten.search(data).group(2)
        except AttributeError as e:
            print('error when get picture info of id:{}, respond code {}, reason {}'.format(
                id, rsp.status_code, rsp.reason))
        else:
            return origin_url, alt

    def get_origin_data(self, id_or_pic):
        if isinstance(id_or_pic, WallHavenPicture):
            origin_url = id_or_pic.origin_url
        else:
            origin_url, alt = self.get_picture_info(id_or_pic)
        rsp = self._session.get(origin_url, stream=True)
        return rsp.iter_content(1024 * 256), int(rsp.headers['Content-Length'])

    def create_picture(self, id):
        origin_url, alt = self.get_picture_info(id)
        resolution = tuple([int(s) for s in alt.split()[1].split('x')])
        return WallHavenPicture(id, resolution, alt, origin_url)

    def download_picture(self, id_or_pic, path):
        if isinstance(id_or_pic, WallHavenPicture):
            origin_url = id_or_pic.origin_url
        else:
            origin_url, alt = self.get_picture_info(id_or_pic)
        file_name = origin_url[origin_url.rfind('/') + 1:]
        path = os.path.join(path, file_name)
        size = 0
        with open(path, 'wb') as f:
            block_iter, total_size = self.get_origin_data(id_or_pic)
            for block in block_iter:
                f.write(block)
                size += len(block)
                print("Download Picture {} {:.2f}%".format(path, 100.0 * size / total_size))

    def get_picture_data(self, id_or_pic):
        if isinstance(id_or_pic, WallHavenPicture):
            origin_url = id_or_pic.origin_url
        else:
            origin_url, alt = self.get_picture_info(id_or_pic)
        rsp = self._session.head(origin_url)
        size = int(rsp.headers['Content-Length'])
        buff = io.BufferedRandom(io.BytesIO(bytearray(size)))
        # 每块分配256KB
        fus = []
        block_count = int(size / self._download_part_size)
        last_size = size % self._download_part_size
        if last_size > 0:
            block_count += 1
        with futures.ThreadPoolExecutor(self._download_max_thread) as executor:
            size_count = 0
            for i in range(block_count):
                fus.append(executor.submit(self._download_part, origin_url, size_count, self._download_part_size))
                size_count += self._download_part_size
            fus.append(executor.submit(self._download_part, origin_url, size_count, last_size))
        for future in futures.as_completed(fus):
            data, start, size = future.result()
            # print('finish block start at %d, size %d' % (start, size))
            buff.seek(start)
            buff.write(data)
        buff.seek(0)
        print('done')
        return buff

    def get_picture_data_block(self, id_or_pic):
        if isinstance(id_or_pic, WallHavenPicture):
            origin_url = id_or_pic.origin_url
        else:
            origin_url, alt = self.get_picture_info(id_or_pic)
        rsp = self._session.get(origin_url)
        size = int(rsp.headers['Content-Length'])
        buff = io.BytesIO(bytearray(size))
        data = self._session.get(origin_url).content
        buff.write(data)
        print('done')
        return buff

    def _download_part(self, url, start: int, size: int):
        headers = {'Range': 'bytes=%d-%d' % (start, start + size)}
        data = self._session.get(url, headers=headers).content
        # print('start from %d write %d byte' % (start, size))
        return data, start, size


class Category(Enum):
    MAIN = 'main'
    LATEST = 'latest'
    TOPLIST = 'toplist'
    RANDOM = 'random'


class PictureTest(unittest.TestCase):

    def setUp(self):
        self.wallhaven = WallHaven()

    def test_pincture_create(self):
        pic = self.wallhaven.create_picture(632744)
        self.assertEqual(pic.origin_url, 'https://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-632744.jpg')
        self.assertEqual(pic.alt, 'General 4096x2304 landscape horizon clouds sunrise mountain top Switzerland Saentis Mountain mountains sun rays sky HDR')
        self.assertTupleEqual(pic.resolution, (4096, 2304))
        self.assertEqual('X'.join([str(s) for s in pic.resolution]), '4096X2304')

    def test_picture_download(self):
        print('test picture_download')
        pic = self.wallhaven.create_picture(632744)
        self.wallhaven.download_picture(pic, "/home/moonwalker/Picture")

    def test_get_main_web_picture(self):
        for p in self.wallhaven.get_main_web_pictures():
            print(p)

    def test_get_latest_web_picture(self):
        for p in self.wallhaven.get_category_picture(Category.LATEST):
            print(p)

    def test_get_picture_data(self):
        data = self.wallhaven.get_picture_data(632744)
        with open('632744.jpg', 'wb') as f:
            f.write(data.read())

    def test_get_picture_data_block(self):
        data = self.wallhaven.get_picture_data_block(632744)
        with open('632744.jpg', 'wb') as f:
            f.write(data.read())

    def test_get_origin_data(self):
        chunk_iter, size = self.wallhaven.get_origin_data(632744)
        arr = io.BufferedRandom(io.BytesIO(bytearray(size)))
        for block in chunk_iter:
            arr.write(block)
        arr.seek(0)
        with open('632744.jpg', 'wb') as f:
            f.write(arr.read())


if __name__ == '__main__':
    unittest.main()
