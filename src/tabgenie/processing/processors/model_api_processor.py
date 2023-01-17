#!/usr/bin/env python3
import logging
import json

from ..processing import Processor
from tinyhtml import h
import requests


logger = logging.getLogger(__name__)


class ModelAPIProcessor(Processor):
    def __init__(self, model_url):
        super().__init__()
        self.model_url = model_url

    def process(self, content):
        data = {"input_text": content, "beam_size": 1}

        try:
            res = requests.post(self.model_url.rstrip("/") + "/generate/", json=data)
            if res.ok:
                out = json.loads(res.text)["out"]
                lis = [h("li")(o) for o in out]
                ul = h("ul")(lis)
                return self.html_render(ul)

        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection to the model API cannot be established.")
            raise ConnectionRefusedError

        except Exception as e:
            raise e
