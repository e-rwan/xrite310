# constants.py

import os
from utils.plot_utils import ColorChannelSet
from typing import Final, Dict, List

UNIQUE_APP_ID: Final[str] = "xrite310_unique_instance"

MEASURES_PATH: Final[str] = os.path.normpath(os.path.join(os.path.dirname(__file__), 'measures'))
ICON_PATH: Final[str] = os.path.normpath(os.path.join(os.path.dirname(__file__), "ressources/kafarddensito.png"))

BAUDRATE: Final[int] = 1200

COLOR_SET: Final[Dict[str|None, ColorChannelSet]] = {
    'vcmy': ColorChannelSet('vcmy', ['grey', 'cyan', 'magenta', 'yellow'], 'abcd'),
    'vrgb': ColorChannelSet('vrgb', ['grey', 'red', 'green', 'blue'], 'abcd'),
}

STATS_LABELS: Final[Dict[str, List[str]]] = {
    "ref": ["Gamma ref", "Gamma ref r", "Gamma ref g", "Gamma ref b"],
    "meas": ["Gamma", "Gamma r", "Gamma g", "Gamma b"]
}