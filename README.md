# GeoMushroom

### WTF is it?
This is (or will be once) just a mushroom heatmap built on top of vk geotagged photos.

### Prerequisites
You need to have: 
* access to the internet
* python 3.x 

Following python packages:
* tensorflow
* vk
* numpy

### How To Use
1. Copy text from get_token.txt into your browser address bar.
2. Press enter. Vk token will be generated and displayed in the address bar. Copy it to clipboard.
3. Paste token into file tokens.txt
4. Run from command line: `python main.py`. This will start vk groups traversal aimed to find geotagged photos of mushrooms.
5. When you are bored, press ctrl+c. Anyway, after previous command finished execution, you can watch the results by calling `python visualizer.py`. This will generate html file **output/mushrooms_heatmap.html**  with google map mushrooms heatmap based on retrieved geotags. 
6. Go and gather mushrooms.

P.S. detected mushrooms can be poisonous. Use at your own risk.

### References
This project is backed by inception model, borrowed from [here](http://download.tensorflow.org/models/image/imagenet/inception-2015-12-05.tgz)

Image classification code is borrowed from [here](https://tensorflow.org/tutorials/image_recognition/)