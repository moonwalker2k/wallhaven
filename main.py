from WallHaven import *

picture_path = '/home/moonwalker/Picture/WallHaven'

if __name__ == '__main__':
    wh = WallHaven()
    for pic in wh.get_category_picture(Category.TOPLIST):
        if pic.resolution[0] >= 2560 and pic.resolution[1] >= 1440:
            print(pic.alt)
            pic.download_picture(picture_path)