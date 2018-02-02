import hashlib
import time
from functools import partial
from os.path import join
from time import sleep
from urllib import request

import pyproj
from shapely.geometry import Polygon, Point
from shapely.ops import transform
import vk
from vk.exceptions import VkAPIError

import classify_image
from common import *

TIME_TO_SLEEP = 0.35
TEMP_DIR = ".tmp"
CACHE_DIR = ".cache"
project = partial(
    pyproj.transform,
    pyproj.Proj(init='epsg:4326'),
    pyproj.Proj('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs'))

class LocalDataSupplier:
    def __init__(self, on_found_latlon):
        self.on_found_latlon = on_found_latlon
        make_sure_path_exists(OUTPUT_DIR)
        self.latlonsfile = join(OUTPUT_DIR, "latlons.txt")


    def set_roi(self, roi):
        print("new roi = " + str(roi))
        self.roi = transform(project, Polygon(roi))
        print(self.roi)

    def retrieve_local_data(self):
        with open(self.latlonsfile, "r") as f:
            for l in f:
                try:
                    lat, lon, url = l.split(' ')
                    point = transform(project, Point(float(lon), float(lat)))
                    if not self.roi.contains(point):
                        continue
                    self.on_found_latlon(lat, lon, url)
                except:
                    pass


class VkScrapper:
    def __init__(self, vkapi, on_found_latlon):
        self.vkapi = vkapi
        self.keywords = {'mushroom', 'bolete', 'fungus'}
        self.group_keywords = {'грибы', 'грибники', 'грибочки'}
        self.user_albums_keywords = {'грибы', 'грибники', 'грибочки', 'дача', 'лес', 'тихая охота', 'mushrooms'}
        #currently unused
        self.city_by_id = {}
        self.countries = {}
        self.roi = None
        self.processed_file = join(CACHE_DIR, "processed.txt")
        make_sure_path_exists(TEMP_DIR)
        make_sure_path_exists(CACHE_DIR)
        self.latlonsfile = join(OUTPUT_DIR, "latlons.txt")
        countries = self._api_call(self.vkapi.database.getCountries, need_all=1)
        self.on_found_latlon = on_found_latlon
        self.tagger = classify_image.ImageTagger('.models')

        if os.path.exists(self.processed_file):
            with open(self.processed_file, "r") as f:
                self.processed = set([s.strip() for s in f])
        else:
            self.processed = set()

        if not countries:
            print("Couldn't retrieve countries")
            return
        for c in countries:
            self.countries[c['cid']] = c['title']
        make_sure_path_exists(OUTPUT_DIR)

    def set_roi(self, roi):
        print("new roi = " + str(roi))
        self.roi = transform(project, Polygon(roi))
        print(self.roi)

    def get_locations_by_user_or_group(self, owner):
        albums = self._api_call(self.vkapi.photos.getAlbums, owner_id=owner)
        if not albums:
            return



        for album in albums:
            if owner > 0: # is owner is normal user, don't process album unless it contains keyword
                for kw in self.user_albums_keywords:
                    if kw in album['title']:
                        break
                else:
                    continue
            photos = self._api_call(self.vkapi.photos.get, owner_id=owner, album_id=album['aid'], extended=True)
            if not photos:
                continue

            try:
                print("Photos in album {}".format(album['title']))
            except UnicodeEncodeError as e:
                print("error printing album title")

            for p in photos:
                self.__process_photo(p)
            time.sleep(TIME_TO_SLEEP)

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
        #self.get_locations_by_groups_members()


    def get_locations_by_groups(self):
        self._process_groups(lambda group: self.get_locations_by_user_or_group(-group.get('gid')))

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
            result = self._api_call(self.vkapi.groups.getMembers, group_id=gid, offset=offset, count=members_per_request)
            offset += members_per_request

            for owner in result['users']:
                self.get_locations_by_user_or_group(owner)
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
