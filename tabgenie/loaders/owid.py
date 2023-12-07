#!/usr/bin/env python3
from ..structs.data import Cell, Table, D2TDataset
import logging
logger = logging.getLogger(__name__)

import sys
sys.path.append('../')
from dataset import OurWorldInData as OurWorldInDataDataset

class OurWorldInData(D2TDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dataset = OurWorldInDataDataset(base_path="..")

    def _load_split(self, split):
        self.data[split] = self.dataset.get_data(split)
