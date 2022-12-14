#!/usr/bin/env python3
import logging
import os
import json

from .processing import Processor, Pipeline

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

    def __init__(self):
        super().__init__()
        # self.width = 350
        # self.height = 400
    
    def process(self, content):
        dataset = content["dataset_obj"]
        triples = dataset.export_table(split=content["split"], table_idx=content["table_idx"], cell_ids=content["cells"], export_format="triples")

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
                            .attr("width", 3000)
                            .attr("height", 400)
                            .call(d3.zoom().on("zoom", function () {{
                                svg.attr("transform", d3.event.transform)
                                }})).append("g")
                            ;
                var graph = triplesToGraph(triples);
                var simulation = update_graph();
            </script>
        """
        return html


# .attr("preserveAspectRatio", "xMinYMin meet")
                            # .attr("viewBox", "0 0 {self.width} {self.height}")