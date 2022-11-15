#!/usr/bin/env python3
import json
import os
import re
from .data import Cell, Table, TabularDataset
# from ..utils.text import Detokenizer

class WikiBio(TabularDataset):
    """
    The WikiBio dataset
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = {}
        # self.detokenizer = Detokenizer()

    def normalize(self, s):
        return s.replace("-lrb-", "(").replace("-rrb-", ")")

    def prepare_table(self, split, index):
        entry = self.data[split][index]

        t = Table()
        t.ref = entry["ref"]
        t.title = entry["title"]
        t.url = entry["url"]

        for key, val in entry["table"].items():
            if val == "<none>":
                continue
            c = Cell(key)
            c.is_row_header = True
            t.add_cell(c)

            c = Cell(val)
            t.add_cell(c)

            t.save_row()

        self.tables[split][index] = t
        return t

    def load(self, split, max_examples=None):
        split_name = split if split != "dev" else "valid"
        refs = []
        titles = []
        urls = []
        tables = []

        with open(os.path.join(self.path, f"{split_name}/{split_name}.sent")) as f:
            for i, line in enumerate(f.readlines()):
                if max_examples and i > max_examples: 
                    break
                refs.append(self.normalize(line.rstrip("\n")))

        with open(os.path.join(self.path, f"{split_name}/{split_name}.title")) as f:
            for i, line in enumerate(f.readlines()):
                if max_examples and i > max_examples: 
                    break
                titles.append(self.normalize(line.rstrip("\n")))

        with open(os.path.join(self.path, f"{split_name}/{split_name}.url")) as f:
            for i, line in enumerate(f.readlines()):
                if max_examples and i > max_examples: 
                    break
                urls.append(self.normalize(line.rstrip("\n")))

        with open(os.path.join(self.path, f"{split_name}/{split_name}.box")) as f:
            for i, line in enumerate(f.readlines()):
                if max_examples and i > max_examples: 
                    break
                items = [x.split(":", maxsplit=1) for x in line.rstrip("\n").split("\t")]
                table = {}

                for key, val in items:
                    key_parse = re.search(r"(.*)_\d+", key)
                    val = self.normalize(val)
                    if key_parse:
                        try:
                            table[key_parse.group(1)] += " " + val
                        except KeyError:
                            table[key_parse.group(1)] = val
                        except IndexError:
                            table[key] = val
                    else:
                        table[key] = val
                
                tables.append(table)
                
        for ref, title, url, table in zip(refs, titles, urls, tables):
            self.data[split].append(
                {
                    "table": table,
                    "ref": ref,
                    "title": title,
                    "url": url,
                }
            )
