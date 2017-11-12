import json
import time
import datetime
import dateutil
import hashlib
import vk
from vk.exceptions import VkAPIError
from os.path import dirname, join
import sys
import os

root_dir = dirname(__file__)
data_dir = join(root_dir, "..", "data")
TIME_TO_SLEEP = 0.35


class VkScrapper:
    def __init__(self, vkapi):
        self.vkapi = vkapi
        pass

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
                print("photo with address {} has geotag: lat = {}, lon = {}".format(p['src_xbig'], p['lat'], p['long']))
            time.sleep(0.333)

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

    scrapper = VkScrapper(vkapi)
    user = 9941496
    scrapper.get_photos(user)

if __name__ == '__main__':
    main()
