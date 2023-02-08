from .cacapo import CACAPO
from .charttotext_s import ChartToTextS
from .dart import DART
from .e2e import E2E
from .eventnarrative import EventNarrative
from .hitab import HiTab
from .logic2text import Logic2Text
from .logicnlg import LogicNLG
from .numericnlg import NumericNLG
from .scigen import SciGen
from .sportsett import SportSettBasketball
from .totto import ToTTo
from .webnlg import WebNLG
from .wikibio import WikiBio
from .wikisql import WikiSQL


DATASET_CLASSES = {
    "cacapo": CACAPO,
    "charttotext-s": ChartToTextS,
    "dart": DART,
    "e2e": E2E,
    "eventnarrative": EventNarrative,
    "hitab": HiTab,
    "logic2text": Logic2Text,
    "logicnlg": LogicNLG,
    "numericnlg": NumericNLG,
    "scigen": SciGen,
    "sportsett": SportSettBasketball,
    "webnlg": WebNLG,
    "wikibio": WikiBio,
    "totto": ToTTo,
    "wikisql": WikiSQL,
}
