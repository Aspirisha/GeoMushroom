import gmplot
from os.path import join
from common import *


def main():
    with open(join(OUTPUT_DIR, "latlons.txt"), "r") as f:
        lat_long = [(float(x[0]), float(x[1]))  for y in f for x in ((y.split(' ')), )]
    latitude, longitude = map(list, zip(*lat_long))

    gmap = gmplot.GoogleMapPlotter(latitude[0], longitude[0], 16)

    #gmap.plot(latitude, longitude, 'cornflowerblue', edge_width=1)
    gmap.heatmap(latitude, longitude, radius=30)

    gmap.draw(join(OUTPUT_DIR, "mushrooms_heatmap.html"))


if __name__ == '__main__':
    main()
