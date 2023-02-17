#!/usr/bin/env python3
import logging
import json

import requests
from tinyhtml import h

from ..processing import Processor


logger = logging.getLogger(__name__)


class ModelAPIProcessor(Processor):
    def __init__(self, model_url):
        super().__init__()
        self.model_url = model_url

    def process(self, content):
        data = {"input_text": content, "beam_size": 1}
        timeout = 25

        try:
            logger.debug(f"Calling model API with data: {data}")
            res = requests.post(self.model_url.rstrip("/") + "/generate/", json=data, timeout=timeout)
            if res.ok:
                out = json.loads(res.text)["out"]

                if len(out) == 1:
                    return self.html_render(h("p")(out[0]))

                lis = [h("li")(o) for o in out]
                ul = h("ul")(lis)
                return self.html_render(ul)

        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection to the model API cannot be established.")
            raise ConnectionRefusedError

        except requests.exceptions.ReadTimeout:
            logger.warning(f"Timeout ({timeout}s) reached when calling model API.")
            raise ConnectionRefusedError

        except Exception as e:
            logger.exception(e)
            raise e
