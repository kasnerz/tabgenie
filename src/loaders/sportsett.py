#!/usr/bin/env python3
from datasets import load_dataset, ReadInstruction
from .data import Cell, Table, TabularDataset, HFTabularDataset


class SportSettBasketball(HFTabularDataset):
    """
    The SportSettBasketball dataset: https://github.com/nlgcat/sport_sett_basketball
    A dataset for generating basketball reports.
    Following up on and overriding the Rotowire dataset.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "GEM/sportsett_basketball"

    def prepare_table(self, split, index):
        entry = self.data[split][index]
        t = Table()
        t.ref = entry["target"]
        game_id = entry['sportsett_id']

        ht = entry["teams"]["home"]
        vt = entry["teams"]["vis"]
        t.title = f"{ht['place']} {ht['name']} vs. {vt['place']} {vt['name']}"

        game_summary = " | ".join([f"{key.title()}: {val}" for key, val in entry["game"].items()])
        t.extra_headers.append(game_summary)
        # TODO next games

        stat_headers = ["AST", "BLK", "DOUBLE", "DREB", "FG3A", "FG3M", "FG3_PCT", "FGA", "FGM", "FG_PCT", "FTA", "FTM", "FT_PCT", "MIN", "OREB", "PF", "PTS", "STL", "TOV", "TREB", "+/-"]

        c = Cell("team")
        c.is_col_header = True
        t.add_cell(c)

        c = Cell("entity")
        c.is_col_header = True
        t.add_cell(c)

        for header in stat_headers:
            c = Cell()
            c.value = header
            c.is_col_header = True
            t.add_cell(c)
        t.save_row()

        for team in ["home", "vis"]:
            c_team = Cell(team)
            c_team.is_row_header = True
            c_team.rowspan = 0
            t.add_cell(c_team)

            line_score = entry["teams"][team]["line_score"]

            for key in line_score.keys():
                c_team.rowspan += 1
                c = Cell(key)
                c.is_row_header = True
                t.add_cell(c)

                for header in stat_headers:
                    val = line_score[key].get(header)
                    c = Cell()
                    c.value = val if val else ""
                    t.add_cell(c)

                t.save_row()

            box_score = entry["teams"][team]["box_score"]

            for item in box_score:
                c_team.rowspan += 1
                c = Cell(item["name"])
                c.is_row_header = True
                t.add_cell(c)

                for header in stat_headers:
                    val = line_score[key].get(header)

                    c = Cell()
                    c.value = val if val else ""
                    t.add_cell(c)
                t.save_row()

        self.tables[split][index] = t
        return t

