import importlib.resources
import json

import logging
import logging.config

# "format": "%(asctime)s | %(levelname)s | %(process)d#%(thread)d | %(module)s.%(funcName)s: %(message)s"}},
_conf = importlib.resources.files("synthmap.log").joinpath("config.json").read_text()
BASE_CONF = json.loads(_conf)


def getLogger(name, conf=BASE_CONF):
    logging.config.dictConfig(conf)
    return logging.getLogger(name)
