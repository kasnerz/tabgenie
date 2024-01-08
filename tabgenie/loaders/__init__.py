from .ice_hockey import IceHockey
from .gsmarena import GSMArena
from .openweather import OpenWeather
from .owid import OurWorldInData
from .wikidata import Wikidata

DATASET_CLASSES = {
    "ice_hockey": IceHockey,
    "gsmarena": GSMArena,
    "openweather": OpenWeather,
    "owid": OurWorldInData,
    "wikidata": Wikidata,
}
