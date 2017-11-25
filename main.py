import time
from os.path import join
from urllib import request
import argparse
from threading import Thread
from time import sleep
import sys
import hashlib
import pyproj
from shapely.geometry import Polygon, Point
from shapely.ops import transform
from functools import partial

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

def controller(scrapper):
    for line in sys.stdin:
        line = line.strip()
        print("Got command: " + line)
        commands = line.split(' ')
        key = commands[0].lower().strip()
        print(key)
        if key == 'start':
            print('starting...')
            coords = []
            try:
                for c in commands[1].split(';'):
                    (lat, lon) = c.split(',')
                    coords.append((float(lon), float(lat)))
            except Exception as e:
                pass
            scrapper.set_roi(coords)
            scrapper.start()
        elif key == 'roi':
            print(line)
            scrapper.set_roi()
        elif key == 'pause':
            print('pausing...')
            scrapper.pause()
        elif key == 'stop':
            print('stopping...')
            scrapper.stop()
            break
        sleep(1)

class VkScrapper:
    def __init__(self, vkapi):
        self.vkapi = vkapi
        self.keywords = {'mushroom', 'bolete', 'fungus'}
        self.running = False
        self.stopped = False
        #currently unused
        self.city_by_id = {}
        self.countries = {}
        self.processed_file = join(CACHE_DIR, "processed.txt")
        make_sure_path_exists(TEMP_DIR)
        make_sure_path_exists(CACHE_DIR)
        countries = self._api_call(self.vkapi.database.getCountries, need_all=1)

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
            photos = self._api_call(self.vkapi.photos.get, owner_id=owner, album_id=album['aid'], extended=True)
            if not photos:
                continue

            try:
                print("Photos in album {}".format(album['title']))
            except UnicodeEncodeError as e:
                print("error printing album title")

            for p in photos:
                while not self.running:
                    if self.stopped:
                        return
                    sleep(1)

                self.__process_photo(p)
            time.sleep(TIME_TO_SLEEP)

    def __process_photo(self, p):
        if not ('long' in p and 'lat' in p):
            return

        lat, lon = p['lat'], p['long']
        point = transform(project, Point(lon, lat))
        if not self.roi.contains(point):
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
            print(tags)
        else:
            print(
                "photo with address {} has no mushrooms and has geotag: lat = {}, lon = {}".format(
                    p[src_var], p['lat'],
                    p['long']))
            with open(join(OUTPUT_DIR, "latlons.txt"), "a") as f:
                f.write("{} {} {}\n".format(lat, lon, p[src_var]))


    def get_locations_by_groups(self, keywords):
        groups_count_per_kw = 1000

        for kw in keywords:
            groups = self._api_call(self.vkapi.groups.search, q=kw, count=groups_count_per_kw, lang='ru')
            if not groups:
                print("Failed to retrieve groups for keyword {}".format(kw))
                return
            for group in groups[1:]:
                try:
                    print("scanning group {} (id {})".format(group.get('name'), group.get('gid')))
                except UnicodeEncodeError as e:
                    print("error printing group title")
                self.get_locations_by_user_or_group(-group.get('gid'))
                if self.stopped:
                    return

    def classify_photo(self, url):
        h = hashlib.md5(str.encode(url)).hexdigest()
        if h in self.processed:
            return None

        image_path = join(TEMP_DIR, 'img.jpg')
        f = open(image_path, 'wb')
        f.write(request.urlopen(url).read())
        f.close()

        with open(self.processed_file, "a") as f:
            f.write("{}\n".format(h))
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

    def start(self):
        self.running = True

    def pause(self):
        self.running = False

    def stop(self):
        self.running = False
        self.stopped = True

def main(roifile=None):
    with open('tokens.txt') as f:
        tokens = [l.strip() for l in f]

    if len(tokens) == 0:
        print("No tokens found!")
        exit(0)

    session = vk.Session(access_token=tokens[0])
    vkapi = vk.API(session)

    keywords = ['грибы', 'грибники', 'грибочки']

    with VkScrapper(vkapi) as scrapper:
        thread = Thread(target=controller, args=(scrapper,))
        thread.start()
        scrapper.get_locations_by_groups(keywords)
    thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='vk mushroom info extractor backend')
    parser.add_argument('--roifile', metavar='filename', type=str,
                        help='path to file containing roi (lat, lon) array')
    parser.add_argument('--outputfile', metavar='filename', type=str,
                        help='path to file where to store extracted (lat, lon)s with mushrooms')
    args = parser.parse_args()
    main(args.roifile)
