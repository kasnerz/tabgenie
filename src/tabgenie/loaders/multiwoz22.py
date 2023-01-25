from ..structs.data import Cell, Table, HFTabularDataset


def filter_empty_recursive(c):
    """Filter out empty strings, Nones, empty sequences  or dictionaries. Recursively from bottom up. Return None if
    nothing is left."""
    if isinstance(c, list):
        processed = [filter_empty_recursive(i) for i in c]
        processed = [i for i in processed if i is not None]
        processed = processed if processed else None
        return processed
    elif isinstance(c, dict):
        processed = ((k, filter_empty_recursive(v)) for k, v in c.items())
        processed = dict((k, v) for k, v in processed if v is not None)
        processed = processed if processed else None
        return processed
    elif isinstance(c, str):
        return c if c else None
    else:
        return c


class MultiWOZ22(HFTabularDataset):
    """
    The MultiWOZ 2.2 dataset: https://github.com/budzianowski/multiwoz/tree/master/data/MultiWOZ_2.2
    Is multi-domain (train, restaurant, hotel, etc) textual goal-oriented dataset."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "multi_woz_v22"
        self.name = "MultiWOZ_2.2"

    def prepare_table(self, split, table_idx):
        def is_highlighted(i, j):
            """High-lights the all columns for given turn"""
            pass

        entry = self.data[split][table_idx]

        t = Table()
        # No reference
        t.set_generated_output("reference", "")
        t.props["dialogue_id"] = entry["dialogue_id"]
        t.props["services"] = " ".join(entry["services"])
        t.props["title"] = "turns"

        turns = entry["turns"]
        col_names = ["turn_id", "speaker", "utterance", "frames", "dialogue_acts"]
        column_vecs = zip(*[turns[c] for c in col_names])

        for name in col_names:
            t.add_cell(Cell(value=name, is_col_header=True))
        t.save_row()

        for turn_id, spk, utt, frames, diacts in column_vecs:
            for v in [turn_id, spk, utt, frames, diacts]:
                v = filter_empty_recursive(v)
                t.add_cell(Cell(value=str(v)))
            t.save_row()

        return t
