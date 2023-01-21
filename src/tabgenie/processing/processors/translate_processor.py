#!/usr/bin/env python3
import requests

from ..processing import Processor


class TranslateProcessor(Processor):

    @staticmethod
    def translate(s):
        url = "https://lindat.mff.cuni.cz/services/translation/api/v2/languages/"
        data = {
            "src": "en",
            "tgt": "cs",
            "input_text": s
        }
        res = requests.post(url, data=data)
        return res.text.strip()
    
    def process(self, content):
        table = content["dataset_obj"].get_table(split=content["split"], table_idx=content["table_idx"])
        try:
            title = table.props["title"]
        except ValueError:
            return ""
        tr = self.translate(title)
        return self.text2html(tr)
