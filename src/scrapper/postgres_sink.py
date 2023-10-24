import logging
import psycopg2
from geopy.geocoders import Nominatim

from scrapper.datasink import DataSink


class PostgresSink(DataSink):
    def __init__(self, config):
        super().__init__(config['name'])
        self.conn = psycopg2.connect(
            database=config['database'],
            host=config['host'],
            user=config['user'],
            password=config['password'],
            port=config['port'])
        self._logger.info('Created PostgresSink')
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
        self.geolocator = Nominatim(user_agent="geoapiExercises")

    def on_mushroom(self, lat, lon, url):
        try:
            location = self.geolocator.reverse(f"{lat},{lon}")
            address = location.raw['address']
            country = address['country']
        except Exception as e:
            self._logger.error(f'Skipping country identififcation: {str(e)}')
            country = None

        try:
            self.cursor.execute(
                "INSERT INTO Mushrooms (longitude, latitude, country, URL, time, location)"
                f"VALUES ({lon}, {lat}, '{country}', '{url}', now(), "
                f"ST_GeomFromText('POINT({lon} {lat})', 4326));")
        except psycopg2.errors.UniqueViolation:
            self._logger.info(f'Url for lat={lat} lon={lon} was already processed')
