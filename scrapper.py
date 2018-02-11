import hashlib
import time
from os.path import join, exists
from urllib import request

import vk
from shapely.geometry import Polygon, Point
from shapely.ops import transform
from vk.exceptions import VkAPIError

import classify_image
from common import make_sure_path_exists, OUTPUT_DIR, project

TIME_TO_SLEEP = 0.35
TEMP_DIR = ".tmp"
CACHE_DIR = ".cache"


class VkScrapper:
    def __init__(self, vkapi, on_found_latlon):
        self.vkapi = vkapi
        self.keywords = {'mushroom', 'bolete', 'fungus'}
        self.group_keywords = {'грибы', 'грибники', 'грибочки'}
        self.user_albums_keywords = {'грибы', 'грибники', 'грибочки', 'дача', 'лес', 'тихая охота', 'mushrooms'}
        self.processed_file = join(CACHE_DIR, "processed.txt")
        make_sure_path_exists(TEMP_DIR)
        make_sure_path_exists(CACHE_DIR)
        make_sure_path_exists(OUTPUT_DIR)
        self.latlonsfile = join(OUTPUT_DIR, "latlons.txt")
        self.on_found_latlon = on_found_latlon
        self.tagger = classify_image.ImageTagger('.models')

        self.processed_users = set()
        if exists(self.processed_file):
            with open(self.processed_file, "r") as f:
                self.processed = set([s.strip() for s in f])
        else:
            self.processed = set()

    def get_locations_by_user_or_group(self, owner, photo_processor):
        albums = self._api_call(self.vkapi.photos.getAlbums, owner_id=owner)
        if not albums:
            return

        for album in albums:
            photos = self._api_call(self.vkapi.photos.get, owner_id=owner, album_id=album['aid'], extended=True)
            if not photos:
                continue

            try:
                print("Photos in album {}".format(album['title']))
            except UnicodeEncodeError as e:
                print("error printing album title")

            for p in photos:
                photo_processor(p)
            time.sleep(TIME_TO_SLEEP)

    def __process_group_photo(self, p):
        try:
            self.__process_photo(p)
            if p['user_id'] > 0 and p['user_id'] not in self.processed_users:  # user uploaded this photo, probably she has many mushroom photos
                self.processed_users.add(p['user_id'])
                print("processing user ", p['user_id'])
                self.get_locations_by_user_or_group(p['user_id'], self.__process_photo)
        except Exception as e:
            print(e)

    def __process_photo(self, p):
        if not ('long' in p and 'lat' in p):
            return

        lat, lon = p['lat'], p['long']
        point = transform(project, Point(lon, lat))
        if (self.roi is not None) and (not self.roi.contains(point)):
            return

        src_variants = ['src_xbig', 'src_big', 'src_xxxbig', 'src']
        for src_var in src_variants:
            if src_var in p:
                tags = self.classify_photo(p[src_var])
                break
        else:
            return

        if not tags:
            return

        if not self.keywords.isdisjoint(tags):
            print("photo with address {} seems to contain mushrooms and has geotag:"
                  " lat = {}, lon = {}".format(p[src_var], lat, lon))

            res = "{} {} {}\n".format(lat, lon, p[src_var])
            with open(self.latlonsfile, "a") as f:
                f.write(res)
            self.on_found_latlon(lat, lon, p[src_var])
        else:
            print(
                "photo with address {} has no mushrooms and has geotag: lat = {}, lon = {}".format(
                    p[src_var], p['lat'],
                    p['long']))

    def get_all_locations(self):
        self.get_locations_by_groups()
        # self.get_locations_by_groups_members()

    def get_locations_by_groups(self):
        self._process_groups(lambda group: self.get_locations_by_user_or_group(
            -group.get('gid'), self.__process_group_photo))

    def _process_groups(self, group_processor):
        groups_count_per_kw = 1000
        for kw in self.group_keywords:
            groups = self._api_call(self.vkapi.groups.search, q=kw, count=groups_count_per_kw, lang='ru')
            if not groups:
                print("Failed to retrieve groups for keyword {}".format(kw))
                return
            for group in groups[1:]:
                try:
                    print("scanning group {} (id {})".format(group.get('name'), group.get('gid')))
                except UnicodeEncodeError as e:
                    print("error printing group title")

                try:
                    group_processor(group)
                except Exception as e:
                    pass

    def get_locations_by_groups_members(self):
        self._process_groups(lambda group: self.get_locations_by_users_in_group(group.get('gid')))

    def get_locations_by_users_in_group(self, gid):
        members_per_request = 1000
        offset = 0

        result = self._api_call(self.vkapi.groups.getMembers, group_id=gid, offset=offset, count=members_per_request)
        while result['count'] > offset:
            result = self._api_call(self.vkapi.groups.getMembers, group_id=gid, offset=offset,
                                    count=members_per_request, fields=["photo_max"])
            offset += members_per_request

            for owner in result['users']:
                self.get_locations_by_user_or_group(owner["id"], self.__process_photo)
            print("Processed {} users".format(len(result['users'])))

    def classify_photo(self, url):
        h = hashlib.md5(str.encode(url)).hexdigest()
        if h in self.processed:
            return None

        image_path = join(TEMP_DIR, 'img.jpg')
        with open(image_path, 'wb') as f:
            f.write(request.urlopen(url).read())

        with open(self.processed_file, "a") as f:
            f.write("{}\n".format(h))
        return self.tagger.run_inference_on_image(image_path)

    def close(self):
        self.tagger.close()

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


if __name__ == "__main__":
    with open('tokens.txt') as f:
        tokens = [l.strip() for l in f]

    if len(tokens) == 0:
        print("No tokens found!")
        exit(0)

    session = vk.Session(access_token=tokens[0])
    vkapi = vk.API(session)


    def on_found_latlon(self, lat, lon, url):
        print("Found mushrooms!")


    scrapper = VkScrapper(vkapi, on_found_latlon)
    scrapper.get_all_locations()
