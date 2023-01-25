from .charttotext_s import ChartToTextS
from .dart import DART
from .e2e import E2E
from .hitab import HiTab
from .logic2text import Logic2Text
from .logicnlg import LogicNLG
from .multiwoz22 import MultiWOZ22
from .numericnlg import NumericNLG
from .scigen import SciGen
from .sportsett import SportSettBasketball
from .totto import ToTTo
from .webnlg import WebNLG
from .wikibio import WikiBio
from .wikisql import WikiSQL


DATASET_CLASSES = {
    "dart": DART,
    "e2e": E2E,
    "hitab": HiTab,
    "charttotext-s": ChartToTextS,
    "logic2text": Logic2Text,
    "logicnlg": LogicNLG,
    "numericnlg": NumericNLG,
    "scigen": SciGen,
    "sportsett": SportSettBasketball,
    "webnlg": WebNLG,
    "wikibio": WikiBio,
    "totto": ToTTo,
    "wikisql": WikiSQL,
    "multiwoz22": MultiWOZ22,
}
