from .datasink import DataSink



class TextfileSink(DataSink):
    def __init__(self, config):
        super().__init__(config['name'])
        self.filename = config['filename']

    def on_mushroom(self, lat, lon, url):
        res = "{} {} {}\n".format(lat, lon, url)
        with open(self.filename, "a") as f:
            f.write(res)
