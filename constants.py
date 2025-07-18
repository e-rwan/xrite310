# constants.py

import os
import sys
from utils.plot_utils import ColorChannelSet
from typing import Final, Dict, List
from pathlib import Path


def get_base_path() -> Path:
    if getattr(sys, 'frozen', False):
        # Exécutable compilé (PyInstaller)
        return Path(sys.executable).parent
    else:
        # Script lancé en mode normal
        return Path(__file__).resolve().parent

BASE_PATH: Final[Path] = get_base_path()

MEASURES_PATH: Final[str] = str(BASE_PATH / "measures")
ICON_PATH: Final[str] = str(BASE_PATH / "ressources" / "kafarddensito.png")

DOC_PATH: Final[str] = str(BASE_PATH / "docs")
DOC_XRITEMANUAL_PATH: Final[str] = str(BASE_PATH / "docs" / "310-42_310_Densitometer_Operation_Manual_en.pdf")
DOC_MANUAL_PATH: Final[str] = str(BASE_PATH / "docs" / "X-Rite 310 App - user manual.md")


UNIQUE_APP_ID: Final[str] = "xrite310_unique_instance"

BAUDRATE: Final[int] = 1200

COLOR_SET: Final[Dict[str|None, ColorChannelSet]] = {
    'vcmy': ColorChannelSet('vcmy', ['grey', 'cyan', 'magenta', 'yellow'], 'abcd'),
    'vrgb': ColorChannelSet('vrgb', ['grey', 'red', 'green', 'blue'], 'abcd'),
}

STATS_LABELS: Final[Dict[str, List[str]]] = {
    "ref": ["Gamma ref", "Gamma ref r", "Gamma ref g", "Gamma ref b"],
    "meas": ["Gamma", "Gamma r", "Gamma g", "Gamma b"]
}