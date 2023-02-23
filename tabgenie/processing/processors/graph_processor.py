#!/usr/bin/env python3
import logging

from ..processing import Processor


logger = logging.getLogger(__name__)


class GraphProcessor(Processor):
    def __init__(self):
        super().__init__()

    def process(self, content):
        triples_str = [f'{{subject: "{t[0]}", predicate: "{t[1]}", object: "{t[2]}"}}' for t in content]
        triples_str = ",\n".join(triples_str)

        html = f"""
            <div id="svg-body" class="panel-body"></div>
            <script>
                var triples = [
                        {triples_str}
                    ];
                var rdf_graph_window_height = 300;

                var svg = d3.select("#svg-body").append("svg")
                            .attr("width", 3000)
                            .attr("height", rdf_graph_window_height)
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
