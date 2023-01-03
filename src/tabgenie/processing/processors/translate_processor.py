#!/usr/bin/env python3

from ..processing import Processor
import requests


class TranslateProcessor(Processor):
    def translate(self, s):
        url = "https://lindat.mff.cuni.cz/services/translation/api/v2/languages/"
        data = {
            "src" : "en",
            "tgt" : "cs",
            "input_text" : s
        }
        res = requests.post(url, data=data)
        return res.text.strip()

    
    def process(self, content):
        table = content["dataset_obj"].get_table(split=content["split"], index=content["table_idx"])
        try:
            title = table.props["title"]
        except ValueError:
            return ""
        tr = self.translate(title)
        return self.text2html(tr)