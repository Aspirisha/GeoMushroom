import hashlib
import firebase_admin
from firebase_admin import credentials, db

from scrapper.datasink import DataSink


class FirebaseSink(DataSink):
    def __init__(self, config):
        super().__init__(config['name'])
        self._logger.debug('FirebaseSink initialization started')
        cred = credentials.Certificate(config['firebase_credentials_path'])

        self._logger.debug('Loaded firebase credentials...')
        app = firebase_admin.initialize_app(
            cred, options={'databaseURL':'https://geomushroom-186520.firebaseio.com'})
        self._logger.debug('Created firebase app...')

    def on_mushroom(self, lat, lon, url):
        self._logger.debug('Processing mushroom in Firebase sink...')
        h = hashlib.md5(str.encode(url)).hexdigest()
        data = {"lat": lat, "lon": lon, "url": url}
        ref = db.reference(f"/mushrooms/{h}")
        ref.set(data)