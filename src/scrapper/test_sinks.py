import yaml
from .scrapper import build_sinks


URL = 'https://sun9-71.userapi.com/impf/c850020/v850020215/84ddd/igvqbzztxqc.jpg?size=453x604&quality=96&sign=85858927bf2618c50a8c3f8b2a53403f&c_uniq_tag=Ybxasv_sK23a4sVlCqzgrs852ek5fDsNwlAnoX3PsGk&type=album'
lat = 59.442780
lon = 29.983130


def test_sinks():
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    sinks = build_sinks(config)
    for sink in sinks:
        sink.on_mushroom(lat, lon, URL)
