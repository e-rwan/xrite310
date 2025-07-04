# constants.py
import os
from utils.plot_utils import ColorChannelSet

UNIQUE_APP_ID = "xrite310_unique_instance"
MEASURES_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), 'measures'))
ICON_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "ressources/kafarddensito.png"))

BAUDRATE = 1200

COLOR_SET = {
            'vcmy': ColorChannelSet('vcmy', ['grey', 'cyan', 'magenta', 'yellow'], 'abcd'),
            'vrgb': ColorChannelSet('vrgb', ['grey', 'red', 'green', 'blue'], 'abcd'),
        }