import os
import errno

OUTPUT_DIR = "output"
APP_ID = '6256422'


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise