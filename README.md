# GeoMushroom

### What is it?
This is just a mushroom heatmap built on top of vk geotagged photos. The repository contains both client and backend code. 

Client code is located under /docs directory, so that the frontend from the web can access it: [geomushroom](https://aspirisha.github.io/GeoMushroom/geomushroom.html).

Backend consists of scrapper, which retrives data from vk and should be run beforehand, and serving application, which just gives clients pieces of information retrieved by scrapper beforehand.


### How to use scrapper
* Create virtualenv with python3
* Install requirements: `pip install -r requirements.txt`
* Install redis for caching and run it
* Follow the link from get_token.txt and copy result token from the address bar.
* Copy file config_template.yaml and paste obtained token under `vk_token` key
* Prepare data sinks:
  - If you want to store results in firebase, create firebase db.
  - For postgres sink, to initialize database you can use `initdb.sql` from the root directory: `psql -a -f initdb.sql`
    * Note however, that postgres sink is not yet ready to be used on client side :) 
    * Install corresponding postgis extension (like postgresql-15-postgis)
* Setup data sinks configuration in previously copied `config.yaml`
* Perform data retrivement from vk by calling `./scrapper.py`

### How to use client
* To build client js code
  - Install npm and necessary packages
  - Run `npx vite build` from `src/client` directory. The result artifacts will be output under `docs/` directory.
* If you want to use own server, you need to change ip hardcoded in docs/geomushroom.js to the one belonging to your server. 
* Open docs/geomushroom.html. This is the user interface to control scrapper. 

P.S. detected mushrooms can be poisonous. Use at your own risk.

<center>Result example</center>

![Alt text](resources/sample.png?raw=true "Title")

### References
Scrapper image classification is backed by [tfhub models](https://www.tensorflow.org/hub)
