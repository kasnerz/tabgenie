#!/usr/bin/env python3

def get_pipeline_class_by_name(pipeline_name):
    pipeline_mapping = {
        "translate": "TranslatePipeline"
    }
    pipeline_module = __import__(
        pipeline_name,
        globals=globals(),
        fromlist=[pipeline_mapping[pipeline_name]],
        level=1,
    )
    pipeline_class = getattr(pipeline_module, pipeline_mapping[pipeline_name])
    return pipeline_class


class Processor:
    def init(self):
        return

    def process(self, inp):
        raise NotImplementedError

    def text2html(self, text):
        return f"<div> {text} </div>"
        # div = h("div")(text)
        # html = div.render()
        # return lxml.etree.tostring(
        #     lxml.html.fromstring(html), encoding="unicode", pretty_print=True
        # )


class Pipeline:
    def __init__(self):
        self.processors = []
    
    def run(self, inp):
        for p in self.processors:
            p.init()

        next_inp = inp
        for p in self.processors:
            next_inp = p.process(next_inp)

        return next_inp


