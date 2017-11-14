import time
from os.path import join
from urllib import request

import vk
from vk.exceptions import VkAPIError

import classify_image
from common import *

TIME_TO_SLEEP = 0.35
TEMP_DIR = ".tmp"


class VkScrapper:
    def __init__(self, vkapi, minp, maxp):
        self.vkapi = vkapi
        self.keywords = {'mushroom', 'bolete', 'fungus'}

        #currently unused
        self.minp = minp
        self.maxp = maxp
        self.city_by_id = {}
        self.countries = {}
        countries = self._api_call(self.vkapi.database.getCountries, need_all=1)

        if not countries:
            print("Couldn't retrieve countries")
            return
        for c in countries:
            self.countries[c['cid']] = c['title']

        make_sure_path_exists(OUTPUT_DIR)

    def get_locations_by_user_or_group(self, owner):
        albums = self._api_call(self.vkapi.photos.getAlbums, owner_id=owner)
        if not albums:
            return

        for album in albums:
            photos = self._api_call(self.vkapi.photos.get, owner_id=owner, album_id=album['aid'], extended=True)
            if not photos:
                continue
            print("Photos in album {}".format(album['title']))

            for p in photos:
                if not ('long' in p and 'lat' in p): continue

                lat, lon = p['lat'], p['long']

                if lat < self.minp[0] or lat > self.maxp[0] \
                        or lon < self.minp[1] or lon > self.maxp[1]: continue
                tags = self.classify_photo(p['src_xbig'])
                if not self.keywords.isdisjoint(tags):
                    print("photo with address {} seems to contain mushrooms and has geotag:"
                          " lat = {}, lon = {}".format(p['src_xbig'], lat, lon))
                    print(tags)
                else:
                    print(
                        "photo with address {} has no mushrooms and has geotag: lat = {}, lon = {}".format(
                            p['src_xbig'], p['lat'],
                            p['long']))
                    with open(join(OUTPUT_DIR, "latlons.txt"), "a") as f:
                        f.write("{} {} {}\n".format(lat, lon, p['src_xbig']))
                time.sleep(TIME_TO_SLEEP)


    def get_locations_by_groups(self, keywords):
        groups_count_per_kw = 1000

        for kw in keywords:
            groups = self._api_call(self.vkapi.groups.search, q=kw, count=groups_count_per_kw, lang='ru')
            if not groups:
                print("Failed to retrieve groups for keyword {}".format(kw))
                return
            for group in groups[1:]:
                print("scanning group {} (id {})".format(group.get('name'), group.get('gid')))
                self.get_locations_by_user_or_group(-group.get('gid'))

    def classify_photo(self, url):
        make_sure_path_exists(TEMP_DIR)
        image_path = join(TEMP_DIR, 'img.jpg')
        f = open(image_path, 'wb')
        f.write(request.urlopen(url).read())
        f.close()

        return self.tagger.run_inference_on_image(image_path)

    def __enter__(self):
        self.tagger = classify_image.ImageTagger('.models')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tagger.close()

    def _api_call(self, method, *args, **kwargs):
        for i in range(3):
            try:
                return method(*args, **kwargs)
            except VkAPIError as e:
                if e.code == 6:  # just too many requests
                    time.sleep(TIME_TO_SLEEP)
                else:
                    print("error {}".format(e.code))
                    return None
        return None


def main():
    with open('tokens.txt') as f:
        tokens = [l.strip() for l in f]

    if len(tokens) == 0:
        print("No tokens found!")
        exit(0)

    session = vk.Session(access_token=tokens[0])
    vkapi = vk.API(session)

    minp = (59.157162, 28.066060)
    maxp = (60.571626, 31.536363)
    keywords = ['грибы', 'грибники', 'грибочки']
    with VkScrapper(vkapi, minp, maxp) as scrapper:
        scrapper.get_locations_by_groups(keywords)


if __name__ == '__main__':
    main()
