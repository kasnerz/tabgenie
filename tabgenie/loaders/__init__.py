from .basketball import Basketball
from .gsmarena import GSMArena
from .openweather import OpenWeather
from .owid import OurWorldInData
from .wikidata import Wikidata

DATASET_CLASSES = {
    "basketball": Basketball,
    "gsmarena": GSMArena,
    "openweather": OpenWeather,
    "owid": OurWorldInData,
    "wikidata": Wikidata,
}
