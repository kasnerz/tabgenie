from .processing import Processor, Pipeline
from tinyhtml import h
import requests

class TranslatePipeline(Pipeline):
    # example pipeline demonstrating pipeline capabilities
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [TranslateProcessor()]



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