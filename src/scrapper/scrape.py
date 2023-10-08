#!/usr/bin/env python

import hashlib
import json
import time
import logging
import yaml
import os
import sys

# temporary solution until proper deployment is done
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from os.path import join, exists
from urllib import request
from scrapper.firebase_sink import FirebaseSink
from scrapper.postgres_sink import PostgresSink
from scrapper.textfile_sink import TextfileSink

import vk
from vk.exceptions import VkAPIError

from scrapper.classify_image import ImageTagger
from scrapper.util import make_sure_path_exists


TIME_TO_SLEEP = 0.35
TEMP_DIR = ".tmp"
CACHE_DIR = ".cache"
VERSION='5.154'

logger = logging.getLogger('scrapper')



class VkScrapper:
    def __init__(self, vkapi, data_sinks, access_token, classifier_config):
        self.vkapi = vkapi
        self.keywords = {'mushroom', 'bolete', 'fungus'}
        self.group_keywords = {'грибы', 'грибники', 'грибочки', 'лес', 'грибов'}
        self.user_albums_keywords = {'грибы', 'грибники', 'грибочки', 'дача', 'лес', 'тихая охота', 'mushrooms'}
        self.processed_file = join(CACHE_DIR, "processed.txt")
        self._access_token = access_token
        make_sure_path_exists(TEMP_DIR)
        make_sure_path_exists(CACHE_DIR)
        self.tagger = ImageTagger('.models', classifier_config)

        self.processed_users = set()
        if exists(self.processed_file):
            with open(self.processed_file, "r") as f:
                self.processed = set([s.strip() for s in f])
        else:
            self.processed = set()

        self.data_sinks = data_sinks

    def get_locations_by_user_or_group(self, owner, photo_processor):
        albums = self._api_call(self.vkapi.photos.getAlbums, owner_id=owner)
        if not albums:
            return

        logger.info('Retrieved %i albums', albums['count'])
        for album in albums['items']:
            photos = self._api_call(self.vkapi.photos.get, owner_id=owner, album_id=album['id'], extended=True)
            if not photos:
                continue

            try:
                logger.info("Found %i photos in album %s", photos['count'], album['title'])
            except UnicodeEncodeError as e:
                logger.error("error printing album title")

            for p in photos['items']:
                photo_processor(p)
            time.sleep(TIME_TO_SLEEP)

    def __process_group_photo(self, p):
        try:
            is_mushroom_photo = self.__process_photo(p)

            if not is_mushroom_photo:
                return
            if p['user_id'] > 0 and p['user_id'] not in self.processed_users:  # user uploaded this photo, probably she has many mushroom photos
                self.processed_users.add(p['user_id'])
                logger.info("processing user %s", p['user_id'])
                self.get_locations_by_user_or_group(p['user_id'], self.__process_photo)
        except Exception as e:
            logger.error(e)

    def __process_photo(self, p):
        if not ('long' in p and 'lat' in p):
            return False

        logger.info('Found photo with geo info')

        def dist(img):
            optimal_width = 512
            optimal_height = 512
            return (img['height'] - optimal_height) ** 2 + (img['width'] - optimal_width) ** 2

        p['sizes'].sort(key=dist)

        url = p['sizes'][0]['url']
        tags = self.classify_photo(url)

        if not tags:
            return False

        if not self.keywords.isdisjoint(tags):
            logger.info("photo with address %s seems to contain mushrooms and has geotag:"
                        " lat = %f, lon = %f", url, p['lat'], p['long'])

            for sink in self.data_sinks:
                sink.on_mushroom(p['lat'], p['long'], url)
            return True
        else:
            logger.info("photo with address %s has no mushrooms and has geotag: lat = %f, lon = %f",
                        url, p['lat'], p['long'])
        return False

    def get_all_locations(self):
        self.get_locations_by_groups()
        # self.get_locations_by_groups_members()

    def get_locations_by_groups(self):
        self._process_groups(lambda group: self.get_locations_by_user_or_group(
            -group.get('id'), self.__process_group_photo))

    def _process_groups(self, group_processor):
        groups_count_per_kw = 1000
        for kw in self.group_keywords:
            groups = self._api_call(self.vkapi.groups.search, q=kw, count=groups_count_per_kw, lang='ru', 
                                    access_token=self._access_token)
            if not groups:
                print("Failed to retrieve groups for keyword {}".format(kw))
                return
            logger.info(f'Extracted {groups["count"]} groups for keyword {kw}')
            for group in groups['items'][1:]:
                try:
                    logger.info("scanning group %s (id %i)", group['name'], group['id'])
                except UnicodeEncodeError as e:
                    logger.error("error printing group title")

                try:
                    group_processor(group)
                except Exception as e:
                    logger.error("Got error: ", e)

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
            logger.info("Processed {} users".format(len(result['users'])))

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
                return method(*args, v=VERSION, **kwargs)
            except VkAPIError as e:
                if e.code == 6:  # just too many requests
                    time.sleep(TIME_TO_SLEEP)
                else:
                    print("error {}".format(e.code))
                    return None
        return None


def build_sinks(config):
    SinkClassByName = {
        'firebase': FirebaseSink,
        'postgres': PostgresSink,
        'text': TextfileSink
    }
    sinks = [SinkClassByName[sink_cfg['type']](sink_cfg['config'])
             for sink_cfg in config['sinks']]
    logger.info(f'Created {len(sinks)} sinks')
    return sinks


if __name__ == "__main__":
    logging.basicConfig(encoding='utf-8', level=logging.INFO, 
                        format='[%(name)s] %(levelname)s:%(message)s')

    logger.setLevel(logging.DEBUG)

    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    if "vk_token" not in config:
        print("VK token not found!")
        exit(0)

    logger.debug('Creating vk api...')
    vkapi = vk.API(access_token=config["vk_token"])
    logger.debug('vk api created...')

    sinks = build_sinks(config)
    scrapper = VkScrapper(vkapi, sinks, config["vk_token"], config['classifier'])
    scrapper.get_all_locations()
