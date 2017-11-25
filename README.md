# GeoMushroom

### WTF is it?
This is (or will be once) just a mushroom heatmap built on top of vk geotagged photos.

### Prerequisites
You need to have: 
* access to the internet
* python 3.x 
* [twisted](https://twistedmatrix.com/trac/)

Following python packages:
* tensorflow
* vk
* numpy
* pyproj
* shapely

### How To Use
1. Copy text from get_token.txt into your browser address bar.
2. Press enter. Vk token will be generated and displayed in the address bar. Copy it to clipboard.
3. Paste token into file tokens.txt
4. Run from command line: `twistd -ny server.py`. This will start scrapper server.
5. Open geomushroom.html which lies in the root directory. This is the user interface to control scrapper. 
Controls are placed in the top right corner. You can set region of interest (ROI) by moving the red polygon on the map.
When scrapping, server will interactively populate map with gathered data by drawing heatmap and putting markers with detected photos 
at geolocations with mushrooms. 

Gathered data is cached so that you won't need to rerun scrapping every time.

P.S. detected mushrooms can be poisonous. Use at your own risk.

<center>Result example</center>

![Alt text](resources/sample.png?raw=true "Title")
### References
This project is backed by inception model, borrowed from [here](http://download.tensorflow.org/models/image/imagenet/inception-2015-12-05.tgz)

Image classification code is borrowed from [here](https://tensorflow.org/tutorials/image_recognition/)