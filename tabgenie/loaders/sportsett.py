#!/usr/bin/env python3
from ..structs.data import Cell, Table, HFTabularDataset


class SportSettBasketball(HFTabularDataset):
    """
    The SportSettBasketball dataset: https://github.com/nlgcat/sport_sett_basketball
    A dataset for generating basketball reports.
    Following up on and overriding the Rotowire dataset.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "GEM/sportsett_basketball"
        self.name = "SportSett Basketball"
        self.extra_info = {"license": "MIT"}

    def _next_game_to_str(self, ng):
        if not ng:
            return ""

        return f"{ng['dayname']} {ng['day']} {ng['month']} {ng['year']}, {ng['opponent_place']} {ng['opponent_name']}, {ng['stadium']}, {ng['city']}"

    def prepare_table(self, entry):
        t = Table()
        t.props["references"] = [entry["target"]]

        ht = entry["teams"]["home"]
        vt = entry["teams"]["vis"]

        t.props["game_id"] = entry["sportsett_id"]
        t.props["ht_name"] = ht.get("name", "")
        t.props["ht_place"] = ht.get("place", "")
        t.props["ht_conference"] = ht.get("conference", "")
        t.props["ht_conference_standing"] = ht.get("conference_standing", "")
        t.props["ht_division"] = ht.get("division", "")
        t.props["ht_game_number"] = ht.get("game_number", "")
        t.props["ht_losses"] = ht.get("losses", "")
        t.props["ht_wins"] = ht.get("wins", "")
        t.props["ht_next_game_id"] = (ht.get("next_game_id", ""),)
        t.props["ht_next_game"] = self._next_game_to_str(ht.get("next_game", ""))
        t.props["vt_name"] = vt.get("name", "")
        t.props["vt_place"] = vt.get("place", "")
        t.props["vt_conference"] = vt.get("conference", "")
        t.props["vt_conference_standing"] = vt.get("conference_standing", "")
        t.props["vt_division"] = vt.get("division", "")
        t.props["vt_game_number"] = vt.get("game_number", "")
        t.props["vt_losses"] = vt.get("losses", "")
        t.props["vt_wins"] = vt.get("wins", "")
        t.props["vt_next_game_id"] = (vt.get("next_game_id", ""),)
        t.props["vt_next_game"] = self._next_game_to_str(vt.get("next_game", ""))

        for key, val in entry["game"].items():
            t.props[key] = val

        stat_headers = [
            "AST",
            "BLK",
            "DOUBLE",
            "DREB",
            "FG3A",
            "FG3M",
            "FG3_PCT",
            "FGA",
            "FGM",
            "FG_PCT",
            "FTA",
            "FTM",
            "FT_PCT",
            "MIN",
            "OREB",
            "PF",
            "PTS",
            "STL",
            "TOV",
            "TREB",
            "+/-",
        ]

        c = Cell("team")
        c.is_col_header = True
        t.add_cell(c)

        c = Cell("entity")
        c.is_col_header = True
        t.add_cell(c)

        c = Cell("period")
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

            c_game = Cell("all")
            c_game.is_row_header = True
            c_game.rowspan = 0
            t.add_cell(c_game)

            for key in line_score.keys():
                c_team.rowspan += 1
                c_game.rowspan += 1
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
                c_player = Cell(item["name"])
                c_player.is_row_header = True
                c_player.rowspan = 0
                t.add_cell(c_player)

                for key in line_score.keys():
                    c_team.rowspan += 1
                    c_player.rowspan += 1

                    c_period = Cell(key)
                    c_period.is_row_header = True
                    t.add_cell(c_period)

                    for header in stat_headers:
                        val = line_score[key].get(header)
                        c = Cell()
                        c.value = val if val else ""
                        t.add_cell(c)

                    t.save_row()

        return t
