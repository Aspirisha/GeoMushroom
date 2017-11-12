import json
import time
import vk
from vk.exceptions import VkAPIError
from os.path import dirname, join
import os
import errno
from urllib import request
import classify_image

root_dir = dirname(__file__)
data_dir = join(root_dir, "..", "data")
TIME_TO_SLEEP = 0.35
TEMP_DIR = ".tmp"


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


class VkScrapper:
    def __init__(self, vkapi):
        self.vkapi = vkapi
        self.keywords = {'mushroom', 'bolete', 'fungus'}

    def get_photos(self, user):
        albums_count = self.vkapi.photos.getAlbumsCount(user_id=user)
        print("User has {} albums".format(albums_count))
        albums = self.vkapi.photos.getAlbums(owner_id=user)
        for album in albums:
            try:
                photos = self.vkapi.photos.get(owner_id=user, album_id=album['aid'], extended=True)
            except VkAPIError as e:
                print("error {}".format(e.code))
                time.sleep(0.333)
                photos = self.vkapi.photos.get(owner_id=user, album_id=album['aid'], extended=True)
            print("Photos in album {}".format(album['title']))

            for p in photos:
                if not ('long' in p and 'lat' in p):
                    continue

                tags = self.classify_photo(self.tagger, p['src_xbig'])
                if not self.keywords.isdisjoint(tags):
                    print("photo with address {} seems to contain mushrooms and has geotag: lat = {}, lon = {}".format(p['src_xbig'], p['lat'],
                                                                                        p['long']))
                    print(tags)
                else:
                    print(
                        "photo with address {} has no mushrooms and has geotag: lat = {}, lon = {}".format(
                            p['src_xbig'], p['lat'],
                            p['long']))
            time.sleep(0.333)

    def classify_photo(self, tagger, url):
        make_sure_path_exists(TEMP_DIR)
        image_path = join(TEMP_DIR, 'img.jpg')
        f = open(image_path, 'wb')
        f.write(request.urlopen(url).read())
        f.close()

        return tagger.run_inference_on_image(image_path)

    def __enter__(self):
        self.tagger = classify_image.ImageTagger('.models')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tagger.close()


def main():
    APP_ID = '6256422'
    with open(join(root_dir, 'tokens.txt')) as f:
        data = json.load(f)
    tokens = data.get('vktokens')

    if len(tokens) == 0:
        print("No tokens found!")
        exit(0)

    session = vk.Session(access_token=tokens[0])
    vkapi = vk.API(session)

    with VkScrapper(vkapi) as scrapper:
        user = 9941496
        scrapper.get_photos(user)


if __name__ == '__main__':
    main()
