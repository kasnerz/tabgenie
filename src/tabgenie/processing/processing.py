#!/usr/bin/env python3

import lxml.etree
import lxml.html


def get_pipeline_class_by_name(pipeline_name):
    pipeline_mapping = {
        "translate": "TranslatePipeline",
        "reference": "ReferencePipeline",
        "model_local": "ModelLocalPipeline",
        "model_api": "ModelAPIPipeline",
        "graph" : "GraphPipeline",
        "text_ie" : "TextIEPipeline",
        "export" : "ExportPipeline"
    }
    pipeline_module = __import__(
        "pipelines." + pipeline_name + "_pipeline",
        globals=globals(),
        fromlist=[pipeline_mapping[pipeline_name]],
        level=1,
    )
    pipeline_class = getattr(pipeline_module, pipeline_mapping[pipeline_name])
    return pipeline_class


class Processor:
    def process(self, content):
        raise NotImplementedError

    def text2html(self, text):
        return f"<div> {text} </div>"

    def html_render(self, el):
        html = el.render()
        return lxml.etree.tostring(
            lxml.html.fromstring(html), encoding="unicode", pretty_print=True
        )


class Pipeline:
    def __init__(self, cfg):
        self.processors = []
        self.cache = {}
        self.cfg = cfg

    def get_from_cache(self, key):
        return self.cache.get(key, None)

    def save_to_cache(self, key, out):
        self.cache[key] = out

    def to_key(self, pipeline_args):
        key = (pipeline_args["dataset"], pipeline_args["split"], pipeline_args["table_idx"])
        return key

    def run(self, pipeline_args, cache_only=False, force=False):
        key = self.to_key(pipeline_args)
        cache_out = self.get_from_cache(key)

        if cache_only or (not force and cache_out):
            return cache_out

        next_inp = pipeline_args

        for p in self.processors:
            next_inp = p.process(next_inp)

        out = next_inp
        self.save_to_cache(key, out)
        return out


