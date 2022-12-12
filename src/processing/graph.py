#!/usr/bin/env python3
import logging
import numpy as np
import os
import torch
import json
import pytorch_lightning as pl
from nlg.inference import Seq2SeqInferenceModule

from .processing import Processor, Pipeline
from .linearize import LinearizeProcessor

from tinyhtml import h
import requests

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

class GraphPipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [GraphProcessor()]

    def to_key(self, content):
        cells = content.get("cells", None)

        if cells:
            cells = str(set(cells))

        key = (content["dataset"], content["split"], content["table_idx"], cells)
        return key


class GraphProcessor(Processor):
    
    def process(self, content):
        table = content["dataset_obj"].get_table(split=content["split"], index=content["table_idx"])

        triples = []
        for row in table.get_cells():
            t = []
            if row[0].is_header():
                continue
            
            t.append(row[0].value)
            t.append(row[1].value)
            t.append(row[2].value)

            triples.append(t)

        triples_str = [
            f"{{subject: \"{t[0]}\", predicate: \"{t[1]}\", object: \"{t[2]}\"}}" for t in triples
        ]
        triples_str = ",\n".join(triples_str)

        html = f"""
            <div id="svg-body" class="panel-body"></div>
            <script>
                var triples = [
                        {triples_str}
                    ];
                var svg = d3.select("#svg-body").append("svg")
                            .attr("width", 350)
                            .attr("height", 300)
                            ;
                var force = d3.layout.force().size([350, 300]);
                var graph = triplesToGraph(triples);
                update();
            </script>
        """
        return html
