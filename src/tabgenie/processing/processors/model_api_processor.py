#!/usr/bin/env python3
import logging
import json

from ..processing import Processor
from tinyhtml import h
import requests

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class ModelAPIProcessor(Processor):
    
    def __init__(self, model_url):
        super().__init__()
        self.model_url = model_url

    def process(self, content):
        data = {
            "input_text" : content,
            "beam_size" : 1
        }
        res = requests.post(self.model_url.rstrip("/") + "/generate/", json=data)

        if res.ok:
            out = json.loads(res.text)["out"]

            lis = [h("li")(o) for o in out]
            ul = h("ul")(lis)

            return self.html_render(ul)

        return ""
