from .processing import Processor, Pipeline
from tinyhtml import h
import requests

class TranslatePipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [Translator()]


class Translator(Processor):
    def translate(self, s):
        url = "https://lindat.mff.cuni.cz/services/translation/api/v2/languages/"
        data = {
            "src" : "en",
            "tgt" : "cs",
            "input_text" : s
        }
        res = requests.post(url, data=data)
        return res.text.strip()

    
    def process(self, inp):
        table = inp["dataset"].get_table(split=inp["content"]["split"], index=inp["content"]["table_idx"])
        try:
            title = table.props["title"]
        except ValueError:
            return ""
        tr = self.translate(title)
        return self.text2html(tr)